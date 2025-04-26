from broker import get_cash, get_price, get_position, buy, sell
from notifier import notify
from risk_manager import RiskManager
from market_monitor import MarketMonitor
from config import *
import time
import datetime
import pytz
import numpy as np
import yfinance as yf

# 初始化风险管理器和市场监控器
risk_manager = RiskManager()
market_monitor = MarketMonitor()

# 为每个股票创建状态字典
states = {symbol: {
    "layers": 0,
    "entry_price": None,
    "last_check_time": None,
} for symbol in TARGETS}

# 全局状态
global_state = {
    "max_equity": 0,
    "current_drawdown": 0
}


def buy_with_percent_cash(symbol, percent):
    price = get_price(symbol)

    # 根据恐慌贪婪指数调整仓位大小
    adjusted_percent = market_monitor.adjust_position_size(percent)

    # 应用股票权重
    symbol_weight = TARGET_WEIGHTS.get(symbol, 1.0 / len(TARGETS))
    adjusted_percent *= symbol_weight

    invest_cash = get_cash() * adjusted_percent

    # 应用风险管理检查
    raw_qty = int(invest_cash // price)
    qty = risk_manager.check_position_size(symbol, price, raw_qty)

    if qty > 0:
        buy(symbol, qty)
        # 更新风险管理器中的持仓数据
        risk_manager.update_position(symbol, price, qty)
        return {
            "action": "buy",
            "symbol": symbol,
            "qty": qty,
            "price": price
        }
    return None


def calculate_atr(symbol, period=14):
    """计算ATR (平均真实波幅)"""
    # 这里应该获取历史数据，但简化起见，使用估计值
    # 实际使用时应当接入历史价格API获取真实ATR
    price = get_price(symbol)

    # 为不同股票设置不同的波动率估计
    volatility_estimates = {
        "SOXL": 0.04,  # 杠杆ETF波动率较高
        "MSTU": 0.035,  # 杠杆ETF波动率高
        "NVDA": 0.025  # 个股波动率相对较低
    }

    volatility = price * volatility_estimates.get(symbol, 0.02)
    return volatility

def calculate_ma_crossover(symbol, short_period=9, long_period=20):
    """
    计算移动平均线金叉死叉信号

    返回:
    1: 金叉信号（买入）
    -1: 死叉信号（卖出）
    0: 无信号
    """
    try:
        # 获取历史数据
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="3mo")

        if len(data) < max(short_period, long_period) + 2:
            return 0  # 数据不足以计算

        # 计算移动平均线
        data[f'MA{short_period}'] = data['Close'].rolling(window=short_period).mean()
        data[f'MA{long_period}'] = data['Close'].rolling(window=long_period).mean()

        # 获取最新的和前一天的均线数据
        current_short_ma = data[f'MA{short_period}'].iloc[-1]
        current_long_ma = data[f'MA{long_period}'].iloc[-1]
        prev_short_ma = data[f'MA{short_period}'].iloc[-2]
        prev_long_ma = data[f'MA{long_period}'].iloc[-2]

        # 判断金叉
        if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma:
            return 1

        # 判断死叉
        if prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma:
            return -1

        return 0
    except Exception as e:
        print(f"计算均线交叉出错: {e}")
        return 0


def process_symbol(symbol):
    # 获取当前价格和持仓
    price = get_price(symbol)
    entry, qty = get_position(symbol)

    # 获取恐慌贪婪指数信号
    fg_signal, fg_value = market_monitor.get_fear_greed_signal()

    # 获取移动平均线交叉信号 (9日/20日)
    ma_signal = calculate_ma_crossover(symbol)

    state = states[symbol]

    # 返回结果
    result = None

    if qty == 0:
        # 检查风险管理条件
        if risk_manager.check_daily_loss_limit():
            notify(f"已达到每日亏损限制，暂停交易")
            return None

        # 金叉信号增强买入条件
        if ma_signal == 1:
            notify(f"{symbol} 检测到金叉信号，考虑买入")

            # 恐慌贪婪指数与金叉信号结合
            if USE_FEAR_GREED_INDEX and fg_signal in ["BUY", "STRONG_BUY"]:
                # 恐慌区域+金叉，强买入信号
                buy_size = LAYER_SIZE * 1.2  # 增加买入比例
                if fg_signal == "STRONG_BUY":
                    buy_size *= EXTREME_FEAR_BOOST
                    notify(f"检测到极度恐慌指数: {fg_value}与金叉共振，大幅增加{symbol}买入仓位")

                result = buy_with_percent_cash(symbol, buy_size)
                if result:
                    state["layers"] = 1
                    state["entry_price"] = price
                    notify(f"金叉+恐慌指数触发买入 {symbol} {result['qty']} 股，价格 {price:.2f}，恐慌指数: {fg_value}")
            else:
                # 仅金叉信号也买入，但比例较小
                result = buy_with_percent_cash(symbol, LAYER_SIZE)
                if result:
                    state["layers"] = 1
                    state["entry_price"] = price
                    notify(f"金叉信号触发买入 {symbol} {result['qty']} 股，价格 {price:.2f}")

        # 原有买入逻辑，但优先级较低
        elif USE_FEAR_GREED_INDEX and fg_signal in ["BUY", "STRONG_BUY"]:
            # 恐慌区域，是买入信号
            buy_size = LAYER_SIZE
            if fg_signal == "STRONG_BUY":
                buy_size *= EXTREME_FEAR_BOOST
                notify(f"检测到极度恐慌指数: {fg_value}，增加买入{symbol}仓位")

            result = buy_with_percent_cash(symbol, buy_size)
            if result:
                state["layers"] = 1
                state["entry_price"] = price
                notify(f"恐慌指数触发买入 {symbol} {result['qty']} 股，价格 {price:.2f}，恐慌指数: {fg_value}")
        else:
            # 常规策略买入（优先级最低）
            result = buy_with_percent_cash(symbol, LAYER_SIZE * 0.8)  # 降低常规买入比例
            if result:
                state["layers"] = 1
                state["entry_price"] = price
                notify(f"首次建仓 {symbol} {result['qty']} 股，价格 {price:.2f}")
    else:
        # 已持仓，判断止盈止损
        change = (price - entry) / entry

        # 死叉信号增强卖出条件
        if ma_signal == -1:
            notify(f"{symbol} 检测到死叉信号，考虑卖出")

            # 如果已经有盈利或在贪婪区域，死叉信号触发卖出
            if change > 0 or (USE_FEAR_GREED_INDEX and fg_signal in ["SELL", "STRONG_SELL"]):
                sell(symbol, qty)
                risk_manager.update_position(symbol, 0, -qty)
                notify(f"死叉信号触发卖出 {symbol} 全部 {qty} 股，价格 {price:.2f}" +
                       (f"，贪婪指数: {fg_value}" if USE_FEAR_GREED_INDEX and fg_signal in ["SELL",
                                                                                           "STRONG_SELL"] else ""))
                state["layers"] = 0
                return {
                    "action": "sell",
                    "symbol": symbol,
                    "qty": qty,
                    "price": price
                }

        # 原有的恐慌贪婪指数卖出逻辑
        if USE_FEAR_GREED_INDEX and fg_signal in ["SELL", "STRONG_SELL"]:
            # 在贪婪区域，是卖出信号
            if fg_signal == "STRONG_SELL" or change > 0:  # 极度贪婪或已有盈利
                sell(symbol, qty)
                risk_manager.update_position(symbol, 0, -qty)
                notify(f"贪婪指数触发卖出 {symbol} 全部 {qty} 股，价格 {price:.2f}，贪婪指数: {fg_value}")
                state["layers"] = 0
                return {
                    "action": "sell",
                    "symbol": symbol,
                    "qty": qty,
                    "price": price
                }

        # ATR止损检查
        if USE_ATR_STOP:
            atr = calculate_atr(symbol)
            atr_stop_price = entry - (atr * ATR_MULTIPLIER)
            if price <= atr_stop_price:
                sell(symbol, qty)
                # 记录实现的亏损
                realized_loss = (price - entry) * qty
                risk_manager.check_daily_loss_limit(realized_loss)
                risk_manager.update_position(symbol, 0, -qty)
                notify(f"ATR止损卖出 {symbol} 全部 {qty} 股，价格 {price:.2f}")
                state["layers"] = 0
                return {
                    "action": "sell",
                    "symbol": symbol,
                    "qty": qty,
                    "price": price
                }

        # 常规止损检查
        if change <= STOP_LOSS:
            sell(symbol, qty)
            # 记录实现的亏损
            realized_loss = (price - entry) * qty
            risk_manager.check_daily_loss_limit(realized_loss)
            risk_manager.update_position(symbol, 0, -qty)
            notify(f"止损卖出 {symbol} 全部 {qty} 股，亏损 {change:.2%}")
            state["layers"] = 0
            return {
                "action": "sell",
                "symbol": symbol,
                "qty": qty,
                "price": price
            }

        # 止盈检查
        elif change >= TAKE_PROFIT:
            sell(symbol, qty)
            risk_manager.update_position(symbol, 0, -qty)
            notify(f"止盈卖出 {symbol} 全部 {qty} 股，盈利 {change:.2%}")
            state["layers"] = 0
            return {
                "action": "sell",
                "symbol": symbol,
                "qty": qty,
                "price": price
            }

        # 跟踪止损检查
        if state["entry_price"] is not None and price > state["entry_price"]:
            highest_price = max(price, risk_manager.position_data.get(symbol, {}).get('highest_price', price))
            risk_manager.position_data.setdefault(symbol, {})['highest_price'] = highest_price

            # 如果从高点回落超过跟踪止损比例，则卖出
            if (highest_price - price) / highest_price >= TRAILING_STOP:
                sell(symbol, qty)
                risk_manager.update_position(symbol, 0, -qty)
                notify(f"跟踪止损卖出 {symbol} 全部 {qty} 股，从高点 {highest_price:.2f} 回落至 {price:.2f}")
                state["layers"] = 0
                return {
                    "action": "sell",
                    "symbol": symbol,
                    "qty": qty,
                    "price": price
                }

        # 判断是否加仓
        if state["entry_price"] is not None:
            drop = (price - state["entry_price"]) / state["entry_price"]
            if drop <= -LAYER_DROP * state["layers"] and state["layers"] < MAX_LAYERS:
                # 检查是否可以根据风险管理规则加仓
                position_risk = risk_manager.calculate_position_risk(symbol)
                if position_risk < -0.03:  # 如果当前亏损已经超过3%
                    notify(f"{symbol} 当前亏损已超过安全线，暂不加仓")
                    return None

                # 金叉信号增强加仓逻辑
                add_amount_multiplier = 1.0
                if ma_signal == 1:
                    add_amount_multiplier = 1.3  # 有金叉时增加加仓力度
                    notify(f"{symbol} 检测到金叉信号，增强加仓力度")

                # 检查恐慌贪婪指数
                if USE_FEAR_GREED_INDEX:
                    buy_size = LAYER_SIZE * add_amount_multiplier

                    # 在恐慌区域加大仓位
                    if fg_signal == "STRONG_BUY":
                        buy_size *= EXTREME_FEAR_BOOST
                        notify(f"检测到极度恐慌指数: {fg_value}，增加{symbol}加仓比例")
                    elif fg_signal == "BUY":
                        buy_size *= 1.2
                    # 在贪婪区域减少仓位
                    elif fg_signal == "SELL":
                        buy_size *= 0.8
                    elif fg_signal == "STRONG_SELL":
                        notify(f"检测到极度贪婪指数: {fg_value}，暂停{symbol}加仓")
                        return None

                    result = buy_with_percent_cash(symbol, buy_size)
                else:
                    result = buy_with_percent_cash(symbol, LAYER_SIZE * add_amount_multiplier)

                if result:
                    risk_manager.update_position(symbol, price, result["qty"])
                    state["layers"] += 1
                    notify(f"{symbol} 触发加仓，第 {state['layers']} 层，加 {result['qty']} 股，当前价格 {price:.2f}")
        else:
            # 如果 entry_price 不存在，更新为当前价格
            state["entry_price"] = price

    return result


def run_strategy():
    """运行所有股票的交易策略"""
    # 检查是否在交易时段
    if not risk_manager.check_market_hours():
        return None

    # 更新账户总值记录以计算回撤
    current_equity = risk_manager.get_total_equity()
    global_state["max_equity"] = max(global_state["max_equity"], current_equity)
    global_state["current_drawdown"] = (global_state["max_equity"] - current_equity) / global_state["max_equity"] if \
    global_state["max_equity"] > 0 else 0

    # 检查最大回撤限制
    if global_state["current_drawdown"] > MAX_DRAWDOWN:
        notify(f"警告: 当前回撤 {global_state['current_drawdown']:.2%} 超过限制 {MAX_DRAWDOWN:.2%}")

    # 为每个股票执行策略
    results = []
    for symbol in TARGETS:
        try:
            result = process_symbol(symbol)
            if result:
                results.append(result)
        except Exception as e:
            notify(f"处理 {symbol} 时出错: {str(e)}")

    return results if results else None
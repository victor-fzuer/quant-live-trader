import time
import datetime
import pytz
from strategy import run_strategy
from risk_manager import RiskManager
from market_monitor import MarketMonitor
from notifier import notify
from chart_generator import ChartGenerator
from dotenv import load_dotenv
from config import *
import traceback
import os

load_dotenv()

# 存储交易记录和资产历史
transactions = []
balance_history = []


def update_transaction_history(action, symbol, qty, price, date=None):
    if date is None:
        date = datetime.datetime.now()

    transaction = {
        'date': date,
        'action': action,
        'symbol': symbol,
        'qty': qty,
        'price': price
    }

    transactions.append(transaction)


def update_balance_history(balance):
    now = datetime.datetime.now()
    balance_history.append((now, balance))


def main():
    risk_manager = RiskManager()
    market_monitor = MarketMonitor()
    chart_generator = ChartGenerator()

    # 记录启动信息
    notify(f"交易系统已启动，交易标的: {', '.join(TARGETS)}")

    # 获取并记录初始恐慌贪婪指数
    if USE_FEAR_GREED_INDEX:
        fg_signal, fg_value = market_monitor.get_fear_greed_signal()
        if fg_value:
            notify(f"当前恐慌贪婪指数: {fg_value} ({market_monitor.fear_greed_index.get_rating_from_score(fg_value)})")

            # 生成恐慌贪婪指数历史图表
            try:
                fg_chart = chart_generator.plot_fear_greed_history()
                if fg_chart:
                    notify(f"已生成恐慌贪婪指数历史图表: {fg_chart}")
            except Exception as e:
                print(f"生成恐慌贪婪指数图表出错: {e}")

    # 生成初始价格图表
    try:
        # 为每只股票生成单独的价格图表
        for symbol in TARGETS:
            price_chart = chart_generator.plot_price_with_fear_greed(symbol)
            if price_chart:
                notify(f"已生成{symbol}价格和恐慌贪婪指数图表: {price_chart}")

        # 生成多股票比较图表
        multi_chart = chart_generator.plot_multiple_stocks(TARGETS)
        if multi_chart:
            notify(f"已生成多股票比较图表: {multi_chart}")
    except Exception as e:
        print(f"生成价格图表出错: {e}")

    # 每日图表生成时间记录
    last_chart_date = datetime.datetime.now().date()

    while True:
        try:
            # 检查市场是否开放
            if not risk_manager.check_market_hours():
                # 市场休市，每小时检查一次
                now = datetime.datetime.now(pytz.timezone('US/Eastern'))
                print(f"市场休市中，当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

                # 生成日图表（如果是新的一天）
                today = now.date()
                if today > last_chart_date and len(balance_history) > 0:
                    try:
                        portfolio_chart = chart_generator.plot_portfolio_performance(transactions, balance_history)

                        # 为每只股票生成价格图表
                        for symbol in TARGETS:
                            price_chart = chart_generator.plot_price_with_fear_greed(symbol)
                            if price_chart:
                                notify(f"已生成{symbol}每日价格图表: {price_chart}")

                        # 生成多股票比较图表
                        multi_chart = chart_generator.plot_multiple_stocks(TARGETS)

                        if portfolio_chart:
                            notify(f"已生成每日投资组合表现图表: {portfolio_chart}")
                        if multi_chart:
                            notify(f"已生成每日多股票比较图表: {multi_chart}")

                        last_chart_date = today
                    except Exception as e:
                        print(f"生成每日图表出错: {e}")

                time.sleep(3600)
                continue

            # 获取市场状况
            market_status, market_data = market_monitor.check_market_conditions()
            print(f"市场状况: {market_status}")

            # 获取恐慌贪婪指数情况
            if USE_FEAR_GREED_INDEX and 'fear_greed' in market_data:
                fg_value = market_data['fear_greed']['value']
                fg_rating = market_data['fear_greed']['rating']
                print(f"恐慌贪婪指数: {fg_value} ({fg_rating})")

                # 如果恐慌或贪婪指数特别极端，发送通知
                if fg_value <= 20 or fg_value >= 80:
                    notify(f"极端市场情绪: 恐慌贪婪指数为 {fg_value} ({fg_rating})")

            # 运行交易策略
            results = run_strategy()

            # 如果策略返回了交易信息，更新历史记录
            if results:
                for result in results:
                    if isinstance(result, dict) and 'action' in result:
                        update_transaction_history(
                            result['action'],
                            result['symbol'],
                            result['qty'],
                            result['price']
                        )

            # 更新资产历史
            try:
                current_equity = risk_manager.get_total_equity()
                update_balance_history(current_equity)
            except Exception as e:
                print(f"更新资产历史出错: {e}")

            # 控制检查频率，防止API请求过于频繁
            # 正常交易时段每5分钟检查一次
            time.sleep(300)

        except Exception as e:
            error_msg = f"系统错误: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            notify(f"交易系统出错: {str(e)}")
            time.sleep(300)  # 发生错误后暂停5分钟


if __name__ == "__main__":
    main()
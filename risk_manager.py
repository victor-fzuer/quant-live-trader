import time
import datetime
import pytz
from broker import get_cash, get_price, get_position
from config import *


class RiskManager:
    def __init__(self):
        self.position_data = {}
        self.daily_loss_limit = DAILY_LOSS_LIMIT
        self.max_position_size = MAX_POSITION_SIZE
        self.max_concentration = MAX_CONCENTRATION
        self.daily_loss = 0
        self.daily_reset_time = None

    def update_position(self, symbol, entry_price=None, qty=0):
        """更新持仓数据"""
        if symbol not in self.position_data:
            self.position_data[symbol] = {
                'entry_price': entry_price,
                'qty': qty,
                'highest_price': entry_price,
                'cost_basis': entry_price * qty if entry_price and qty else 0
            }
        else:
            position = self.position_data[symbol]
            if qty > 0 and entry_price:
                # 计算新的平均成本
                old_cost = position['cost_basis']
                new_cost = entry_price * qty
                position['cost_basis'] = old_cost + new_cost
                position['qty'] += qty
                position['entry_price'] = position['cost_basis'] / position['qty'] if position['qty'] > 0 else 0
            elif qty < 0:
                # 减仓或清仓
                position['qty'] += qty  # qty为负值
                if position['qty'] <= 0:
                    position['qty'] = 0
                    position['cost_basis'] = 0
                    position['entry_price'] = 0

    def check_position_size(self, symbol, price, qty):
        """检查持仓大小是否超过限制"""
        total_equity = self.get_total_equity()
        new_position_value = price * qty

        # 检查单个头寸大小限制
        if new_position_value / total_equity > self.max_position_size:
            max_qty = int((total_equity * self.max_position_size) / price)
            return max_qty

        # 检查现有持仓的集中度
        total_position_value = 0
        for sym, pos in self.position_data.items():
            if pos['qty'] > 0:
                current_price = get_price(sym)
                total_position_value += current_price * pos['qty']

        if (total_position_value + new_position_value) / total_equity > self.max_concentration:
            max_additional = (total_equity * self.max_concentration) - total_position_value
            max_qty = int(max_additional / price)
            return max_qty if max_qty > 0 else 0

        return qty

    def check_daily_loss_limit(self, realized_loss=0):
        """检查当日亏损是否超过限制"""
        # 检查是否需要重置每日计数
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        if self.daily_reset_time is None or now.date() > self.daily_reset_time.date():
            self.daily_loss = 0
            self.daily_reset_time = now

        # 更新当日亏损
        self.daily_loss += realized_loss

        # 检查是否超过限制
        if self.daily_loss >= self.daily_loss_limit:
            return True
        return False

    def get_total_equity(self):
        """获取总资产价值"""
        cash = get_cash()
        position_value = 0
        for symbol, pos in self.position_data.items():
            if pos['qty'] > 0:
                current_price = get_price(symbol)
                position_value += current_price * pos['qty']
        return cash + position_value

    def calculate_position_risk(self, symbol):
        """计算特定持仓的风险值"""
        if symbol not in self.position_data or self.position_data[symbol]['qty'] <= 0:
            return 0

        position = self.position_data[symbol]
        current_price = get_price(symbol)
        unrealized_pnl = (current_price - position['entry_price']) * position['qty']
        position_value = current_price * position['qty']

        # 风险值 = 未实现盈亏/持仓价值
        risk = unrealized_pnl / position_value if position_value > 0 else 0
        return risk

    def check_market_hours(self):
        """检查当前是否在交易时段"""
        now = datetime.datetime.now(pytz.timezone('US/Eastern'))
        is_weekend = now.weekday() >= 5  # 5=周六, 6=周日

        if is_weekend:
            return False

        market_open = datetime.time(9, 30)
        market_close = datetime.time(16, 0)

        if TRADE_EXTENDED_HOURS:
            # 盘前9:00到盘后20:00
            market_open = datetime.time(9, 0)
            market_close = datetime.time(20, 0)

        current_time = now.time()

        return market_open <= current_time <= market_close
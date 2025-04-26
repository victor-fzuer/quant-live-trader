import datetime
import pytz
import yfinance as yf
import numpy as np
from config import *
from market_sentiment import FearGreedIndex


class MarketMonitor:
    def __init__(self):
        self.market_indexes = ["SPY", "QQQ", "VIX"]
        self.cached_data = {}
        self.cache_time = None
        self.cache_expiry = 300  # 缓存5分钟
        self.fear_greed_index = FearGreedIndex()

    def _get_market_data(self):
        """获取市场指数数据"""
        now = datetime.datetime.now()

        # 如果缓存有效，使用缓存
        if self.cache_time and (now - self.cache_time).total_seconds() < self.cache_expiry:
            return self.cached_data

        data = {}
        for idx in self.market_indexes:
            try:
                ticker = yf.Ticker(idx)
                hist = ticker.history(period="2d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Close'].iloc[-2]
                    change = (current - prev) / prev
                    data[idx] = {
                        'price': current,
                        'change': change
                    }
            except Exception as e:
                print(f"获取{idx}数据出错: {e}")

        # 获取恐慌贪婪指数
        if USE_FEAR_GREED_INDEX:
            fear_greed_value, fear_greed_rating = self.fear_greed_index.get_fear_greed_index()
            if fear_greed_value is not None:
                data['fear_greed'] = {
                    'value': fear_greed_value,
                    'rating': fear_greed_rating
                }

        # 更新缓存
        self.cached_data = data
        self.cache_time = now
        return data

    def check_market_conditions(self):
        """检查市场状况，返回市场评估结果"""
        data = self._get_market_data()

        # 市场评估变量
        market_strength = 0

        # 评估SPY (S&P 500 ETF)
        if 'SPY' in data:
            spy_change = data['SPY']['change']
            if spy_change > 0.01:  # 上涨超过1%
                market_strength += 1
            elif spy_change < -0.01:  # 下跌超过1%
                market_strength -= 1

        # 评估QQQ (纳斯达克100 ETF)
        if 'QQQ' in data:
            qqq_change = data['QQQ']['change']
            if qqq_change > 0.01:
                market_strength += 1
            elif qqq_change < -0.01:
                market_strength -= 1

        # 评估VIX (波动率指数)
        if 'VIX' in data:
            vix = data['VIX']['price']
            if vix > 30:  # 高波动性
                market_strength -= 1
            elif vix < 15:  # 低波动性
                market_strength += 1

        # 评估恐慌贪婪指数
        if 'fear_greed' in data:
            fg_value = data['fear_greed']['value']
            if fg_value <= 25:  # 极度恐慌
                market_strength += 2  # 极度恐慌是买入信号，市场趋向反转
            elif fg_value <= 40:  # 恐慌
                market_strength += 1
            elif fg_value >= 80:  # 极度贪婪
                market_strength -= 2  # 极度贪婪是卖出信号，市场趋向反转
            elif fg_value >= 60:  # 贪婪
                market_strength -= 1

        # 返回市场状况
        if market_strength >= 2:
            return "强势", data
        elif market_strength <= -2:
            return "弱势", data
        else:
            return "中性", data

    def adjust_position_size(self, base_size):
        """根据市场状况调整仓位大小"""
        market_status, data = self.check_market_conditions()
        multiplier = 1.0

        # 根据恐慌贪婪指数调整仓位
        if USE_FEAR_GREED_INDEX and 'fear_greed' in data:
            fg_value = data['fear_greed']['value']

            if fg_value <= 20:  # 极度恐慌
                multiplier *= EXTREME_FEAR_BOOST  # 极度恐慌时增加仓位
            elif fg_value <= FEAR_BUY_THRESHOLD:  # 恐慌
                multiplier *= 1.2  # 恐慌时小幅增加仓位
            elif fg_value >= 80:  # 极度贪婪
                multiplier *= EXTREME_GREED_REDUCE  # 极度贪婪时减少仓位
            elif fg_value >= GREED_SELL_THRESHOLD:  # 贪婪
                multiplier *= 0.8  # 贪婪时小幅减少仓位

        # 根据市场状况进一步调整
        if market_status == "强势":
            multiplier *= 1.2  # 市场强势时增加20%仓位
        elif market_status == "弱势":
            multiplier *= 0.8  # 市场弱势时减少20%仓位

        return base_size * multiplier

    def get_fear_greed_signal(self):
        """获取恐慌贪婪指数信号"""
        if not USE_FEAR_GREED_INDEX:
            return "NEUTRAL", None

        return self.fear_greed_index.get_buy_sell_signal()
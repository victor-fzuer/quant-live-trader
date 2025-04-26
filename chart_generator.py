import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import yfinance as yf
import os
from datetime import datetime, timedelta
from market_sentiment import FearGreedIndex
from config import TARGETS

TARGET_ETF = TARGETS[0] if TARGETS else "SOXL"


class ChartGenerator:
    def __init__(self, output_dir="charts"):
        self.output_dir = output_dir
        self.fear_greed_index = FearGreedIndex()

        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def get_historical_data(self, symbol, period="6mo"):
        """获取历史价格数据"""
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        return data

    def plot_price_with_fear_greed(self, symbol, period="6mo"):
        """绘制价格图表和恐慌贪婪指数"""
        # 获取价格数据
        price_data = self.get_historical_data(symbol, period)

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

        # 绘制价格图
        ax1.plot(price_data.index, price_data['Close'], 'b-', label=f'{symbol} Price')
        ax1.set_title(f'{symbol} Price Chart with Fear & Greed Index')
        ax1.set_ylabel('Price ($)')
        ax1.grid(True)
        ax1.legend(loc='upper left')

        # 添加20日和50日移动平均线
        price_data['MA20'] = price_data['Close'].rolling(window=20).mean()
        price_data['MA50'] = price_data['Close'].rolling(window=50).mean()
        ax1.plot(price_data.index, price_data['MA20'], 'r--', label='20-day MA')
        ax1.plot(price_data.index, price_data['MA50'], 'g--', label='50-day MA')

        # 模拟恐慌贪婪指数历史数据（通常需要额外API）
        # 这里使用简化模型基于价格波动模拟指数
        dates = []
        values = []

        # 模拟历史恐慌贪婪指数
        # 实际应用中应当从API获取真实历史数据
        for i in range(len(price_data) - 20):
            date = price_data.index[i + 20]
            price_change = (price_data['Close'][i + 20] - price_data['Close'][i]) / price_data['Close'][i]
            volatility = price_data['Close'][i:i + 20].pct_change().std() * np.sqrt(20)

            # 基于价格变化和波动率的简单模型
            # 实际恐慌贪婪指数考虑更多因素
            simulated_fg = 50 + (price_change * 200) - (volatility * 200)
            simulated_fg = max(0, min(100, simulated_fg))

            dates.append(date)
            values.append(simulated_fg)

        # 获取当前恐慌贪婪指数
        current_fg, _ = self.fear_greed_index.get_fear_greed_index()
        if current_fg:
            dates.append(price_data.index[-1])
            values.append(current_fg)

        # 绘制恐慌贪婪指数
        scatter = ax2.scatter(dates, values, c=values, cmap='RdYlGn', vmin=0, vmax=100, s=30)
        ax2.set_ylabel('Fear & Greed Index')
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        ax2.axhline(y=25, color='r', linestyle='--', alpha=0.5)  # 极度恐慌线
        ax2.axhline(y=75, color='g', linestyle='--', alpha=0.5)  # 极度贪婪线

        # 添加颜色条
        cbar = fig.colorbar(scatter, ax=ax2)
        cbar.set_label('Fear & Greed Index')

        # 添加恐慌贪婪区域标签
        ax2.text(dates[0], 12.5, 'Extreme Fear', color='r', ha='left')
        ax2.text(dates[0], 50, 'Neutral', color='gray', ha='left')
        ax2.text(dates[0], 87.5, 'Extreme Greed', color='g', ha='left')

        # 设置日期格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/{symbol}_price_fg_{timestamp}.png"
        plt.savefig(filename)
        plt.close()

        return filename

    def plot_multiple_stocks(self, symbols=None, period="6mo"):
        """绘制多只股票的价格对比图"""
        if symbols is None:
            symbols = TARGETS

        # 获取价格数据
        data = {}
        for symbol in symbols:
            df = self.get_historical_data(symbol, period)
            if not df.empty:
                data[symbol] = df

        if not data:
            return None

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

        # 绘制价格图，标准化为初始价格的百分比变化
        for symbol, df in data.items():
            # 计算百分比变化
            normalized = df['Close'] / df['Close'].iloc[0] * 100 - 100
            ax1.plot(df.index, normalized, label=f'{symbol}')

        ax1.set_title('Price Comparison (% Change)')
        ax1.set_ylabel('% Change from Start')
        ax1.grid(True)
        ax1.legend(loc='upper left')

        # 获取恐慌贪婪指数
        fg_signal, fg_value = self.fear_greed_index.get_fear_greed_index()

        # 在下方图表显示当前恐慌贪婪指数
        # 这里使用简化模拟历史数据
        dates = []
        values = []

        # 模拟历史恐慌贪婪指数
        # 实际应用中应当从API获取真实历史数据
        today = datetime.now()
        for i in range(30, 0, -1):
            date = today - timedelta(days=i)
            dates.append(date)
            # 简单模拟，实际应获取真实数据
            values.append(50 + 20 * np.sin(i / 5))

        # 添加当前值
        if fg_value:
            dates.append(today)
            values.append(fg_value)

        # 绘制恐慌贪婪指数
        scatter = ax2.scatter(dates, values, c=values, cmap='RdYlGn', vmin=0, vmax=100, s=30)
        ax2.set_ylabel('Fear & Greed Index')
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        ax2.axhline(y=25, color='r', linestyle='--', alpha=0.5)  # 极度恐慌线
        ax2.axhline(y=75, color='g', linestyle='--', alpha=0.5)  # 极度贪婪线

        # 添加颜色条
        cbar = fig.colorbar(scatter, ax=ax2)
        cbar.set_label('Fear & Greed Index')

        # 设置日期格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/multiple_stocks_comparison_{timestamp}.png"
        plt.savefig(filename)
        plt.close()

        return filename

    def plot_portfolio_performance(self, transactions, balance_history):
        """
        绘制投资组合表现

        transactions: 交易记录列表
        balance_history: 余额历史记录，格式为 [(datetime, balance), ...]
        """
        if not transactions or not balance_history:
            return None

        # 准备数据
        dates = [b[0] for b in balance_history]
        balances = [b[1] for b in balance_history]

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        # 绘制资产曲线
        ax1.plot(dates, balances, 'b-', label='Portfolio Value')
        ax1.set_title('Portfolio Performance')
        ax1.set_ylabel('Value ($)')
        ax1.grid(True)

        # 标记交易点
        buy_dates = []
        buy_values = []
        sell_dates = []
        sell_values = []

        for tx in transactions:
            if tx['action'] == 'buy':
                buy_dates.append(tx['date'])
                # 找到对应日期的资产价值
                idx = min(range(len(dates)), key=lambda i: abs((dates[i] - tx['date']).total_seconds()))
                buy_values.append(balances[idx])
            elif tx['action'] == 'sell':
                sell_dates.append(tx['date'])
                # 找到对应日期的资产价值
                idx = min(range(len(dates)), key=lambda i: abs((dates[i] - tx['date']).total_seconds()))
                sell_values.append(balances[idx])

        ax1.scatter(buy_dates, buy_values, color='g', s=50, label='Buy')
        ax1.scatter(sell_dates, sell_values, color='r', s=50, label='Sell')
        ax1.legend()

        # 计算并绘制回撤
        if len(balances) > 1:
            # 计算累计最大值
            running_max = pd.Series(balances).cummax()
            # 计算相对于累计最大值的回撤
            drawdown = (pd.Series(balances) - running_max) / running_max * 100

            ax2.fill_between(dates, drawdown, 0, color='r', alpha=0.3)
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_title('Portfolio Drawdown')
            ax2.grid(True)

            # 标记最大回撤
            max_drawdown_idx = drawdown.idxmin()
            max_drawdown = drawdown.min()
            ax2.scatter([dates[max_drawdown_idx]], [max_drawdown], color='darkred', s=50)
            ax2.text(dates[max_drawdown_idx], max_drawdown, f'  Max DD: {max_drawdown:.2f}%', color='darkred')

        # 设置日期格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/portfolio_performance_{timestamp}.png"
        plt.savefig(filename)
        plt.close()

        return filename

    def plot_fear_greed_history(self):
        """绘制恐慌贪婪指数历史"""
        # 注意：这需要一个能获取历史恐慌贪婪指数的API
        # 这里使用模拟数据示例

        # 获取模拟历史数据
        today = datetime.now()
        dates = [today - timedelta(days=i) for i in range(30, 0, -1)]

        # 模拟数据 - 实际应用中需要从API获取
        # 这里随机生成一些值，但保持一定的自相关性
        np.random.seed(42)  # 为了重现性
        values = []
        last_value = 50
        for i in range(30):
            change = np.random.normal(0, 5)
            new_value = last_value + change
            new_value = max(0, min(100, new_value))  # 确保在0-100范围内
            values.append(new_value)
            last_value = new_value

        # 添加当前值
        current_fg, _ = self.fear_greed_index.get_fear_greed_index()
        if current_fg:
            dates.append(today)
            values.append(current_fg)

        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))

        # 使用渐变颜色
        points = ax.scatter(dates, values, c=values, cmap='RdYlGn', vmin=0, vmax=100, s=50)

        # 添加线连接点
        ax.plot(dates, values, 'k-', alpha=0.3)

        # 添加标题和标签
        ax.set_title('Fear & Greed Index History')
        ax.set_ylabel('Index Value')
        ax.set_ylim(0, 100)

        # 添加水平参考线和标签
        ax.axhline(y=25, color='r', linestyle='--', alpha=0.5)
        ax.axhline(y=75, color='g', linestyle='--', alpha=0.5)
        ax.text(dates[0], 12.5, 'Extreme Fear', color='r')
        ax.text(dates[0], 50, 'Neutral', color='gray')
        ax.text(dates[0], 87.5, 'Extreme Greed', color='g')

        # 添加颜色条
        cbar = fig.colorbar(points)
        cbar.set_label('Fear & Greed Index')

        # 设置日期格式
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        ax.grid(True)
        plt.tight_layout()

        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/fear_greed_history_{timestamp}.png"
        plt.savefig(filename)
        plt.close()

        return filename

    def plot_price_with_ma_crossover(self, symbol, period="6mo", short_period=9, long_period=20):
        """绘制价格图表，包含移动平均线金叉死叉指标"""
        # 获取价格数据
        price_data = self.get_historical_data(symbol, period)

        # 计算短期和长期移动平均线
        price_data[f'MA{short_period}'] = price_data['Close'].rolling(window=short_period).mean()
        price_data[f'MA{long_period}'] = price_data['Close'].rolling(window=long_period).mean()

        # 计算金叉死叉信号
        price_data['Signal'] = 0
        # 金叉：短期均线从下方穿过长期均线
        price_data.loc[(price_data[f'MA{short_period}'] > price_data[f'MA{long_period}']) &
                       (price_data[f'MA{short_period}'].shift(1) <= price_data[f'MA{long_period}'].shift(1)),
        'Signal'] = 1
        # 死叉：短期均线从上方穿过长期均线
        price_data.loc[(price_data[f'MA{short_period}'] < price_data[f'MA{long_period}']) &
                       (price_data[f'MA{short_period}'].shift(1) >= price_data[f'MA{long_period}'].shift(1)),
        'Signal'] = -1

        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})

        # 绘制价格图
        ax1.plot(price_data.index, price_data['Close'], 'b-', label=f'{symbol} Price')
        ax1.set_title(f'{symbol} Price Chart with MA Crossover ({short_period}/{long_period})')
        ax1.set_ylabel('Price ($)')
        ax1.grid(True)

        # 添加移动平均线
        ax1.plot(price_data.index, price_data[f'MA{short_period}'], 'r-', label=f'{short_period}-day MA')
        ax1.plot(price_data.index, price_data[f'MA{long_period}'], 'g-', label=f'{long_period}-day MA')

        # 标记金叉位置
        golden_cross = price_data[price_data['Signal'] == 1]
        ax1.scatter(golden_cross.index, golden_cross['Close'], marker='^', color='gold', s=100, label='Golden Cross',
                    zorder=5)

        # 标记死叉位置
        death_cross = price_data[price_data['Signal'] == -1]
        ax1.scatter(death_cross.index, death_cross['Close'], marker='v', color='black', s=100, label='Death Cross',
                    zorder=5)

        ax1.legend(loc='upper left')

        # 计算恐慌贪婪指数并在第二个子图表示
        dates = []
        values = []

        # 添加恐慌贪婪指数历史模拟
        for i in range(len(price_data) - 20):
            date = price_data.index[i + 20]
            price_change = (price_data['Close'][i + 20] - price_data['Close'][i]) / price_data['Close'][i]
            volatility = price_data['Close'][i:i + 20].pct_change().std() * np.sqrt(20)

            # 简化模型
            simulated_fg = 50 + (price_change * 200) - (volatility * 200)
            simulated_fg = max(0, min(100, simulated_fg))

            dates.append(date)
            values.append(simulated_fg)

        # 获取当前恐慌贪婪指数
        current_fg, _ = self.fear_greed_index.get_fear_greed_index()
        if current_fg:
            dates.append(price_data.index[-1])
            values.append(current_fg)

        # 绘制恐慌贪婪指数
        scatter = ax2.scatter(dates, values, c=values, cmap='RdYlGn', vmin=0, vmax=100, s=30)
        ax2.set_ylabel('Fear & Greed Index')
        ax2.set_ylim(0, 100)
        ax2.grid(True)
        ax2.axhline(y=25, color='r', linestyle='--', alpha=0.5)  # 极度恐慌线
        ax2.axhline(y=75, color='g', linestyle='--', alpha=0.5)  # 极度贪婪线

        # 添加颜色条
        cbar = fig.colorbar(scatter, ax=ax2)
        cbar.set_label('Fear & Greed Index')

        # 设置日期格式
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

        plt.tight_layout()

        # 保存图表
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/{symbol}_ma_crossover_{short_period}_{long_period}_{timestamp}.png"
        plt.savefig(filename)
        plt.close()

        return filename
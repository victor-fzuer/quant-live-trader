import unittest
import os
from chart_generator import ChartGenerator
from config import TARGETS
import yfinance as yf
from strategy import calculate_ma_crossover


class MACrossoverTests(unittest.TestCase):
    def setUp(self):
        self.chart_gen = ChartGenerator(output_dir="test_charts")

    def test_ma_crossover_chart(self):
        """测试生成金叉死叉图表"""
        for symbol in TARGETS:
            chart_path = self.chart_gen.plot_price_with_ma_crossover(symbol)
            print(f"生成 {symbol} 金叉死叉图表: {chart_path}")

            self.assertTrue(os.path.exists(chart_path), f"{symbol} 金叉死叉图表文件应该已创建")
            self.assertTrue(os.path.getsize(chart_path) > 10000, f"{symbol} 金叉死叉图表文件大小应该合理")

    def test_ma_crossover_signal(self):
        """测试金叉死叉信号计算"""
        for symbol in TARGETS:
            signal = calculate_ma_crossover(symbol)
            print(f"{symbol} 金叉死叉信号: {signal}")

            # 信号应该是 -1, 0 或 1
            self.assertTrue(signal in [-1, 0, 1], f"{symbol} 金叉死叉信号应该是 -1, 0 或 1")

    def test_different_ma_periods(self):
        """测试不同均线周期的金叉死叉"""
        symbol = TARGETS[0]

        # 测试不同的移动平均线组合
        ma_pairs = [(5, 20), (9, 20), (10, 30), (50, 200)]

        for short_ma, long_ma in ma_pairs:
            chart_path = self.chart_gen.plot_price_with_ma_crossover(
                symbol, short_period=short_ma, long_period=long_ma)
            print(f"生成 {symbol} {short_ma}/{long_ma} 均线金叉死叉图表: {chart_path}")

            self.assertTrue(os.path.exists(chart_path),
                            f"{symbol} {short_ma}/{long_ma} 均线金叉死叉图表文件应该已创建")


if __name__ == '__main__':
    unittest.main()
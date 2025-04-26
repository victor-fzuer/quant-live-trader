import unittest
import os
from chart_generator import ChartGenerator
from market_sentiment import FearGreedIndex
from config import TARGETS


class ChartGeneratorTests(unittest.TestCase):
    def setUp(self):
        # 测试前的设置，创建图表生成器实例
        self.chart_gen = ChartGenerator(output_dir="test_charts")

    def tearDown(self):
        # 测试后的清理，可以选择保留图表或删除
        pass

    def test_fear_greed_index(self):
        # 测试恐慌贪婪指数获取
        fg_index = FearGreedIndex()
        value, rating = fg_index.get_fear_greed_index()
        print(f"当前恐慌贪婪指数: {value} ({rating})")

        # 验证指数是否在有效范围内
        if value is not None:  # 考虑API可能失败的情况
            self.assertTrue(0 <= value <= 100, "恐慌贪婪指数应该在0-100范围内")

    def test_fear_greed_chart(self):
        # 测试恐慌贪婪指数历史图表生成
        chart_path = self.chart_gen.plot_fear_greed_history()
        print(f"生成恐慌贪婪指数图表: {chart_path}")

        # 验证文件是否存在且大小合理
        self.assertTrue(os.path.exists(chart_path), "图表文件应该已创建")
        self.assertTrue(os.path.getsize(chart_path) > 10000, "图表文件大小应该合理")

    def test_stock_price_charts(self):
        # 测试每个股票的价格图表生成
        for symbol in TARGETS:
            chart_path = self.chart_gen.plot_price_with_fear_greed(symbol)
            print(f"生成{symbol}价格图表: {chart_path}")

            # 验证文件是否存在且大小合理
            self.assertTrue(os.path.exists(chart_path), f"{symbol}图表文件应该已创建")
            self.assertTrue(os.path.getsize(chart_path) > 10000, f"{symbol}图表文件大小应该合理")

    def test_multiple_stocks_chart(self):
        # 测试多股票比较图表生成
        chart_path = self.chart_gen.plot_multiple_stocks()
        print(f"生成多股票比较图表: {chart_path}")

        # 验证文件是否存在且大小合理
        self.assertTrue(os.path.exists(chart_path), "多股票比较图表文件应该已创建")
        self.assertTrue(os.path.getsize(chart_path) > 10000, "多股票比较图表文件大小应该合理")

    def test_custom_period_chart(self):
        # 测试不同时间周期的图表生成
        periods = ["1mo", "3mo", "1y", "2y"]
        for period in periods:
            chart_path = self.chart_gen.plot_price_with_fear_greed(TARGETS[0], period=period)
            print(f"生成{TARGETS[0]} {period}周期图表: {chart_path}")

            # 验证文件是否存在
            self.assertTrue(os.path.exists(chart_path), f"{period}周期图表文件应该已创建")


if __name__ == '__main__':
    unittest.main()
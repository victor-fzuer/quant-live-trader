import requests
from bs4 import BeautifulSoup
import datetime
import pytz
import json
import os
import time


class FearGreedIndex:
    def __init__(self):
        self.cache_file = "fear_greed_cache.json"
        self.cache_timeout = 3600  # 1小时缓存
        self.last_update = 0
        self.current_value = None
        self.current_rating = None

    def load_cache(self):
        """从缓存文件加载恐慌贪婪指数数据"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.last_update = data.get('timestamp', 0)
                    self.current_value = data.get('value')
                    self.current_rating = data.get('rating')

                    # 检查缓存是否过期
                    if time.time() - self.last_update <= self.cache_timeout:
                        return True
            except Exception as e:
                print(f"读取缓存文件失败: {e}")
        return False

    def save_cache(self):
        """保存恐慌贪婪指数数据到缓存文件"""
        try:
            data = {
                'timestamp': time.time(),
                'value': self.current_value,
                'rating': self.current_rating
            }
            with open(self.cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"保存缓存文件失败: {e}")

    def get_fear_greed_index(self):
        """获取CNN恐慌贪婪指数"""
        # 检查缓存
        if self.load_cache():
            return self.current_value, self.current_rating

        try:
            url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                if 'fear_and_greed' in data and 'score' in data['fear_and_greed']:
                    score = data['fear_and_greed']['score']
                    rating = self.get_rating_from_score(score)

                    self.current_value = score
                    self.current_rating = rating
                    self.save_cache()

                    return score, rating

            # 备用方法
            return self._scrape_fear_greed_index()

        except Exception as e:
            print(f"获取恐慌贪婪指数失败: {e}")
            # 如果当前缓存有值，返回缓存的值
            if self.current_value is not None and self.current_rating is not None:
                return self.current_value, self.current_rating
            return None, None

    def _scrape_fear_greed_index(self):
        """备用方法：从CNN网站爬取恐慌贪婪指数"""
        try:
            url = "https://www.cnn.com/markets/fear-and-greed"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 尝试不同的选择器查找指数值
                meter_element = soup.select_one('.market-fng-gauge__meter-value')
                if meter_element:
                    value_text = meter_element.text.strip()
                    try:
                        value = int(value_text)
                        rating = self.get_rating_from_score(value)

                        self.current_value = value
                        self.current_rating = rating
                        self.save_cache()

                        return value, rating
                    except ValueError:
                        pass

            # 如果当前缓存有值，返回缓存的值
            if self.current_value is not None and self.current_rating is not None:
                return self.current_value, self.current_rating
            return None, None

        except Exception as e:
            print(f"爬取恐慌贪婪指数失败: {e}")
            # 如果当前缓存有值，返回缓存的值
            if self.current_value is not None and self.current_rating is not None:
                return self.current_value, self.current_rating
            return None, None

    def get_rating_from_score(self, score):
        """根据分数确定评级"""
        if score <= 25:
            return "Extreme Fear"
        elif score <= 45:
            return "Fear"
        elif score <= 55:
            return "Neutral"
        elif score <= 75:
            return "Greed"
        else:
            return "Extreme Greed"

    def get_buy_sell_signal(self):
        """根据恐慌贪婪指数生成买卖信号"""
        value, rating = self.get_fear_greed_index()

        if value is None:
            return "NEUTRAL", None

        if value <= 25:
            return "STRONG_BUY", value  # 极度恐慌 - 强烈买入信号
        elif value <= 40:
            return "BUY", value  # 恐慌 - 买入信号
        elif value <= 60:
            return "NEUTRAL", value  # 中性 - 持有信号
        elif value <= 80:
            return "SELL", value  # 贪婪 - 卖出信号
        else:
            return "STRONG_SELL", value  # 极度贪婪 - 强烈卖出信号
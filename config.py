STOP_LOSS = -0.05      # -5% 止损
TAKE_PROFIT = 0.10     # +10% 止盈
MAX_LAYERS = 3         # 最多加仓 3 层
LAYER_DROP = 0.05      # 每跌 5% 加一层
LAYER_SIZE = 0.10      # 每层投入本金 10%

# 交易标的列表
TARGETS = ["SOXL", "MSTU", "NVDA"]  # 三只目标股票
TARGET_WEIGHTS = {     # 资金分配权重
    "SOXL": 0.33,
    "MSTU": 0.33,
    "NVDA": 0.34
}

# 风险管理配置
DAILY_LOSS_LIMIT = 0.03    # 单日最大亏损限制（账户总值的3%）
MAX_POSITION_SIZE = 0.20   # 单个头寸最大占比（账户总值的20%）
MAX_CONCENTRATION = 0.60   # 最大仓位集中度（账户总值的60%）
TRADE_EXTENDED_HOURS = False  # 是否在盘前盘后交易
TRAILING_STOP = 0.03       # 3%跟踪止损
VOLATILITY_ADJUST = True   # 是否根据波动率调整仓位
CORRELATION_CHECK = True   # 是否检查相关性
MAX_DRAWDOWN = 0.15        # 最大回撤限制（15%）
USE_ATR_STOP = True        # 使用ATR止损
ATR_MULTIPLIER = 3.0       # ATR乘数

# 恐慌贪婪指数配置
USE_FEAR_GREED_INDEX = True  # 是否使用恐慌贪婪指数
FEAR_BUY_THRESHOLD = 30      # 小于此值时考虑买入
GREED_SELL_THRESHOLD = 70    # 大于此值时考虑卖出
EXTREME_FEAR_BOOST = 1.5     # 极度恐慌时增加仓位比例
EXTREME_GREED_REDUCE = 0.5   # 极度贪婪时减少仓位比例
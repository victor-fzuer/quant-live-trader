# 基于 Alpaca 的美股量化轮动机器人
### 1、项目结构
```text
├── .env                   # 包含API密钥等敏感信息
├── broker.py              # 交易执行接口
├── config.py              # 配置参数
├── main.py                # 主程序入口
├── notifier.py            # 通知功能
├── requirements.txt       # 依赖列表
├── strategy.py            # 交易策略实现
├── risk_manager.py        # 风险管理
├── market_monitor.py      # 市场监控
├── market_sentiment.py    # 恐慌贪婪指数
├── chart_generator.py     # 图表生成
└── charts/                # 图表输出目录(会自动创建)
```
### 2、目前暂定交易规则
- 每周一轮动策略买入 ETF（比如 SOXL/MSTU）
- 每日执行止盈（+10%）止损（-5%）
- 每次建仓只使用 10% 本金
- 实盘执行（接入 Alpaca 或美股券商）
- 微信通知（企业微信推送）
- 每天自动运行（cron）
- 回撤 5% 加仓（最多三层）
#### 2.1、指标策略
- 金叉死叉图表生成：
  - 可视化展示移动平均线的交叉情况和历史交叉点 
  - 多种均线周期支持：可以灵活选择不同的短期和长期均线组合
- 买入策略增强： 
  - 金叉作为买入信号 
  - 金叉+恐慌指数形成更强的买入信号 
  - 加仓时遇到金叉会增加加仓力度
- 卖出策略增强： 
  - 死叉作为卖出信号 
  - 死叉+贪婪指数或盈利形成更强的卖出信号
- 信号共振机制：
  - 技术分析(金叉死叉)与市场情绪(恐慌贪婪指数)相结合，提高决策质
### 3、使用方法
[注册alpaca交易api账号](https://alpaca.markets/)

[登录Server酱获取微信推送账号](https://sct.ftqq.com/login)
```bash
# 安装依赖
pip install -r requirements.txt
# 修改环境变量
vim .env
# 执行策略
python main.py
# 设置定时任务，每天22:30运行
crontab -e
# 使用nohup在后台运行
nohup python main.py > trading.log 2>&1 &
```
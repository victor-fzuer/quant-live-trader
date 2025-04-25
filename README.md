# 基于 Alpaca 的美股量化轮动机器人
### 1、目前暂定交易规则
- 每周一轮动策略买入 ETF（比如 SOXL/MSTU）
- 每日执行止盈（+10%）止损（-5%）
- 每次建仓只使用 10% 本金
- 实盘执行（接入 Alpaca 或美股券商）
- 微信通知（企业微信推送）
- 每天自动运行（cron）
- 回撤 5% 加仓（最多三层）
### 2、使用方法
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
```
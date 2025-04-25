import os
import alpaca_trade_api as tradeapi
from dotenv import load_dotenv

loaded = load_dotenv()  # 加载.env文件中的变量
print("dotenv loaded:", loaded)
key = os.getenv('ALPACA_API_KEY')
secret = os.getenv('ALPACA_API_SECRET')
url = os.getenv('ALPACA_API_BASE_URL')

print("KEY:", os.getenv("ALPACA_API_KEY"))
print("SECRET:", os.getenv("ALPACA_API_SECRET"))
print("URL:", os.getenv("ALPACA_API_BASE_URL"))

assert key and secret and url

api = tradeapi.REST(
    key_id=key,
    secret_key=secret,
    base_url=url,
)

def get_price(symbol):
    return float(api.get_latest_trade(symbol).price)

def get_position(symbol):
    try:
        pos = api.get_position(symbol)
        return float(pos.avg_entry_price), int(float(pos.qty))
    except:
        return None, 0

def get_cash():
    return float(api.get_account().cash)

def buy(symbol, qty):
    api.submit_order(symbol=symbol, qty=qty, side="buy", type="market", time_in_force="gtc")

def sell(symbol, qty):
    api.submit_order(symbol=symbol, qty=qty, side="sell", type="market", time_in_force="gtc")

def close_all():
    positions = api.list_positions()
    for p in positions:
        side = "sell" if float(p.qty) > 0 else "buy"
        qty = abs(int(float(p.qty)))
        sell(p.symbol, qty)
import os
import alpaca_trade_api as tradeapi

api = tradeapi.REST(
    os.getenv("APCA_API_KEY_ID"),
    os.getenv("APCA_API_SECRET_KEY"),
    base_url="https://paper-api.alpaca.markets"
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
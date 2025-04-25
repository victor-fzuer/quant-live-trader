from broker import get_cash, get_price, get_position, buy, sell
from notifier import notify
from config import *

state = {
    "layers": 0,
    "entry_price": None
}

def run_strategy():
    price = get_price(TARGET_ETF)
    entry, qty = get_position(TARGET_ETF)

    if qty == 0:
        # 初次建仓
        invest_cash = get_cash() * LAYER_SIZE
        buy_qty = int(invest_cash // price)
        if buy_qty > 0:
            buy(TARGET_ETF, buy_qty)
            state["layers"] = 1
            state["entry_price"] = price
            notify(f"首次建仓 {TARGET_ETF} {buy_qty} 股，价格 {price:.2f}")
    else:
        # 已持仓，判断止盈止损
        change = (price - entry) / entry
        if change <= STOP_LOSS:
            sell(TARGET_ETF, qty)
            notify(f"止损卖出 {TARGET_ETF} 全部 {qty} 股，亏损 {change:.2%}")
            state["layers"] = 0
        elif change >= TAKE_PROFIT:
            sell(TARGET_ETF, qty)
            notify(f"止盈卖出 {TARGET_ETF} 全部 {qty} 股，盈利 {change:.2%}")
            state["layers"] = 0
        else:
            # 判断是否加仓
            drop = (price - state["entry_price"]) / state["entry_price"]
            if drop <= -LAYER_DROP and state["layers"] < MAX_LAYERS:
                invest_cash = get_cash() * LAYER_SIZE
                add_qty = int(invest_cash // price)
                if add_qty > 0:
                    buy(TARGET_ETF, add_qty)
                    state["layers"] += 1
                    notify(f"触发加仓，第 {state['layers']} 层，加 {add_qty} 股，当前价格 {price:.2f}")

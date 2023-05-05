from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import *

import pandas as pd

import threading
import time


class TestWrapper(EWrapper):
    def __init__(self):
        pass

class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

class TestApp(TestWrapper, TestClient):
    def __init__(self):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)
        self.data = [] #Initialize variable to store candle
        self.nextorderId = None

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 2 and reqId == 1:
            print('The current ask price is: ', price)

    def historicalData(self, reqId, bar):
        print(f'Time: {bar.date} Close: {bar.close}')
        self.data.append([bar.date, bar.close])

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId
        print('The next valid order id is: ', self.nextorderId)

    def orderStatus(self, orderId, status, filled, remaining, avgFullPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print('orderStatus - orderid:', orderId, 'status:', status, 'filled', filled, 'remaining', remaining, 'lastFillPrice', lastFillPrice)
	
    def openOrder(self, orderId, contract, order, orderState):
        print('openOrder id:', orderId, contract.symbol, contract.secType, '@', contract.exchange, ':', order.action, order.orderType, order.totalQuantity, orderState.status)

    def execDetails(self, reqId, contract, execution):
        print('Order Executed: ', reqId, contract.symbol, contract.secType, contract.currency, execution.execId, execution.orderId, execution.shares, execution.lastLiquidity)


def run_loop(app):
    app.run()

#Function to create FX Order contract
def FX_order(symbol):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = "USD"
    return contract

def main():
    app = TestApp()
    app.connect("127.0.0.1", 7497, clientId=0)

    api_thread = threading.Thread(target=run_loop, daemon=True, args=[app])
    api_thread.start()

    #Check if the API is connected via orderid
    while True:
        if isinstance(app.nextorderId, int):
            print('connected')
            break
        else:
            print('waiting for connection')
            time.sleep(1)

    #Create contract object
    apple_contract = Contract()
    apple_contract.symbol = 'AAPL'
    apple_contract.secType = 'STK'
    apple_contract.exchange = 'SMART'
    apple_contract.currency = 'USD'

    #Request Market Data
    app.reqMktData(1, apple_contract, '', False, False, [])

    #Create contract object
    eurusd_contract = Contract()
    eurusd_contract.symbol = 'EUR'
    eurusd_contract.secType = 'CASH'
    eurusd_contract.exchange = 'IDEALPRO'
    eurusd_contract.currency = 'USD'

    #Request historical candles
    app.reqHistoricalData(1, eurusd_contract, '', '5 D', '1 min', 'BID', 0, 2, False, [])
    time.sleep(2)

    df = pd.DataFrame(app.data, columns=['DateTime', 'Close'])
    df['DateTime'] = pd.to_datetime(df['DateTime'], unit='s')
    df['20SMA'] = df['Close'].rolling(20).mean()
    print(df.tail(10))
    df.to_csv('EURUSD_Minute.csv')
    df.plot()

    #Create order object
    order = Order()
    order.action = 'BUY'
    order.totalQuantity = 1000
    order.orderType = 'LMT'
    order.lmtPrice = '1.10'

    #Place order
    app.placeOrder(app.nextorderId, FX_order('AAPL'), order)
    #app.nextorderId += 1

    time.sleep(3)

    #Cancel order 
    print('cancelling order')
    app.cancelOrder(app.nextorderId, "")

    app.disconnect()

if __name__ == '__main__':
    main()

import bittrex
import requests
import json
import time

def monitor_currency(coin):
    daily_high = None
    threshold_percentage = 15
    last_price = None
    iterations = 0

    while True:
        # every 10 seconds retrieve BTC price in respect to USD
        current_price = requests.get('https://min-api.cryptocompare.com/data/price?fsym=%s&tsyms=USD&e=Bittrex'%coin).json()
        if last_price is None:
            last_price = current_price['USD']
        if current_price['USD'] > daily_high:
            daily_high = current_price['USD']

        if current_price['USD'] < daily_high * (100 - threshold_percentage)/100:
            # bitcoin has dropped by threshold_percentage
            purchase_btc()

        if iterations % 3 == 0:
            print 'Daily high: {}'.format(str(daily_high))

        percent_change = (current_price['USD'] - last_price)/current_price['USD']
        print 'Current Price: {}'.format(str(current_price['USD'])) + ', Change: {0:.5f}%'.format(percent_change)

        iterations += 1
        last_price = current_price['USD']
        # time.sleep(3)

# move coins from alt coins to bitcoins
def purchase_btc():
    bt = bittrex.Bittrex(data['jeffrey']['key'], data['jeffrey']['secret'])

    balance = bt.get_balances()['result']
    if not balance:
        print 'You\'re broke :('


with open('../secrets.json') as data_file:
    data = json.load(data_file)

monitor_currency('BTC')

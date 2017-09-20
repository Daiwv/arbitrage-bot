import bittrex
import requests
from datetime import datetime
import collections

bt = bittrex.Bittrex('APIKEY', 'APISECRET')

buy_volume = {}
sell_volume = {}

market_history = requests.get('https://bittrex.com/api/v1.1/public/getmarkethistory?market=BTC-LTC').json()['result']
for order in market_history:
    timestamp = datetime.strptime(order['TimeStamp'], '%Y-%m-%dT%H:%M:%S.%f')
    seconds = datetime.strftime(timestamp, '%Y-%m-%d %H:%M:%S')
    if order['OrderType'] == 'SELL':
        sell_volume[seconds] = sell_volume.get(seconds, 0) + order['Quantity']
    elif order['OrderType'] == 'BUY':
        buy_volume[seconds] = sell_volume.get(seconds, 0) + order['Quantity']

chronological_buy_volume = collections.OrderedDict(sorted(buy_volume.items()))
print 'buy_volume: ' + str(chronological_buy_volume)
print sell_volume

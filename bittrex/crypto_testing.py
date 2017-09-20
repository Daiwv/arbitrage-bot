import bittrex
import requests

bt = bittrex.Bittrex('APIKEY', 'APISECRET')

# get the current price
# bt.get_ticker('BTC-TRIG')

# content = html.fromstring(page.content)
# recent = content.xpath('//text()')
# print recent

# place buy and sell LIMIT orders
# bt.buy_limit('BTC-TRIG', 2000, 0.00015)
# bt.sell_limit('BTC-TRIG', 2000, 0.00015)

# get list of all coins listed on BitTrex
# btc_currencies = [x['MarketCurrency'] for x in bt.get_markets()['result'] if x['BaseCurrency'] == 'BTC']
# print(btc_currencies)

# loop through all of those currencies to find out how many minutes per hour there was trading
def get_trading_minutes(coin):
    sdt = requests.get('https://min-api.cryptocompare.com/data/histominute?fsym=%s&tsym=BTC&limit=60&aggregate=1&e=BitTrex&ts=1498147200'%coin).json()['Data']
    mins = 0
    tradingMins = 0
    for m in sdt:
        mins += 1
        if m['volumefrom'] > 0:
            tradingMins += 1
    return tradingMins, mins

for coin in btc_currencies:
    print(coin, get_trading_minutes(coin))

from __future__ import print_function
import sys
sys.path.append('/Users/jeffreytai/Documents/Science/bittrex')

from bittrex import Bittrex
import json
from arbitrage_trading import Utils

with open('secrets.json') as data_file:
    data = json.load(data_file)

bt = Bittrex(data['deeson']['key'], data['deeson']['secret'])
utils = Utils()

balance = bt.get_balance('BTC')
print("bitcoin balance")
utils.pretty_print(balance)

balance = bt.get_balance('ETH')
print("ethereum balance")
utils.pretty_print(balance)

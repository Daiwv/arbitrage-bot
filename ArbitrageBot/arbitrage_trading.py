from __future__ import print_function
import sys
sys.path.append('/Users/jeffreytai/Documents/Science/bittrex')

from bittrex import Bittrex
import datetime
import requests
import json
import time
from utils.utils import Utils

import multiprocessing
import Queue


# CONSTANTS
ETHEREUM = 'ETH'
BITCOIN = 'BTC'
LITECOIN = 'LTC'
PROFIT_THRESHOLD = 0.025
# MINIMUM_BUY_ORDER = 0.0006 #in BTC
TRANSACTION_FEE = .0025
IS_TEST = False

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

class ArbitrageOrder:
    def __init__(self, source, destination, coin):
        self.source = source
        self.destination = destination
        self.coin = coin
        if source == BITCOIN:
            self.minimum_buy_order = 0.0006
        elif source == ETHEREUM:
            self.minimum_buy_order = utils.conversion(BITCOIN, 0.0006, ETHEREUM, 'Last')
        else:
            print("Coin is not bitcoin or ether")
            sys.exit()

    def validate_coin(self):
        """
        Checks if the arbitrage coin can be exchanged to both source and destination
        """
        btc_ticker = bt.get_ticker(BITCOIN + '-' + self.coin)
        eth_ticker = bt.get_ticker(ETHEREUM + '-' + self.coin)

        if btc_ticker['success'] and eth_ticker['success']:
            return True
        return False

    def get_baseline(self):
        """
        Returns the current exchange rate from source to destination
        """
        pair = bt.get_ticker(BITCOIN + '-' + ETHEREUM)
        if pair['success'] and self.source == BITCOIN and pair['result']['Ask'] is not None:
            baseline = pair['result']['Ask']
        elif pair['success'] and self.source == ETHEREUM and pair['result']['Ask'] is not None:
            baseline = 1 / pair['result']['Ask']
        else:
            baseline = None
        return baseline

    def arbitrage_coin_value(self, tx_fee_reduction):
        """
        Returns the current exchange rate from source to coin to destination, accounting for fees
        """
        source_ticker = bt.get_ticker(self.source + '-' + self.coin)
        dest_ticker = bt.get_ticker(self.destination + '-' + self.coin)

        source_ask = source_ticker['result']['Ask'] if source_ticker['success'] else None
        dest_ask = dest_ticker['result']['Ask'] if dest_ticker['success'] else None
        if source_ask is not None and dest_ask is not None:
            val = source_ask / dest_ask * tx_fee_reduction * tx_fee_reduction
            return val
        else:
            return 0


    def calculate_profit(self, tx_fee):
        baseline_value = self.get_baseline()
        arbitrage_value = self.arbitrage_coin_value(1 - tx_fee)
        profit = arbitrage_value / baseline_value - 1
        return profit

def purchase_minimum_buy_order(arbitrage_order, mp_queue, is_test = False):
    source_market = arbitrage_order.source + '-' + arbitrage_order.coin
    destination_market = arbitrage_order.destination + '-' + arbitrage_order.coin
    source_orderbook = bt.get_orderbook(source_market, SELL_ORDERBOOK)
    destination_orderbook = bt.get_orderbook(destination_market, BUY_ORDERBOOK)

    while (source_orderbook['success'] and destination_orderbook['success']):

        source_sell_order = source_orderbook['result'][0]
        destination_sell_order = destination_orderbook['result'][0]

        # print("first source sell order:", source_sell_order['Quantity'], arbitrage_order.coin, "at the price of", source_sell_order['Rate'], arbitrage_order.source)
        # print("first destination buy order:", destination_sell_order['Quantity'], arbitrage_order.coin, "at the price of", destination_sell_order['Rate'], arbitrage_order.destination)

        print("purchasing", arbitrage_order.minimum_buy_order, arbitrage_order.source, "worth of", arbitrage_order.coin)
        purchase_quantity = arbitrage_order.minimum_buy_order / source_sell_order['Rate']

        if not is_test:
            purchase_txn = bt.buy_limit(source_market, purchase_quantity, source_sell_order['Rate'])
            utils.pretty_print(purchase_txn)
            if purchase_txn['message'] == 'INSUFFICIENT_FUNDS':
                sys.exit()


        test_count = 0
        maximum_tries = 3
        wallet = bt.get_balance(arbitrage_order.coin)
        while wallet['success'] == False or wallet['result']['Balance'] is None:
            print("No balance")
            wallet = bt.get_balance(arbitrage_order.coin)

            # if testing, need to continue listening to queue to stop processing
            if is_test:
                if (test_count > maximum_tries):
                    break
                test_count += 1

                try:
                    msg = mp_queue.get_nowait()
                except Queue.Empty:
                    pass
                else:
                    print("msg:", msg)
                    if msg == 'kill':
                        mp_queue.put_nowait('kill')
                        break


        sell_amount = wallet['result']['Balance']
        print("selling",sell_amount,"worth of",arbitrage_order.coin)

        print("destination sell order rate:",destination_sell_order['Rate'])
        if not is_test:
            sell_txn = bt.sell_limit(destination_market, sell_amount, destination_sell_order['Rate'])
            utils.pretty_print(sell_txn)

        try:
            msg = mp_queue.get_nowait()
        except Queue.Empty:
            pass
        else:
            print("msg:",msg)
            if msg == 'kill':
                mp_queue.put_nowait('done')
                break

        source_orderbook = bt.get_orderbook(source_market, SELL_ORDERBOOK)
        destination_orderbook = bt.get_orderbook(destination_market, BUY_ORDERBOOK)


def run_arbitrage(arbitrage_order, tx_fee = 0):
    """
    Queries Bittrex to calculate direct exchange value and arbitrage value of all valid coins
    :param arbitrage_order: Contains source coin, destination coin, and arbitrage coin
    :type source: class
    :param tx_fee: transaction fee
    :type tx_fee: decimal
    """
    profit = arbitrage_order.calculate_profit(tx_fee)
    print("profit:", profit)

    if profit > PROFIT_THRESHOLD:
        print(arbitrage_order.coin, "PROFITABLE:", str(profit * 100), "%!!!!!!!!!")
        mp_queue = multiprocessing.Queue()
        child = multiprocessing.Process(target=purchase_minimum_buy_order, args=(arbitrage_order,(mp_queue),IS_TEST))
        child.daemon = True
        child.start()

        balance = bt.get_balance(arbitrage_order.source)

        # check every second for profit threshold
        while profit > PROFIT_THRESHOLD and balance['success'] and balance['result']['Balance'] > arbitrage_order.minimum_buy_order:
            profit = arbitrage_order.calculate_profit(tx_fee)
            print("profit:", profit)
            balance = bt.get_balance(arbitrage_order.source)
            time.sleep(1)

        mp_queue.put('kill')
        while True:
            try:
            # if not mp_queue.empty():
                msg = mp_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                if msg == 'done':
                    child.terminate()
                    break
                else:
                    mp_queue.put(msg)
                # mp_queue.task_done()

        # after running arbitrage, sleep for 5 seconds to avoid overloading API
        time.sleep(5)
    else:
        print(arbitrage_order.coin, "not profitable")


with open('secrets.json') as data_file:
    data = json.load(data_file)

bt = Bittrex(data['deeson']['key'], data['deeson']['secret'])
utils = Utils(bt)
print("Bitcoin")
balance = bt.get_balance(BITCOIN)
utils.pretty_print(balance)

print("Ether")
eth_balance = bt.get_balance(ETHEREUM)
utils.pretty_print(eth_balance)

# while balance['success']:
#     valid_coins = []
#
#     result = bt.get_currencies()
#     if (result['success']):
#         # gets list of coins that can be traded for both ETH and BTC
#         coins = [coin.get('Currency') for coin in result['result'] if coin.get('Currency') not in [ETHEREUM, BITCOIN, LITECOIN]]
#         for coin in coins:
#             try:
#                 arbitrage_order = ArbitrageOrder(ETHEREUM, BITCOIN, coin)
#                 if (arbitrage_order.validate_coin()):
#                     valid_coins.append(coin)
#                     print(coin)
#                     run_arbitrage(arbitrage_order, TRANSACTION_FEE)
#             except ValueError:
#                 pass
#
#     # if retrieving balance failed, need to slow down on using the API
#     else:
#         time.sleep(60)
#
#     balance = bt.get_balance(BITCOIN)
#     utils.pretty_print(balance)

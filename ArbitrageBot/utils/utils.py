from __future__ import print_function
import json
import logging

class Utils:
    def __init__(self, bt):
        self.bt = bt

    #debugging purposes
    def pretty_print(self, dict):
        string = json.dumps(dict)
        parsed = json.loads(string)
        print(json.dumps(parsed, indent = 4, sort_keys = True))

    def log_transaction(self):
        date_string = datetime.datetime.today().strftime('%m-%d-%Y')
        logging.basicConfig(filename=date_string + '.log', level=logging.INFO)
        datetime_string = datetime.datetime.today().strftime('%m-%d-%Y %H:%M:%S')

    def conversion(self, base, base_value, counter, result_type):
        pair = self.bt.get_ticker(base + '-' + counter)
        if pair['success']:
            return base_value / pair['result'][result_type]
        return None

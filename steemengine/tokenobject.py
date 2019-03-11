from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from steemengine.api import Api


class Token(dict):
    """ steem-engine token dict

        :param str token: Name of the token
    """
    def __init__(self, symbol):
        self.api = Api()
        if isinstance(symbol, dict):
            self.symbol = symbol["symbol"]
            super(Token, self).__init__(symbol)
        else:
            self.symbol = symbol.upper()
            self.refresh()

    def refresh(self):
        info = self.get_info()
        super(Token, self).__init__(info)

    def get_info(self):
        """Returns information about the token"""
        token = self.api.find_one("tokens", "tokens", query={"symbol": self.symbol})
        if len(token) > 0:
            return token[0]
        else:
            return token

    def get_holder(self, limit=1000, offset=0):
        """Returns all token holders"""
        holder = self.api.find("tokens", "balances", query={"symbol": self.symbol}, limit=limit, offset=offset)
        return holder

    def get_market_info(self):
        """Returns market information"""
        metrics = self.api.find_one("market", "metrics", query={"symbol": self.symbol})
        if len(metrics) > 0:
            return metrics[0]
        else:
            return metrics        

    def get_buy_book(self, limit=100, offset=0):
        """Returns the buy book"""
        holder = self.api.find("market", "buyBook", query={"symbol": self.symbol}, limit=limit, offset=offset)
        return holder

    def get_sell_book(self, limit=100, offset=0):
        """Returns the sell book"""
        holder = self.api.find("market", "sellBook", query={"symbol": self.symbol}, limit=limit, offset=offset)
        return holder

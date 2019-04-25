from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from steemengine.api import Api
from steemengine.tokenobject import Token


class Tokens(list):
    """ Access the steem-engine tokens
    """
    def __init__(self, url=None, rpcurl=None, **kwargs):
        self.api = Api(url=url, rpcurl=rpcurl)
        self.refresh()

    def refresh(self):
        super(Tokens, self).__init__(self.get_token_list())

    def get_token_list(self):
        """Returns all available token as list"""
        tokens = self.api.find("tokens", "tokens", query={})
        return tokens

    def get_token(self, symbol):
        """Returns Token from given token symbol. Is None
            when token does not exists.
        """
        for t in self:
            if t["symbol"].lower() == symbol.lower():
                return Token(t)
        return None


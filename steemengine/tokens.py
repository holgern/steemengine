from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta, date
import time
import io
import json
import requests
from timeit import default_timer as timer
import logging
from steemengine.api import Api


class Tokens(list):
    """ Access the steem-engine tokens
    """
    def __init__(self, **kwargs):
        self.api = Api()
        self.refresh()

    def refresh(self):
        super(Tokens, self).__init__(self.get_token_list())

    def get_token_list(self):
        """Returns all available token as list"""
        tokens = self.api.find("tokens", "tokens", query={})
        return tokens

    def get_token(self, symbol):
        """Returns dict from given token symbol. Is None
            when token does not exists.
        """
        for t in self:
            if t["symbol"].lower() == symbol.lower():
                return t
        return None

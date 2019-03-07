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
from steemengine.exceptions import (TokenDoesNotExists, TokenNotInWallet, InsufficientTokenAmount)
from beem.instance import shared_steem_instance
from beem.account import Account


class Wallet(list):
    """ Access the steem-engine wallet

        :param str account: Name of the account
        :param Steem steem_instance: Steem
               instance
    """
    def __init__(self, account, steem_instance=None):
        self.api = Api()
        self.steem = steem_instance or shared_steem_instance()
        check_account = Account(account, steem_instance=self.steem)
        self.account = account
        self.refresh()

    def refresh(self):
        super(Wallet, self).__init__(self.get_balances())

    def get_balances(self):
        """Returns all token within the wallet as list"""
        balances = self.api.find("tokens", "balances", query={"account": self.account})
        return balances

    def change_account(self, account):
        """Changes the wallet account"""
        check_account = Account(account, steem_instance=self.steem)
        self.account = account
        self.refresh()

    def get_token(self, symbol):
        """Returns a token from the wallet. Is None when not available."""
        for t in self:
            if t["symbol"].lower() == symbol.lower():
                return t
        return None

    def transfer(self, to, amount, symbol, memo=""):
        """Transfer a token to another account.

            :param str to: Recipient
            :param float amount: Amount to transfer
            :param str symbol: Token to transfer
            :param str memo: (optional) Memo


            Transfer example:

            .. code-block:: python

                from steemengine.wallet import Wallet
                from beem import Steem
                active_wif = "5xxxx"
                stm = Steem(keys=[active_wif])
                wallet = Wallet("test", steem_instance=stm)
                wallet.transfer("test1", 1, "ENG", "test")
        """
        token = self.get_token(symbol)
        if token is None:
            raise TokenNotInWallet("%s is not in wallet." % symbol)
        if float(token["balance"]) < float(amount):
            raise InsufficientTokenAmount("Only %.3f in wallet" % float(token["balance"]))
        check_to = Account(to, steem_instance=self.steem)
        contractPayload = {"symbol":symbol.upper(),"to":to,"quantity":str(amount),"memo":memo}
        json_data = {"contractName":"tokens","contractAction":"transfer",
                     "contractPayload":contractPayload}
        tx = self.steem.custom_json("ssc-mainnet1", json_data, required_auths=[self.account])
        return tx

    def get_history(self, symbol, limit=1000, offset=0):
        """Returns the transfer history of a token"""
        return self.api.get_history(self.account, symbol, limit, offset)

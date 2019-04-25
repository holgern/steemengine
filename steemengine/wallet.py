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
import decimal
from steemengine.api import Api
from steemengine.tokenobject import Token
from steemengine.exceptions import (TokenDoesNotExists, TokenNotInWallet, InsufficientTokenAmount, TokenIssueNotPermitted, MaxSupplyReached, InvalidTokenAmount)
from beem.instance import shared_steem_instance
from beem.account import Account


class Wallet(list):
    """ Access the steem-engine wallet

        :param str account: Name of the account
        :param Steem steem_instance: Steem
               instance
               
        Wallet example:

            .. code-block:: python

                from steemengine.wallet import Wallet
                wallet = Wallet("test")
                print(wallet)

    """
    def __init__(self, account, url=None, rpcurl=None, steem_instance=None):
        self.api = Api(url=url, rpcurl=rpcurl)
        self.steem = steem_instance or shared_steem_instance()
        check_account = Account(account, steem_instance=self.steem)
        self.account = check_account["name"]
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
        self.account = check_account["name"]
        self.refresh()

    def get_token(self, symbol):
        """Returns a token from the wallet. Is None when not available."""
        for token in self:
            if token["symbol"].lower() == symbol.lower():
                return token
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
        token_in_wallet = self.get_token(symbol)
        if token_in_wallet is None:
            raise TokenNotInWallet("%s is not in wallet." % symbol)
        if float(token_in_wallet["balance"]) < float(amount):
            raise InsufficientTokenAmount("Only %.3f in wallet" % float(token_in_wallet["balance"]))
        token = Token(symbol)
        quant_amount = token.quantize(amount)
        if quant_amount <= decimal.Decimal("0"):
            raise InvalidTokenAmount("Amount to transfer is below token precision of %d" % token["precision"])
        check_to = Account(to, steem_instance=self.steem)
        contract_payload = {"symbol":symbol.upper(),"to":to,"quantity":str(quant_amount),"memo":memo}
        json_data = {"contractName":"tokens","contractAction":"transfer",
                     "contractPayload":contract_payload}
        tx = self.steem.custom_json("ssc-mainnet1", json_data, required_auths=[self.account])
        return tx

    def issue(self, to, amount, symbol):
        """Issues a specific token amount.

            :param str to: Recipient
            :param float amount: Amount to issue
            :param str symbol: Token to issue


            Issue example:

            .. code-block:: python

                from steemengine.wallet import Wallet
                from beem import Steem
                active_wif = "5xxxx"
                stm = Steem(keys=[active_wif])
                wallet = Wallet("test", steem_instance=stm)
                wallet.issue(1, "my_token")
        """
        token = Token(symbol)
        if token["issuer"] != self.account:
            raise TokenIssueNotPermitted("%s is not the issuer of token %s" % (self.account, symbol))
        
        if token["maxSupply"] == token["supply"]:
            raise MaxSupplyReached("%s has reached is maximum supply of %d" % (symbol, token["maxSupply"]))
        quant_amount = token.quantize(amount)
        if quant_amount <= decimal.Decimal("0"):
            raise InvalidTokenAmount("Amount to issue is below token precision of %d" % token["precision"])        
        check_to = Account(to, steem_instance=self.steem)
        contract_payload = {"symbol":symbol.upper(),"to":to,"quantity":str(quant_amount)}
        json_data = {"contractName":"tokens","contractAction":"issue",
                     "contractPayload":contract_payload}
        tx = self.steem.custom_json("ssc-mainnet1", json_data, required_auths=[self.account])
        return tx

    def get_history(self, symbol, limit=1000, offset=0):
        """Returns the transfer history of a token"""
        return self.api.get_history(self.account, symbol, limit, offset)

    def get_buy_book(self, symbol=None, limit=100, offset=0):
        """Returns the buy book for the wallet account. When symbol is set,
            the order book from the given token is shown.
        """
        if symbol is None:
            buy_book = self.api.find("market", "buyBook", query={"account": self.account}, limit=limit, offset=offset)
        else:
            buy_book = self.api.find("market", "buyBook", query={"symbol": symbol, "account": self.account}, limit=limit, offset=offset)
        return buy_book

    def get_sell_book(self, symbol=None, limit=100, offset=0):
        """Returns the sell book for the wallet account. When symbol is set,
            the order book from the given token is shown.
        """        
        if symbol is None:
            sell_book = self.api.find("market", "sellBook", query={"account": self.account}, limit=limit, offset=offset)
        else:
            sell_book = self.api.find("market", "sellBook", query={"symbol": symbol, "account": self.account}, limit=limit, offset=offset)
        return sell_book

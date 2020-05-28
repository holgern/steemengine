# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
from beem import Steem
from beem.account import Account
from beem.nodelist import NodeList
from beem.utils import formatTimeString, addTzInfo
from beem.blockchain import Blockchain
from beem.exceptions import WrongMasterPasswordException
from steemengine.api import Api
from steemengine.tokens import Tokens
from steemengine.tokenobject import Token
from steemengine.market import Market
from steemengine.wallet import Wallet
from prettytable import PrettyTable
import time
import json
import click
import logging
import sys
import os
import io
import argparse
import re
import six
from beem.instance import set_shared_blockchain_instance, shared_blockchain_instance
from steemengine.version import version as __version__
click.disable_unicode_literals_warning = True
log = logging.getLogger(__name__)
try:
    import keyring
    if not isinstance(keyring.get_keyring(), keyring.backends.fail.Keyring):
        KEYRING_AVAILABLE = True
    else:
        KEYRING_AVAILABLE = False
except ImportError:
    KEYRING_AVAILABLE = False


def unlock_wallet(stm, password=None, allow_wif=True):
    if stm.unsigned and stm.nobroadcast:
        return True
    if not stm.wallet.locked():
        return True
    password_storage = stm.config["password_storage"]
    if not password and KEYRING_AVAILABLE and password_storage == "keyring":
        password = keyring.get_password("beem", "wallet")
    if not password and password_storage == "environment" and "UNLOCK" in os.environ:
        password = os.environ.get("UNLOCK")
    if bool(password):
        stm.wallet.unlock(password)
    else:
        if allow_wif:
            password = click.prompt("Password to unlock wallet or posting/active wif", confirmation_prompt=False, hide_input=True)
        else:
            password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
        try:
            stm.wallet.unlock(password)
        except:
            try:
                stm.wallet.setKeys([password])
                print("Wif accepted!")
                return True                
            except:
                if allow_wif:
                    raise WrongMasterPasswordException("entered password is not a valid password/wif")
                else:
                    raise WrongMasterPasswordException("entered password is not a valid password")

    if stm.wallet.locked():
        if password_storage == "keyring" or password_storage == "environment":
            print("Wallet could not be unlocked with %s!" % password_storage)
            password = click.prompt("Password to unlock wallet", confirmation_prompt=False, hide_input=True)
            if bool(password):
                unlock_wallet(stm, password=password)
                if not stm.wallet.locked():
                    return True
        else:
            print("Wallet could not be unlocked!")
        return False
    else:
        print("Wallet Unlocked!")
        return True


@click.group(chain=True)
@click.option(
    '--node', '-n', default="https://api.steemit.com", help="URL for public Steem API (e.g. https://api.steemit.com)")
@click.option(
    '--no-broadcast', '-d', is_flag=True, default=False, help="Do not broadcast")
@click.option(
    '--verbose', '-v', default=3, help='Verbosity')
@click.version_option(version=__version__)
def cli(node, no_broadcast, verbose):
    # Logging
    log = logging.getLogger(__name__)
    verbosity = ["critical", "error", "warn", "info", "debug"][int(
        min(verbose, 4))]
    log.setLevel(getattr(logging, verbosity.upper()))
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, verbosity.upper()))
    ch.setFormatter(formatter)
    log.addHandler(ch)
    debug = verbose > 0
    stm = Steem(
        node=node,
        nobroadcast=no_broadcast,
        )
    set_shared_blockchain_instance(stm)    
    pass


@cli.command()
@click.argument('objects', nargs=-1)
def info(objects):
    """ Show basic blockchain info

        General information about steem-engine, a block, an account, a token,
        and a transaction id
    """
    stm = None   
    api = Api()

    if not objects:
        latest_block = api.get_latest_block_info()
        tokens = Tokens()
        t = PrettyTable(["Key", "Value"])
        t.align = "l"
        t.add_row(["latest block number", latest_block["blockNumber"]])
        t.add_row(["latest steem block", latest_block["refSteemBlockNumber"]])
        t.add_row(["latest timestamp", latest_block["timestamp"]])
        t.add_row(["Number of created tokens", len(tokens)])
        print(t.get_string())
    for obj in objects:
        if re.match("^[0-9-]*$", obj):
            block_info = api.get_block_info(int(obj))
            print("Block info: %d" % (int(obj)))
            trx_nr = 0
            for trx in block_info["transactions"]:
                trx_nr += 1
                t = PrettyTable(["Key", "Value"])
                t.align = "l"
                t.add_row(["trx_nr", str(trx_nr)])
                t.add_row(["action", trx["action"]])
                t.add_row(["contract", trx["contract"]])
                t.add_row(["logs", json.dumps(json.loads(trx["logs"]), indent=4)])
                t.add_row(["payload", json.dumps(json.loads(trx["payload"]), indent=4)])
                t.add_row(["refSteemBlockNumber", trx["refSteemBlockNumber"]])
                t.add_row(["timestamp", block_info["timestamp"]])
                t.add_row(["sender", trx["sender"]])
                t.add_row(["transactionId", trx["transactionId"]])
                print(t.get_string())
        elif re.match("^[A-Z0-9\-\._]{1,16}$", obj):
            print("Token: %s" % obj)
            tokens = Tokens()
            token = tokens.get_token(obj)
            if token is None:
                print("Could not found token %s" % obj)
                return
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            metadata = json.loads(token["metadata"])
            for key in token:
                if key == "metadata":
                    if "url" in metadata:
                        t.add_row(["metadata_url", metadata["url"]])
                    if "icon" in metadata:
                        t.add_row(["metadata_icon", metadata["icon"]])
                    if "desc" in metadata:
                        t.add_row(["metadata_desc", metadata["desc"]])            
                else:
                    t.add_row([key, token[key]])
            market_info = token.get_market_info()
            if market_info is not None:
                for key in market_info:
                    if key in ["_id", "symbol"]:
                        continue
                    t.add_row([key, market_info[key]])
            print(t.get_string())
        elif re.match("^[a-zA-Z0-9\-\._]{2,16}$", obj):
            print("Token Wallet: %s" % obj)
            if stm is None:
                nodelist = NodeList()
                nodelist.update_nodes()
                stm = Steem(node=nodelist.get_nodes())                
            wallet = Wallet(obj, steem_instance=stm)
            t = PrettyTable(["id", "symbol", "balance", "stake", "pendingUnstake"])
            t.align = "l"
            for token in wallet:
                if "stake" in token:
                    stake = token["stake"]
                else:
                    stake = "-"
                if "pendingUnstake" in token:
                    pendingUnstake = token["pendingUnstake"]
                else:
                    pendingUnstake = "-"
                t.add_row([token["_id"], token["symbol"], token["balance"], stake, pendingUnstake])
            print(t.get_string(sortby="id"))
        elif len(obj) == 40:
            print("Transaction Id: %s" % obj)
            trx = api.get_transaction_info(obj)
            if trx is None:
                print("trx_id: %s is not a valid steem-engine trx_id!" % obj)
                return
            payload = json.loads(trx["payload"])
            logs = json.loads(trx["logs"])
            t = PrettyTable(["Key", "Value"])
            t.align = "l"
            t.add_row(["blockNumber", str(trx["blockNumber"])])
            t.add_row(["action", trx["action"]])
            t.add_row(["contract", trx["contract"]])
            t.add_row(["logs", json.dumps(logs, indent=4)])
            t.add_row(["payload", json.dumps(payload, indent=4)])
            t.add_row(["refSteemBlockNumber", trx["refSteemBlockNumber"]])
            t.add_row(["sender", trx["sender"]])
            t.add_row(["transactionId", trx["transactionId"]])
            print(t.get_string())            


@cli.command()
@click.argument('symbol', nargs=1)
@click.option('--top', '-t', help='Show only the top n accounts', default=50)
def richlist(symbol, top):
    """ Shows the richlist of a token

    """
    token = Token(symbol)
    holder = token.get_holder()
    market_info = token.get_market_info()
    last_price = float(market_info["lastPrice"])
    sorted_holder = sorted(holder, key=lambda account: float(account["balance"]), reverse=True)
    t = PrettyTable(["Balance", "Account", "Value [STEEM]"])
    t.align = "l"
    for balance in sorted_holder[:int(top)]:
        t.add_row([balance["balance"], balance["account"], "%.3f" % (float(balance["balance"]) * last_price)])
    print(t.get_string())


@cli.command()
@click.argument('to', nargs=1)
@click.argument('amount', nargs=1, required=False)
@click.argument('token', nargs=1, required=False)
@click.argument('memo', nargs=1, required=False)
@click.option('--memos', '-m', help="Can be used when all tokens should be send")
@click.option('--account', '-a', help='Transfer from this account')
def transfer(to, amount, token, memo, memos, account):
    """Transfer a token"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not account:
        account = stm.config["default_account"]
    if not bool(memo):
        memo = ''
    if not bool(memos):
        memos = ''    
    if not unlock_wallet(stm):
        return
    wallet = Wallet(account, steem_instance=stm)
    if amount is None and token is None:
        token = amount
        amount = 0
        tokens = Tokens()
        
        for t in wallet:
            token = t["symbol"]
            amount = float(t["balance"])
            if amount == 0:
                continue
            token_obj = tokens.get_token(token)
            market_info = token_obj.get_market_info()
            if market_info is None:
                print("transfer  %.8f %s to %s?" % (amount, token, to))
            else:
                last_price = float(market_info["lastPrice"])
                highest_bid = float(market_info["highestBid"])
                if highest_bid == 0:
                    price = last_price
                else:
                    price = highest_bid
                hive_amount = price*amount
                print("transfer %.8f %s (value %.3f STEEM) to %s?" % (amount, token, hive_amount, to))
            ret = input("continue [y/n]?")
            if ret not in ["y", "yes"]:
                continue
            tx = wallet.transfer(to, amount, token, memos)
            tx = json.dumps(tx, indent=4)
            print(tx)
        return
    elif token is None:
        token = amount
        amount = 0
        for t in wallet:
            if t["symbol"] == token:
                amount = float(t["balance"])
        if amount == 0:
            print("Amount of %s is 0" % token)
            return
        tokens = Tokens()
        token_obj = tokens.get_token(token)   
        market_info = token_obj.get_market_info()
        last_price = float(market_info["lastPrice"])
        highest_bid = float(market_info["highestBid"])
        if highest_bid == 0:
            price = last_price
        else:
            price = highest_bid
        hive_amount = price*amount
        print("transfer %.8f %s (value %.3f STEEM) to %s?" % (amount, token, hive_amount, to))
        ret = input("continue [y/n]?")
        if ret not in ["y", "yes"]:
            return
        memo = memos    
    tx = wallet.transfer(to, amount, token, memo)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('to', nargs=1)
@click.argument('amount', nargs=1)
@click.argument('token', nargs=1)
@click.option('--account', '-a', help='Transfer from this account')
def issue(to, amount, token, account):
    """Issue a token"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    wallet = Wallet(account, steem_instance=stm)
    tx = wallet.issue(to, amount, token)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1, required=False)
@click.argument('token', nargs=1, required=False)
@click.option('--account', '-a', help='Stake from this account')
def stake(amount, token, account):
    """stake a token"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return        
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    wallet = Wallet(account, steem_instance=stm)
    if amount is None and token is None:
        token = amount
        amount = 0
        tokens = Tokens()
        for t in wallet:
            token = t["symbol"]
            amount = float(t["balance"])
            if amount == 0:
                continue
            token_obj = tokens.get_token(token)
            if not token_obj["stakingEnabled"]:
                continue
            market_info = token_obj.get_market_info()
            if market_info is None:
                print("stake %.8f %s?" % (amount, token))
            else:
                last_price = float(market_info["lastPrice"])
                highest_bid = float(market_info["highestBid"])
                if highest_bid == 0:
                    price = last_price
                else:
                    price = highest_bid
                steem_amount = price*amount
                print("stake %.8f %s (value %.3f STEEM)?" % (amount, token, steem_amount))
            ret = input("continue [y/n]?")
            if ret not in ["y", "yes"]:
                continue
            tx = wallet.stake(amount, token)
            tx = json.dumps(tx, indent=4)
            print(tx)
        return
    elif token is None:
        token = amount
        amount = 0
        for t in wallet:
            if t["symbol"] == token:
                amount = float(t["balance"])
        if amount == 0:
            print("Amount of %s is 0" % token)
            return
        tokens = Tokens()
        token_obj = tokens.get_token(token)
        if not token_obj["stakingEnabled"]:
            print("%s is not stakable" % token)
            return        
        market_info = token_obj.get_market_info()
        last_price = float(market_info["lastPrice"])
        highest_bid = float(market_info["highestBid"])
        if highest_bid == 0:
            price = last_price
        else:
            price = highest_bid
        steem_amount = price*amount
        print("stake %.8f %s (value %.3f STEEM)?" % (amount, token, steem_amount))
        ret = input("continue [y/n]?")
        if ret not in ["y", "yes"]:
            return    
    tx = wallet.stake(amount, token)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1, required=False)
@click.argument('token', nargs=1, required=False)
@click.option('--account', '-a', help='Transfer from this account')
def unstake(amount, token, account):
    """unstake a token"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return        
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    wallet = Wallet(account, steem_instance=stm)
    if amount is None and token is None:
        token = amount
        amount = 0
        tokens = Tokens()
        
        for t in wallet:
            token = t["symbol"]
            amount = float(t["balance"])
            stake = float(t["stake"])
            if stake == 0:
                continue
            token_obj = tokens.get_token(token)
            if not token_obj["stakingEnabled"]:
                continue
            market_info = token_obj.get_market_info()
            if market_info is None:
                print("unstake %.8f %s?" % (stake, token))
            else:
                last_price = float(market_info["lastPrice"])
                highest_bid = float(market_info["highestBid"])
                if highest_bid == 0:
                    price = last_price
                else:
                    price = highest_bid
                steem_amount = price*stake
                print("unstake %.8f %s (value %.3f STEEM)?" % (stake, token, steem_amount))
            ret = input("continue [y/n]?")
            if ret not in ["y", "yes"]:
                continue
            tx = wallet.unstake(stake, token)
            tx = json.dumps(tx, indent=4)
            print(tx)
        return
    elif token is None:
        token = amount
        amount = 0
        for t in wallet:
            if t["symbol"] == token:
                amount = float(t["stake"])
        if amount == 0:
            print("Staked Amount of %s is 0" % token)
            return
        tokens = Tokens()
        token_obj = tokens.get_token(token)
        if not token_obj["stakingEnabled"]:
            print("%s is not stakable" % token)
            return        
        market_info = token_obj.get_market_info()
        last_price = float(market_info["lastPrice"])
        highest_bid = float(market_info["highestBid"])
        if highest_bid == 0:
            price = last_price
        else:
            price = highest_bid
        steem_amount = price*amount
        print("unstake %.8f %s (value %.3f STEEM)?" % (amount, token, steem_amount))
        ret = input("continue [y/n]?")
        if ret not in ["y", "yes"]:
            return    
    tx = wallet.unstake(amount, token)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('trx_id', nargs=1)
@click.option('--account', '-a', help='Transfer from this account')
def cancel_unstake(amount, trx_id):
    """unstake a token"""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return    
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    wallet = Wallet(account, steem_instance=stm)
    tx = wallet.cancel_unstake(trx_id)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='withdraw from this account')
def withdraw(amount, account):
    """Widthdraw STEEMP to account as STEEM."""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return    
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    market = Market(steem_instance=stm)
    tx = market.withdraw(account, amount)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.option('--account', '-a', help='withdraw from this account')
def deposit(amount, account):
    """Deposit STEEM to market in exchange for STEEMP."""
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    if not account:
        account = stm.config["default_account"]
    if not unlock_wallet(stm):
        return
    market = Market(steem_instance=stm)
    tx = market.deposit(account, amount)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1)
@click.argument('token', nargs=1)
@click.argument('price', nargs=1)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
def buy(amount, token, price, account):
    """Put a buy-order for a token to the steem-engine market

    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    if account is None:
        account = stm.config["default_account"]
    market = Market(steem_instance=stm)
    if not unlock_wallet(stm):
        return
    tx = market.buy(account, amount, token, price)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('amount', nargs=1, required=False)
@click.argument('token', nargs=1, required=False)
@click.argument('price', nargs=1, required=False)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
def sell(amount, token, price, account):
    """Put a sell-order for a token to the steem-engine market

    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    if account is None:
        account = stm.config["default_account"]
    if amount is None and price is None and token is None:
        if not unlock_wallet(stm):
            return
        token = amount
        amount = 0
        tokens = Tokens()
        wallet = Wallet(account, steem_instance=stm)
        market = Market(steem_instance=stm)
        for t in wallet:
            token = t["symbol"]
            amount = float(t["balance"])
            if amount == 0:
                continue
            token_obj = tokens.get_token(token)
            market_info = token_obj.get_market_info()
            if market_info is None:
                continue
            last_price = float(market_info["lastPrice"])
            highest_bid = float(market_info["highestBid"])
            if highest_bid == 0:
                price = last_price
            else:
                price = highest_bid
            steem_amount = price*amount
            if steem_amount < 0.001:
                continue
            print("%s: using %.8f as price to sell %.8f %s for %.8f STEEM" % (token, price, amount, token, steem_amount))
            ret = input("continue [y/n]?")
            if ret not in ["y", "yes"]:
                continue
            tx = market.sell(account, amount, token, price)
            tx = json.dumps(tx, indent=4)
            print(tx)
        return
        
    elif price is None and token is None:
        token = amount
        amount = 0
        wallet = Wallet(account, steem_instance=stm)
        for t in wallet:
            if t["symbol"] == token:
                amount = float(t["balance"])
        if amount == 0:
            print("Amount of %s is 0" % token)
            return
        tokens = Tokens()
        token_obj = tokens.get_token(token)
        market_info = token_obj.get_market_info()
        last_price = float(market_info["lastPrice"])
        highest_bid = float(market_info["highestBid"])
        if highest_bid == 0:
            price = last_price
        else:
            price = highest_bid
        steem_amount = price*amount
        print("using %.8f as price to sell %.8f %s for %.8f STEEM" % (price, amount, token, steem_amount))
        ret = input("continue [y/n]?")
        if ret not in ["y", "yes"]:
            return
        
    market = Market(steem_instance=stm)
    if not unlock_wallet(stm):
        return
    tx = market.sell(account, amount, token, price)
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('order_type', nargs=1)
@click.argument('order_id', nargs=1, required=False)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
@click.option('--yes', '-y', help='Answer yes to all questions', is_flag=True, default=False)
def cancel(order_type, order_id, account, yes):
    """Cancel a buy/sell order
    
        order_type is either sell or buy
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    if account is None:
        account = stm.config["default_account"]
    market = Market(steem_instance=stm)
    if not unlock_wallet(stm):
        return
    if order_id is None and order_type == "buy":
        wallet = Wallet(account, steem_instance=stm)
        for t in wallet:
            token = t["symbol"]
            buy_book = market.get_buy_book(token, account)
            sorted_buy_book = sorted(buy_book, key=lambda account: float(account["price"]), reverse=True)    
            for order in sorted_buy_book:
                print("Cancel sell order with id: %s for %.8f %s at %s" % (order["_id"], float(order["quantity"]), token, float(order["price"])))
                if not yes:
                    ret = input("continue [y/n]?")
                    if ret not in ["y", "yes"]:
                        continue            
                tx = market.cancel(account, order_type, int(order_id))
                tx = json.dumps(tx, indent=4)
                print(tx)
                if yes:
                    time.sleep(4)
        return
    elif order_id is None and order_type == "sell":
        wallet = Wallet(account, steem_instance=stm)
        for t in wallet:
            token = t["symbol"]
            sell_book = market.get_sell_book(token, account)
            sorted_sell_book = sorted(sell_book, key=lambda account: float(account["price"]), reverse=True)    
            for order in sorted_sell_book:
                print("Cancel sell order with id: %s for %.8f %s at %s" % (order["_id"], float(order["quantity"]), token, float(order["price"])))
                if not yes:
                    ret = input("continue [y/n]?")
                    if ret not in ["y", "yes"]:
                        continue            
                tx = market.cancel(account, order_type, int(order_id))
                tx = json.dumps(tx, indent=4)
                print(tx)
                if yes:
                    time.sleep(4)                
        return        
    tx = market.cancel(account, order_type, int(order_id))
    tx = json.dumps(tx, indent=4)
    print(tx)


@cli.command()
@click.argument('token', nargs=1, required=False)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
def buybook(token, account):
    """Returns the buy book for the given token

    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    market = Market(steem_instance=stm)
    if token is None:
        if account is None:
            account = stm.config["default_account"]        
        wallet = Wallet(account, steem_instance=stm)
        table = PrettyTable(["token", "order_id", "account", "quantity", "price"])
        table.align = "l"        
        for t in wallet:
            token = t["symbol"]
            buy_book = market.get_buy_book(token, account)
            sorted_buy_book = sorted(buy_book, key=lambda account: float(account["price"]), reverse=True)    
            for order in sorted_buy_book:
                table.add_row([token, order["_id"], order["account"], order["quantity"], order["price"]])   
        print(table.get_string())   
    else:    
        buy_book = market.get_buy_book(token, account)
        sorted_buy_book = sorted(buy_book, key=lambda account: float(account["price"]), reverse=True)
        t = PrettyTable(["order_id", "account", "quantity", "price"])
        t.align = "l"
        for order in sorted_buy_book:
            t.add_row([order["_id"], order["account"], order["quantity"], order["price"]])
        print(t.get_string())    


@cli.command()
@click.argument('token', nargs=1, required=False)
@click.option('--account', '-a', help='Buy with this account (defaults to "default_account")')
def sellbook(token, account):
    """Returns the sell book for the given token
    """
    stm = shared_blockchain_instance()
    if stm.rpc is not None:
        stm.rpc.rpcconnect()
    if not stm.is_steem:
        print("Please set a Steem node")
        return
    market = Market(steem_instance=stm)
    if token is None:
        if account is None:
            account = stm.config["default_account"]        
        wallet = Wallet(account, steem_instance=stm)
        table = PrettyTable(["token", "order_id", "account", "quantity", "price"])
        table.align = "l"        
        for t in wallet:
            token = t["symbol"]
            sell_book = market.get_sell_book(token, account)
            sorted_sell_book = sorted(sell_book, key=lambda account: float(account["price"]), reverse=False)  
            for order in sorted_sell_book:
                table.add_row([token, order["_id"], order["account"], order["quantity"], order["price"]])   
        print(table.get_string())   
    else:    
        sell_book = market.get_sell_book(token, account)
        sorted_sell_book = sorted(sell_book, key=lambda account: float(account["price"]), reverse=False)
        t = PrettyTable(["order_id", "account", "quantity", "price"])
        t.align = "l"
        for order in sorted_sell_book:
            t.add_row([order["_id"], order["account"], order["quantity"], order["price"]])
        print(t.get_string())  


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ['SSL_CERT_FILE'] = os.path.join(sys._MEIPASS, 'lib', 'cert.pem')
        cli(sys.argv[1:])
    else:
        cli()

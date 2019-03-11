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
from beem.instance import set_shared_steem_instance, shared_steem_instance
from steemengine.version import version as __version__
click.disable_unicode_literals_warning = True
log = logging.getLogger(__name__)


@click.group(chain=True)
@click.option(
    '--verbose', '-v', default=3, help='Verbosity')
@click.version_option(version=__version__)
def cli(verbose):
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
                    if key in ["$loki", "symbol"]:
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
            t = PrettyTable(["id", "symbol", "balance"])
            t.align = "l"
            for token in wallet:
                t.add_row([token["$loki"], token["symbol"], token["balance"]])
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


if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        os.environ['SSL_CERT_FILE'] = os.path.join(sys._MEIPASS, 'lib', 'cert.pem')
        cli(sys.argv[1:])
    else:
        cli()

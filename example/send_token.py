from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
from datetime import datetime, timedelta
import time
import io
import logging
from beem import Steem
from steemengine.api import Api
from beembase import transactions, operations
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    stm = Steem()
    stm.wallet.unlock(pwd="pwd123")
    
    api = Api()
    balance = api.find("tokens", "balances", query={"account": "beembot", "symbol": "DRAGON"})
    
    if len(balance) > 0 and balance[0]["balance"] >= 0.01:
        print(balance[0])
        json_data = {"contractName":"tokens","contractAction":"transfer","contractPayload":{"symbol":"DRAGON","to":"holger80","quantity":0.01,"memo":"Test"}}
        
        op = operations.Custom_json(
            **{
                "json": json_data,
                "required_auths": ["beembot"],
                "required_posting_auths": [],
                "id": "	ssc-mainnet1",
                "prefix": "STM",
            })
        print(stm.finalizeOp(op, "beembot", "active"))
        
    else:
        print("Could not sent")
    balance = api.find("tokens", "balances", query={"account": "beembot", "symbol": "DRAGON"})
    print("new balance %.2f" % balance[0]["balance"])

    
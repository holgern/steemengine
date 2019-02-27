# steemengine
Python tools for obtaining and processing steem engine tokens

[![Build Status](https://travis-ci.org/holgern/steemengine.svg?branch=master)](https://travis-ci.org/holgern/steemengine)

## Installation
```
pip install steemengine
```


## Commands
Get the latest block of the sidechain
```
from steemengine.api import Api
api = Api()
print(api.getLatestBlockInfo())
```

Get the block with the specified block number of the sidechain
```
from steemengine.api import Api
api = Api()
print(api.getBlockInfo(1910))
```

Retrieve the specified transaction info of the sidechain
```
from steemengine.api import Api
api = Api()
print(api.getTransactionInfo("e6c7f351b3743d1ed3d66eb9c6f2c102020aaa5d"))
```

Get the contract specified from the database
```
from steemengine.api import Api
api = Api()
print(api.getContract("tokens"))
```

Get an array of objects that match the query from the table of the specified contract
```
from steemengine.api import Api
api = Api()
print(api.find("tokens", "tokens"))
```

Get the object that matches the query from the table of the specified contract
```
from steemengine.api import Api
api = Api()
print(api.findOne("tokens", "tokens"))
```

Get the transaction history for an account and a token
```
from steemengine.api import Api
api = Api()
print(api.get_history("holger80", "NINJA"))
```
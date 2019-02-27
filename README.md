# steemengine
Python tools for obtaining and processing steem engine tokens

[![Build Status](https://travis-ci.org/holgern/steemengine.svg?branch=master)](https://travis-ci.org/holgern/steemengine)

## Installation
```
pip install steemengine
```


## Commands
```
from steemengine.api import Api
api = Api()
print(api.getLatestBlockInfo())
```

```
from steemengine.api import Api
api = Api()
print(api.getBlockInfo(1910))
```

```
from steemengine.api import Api
api = Api()
print(api.getContract("tokens"))
```

```
from steemengine.api import Api
api = Api()
print(api.find("tokens", "tokens"))
```

```
from steemengine.api import Api
api = Api()
print(api.findOne("tokens", "tokens"))
```

```
from steemengine.api import Api
api = Api()
print(api.get_history("holger80", "NINJA"))
```
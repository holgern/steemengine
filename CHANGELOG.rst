## 0.4.0
* quantize added to Token class
* TokenDoesNotExists is raised in the Token class when token does not exists
* Exception InvalidTokenAmount is raised when amount to transfer or to issue is below precision
* new issue function added to wallet
* token precision is taken into account for transfer and issue
* TokenIssueNotPermitted is raised when an account which is not the token issuer tries to issue
* Add amount quantization to deposit, withdraw, buy and sell
* Add transfer, issue, withdraw, deposit, buy, sell, cancel, buybook, sellbook to CLI

## 0.3.1
* Fix circular dependency

## 0.3.0
* Token class added, allows to get information about markets, holder and the token itself
* CLI added for showing information about blocks, transaction, token and accounts
* more unit tests
* buy/sell book for account added

## 0.2.0
* Market, Tokens and Wallet class added
* Token transfer are possible
* Market buy/sell/cancel of token is possible
* deposit/withdrawel added

## 0.1.0
* Inital version
* Api class added
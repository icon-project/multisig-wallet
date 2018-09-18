## Multi Signature Wallet SCORE
This document describes a Multi Signature Wallet SCORE and provides guide line and APIs of how to use this service.

## Definition & Purpose

Multi Signature Wallet is a SCORE that makes more than one users managing ICON funds safely.  Multi Signature Wallet can prevent one person from running off with the icx or tokens and reduce key person risk in case one person is incapacitated or loses their keys. We adopted multisig wallet mechanism inspired by **gnosis**.

## How To Use
#### Definition

##### Wallet
SCORE which ICX and tokens are stored in. stored icx and tokens can be used(transferred) only when satisfying Internally set conditions of wallet.

##### Wallet owner
addresses who have Participation rights of Wallet SCORE. 

##### Transaction
transaction which wallet owner initiate to change wallet's state(e.g. transfer tokens or ICX which is stored in wallet, add new wallet owner, change requirements of confirmations(2to3 -> 3to3) etc).

##### Requirement
The number of approvals of the wallet owner required for the Transaction to actually execute.

#### Logic

First step is deploying multisig wallet SCORE. At the time of deployment, you can set wallet owners and requirement.  For examples, if you want to use wallet which set three wallet owners and needs two confirmations for executing a transaction(2 to 3), you have to input two parameters 1) three wallet addresses of string,  2) required '2' when deploying wallet

(e.g. "_walletOwners": "hx4fd1~, hx9f31~, hxbf9~", "_required": "2")

After deploying wallet, wallet owners can deposit ICX and tokens(simply 'send icx' and 'transfer' token to wallet) and manage it. When using funds or changing Internally set conditions, use ```submitTransaction``` method. For example, if you want to send 10 ICX to specific address, call ```submitTransaction``` with ballow parameters.
```json
{
    '_destination': "hx43fe2~",
 	'_method': "",
    '_params': "",
    '_description': 'send 10 icx to token score',
    '_value': '0x0a'
}
```
After the transaction is registered, other wallet owners can confirm to this transaction using ```confirmTransaction``` method, and if the number of confirmations meets 'requrement', finally 'sending 10 icx' is executed. all transactions' information is saved in wallet eternally.

## Specification

### Methods(Read-only)

ballow is list of read-only method. by calling these method, you can get information of wallet.

#### getRequirements
```python
@external(readonly=True)
def getRequirements(self) -> int:
```

#### getTransactionInfo
```python
@external(readonly=True)
def getTransactionInfo(self, _transactionId: int) -> bytes:
```

#### getTransactionsExecuted
```python
@external(readonly=True)
def getTransactionsExecuted(self, _transactionId: int) -> bool:
```

####  checkIsWalletOwner
```python
@external(readonly=True)
def checkIsWalletOwner(self, _walletOwner: Address)-> bool:
```

#### getWalletOwners
```python
@external(readonly=True)
def getWalletOwners(self, _from: int, _to: int)-> list:
```

#### getConfirmationCount
```python
@external(readonly=True)
def getConfirmationCount(self, _transactionId: int)-> int:
```

#### getConfirmations
```python
@external(readonly=True)
def getConfirmations(self, _from: int, _to: int, _transactionId: int)-> list:
```
#### getTransactionCount
```python
@external(readonly=True)
def getTransactionCount(self, _pending: bool=True, _executed: bool=True)-> int:
```
#### getTransactionIds
```python
@external(readonly=True)
def getTransactionIds(self, _from: int, _to: int, _pending: bool=True, _executed: bool=True)-> list:
```


### Methods

ballow is list of method. 

#### submitTransaction

```python
@external
def submitTransaction(self, _destination: Address, _method: str="", _params: str="", _value: int=0, _description: str=""):

```

#### confirmTransaction
```python
@external
def confirmTransaction(self, _transactionId: int):
```
#### revokeTransaction
```python
@external
def revokeTransaction(self, _transactionId: int):
```
### Methods(Only called by wallet)

#### addWalletOwner

```python
@external
def addWalletOwner(self, _walletOwner: Address):
```
#### replaceWalletOwner
```python
@external
def replaceWalletOwner(self, _walletOwner: Address, _newWalletOwner: Address):
```
#### removeWalletOwner
```python
@external
def removeWalletOwner(self, _walletOwner: Address):
```
#### changeRequirement
```python
@external
def changeRequirement(self, _required: int):
```

### Eventlogs

#### Confirmation
```python
@eventlog(indexed=2)
def Confirmation(self, _sender: Address, _transactionId: int):
        pass
```
#### Revocation
```python
@eventlog(indexed=2)
def Revocation(self, _sender: Address, _transactionId: int):
        pass
```
#### Submission
```python
@eventlog(indexed=1)
def Submission(self, _transactionId: int):
        pass
```
#### Execution
```python
@eventlog(indexed=1)
def Execution(self, _transactionId: int):
        pass
```
#### ExecutionFailure
```python
@eventlog(indexed=1)
def ExecutionFailure(self, _transactionId: int):
        pass
```
#### Deposit
```python
@eventlog(indexed=1)
def Deposit(self, _sender: Address, _value: int):
        pass
```
#### DepsitToken
```python
@eventlog(indexed=1)
def DepositToken(self, _sender: Address, _value: int, _data: bytes):
        pass
```
#### WalletOwnerAddition
```python
@eventlog(indexed=1)
def WalletOwnerAddition(self, _walletOwner: Address):
        pass
```
#### WalletOwnerRemoval
```python
@eventlog(indexed=1)
def WalletOwnerRemoval(self, _walletOwner: Address):
        pass
```
#### Requirement
```python
@eventlog
def RequirementChange(self, _required: int):
        pass
```

## Implementation
* will be updated

## References
* [https://github.com/gnosis/MultiSigWallet](https://github.com/gnosis/MultiSigWallet)

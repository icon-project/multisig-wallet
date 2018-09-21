## Multi Signature Wallet SCORE
This document describes a Multi Signature Wallet SCORE and provides guide line and APIs of how to use this service.

## Definition & Purpose

Multi Signature Wallet is a SCORE that makes more than one users managing ICON funds safely.  Multi Signature Wallet can prevent one person from running off with the icx or tokens and reduce key person risk in case one person is incapacitated or loses their keys. We adopted multisig wallet mechanism inspired by **gnosis**.

## How To Use
### Definition

#### Wallet
SCORE which ICX and tokens are stored in. stored icx and tokens can be used(transferred) only when satisfying Internally set conditions of wallet.

#### Wallet owner
Addresses who have Participation rights of Wallet SCORE. 

#### Transaction
Transaction which wallet owner initiate to change wallet's state(e.g. transfer tokens or ICX which is stored in wallet, add new wallet owner, change requirements of confirmations(2to3 -> 3to3) etc).

#### Requirement
The number of approvals of the wallet owners required for the transaction to be executed.

### Logic

First step is deploying multisig wallet SCORE. At the time of deployment, you can set wallet owners and requirement.  For examples, if you want to use wallet which is set three wallet owners and needs two confirmations for executing a transaction(2 to 3), you have to input two parameters 1) three wallet addresses of string,  2) required '2' when deploying wallet.

```json
{
    "_walletOwners": "hx4fd1~, hx9f31~, hxbf9~",
 	"_required": "2"
}
```

After deploying wallet, wallet owners can deposit ICX and tokens(simply 'send icx' and 'transfer' token to the wallet) and manage it. When using funds or changing Internally set conditions, use ```submitTransaction``` method. For example, if you want to send 10 ICX to the specific address, call ```submitTransaction``` with below parameters.
```json
{
    "_destination": "hx43fe2~",
 	"_method": "",
    "_params": "",
    "_description": "send 10 icx to token score",
    "_value": "0x0a"
}
```
After the transaction is registered, other wallet owners can confirm to this transaction using ```confirmTransaction``` method, and if the number of confirmations meets 'requrement', finally 'sending 10 icx' is executed. all transactions' information is saved in wallet eternally.

## Specification

### Methods(Read-only)

Below is list of read-only method. by calling these method, you can get information of wallet.

#### getRequirements

Returns the requirements.

```python
@external(readonly=True)
def getRequirements(self) -> int:
```

#### getTransactionInfo

Returns the transaction data for each id.

```python
@external(readonly=True)
def getTransactionInfo(self, _transactionId: int) -> dict:
```

#### getTransactionsExecuted

Returns boolean which shows whether transaction is executed or not.

```python
@external(readonly=True)
def getTransactionsExecuted(self, _transactionId: int) -> bool:
```

####  checkIsWalletOwner

Return boolean which shows whether address is wallet owner or not.

```python
@external(readonly=True)
def checkIsWalletOwner(self, _walletOwner: Address)-> bool:
```

#### getWalletOwners

Return list of wallet owners.

```python
@external(readonly=True)
def getWalletOwners(self, _from: int, _to: int)-> list:
```

#### getConfirmationCount

Return each transactions' confirmation count.

```python
@external(readonly=True)
def getConfirmationCount(self, _transactionId: int)-> int:
```

#### getConfirmations

Return list of wallet owner who have been confirmed to the transaction.

```python
@external(readonly=True)
def getConfirmations(self, _from: int, _to: int, _transactionId: int)-> list:
```
#### getTransactionCount

Return total number of transactions which is submitted in the wallet.

```python
@external(readonly=True)
def getTransactionCount(self, _pending: bool=True, _executed: bool=True)-> int:
```
#### getTransactionList

Return list of transaction.

```python
@external(readonly=True)
def getTransactionList(self, _offset: int, _count: int, _pending: bool=True, _executed: bool=True)-> list:
```



### Methods

Below is a list of the method which wallet owner can call.  

#### submitTransaction

Submit transaction which is to be executed when the number of confirmations meets 'requrement'. Only wallet owners can call this method. The wallet owner who has called this method be confirmed to this transaction as soon as submit transaction successfully.

```python
@external
def submitTransaction(self, _destination: Address, _method: str="", _params: str="", _value: int=0, _description: str=""):

```

#### confirmTransaction

Confirm a transaction corresponding to ```_transactionId```. as soon as a transaction's confirmation count meets  'requrement', transaction is executed. Only wallet owners can call this method.

```python
@external
def confirmTransaction(self, _transactionId: int):
```
#### revokeTransaction

Revoke confirmation of a transaction corresponding to  ```_transactionId```.  Only already confirmed wallet owner can revoke there own confirmation of a transaction. Wallet owner can't revoke others confirmation.

```python
@external
def revokeTransaction(self, _transactionId: int):
```


### Methods(Only called by wallet)

These methods only can be called by multisig wallet SCORE itself. If you want to execute these methods, call ```submitTransaction``` and input method's information as a parameter.

#### addWalletOwner

Add new wallet owner. 

```python
@external
def addWalletOwner(self, _walletOwner: Address):
```
#### replaceWalletOwner

Replace existing wallet owner to new wallet owner.

```python
@external
def replaceWalletOwner(self, _walletOwner: Address, _newWalletOwner: Address):
```
#### removeWalletOwner

Remove existing wallet owner.

```python
@external
def removeWalletOwner(self, _walletOwner: Address):
```
#### changeRequirement

Change requirement. ```_required``` can't exceed the number of wallet owner. 

```python
@external
def changeRequirement(self, _required: int):
```



### Eventlogs

#### Confirmation

Must trigger on any successful confirmation.

```python
@eventlog(indexed=2)
def Confirmation(self, _sender: Address, _transactionId: int):
        pass
```
#### Revocation

Must trigger on revoke confirmation.

```python
@eventlog(indexed=2)
def Revocation(self, _sender: Address, _transactionId: int):
        pass
```
#### Submission

Must trigger on submit transaction.

```python
@eventlog(indexed=1)
def Submission(self, _transactionId: int):
        pass
```
#### Execution

Must trigger on the transaction being executed successfully.

```python
@eventlog(indexed=1)
def Execution(self, _transactionId: int):
        pass
```
#### ExecutionFailure

Must trigger on a failure of the transaction execution.

```python
@eventlog(indexed=1)
def ExecutionFailure(self, _transactionId: int):
        pass
```
#### Deposit

Must trigger on deposit ICX to MultiSig Wallet SCORE.

```python
@eventlog(indexed=1)
def Deposit(self, _sender: Address, _value: int):
        pass
```
#### DepsitToken

Must trigger on deposit token to MultiSig Wallet SCORE.

```python
@eventlog(indexed=1)
def DepositToken(self, _sender: Address, _value: int, _data: bytes):
        pass
```
#### WalletOwnerAddition

Must trigger on adding new wallet owner.

```python
@eventlog(indexed=1)
def WalletOwnerAddition(self, _walletOwner: Address):
        pass
```
#### WalletOwnerRemoval

Must trigger on removing wallet owner.

```python
@eventlog(indexed=1)
def WalletOwnerRemoval(self, _walletOwner: Address):
        pass
```
#### Requirement

Must trigger on changing requirement.

```python
@eventlog
def RequirementChange(self, _required: int):
        pass
```

## Implementation
* will be updated

## References
* [https://github.com/gnosis/MultiSigWallet](https://github.com/gnosis/MultiSigWallet)


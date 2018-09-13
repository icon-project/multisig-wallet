from iconservice import *
from .type_converter.type_converter import params_type_converter
from .qualification_check.qualification_check import *

from struct import Struct, pack, unpack
import json

#Todo: modify values
VALUE_BYTES = 32
ADDRESS_BYTES = 21
METHOD_BYTES = 50
PARAMS_BYTES = 150
DESCRIPTION_BYTES = 50
DATA_BYTE_ORDER = 'big'


class Transaction:
    _struct = \
        Struct(f'>?x{ADDRESS_BYTES}sx{METHOD_BYTES}sx{PARAMS_BYTES}sx{VALUE_BYTES}sx{DESCRIPTION_BYTES}s')

    def __init__(self,
                 destination: Address,
                 method: str,
                 params: str,
                 value: int,
                 description: str,
                 executed: bool=False):

        self._executed = executed
        self._destination = destination
        # as None type can't be converted to bytes, must be changed to ""
        self._method = "" if method is None else method
        self._params = "" if params is None else params
        self._value = value
        self._description = description

    @property
    def executed(self) -> bool:
        return self._executed

    @executed.setter
    def executed(self, executed: bool):
        self._executed = executed

    @property
    def destination(self) -> Address:
        return self._destination

    @property
    def method(self) -> str:
        return self._method

    @property
    def params(self) -> str:
        return self._params

    @property
    def value(self) -> int:
        return self._value

    @property
    def description(self) -> str:
        return self._description

    @staticmethod
    def from_bytes(buf: bytes):
        executed, destination, method, params, value, description = \
            Transaction._struct.unpack(buf)

        return Transaction(executed=bool(executed),
                           destination=Address.from_bytes(destination.strip(b'\x00')),
                           method=method.strip(b'\x00').decode(encoding="utf-8"),
                           params=params.strip(b'\x00').decode(encoding="utf-8"),
                           value=int.from_bytes(value, DATA_BYTE_ORDER),
                           description=description.strip(b'\x00').decode(encoding="utf-8"))

    def to_bytes(self) -> bytes:
        transaction = Transaction._struct.pack\
            (self._executed,
             self._destination.to_bytes(),
             self._method.encode(encoding="utf-8"),
             self._params.encode(encoding="utf-8"),
             #Todo: need to be refactoring
             self._value.to_bytes(VALUE_BYTES, DATA_BYTE_ORDER),
             self._description.encode(encoding="utf-8"))
        print(transaction)
        return transaction


class MultiSigWallet(IconScoreBase, IconScoreException):
    _MAX_WALLET_OWNER_COUNT = 50

    @eventlog(indexed=2)
    def Confirmation(self, _sender: Address, _transactionId: int):
        pass

    @eventlog(indexed=2)
    def Revocation(self, _sender: Address, _transactionId: int):
        pass

    @eventlog(indexed=1)
    def Submission(self, _transactionId: int):
        pass

    @eventlog(indexed=1)
    def Execution(self, _transactionId: int):
        pass

    @eventlog(indexed=1)
    def ExecutionFailure(self, _transactionId: int):
        pass

    @eventlog(indexed=1)
    def Deposit(self, _sender: Address, _value: int):
        pass

    @eventlog(indexed=1)
    def DepositToken(self, _sender: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=1)
    def WalletOwnerAddition(self, _walletOwner: Address):
        pass

    @eventlog(indexed=1)
    def WalletOwnerRemoval(self, _walletOwner: Address):
        pass

    @eventlog
    def RequirementChange(self, _required: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        # _transactions_info's key: transaction_id(int type)
        self._transactions = DictDB('transactions', db, value_type=bytes)
        # _confirmations's key: transaction_id(int type), address(Address type)
        self._confirmations = DictDB('confirmations', db, value_type=bool, depth=2)
        # _is_wallet_owner's key: address(Address type)
        self._is_wallet_owner = DictDB('is_wallet_owner', db, value_type=bool)
        self._wallet_owners = ArrayDB('wallet_owners', db, value_type=Address)
        self._required = VarDB('required', db, value_type=int)
        self._transaction_count = VarDB('transactionCount', db, value_type=int)

    def on_install(self, _walletOwners: str, _required: int) -> None:
        super().on_install()

        _walletOwners = _walletOwners.replace(" ", "").split(',')
        for wallet_owner in _walletOwners:
            wallet_owner_addr = Address.from_string(wallet_owner)
            self._wallet_owners.put(wallet_owner_addr)
            self._is_wallet_owner[wallet_owner_addr] = True

        self._required = _required
        self._transaction_count = 0

    def on_update(self) -> None:
        super().on_update()

    def _is_convertible_params_format(self, json_formatted_params: str):
        # when user input None as a _params' value,
        # this will be changed to "" when set Transaction structure
        # "" will be changed to {} when finally execute transaction. so doesn't check format
        if json_formatted_params != "" and json_formatted_params is not None:
            try:
                params = json.loads(json_formatted_params)
                for param in params:
                    params_type_converter(param['type'], param['value'])
            except ValueError as e:
                self.revert(f"json format error: {e}")
            except IconScoreException as e:
                self.revert(f"{e}")
            except:
                self.revert(f"can't convert params json data, check the format")

    def not_null(self, address: Address):
        #Todo: check this parts
        hx_null = Address.from_string("hx0000000000000000000000000000000000000000")
        cx_null = Address.from_string("cx0000000000000000000000000000000000000000")
        if address== hx_null or address == cx_null:
            self.revert("invalid address")

    def wallet_owner_does_not_exist(self, wallet_owner: Address):
        if self._is_wallet_owner[wallet_owner] is True:
            self.revert(f"{wallet_owner} is already exist as a owner of wallet")

    def wallet_owner_exist(self, wallet_owner: Address):
        if self._is_wallet_owner[wallet_owner] is False:
            self.revert(f"{wallet_owner} is not a owner of wallet")

    def transaction_exists(self, transaction_id: int):
        if self._transactions[transaction_id] is None or self._transaction_count <= transaction_id:
            self.revert(f"transaction id '{transaction_id}' is not exist")

    def confirmed(self, transaction_id: int, wallet_owner: Address):
        if self._confirmations[transaction_id][wallet_owner] is False:
            self.revert(f"{wallet_owner} hasn't confirmed to transaction id '{transaction_id}' yet")

    def not_confirmed(self, transation_id: int, wallet_owner: Address):
        if self._confirmations[transation_id][wallet_owner] is True:
            self.revert(f"{wallet_owner} has already confirmed to transaction '{transation_id}'")

    def not_executed(self, transaction_id: int):
        if self._transactions[transaction_id][0] is True:
            self.revert(f"transaction id '{transaction_id}' has already executed")

    def valid_requirement(self, wallet_owner_count: int, required: int):
        if wallet_owner_count > self._MAX_WALLET_OWNER_COUNT or \
                required > wallet_owner_count or \
                required <= 0 or \
                wallet_owner_count == 0:
            self.revert(f"invalid requirement")

    @payable
    def fallback(self):
        if self.msg.value > 0:
            # event log
            self.Deposit(self.msg.sender, self.msg.value)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        if _value > 0:
            self.DepositToken(_from, _value, _data)

    @external
    def submitTransaction(self, _destination: Address, _method: str="", _params: str="", _value: int=0, _description: str=""):
        # supplement from gnosis
        self.wallet_owner_exist(self.msg.sender)
        # reason why expand the scope of validation is
        # to prevent failure of executing transaction caused by 'params' conversion problems
        self._is_convertible_params_format(_params)

        # add transaction
        transaction_id = self._add_transaction(_destination, _method, _params, _value, _description)
        # confirm_transaction
        self.confirmTransaction(transaction_id)

    @external
    def confirmTransaction(self, _transactionId: int):
        self.wallet_owner_exist(self.msg.sender)
        self.transaction_exists(_transactionId)
        self.not_confirmed(_transactionId, self.msg.sender)

        self._confirmations[_transactionId][self.msg.sender] = True
        # event log
        self.Confirmation(self.msg.sender, _transactionId)

        self._execute_transaction(_transactionId)

    @external
    def revokeTransaction(self, _transactionId: int):
        self.wallet_owner_exist(self.msg.sender)
        self.transaction_exists(_transactionId)
        self.not_executed(_transactionId)
        self.confirmed(_transactionId, self.msg.sender)

        self._confirmations[_transactionId][self.msg.sender] = False
        # eventlog
        self.Revocation(self.msg.sender, _transactionId)

    def _add_transaction(self, destination: Address, method: str, params: str, value: int, description: str) ->int:
        self.not_null(destination)

        transaction = Transaction(destination=destination,
                                  method=method,
                                  params=params,
                                  value=value,
                                  description=description
                                  )
        transaction_id = self._transaction_count

        self._transactions[transaction_id] = transaction.to_bytes()
        self._transaction_count = transaction_id + 1
        # event log
        self.Submission(transaction_id)
        return transaction_id

    def _execute_transaction(self, transaction_id: int):
        # as this method can't be called from other SCORE or EOA, doesn't check owner, transactions_id, confirmations.
        # (already checked in confirmTransaction method)
        if self._is_confirmed(transaction_id):
            txn = self._transactions[transaction_id]
            if self._external_call(txn):
                self._transactions[transaction_id] = True.to_bytes(1, 'big') + self._transactions[transaction_id][1:]
                # event log
                self.Execution(transaction_id)
            else:
                # event log
                self.ExecutionFailure(transaction_id)

    def _external_call(self, serialized_tx: bytes)->bool:
        transaction = Transaction.from_bytes(serialized_tx)

        # if method == "" -> None
        method_name = None if transaction.method == "" else transaction.method
        # if params == "" -> {}
        method_params = {}
        if transaction.params != "":
            params = json.loads(transaction.params)
            for param in params:
                method_params[param['name']] = params_type_converter(param['type'], param['value'])

        try:
            if transaction.destination.is_contract:
                self.call(addr_to=transaction.destination,
                          func_name=method_name,
                          kw_dict=method_params,
                          amount=transaction.value)
            else:
                self.icx.transfer(transaction.destination, transaction.value)
            execute_result = True
        except:
            execute_result = False

        return execute_result

    def _is_confirmed(self, transaction_id) -> bool:
        count = 0
        for wallet_owner in self._wallet_owners:
            if self._confirmations[transaction_id][wallet_owner] is True:
                count += 1

        return count == self._required

    @only_wallet
    @external
    def addWalletOwner(self, _walletOwner: Address):
        self.wallet_owner_does_not_exist(_walletOwner)
        self.not_null(_walletOwner)
        # check if owner's count exceed _MAX_OWNER_COUNT
        self.valid_requirement(len(self._wallet_owners) + 1, self._required)

        self._wallet_owners.put(_walletOwner)
        self._is_wallet_owner[_walletOwner] = True
        # event log
        self.WalletOwnerAddition(_walletOwner)

    @only_wallet
    @external
    def replaceWalletOwner(self, _walletOwner: Address, _newWalletOwner: Address):
        self.wallet_owner_exist(_walletOwner)
        self.wallet_owner_does_not_exist(_newWalletOwner)

        for idx, wallet_owner in enumerate(self._wallet_owners):
            if wallet_owner == _walletOwner:
                self._wallet_owners[idx] = _newWalletOwner
                break

        del self._is_wallet_owner[_walletOwner]
        self._is_wallet_owner[_newWalletOwner] = True

        # event log
        self.WalletOwnerRemoval(_walletOwner)
        self.WalletOwnerAddition(_newWalletOwner)

    @only_wallet
    @external
    def removeWalletOwner(self, _walletOwner: Address):
        self.wallet_owner_exist(_walletOwner)
        # if all owners are removed, this contract can not be executed.
        # so check if _owner is only one left in this wallet
        self.valid_requirement(len(self._wallet_owners) - 1, self._required)

        for idx, wallet_owner in enumerate(self._wallet_owners):
            if wallet_owner == _walletOwner:
                self._wallet_owners[idx] = self._wallet_owners.pop()
                break

        del self._is_wallet_owner[_walletOwner]
        # event log
        self.WalletOwnerRemoval(_walletOwner)

    @only_wallet
    @external
    def changeRequirement(self, _required: int):
        self.valid_requirement(len(self._wallet_owners), _required)

        self._required = _required
        # event log
        self.RequirementChange(_required)

    #TODO: check external readonly method need to check params' data
    @external(readonly=True)
    def getRequirements(self) -> int:
        return self._required

    @external(readonly=True)
    def getTransactionInfo(self, _transactionId: int) -> bytes:
        #Todo: need to be changed: return informative data
        return self._transactions[_transactionId]

    @external(readonly=True)
    def getTransactionsExecuted(self, _transactionId: int) -> bool:
        return self._transactions[_transactionId][0]

    @external(readonly=True)
    def checkIsWalletOwner(self, _walletOwner: Address)-> bool:
        return self._is_wallet_owner[_walletOwner]

    @external(readonly=True)
    def getWalletOwners(self, _from: int, _to: int)-> list:
        wallet_owner_list = []
        for idx, wallet_owner in enumerate(self._wallet_owners, start=_from):
            if idx == _to:
                break
            wallet_owner_list.append(wallet_owner)

        return wallet_owner_list

    @external(readonly=True)
    def getConfirmationCount(self, _transactionId: int)-> int:
        count = 0
        for wallet_owner in self._wallet_owners:
            if self._confirmations[_transactionId][wallet_owner]:
                count += 1
        return count

    @external(readonly=True)
    def getConfirmations(self, _from: int, _to: int, _transactionId: int)-> list:
        confirmed_addrs = []
        for idx, wallet_owner in enumerate(self._wallet_owners, start=_from):
            if idx == _to:
                break
            if self._confirmations[_transactionId][wallet_owner]:
                confirmed_addrs.append(wallet_owner)

        return confirmed_addrs

    @external(readonly=True)
    def getTransactionCount(self, _pending: bool, _executed: bool)-> int:
        tx_count = 0
        for tx_id in range(self._transaction_count):
            if (_pending and not self._transactions[tx_id][0]) or (_executed and self._transactions[tx_id][0]):
                tx_count += 1

        return tx_count

    @external(readonly=True)
    def getTransactionIds(self, _from: int, _to: int, _pending: bool, _executed: bool)-> list:
        transaction_ids = []
        for tx_id in range(_from, _to):
            if (_pending and not self._transactions[tx_id][0]) or (_executed and self._transactions[tx_id][0]):
                transaction_ids.append(tx_id)

        return transaction_ids

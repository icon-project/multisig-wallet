from iconservice import *
from .type_converter.type_converter import params_type_converter
from .qualification_check.qualification_check import *

from struct import Struct, pack, unpack
import json


class Transaction:
    _struct = Struct(f'>?x21sx150sx300sx32sx300s')

    def __init__(self,
                 destination: Address,
                 method: str,
                 params: str,
                 value: int,
                 description: str,
                 executed: bool=False):

        self._executed = executed
        self._destination = destination
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

    @destination.setter
    def destination(self, destination: Address):
        self._destination = destination

    @property
    def method(self) -> str:
        return self._method

    @method.setter
    def method(self, method: str):
        self._method = method

    @property
    def params(self) -> str:
        return self._params

    @params.setter
    def params(self, params: str):
        self._params = params

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, value: str):
        self._value = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, description: str):
        self._description = description

    @staticmethod
    def from_bytes(buf: bytes):
        executed, destination, method, params, value, description = \
            Transaction._struct.unpack(buf)

        return Transaction(Address.from_bytes(destination.strip(b'\x00')),
                           method.strip(b'\x00').decode(encoding="utf-8"),
                           params.strip(b'\x00').decode(encoding="utf-8"),
                           int.from_bytes(value, 'big'),
                           description.strip(b'\x00').decode(encoding="utf-8"),
                           bool(executed))

    def to_bytes(self) -> bytes:
        transaction = Transaction._struct.pack\
            (self._executed,
             self._destination.to_bytes(),
             self._method.encode(encoding="utf-8"),
             self._params.encode(encoding="utf-8"),
             #Todo: need to be refactoring
             self._value.to_bytes(32, 'big'),
             self._description.encode(encoding="utf-8"))
        print(transaction)
        return transaction

class MultiSigWallet(IconScoreBase, IconScoreException):
    _MAX_OWNER_COUNT = 50

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
    def OwnerAddition(self, _owner: Address):
        pass

    @eventlog(indexed=1)
    def OwnerRemoval(self, _owner: Address):
        pass

    @eventlog
    def RequirementChange(self, _required: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        #Todo: change transaction data to Struct
        # _transactions_info's key: transaction_id(int type)
        self._transactions = DictDB('transactions', db, value_type=bytes)
        # _confirmations's key: transaction_id(int type), address(Address type)
        self._confirmations = DictDB('confirmations', db, value_type=bool, depth=2)
        # _is_owner's key: address(Address type)
        self._is_owner = DictDB('is_owner', db, value_type=bool)
        self._owners = ArrayDB('owners', db, value_type=Address)
        self._required = VarDB('required', db, value_type=int)
        self._transaction_count = VarDB('transactionCount', db, value_type=int)

    def on_install(self, _owners: str, _required: int) -> None:
        super().on_install()

        _owners = _owners.replace(" ", "").split(',')
        for owner in _owners:
            owner_addr = Address.from_string(owner)
            self._owners.put(owner_addr)
            self._is_owner[owner_addr] = True

        self._required = _required
        self._transaction_count = 0

    def on_update(self) -> None:
        super().on_update()

    def _is_json(self, jsons: str):
        try:
            json.loads(jsons)
        except ValueError as e:
            self.revert(f"json format error: {e}")

    def not_null(self, address: Address):
        #Todo: check this parts
        hx_null = Address.from_string("hx0000000000000000000000000000000000000000")
        cx_null = Address.from_string("cx0000000000000000000000000000000000000000")
        if address== hx_null or address == cx_null:
            self.revert("invalid address")

    def owner_does_not_exist(self, owner: Address):
        if self._is_owner[owner] is True:
            self.revert(f"{owner} is already exist as a owner of wallet")

    def owner_exist(self, owner: Address):
        if self._is_owner[owner] is False:
            self.revert(f"{owner} is not a owner of wallet")

    def transaction_exists(self, transaction_id: int):
        if self._transactions[transaction_id] is None or self._transaction_count <= transaction_id:
            self.revert(f"transaction '{transaction_id}' is not exist")

    def confirmed(self, transaction_id: int, owner: Address):
        if self._confirmations[transaction_id][owner] is False:
            self.revert(f"{owner} hasn't confirmed to transaction '{transaction_id}' yet")

    def not_confirmed(self, transation_id: int, owner: Address):
        if self._confirmations[transation_id][owner] is True:
            self.revert(f"{owner} has already confirmed to transaction '{transation_id}'")

    def not_executed(self, transaction_id: int):
        if self._transactions[transaction_id][0] is True:
            self.revert(f"transaction '{transaction_id}' has already executed")

    def valid_requirement(self, owner_count: int, required: int):
        if owner_count > self._MAX_OWNER_COUNT or \
                required > owner_count or \
                required <= 0 or \
                owner_count == 0:
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
        self.owner_exist(self.msg.sender)

        # when user input "" or None as a _params' value,
        # this will be changed to {} so doesn't check json format
        if _params != "" and _params is not None:
            self._is_json(_params)

        # add transaction
        transaction_id = self._add_transaction(_destination, _method, _params, _value, _description)
        # confirm_transaction
        self.confirmTransaction(transaction_id)

    @external
    def confirmTransaction(self, _transaction_id: int):
        self.owner_exist(self.msg.sender)
        self.transaction_exists(_transaction_id)
        self.not_confirmed(_transaction_id, self.msg.sender)

        self._confirmations[_transaction_id][self.msg.sender] = True
        # event log
        self.Confirmation(self.msg.sender, _transaction_id)

        self._execute_transaction(_transaction_id)

    @external
    def revokeTransaction(self, _transaction_id: int):
        self.owner_exist(self.msg.sender)
        self.confirmed(_transaction_id, self.msg.sender)
        self.not_executed(_transaction_id)

        self._confirmations[_transaction_id][self.msg.sender] = False
        # eventlog
        self.Revocation(self.msg.sender, _transaction_id)

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
                #Todo: need refactoring
                transaction = bytearray(self._transactions[transaction_id])
                # change executed: False => True
                transaction[0] = True
                self._transactions[transaction_id] = bytes(transaction)
                # event log
                self.Execution(transaction_id)
            else:
                # event log
                self.ExecutionFailure(transaction_id)

    def _external_call(self, serialized_tx: bytes)->bool:
        transaction = Transaction.from_bytes(serialized_tx)
        # convert Address from string to Address type

        method_params = {}
        if transaction.params != "" and transaction.params is not None:
            params = json.loads(transaction.params)

            for param in params:
                print('param', type(param['value']))
                method_params[param['name']] = params_type_converter(param['type'], param['value'])

        print('external', transaction.method == "", method_params, transaction.value)
        try:
            if transaction.destination.is_contract:
                print('is_contract', transaction.destination, transaction.method == None)
                self.call(addr_to=transaction.destination,
                          func_name=None if transaction.method == "" else transaction.method,
                          kw_dict=method_params,
                          amount=transaction.value)
            else:
                print('is_eoa', transaction.destination)
                self.icx.transfer(transaction.destination, transaction.value)
            execute_result = True
        except:
            print('excepted')
            execute_result = False

        return execute_result

    def _is_confirmed(self, transaction_id) -> bool:
        count = 0
        for owner in self._owners:
            if self._confirmations[transaction_id][owner] is True:
                count += 1

        return count == self._required

    @only_wallet
    @external
    #todo: walletowner
    def addOwner(self, _owner: Address):
        self.owner_does_not_exist(_owner)
        self.not_null(_owner)
        # check if owner's count exceed _MAX_OWNER_COUNT
        self.valid_requirement(len(self._owners)+1, self._required)

        self._owners.put(_owner)
        self._is_owner[_owner] = True
        # event log
        self.OwnerAddition(_owner)

    @only_wallet
    @external
    def replaceOwner(self, _owner: Address, _newOwner: Address):
        self.owner_exist(_owner)
        self.owner_does_not_exist(_newOwner)

        for idx, owner in enumerate(self._owners):
            if owner == _owner:
                self._owners[idx] = _newOwner
                break

        del self._is_owner[_owner]
        self._is_owner[_newOwner] = True

        # event log
        self.OwnerRemoval(_owner)
        self.OwnerAddition(_newOwner)

    @only_wallet
    @external
    def removeOwner(self, _owner: Address):
        self.owner_exist(_owner)
        # if all owners are removed, this contract can not be executed.
        # so check if _owner is only one left in this wallet
        self.valid_requirement(len(self._owners) - 1, self._required)

        for idx, owner in enumerate(self._owners):
            if owner == _owner:
                self._owners[idx] = self._owners.pop()
                break

        del self._is_owner[_owner]
        # event log
        self.OwnerRemoval(_owner)

    @only_wallet
    @external
    def changeRequirement(self, _required: int):
        self.valid_requirement(len(self._owners), _required)

        self._required = _required
        # event log
        self.RequirementChange(_required)

    #TODO: check external readonly method need to check params' data
    @external(readonly=True)
    def getRequirements(self) -> int:
        return self._required

    @external(readonly=True)
    def getTransaction_info(self, _transactionId: int) -> bytes:
        #Todo: need to be changed: return informative data
        return self._transactions[_transactionId]

    @external(readonly=True)
    def getTransactionsExecuted(self, _transactionId: int) -> bool:
        return self._transactions[_transactionId][0]

    @external(readonly=True)
    def checkIsOwner(self, _owner: Address)-> bool:
        return self._is_owner[_owner]

    @external(readonly=True)
    def getOwners(self, _from: int, _to: int)-> list:
        owner_list = []
        for idx, owner in enumerate(self._owners, start=_from):
            if idx == _to:
                break
            owner_list.append(owner)

        return owner_list

    @external(readonly=True)
    def getConfirmationCount(self, _transactionId: int)-> int:
        count = 0
        for owner in self._owners:
            if self._confirmations[_transactionId][owner]:
                count += 1
        return count

    @external(readonly=True)
    def getConfirmations(self, _from: int, _to: int, _transactionId: int)-> list:
        confirmed_addrs = []
        for idx, owner in enumerate(self._owners, start=_from):
            if idx == _to:
                break
            if self._confirmations[_transactionId][owner]:
                confirmed_addrs.append(owner)

        return confirmed_addrs

    @external(readonly=True)
    def getTransactionCount(self, _pending: bool, _executed: bool)-> int:
        tx_count = 0
        for tx_id in range(self._transaction_count):
            if (_pending and not self._transactions_executed[tx_id]) or (_executed and self._transactions_executed[tx_id]):
                tx_count += 1

        return tx_count

    @external(readonly=True)
    def getTransactionIds(self, _from: int, _to: int, _pending: bool, _executed: bool)-> list:
        transaction_ids = []
        for tx_id in range(_from, _to):
            if (_pending and not self._transactions_executed[tx_id]) or (_executed and self._transactions_executed[tx_id]):
                transaction_ids.append(tx_id)

        return transaction_ids

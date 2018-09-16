# -*- coding: utf-8 -*-

# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from .type_converter.type_converter import params_type_converter
from .qualification_check.qualification_check import *
from .transaction import Transaction


class MultiSigWallet(IconScoreBase, IconScoreException):
    _MAX_WALLET_OWNER_COUNT = 50
    _MAX_DATA_REQUEST_AMOUNT = 50


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

        _walletOwners = _walletOwners.replace(" ", "").split(",")
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
        # this will be changed to "" when creating Transaction instance.
        # "" will be changed to {} when finally execute transaction. so doesn't check format
        if json_formatted_params != "" and json_formatted_params is not None:
            try:
                params = json.loads(json_formatted_params)
                for param in params:
                    params_type_converter(param["type"], param["value"])
            except ValueError as e:
                self.revert(f"json format error: {e}")
            except IconScoreException as e:
                self.revert(f"{e}")
            except:
                self.revert(f"can't convert 'params' json data, check the 'params' parameter")

    def not_null(self, address: Address):
        #Todo: check(governance and null address)
        hx_null = Address.from_string("hx0000000000000000000000000000000000000000")
        cx_null = Address.from_string("cx0000000000000000000000000000000000000000")
        if address == hx_null or address == cx_null:
            self.revert("invalid address")

    def wallet_owner_does_not_exist(self, wallet_owner: Address):
        if self._is_wallet_owner[wallet_owner] is True:
            self.revert(f"{wallet_owner} already exists as an owner of the wallet")

    def wallet_owner_exist(self, wallet_owner: Address):
        if self._is_wallet_owner[wallet_owner] is False:
            self.revert(f"{wallet_owner} is not an owner of wallet")

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
        # before call this method, check if transaction is exists(use transaction_exists method)
        if self._transactions[transaction_id][0] is True:
            self.revert(f"transaction id '{transaction_id}' has already been executed")

    def valid_requirement(self, wallet_owner_count: int, required: int):
        if wallet_owner_count > self._MAX_WALLET_OWNER_COUNT or \
                required > wallet_owner_count or \
                required <= 0 or \
                wallet_owner_count == 0:
            self.revert(f"invalid requirement")

    @payable
    def fallback(self):
        if self.msg.value > 0:

            self.Deposit(self.msg.sender, self.msg.value)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        if _value > 0:
            self.DepositToken(_from, _value, _data)

    @external
    def submitTransaction(self, _destination: Address, _method: str="", _params: str="", _value: int=0, _description: str=""):
        self.wallet_owner_exist(self.msg.sender)
        # prevent failure of executing transaction caused by 'params' conversion problems
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

        self.Confirmation(self.msg.sender, _transactionId)

        self._execute_transaction(_transactionId)

    @external
    def revokeTransaction(self, _transactionId: int):
        self.wallet_owner_exist(self.msg.sender)
        self.transaction_exists(_transactionId)
        self.not_executed(_transactionId)
        self.confirmed(_transactionId, self.msg.sender)

        self._confirmations[_transactionId][self.msg.sender] = False

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

        self.Submission(transaction_id)
        return transaction_id

    def _execute_transaction(self, transaction_id: int):
        # as this method can't be called from other SCORE or EOA, doesn't check owner, transactions_id, confirmations.
        if self._is_confirmed(transaction_id):
            txn = self._transactions[transaction_id]
            if self._external_call(txn):
                self._transactions[transaction_id] = True.to_bytes(1, 'big') + self._transactions[transaction_id][1:]

                self.Execution(transaction_id)
            else:

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
        # check if owner's count exceed '_MAX_OWNER_COUNT'
        self.valid_requirement(len(self._wallet_owners) + 1, self._required)

        self._wallet_owners.put(_walletOwner)
        self._is_wallet_owner[_walletOwner] = True

        self.WalletOwnerAddition(_walletOwner)

    @only_wallet
    @external
    def replaceWalletOwner(self, _walletOwner: Address, _newWalletOwner: Address):
        self.wallet_owner_exist(_walletOwner)
        self.wallet_owner_does_not_exist(_newWalletOwner)
        self.not_null(_newWalletOwner)

        for idx, wallet_owner in enumerate(self._wallet_owners):
            if wallet_owner == _walletOwner:
                self._wallet_owners[idx] = _newWalletOwner
                break

        del self._is_wallet_owner[_walletOwner]
        self._is_wallet_owner[_newWalletOwner] = True

        self.WalletOwnerRemoval(_walletOwner)
        self.WalletOwnerAddition(_newWalletOwner)

    @only_wallet
    @external
    def removeWalletOwner(self, _walletOwner: Address):
        self.wallet_owner_exist(_walletOwner)
        # if all owners are removed, this contract can not be executed.
        # so check if _owner is only one left in this wallet
        self.valid_requirement(len(self._wallet_owners) - 1, self._required)

        for idx, owner in enumerate(self._wallet_owners):
            if owner == _walletOwner:
                if idx == len(self._wallet_owners)-1:
                    self._wallet_owners.pop()
                else:
                    self._wallet_owners[idx] = self._wallet_owners.pop()
                break

        del self._is_wallet_owner[_walletOwner]

        self.WalletOwnerRemoval(_walletOwner)

    @only_wallet
    @external
    def changeRequirement(self, _required: int):
        self.valid_requirement(len(self._wallet_owners), _required)

        self._required = _required

        self.RequirementChange(_required)

    @external(readonly=True)
    def getRequirements(self) -> int:
        return self._required

    @external(readonly=True)
    def getTransactionInfo(self, _transactionId: int) -> bytes:
        return self._transactions[_transactionId]

    @external(readonly=True)
    def getTransactionsExecuted(self, _transactionId: int) -> bool:
        if self._transactions[_transactionId] is not None:
            return self._transactions[_transactionId][0]
        else:
            return None

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
        if _to - _from >= self._MAX_DATA_REQUEST_AMOUNT:
            raise IconScoreException("Requests that exceed the allowed amount")

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
        if _to - _from >= self._MAX_DATA_REQUEST_AMOUNT:
            raise IconScoreException("Requests that exceed the allowed amount")

        transaction_ids = []

        # prevent searching not existed transaction
        _to = _to if self._transaction_count > _to else self._transaction_count

        for tx_id in range(_from, _to):
            if (_pending and not self._transactions[tx_id][0]) or (_executed and self._transactions[tx_id][0]):
                transaction_ids.append(tx_id)

        return transaction_ids

    #todo: return transactions list
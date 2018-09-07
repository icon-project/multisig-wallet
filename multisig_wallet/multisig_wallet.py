from iconservice import *
from .type_converter import type_converter
from .qualification_check.qualification_check import *

import json


class MultiSigWallet(IconScoreBase, IconScoreException):
    _MAX_OWNER_COUNT = 50

    @eventlog(indexed=2)
    def Confirmation(self, sender:Address, transaction_id: int):
        pass

    @eventlog(indexed=2)
    def Revocation(self, sender:Address, transaction_id: int):
        pass

    @eventlog(indexed=1)
    def Submission(self, transaction_id: int):
        pass

    @eventlog(indexed=1)
    def Execution(self, transaction_id: int):
        pass

    @eventlog(indexed=1)
    def ExecutionFailure(self, transaction_id: int):
        pass

    @eventlog(indexed=1)
    def Deposit(self, sender: Address, value: int):
        pass

    @eventlog(indexed=1)
    def OwnerAddition(self, owner: Address):
        pass

    @eventlog(indexed=1)
    def OwnerRemoval(self, owner: Address):
        pass

    @eventlog
    def RequirementChange(self, required: int):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._transactions_info = DictDB('transactions_info', db, value_type=str)
        self._transactions_executed = DictDB('transactions_executed', db, value_type=bool)
        self._confirmations = DictDB('confirmations', db, value_type=bool, depth=2)
        self._is_owner = DictDB('is_owner', db, value_type=bool)
        self._owners = ArrayDB('owners', db, value_type=Address)
        self._required = VarDB('required', db, value_type=int)
        self._transaction_count = VarDB('transactionCount', db, value_type=int)

    def on_install(self, owners: str, required: int) -> None:
        super().on_install()
        owners = owners.split(',')
        owners = [Address.from_string(owner) for owner in owners]

        for owner in owners:
            self._is_owner[owner] = True

        self._owners = owners
        self._required = required
        self._transaction_count = 0

    def on_update(self) -> None:
        super().on_update()

    def not_null(self, address: Address):
        # TODO: check in SCORE, what is 0 address
        if address is 0:
            raise IconScoreException

    def owner_does_not_exist(self, owner: Address):
        if self._is_owner[owner] is True:
            raise IconScoreException

    def owner_exist(self, owner: Address):
        if self._is_owner[owner] is False:
            raise IconScoreException

    def transaction_exists(self, transaction_id: int):
        if self._transactions_info[transaction_id] == "":
            raise IconScoreException

    def confirmed(self, transation_id: int, owner: Address):
        if self._confirmations[transation_id][str(owner)] is False:
            raise IconScoreException

    def not_confirmed(self, transation_id: int, owner: Address):
        if self._confirmations[transation_id][str(owner)] is True:
            raise IconScoreException

    def not_executed(self, transaction_id: int):
        if self._transactions_executed[transaction_id] is True:
            raise IconScoreException

    def valid_requirement(self, owner_count: int, required: int):
        if owner_count > self._MAX_OWNER_COUNT or \
                required > owner_count or \
                required <= 0 or \
                owner_count is 0:
            raise IconScoreException

    @payable
    def fallback(self):
        if self.msg.value > 0:
            self.Deposit(self.msg.sender, self.msg.value)

    @external
    def submitTransaction(self, _destination: Address, _method: str, _params: str, _descrpition: str):
        # supplement from gnosis
        self.owner_exist(self.msg.sender)
        # add transaction
        transaction_id = self._add_transaction(_destination, _method, _params, _descrpition)
        # confirm_transaction
        self.confirmTransaction(transaction_id)

    def _add_transaction(self, _destination: Address, _method: str, _params: str, _descrpition: str) ->int:
        self.not_null(_destination)

        transaction_id = self._transaction_count

        #TODO: make transaction information format before input to DB
        self._transaction_count = transaction_id + 1

        self.Submission(transaction_id)
        return transaction_id

    @external
    def confirmTransaction(self, transaction_id: int):
        self.owner_exist(self.msg.sender)
        self.transaction_exists(transaction_id)
        self.not_confirmed(transaction_id,self.msg.sender)

        self._confirmations[transaction_id][str(self.msg.sender)] = True
        # eventlog
        self.Confirmation(self.msg.sender, transaction_id)

        self._execute_transaction(transaction_id)

    def _execute_transaction(self, transaction_id: int):
        # reason why check twice is for the case that someone call this function from another wallet.
        self.owner_exist(self.msg.sender)
        self.confirmed(transaction_id, self.msg.sender)
        self.not_executed(transaction_id)

        if(self._is_confirmed(transaction_id)):
            txn = self._transactions_info[transaction_id]
            #TODO: implement external call
            if(self._external_call()):
                self._transactions_executed[transaction_id] = True
                self.Execution(transaction_id)
            else:
                self.ExecutionFailure(transaction_id)

    def _external_call(self)->bool:
        pass

    @external
    def revokeTransaction(self, transaction_id: int):
        self.owner_exist(self.msg.sender)
        self.confirmed(transaction_id, self.msg.sender)
        self.not_executed(transaction_id)

        self._confirmations[transaction_id][str(self.msg.sender)] = False
        # eventlog
        self.Revocation(self.msg.sender, transaction_id)

    def _is_confirmed(self, transaction_id) -> bool:
        count = 0
        for owner in self._owners:
            if self._confirmations[transaction_id][str(owner)] is True:
                count += 1
            if count is self._required:
                return True
        return False

    @only_wallet
    def _add_owner(self, _owner: Address):
        self.owner_does_not_exist(_owner)
        self.not_null(_owner)
        self.valid_requirement(len(self._owners)+1, self._required)

        self._is_owner[_owner] = True
        self._owners.put(_owner)
        self.OwnerAddition(_owner)

    @only_wallet
    def _replace_owner(self, _owner: Address, _new_owner: Address):
        self.owner_exist(_owner)
        self.owner_does_not_exist(_new_owner)

        for idx, owner in enumerate(self._owners):
            if owner == _owner:
                self._owners[idx] = _new_owner
                break

        self._is_owner[_owner] = False
        self._is_owner[_new_owner] = True

        self.OwnerRemoval(_owner)
        self.OwnerAddition(_new_owner)

    @only_wallet
    def _remove_owner(self, _owner: Address):
        self.owner_exist(_owner)

        for idx, owner in enumerate(self._owners):
            if owner == _owner:
                self._owners[idx] = self._owners.pop()
                break

        self._is_owner[_owner] = False
        self.OwnerRemoval(_owner)

    @only_wallet
    def _change_requirement(self, _required: int):
        self.valid_requirement(len(self._owners), _required)

        self._required = _required
        self.RequirementChange(_required)

    @external(readonly=True)
    def getOwners(self)-> list:
        return self._owners

    @external(readonly=True)
    def getConfirmationCount(self, _transaction_id: int)-> int:
        count = 0
        for owner in self._owners:
            if self._confirmations[_transaction_id][str(owner)]:
                count += 1
        return count

    @external(readonly=True)
    def getConfirmations(self, _transaction_id: int)-> list:
        confirmed_addrs = []
        for owner in self._owners:
            if self._confirmations[_transaction_id][str(owner)]:
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
    def getTransactionIds(self, _from: int, _to: int, _pending:bool, _executed:bool)-> list:
        transaction_ids = []
        for tx_id in range():
            if (_pending and not self._transactions_executed[tx_id]) or (_executed and self._transactions_executed[tx_id]):
                transaction_ids.append(tx_id)

        return transaction_ids

    @external(readonly=True)
    def getRequirements(self)-> int:
        return self._required

    @external(readonly=True)
    def getTransaction_info(self, _transaction_id: int) -> str:
        return self._transactions_info[_transaction_id]

    @external(readonly=True)
    def getTransactionsExecuted(self, _transaction_id: int) -> bool:
        return self._transactions_executed[_transaction_id]
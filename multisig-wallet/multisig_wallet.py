from iconservice import *


class MultiSigWallet(IconScoreBase, IconScoreException):
    _MAX_OWNER_COUNT = 50
    _SUBMITABLE_METHOD = ['_send_icx']

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

    @external
    def submitTransaction(self, method_name: str, params: str):
        pass

    def _add_transaction(self, method_name: str, params: str) ->int:
        pass

    @external
    def confirmTransaction(self, transaction_id: int):
        pass

    def _execute_transaction(self, transaction_id: int):
        pass

    def _external_call(self, method_name: str, params: str):
        pass


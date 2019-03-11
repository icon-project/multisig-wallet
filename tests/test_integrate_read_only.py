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

from iconservice.base.exception import RevertException

from tests import create_address
from tests.test_integrate_base import TestIntegrateBase
from iconservice import IconScoreException, ZERO_SCORE_ADDRESS
from iconservice import *


class TestIntegrateReadOnly(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_get_transaction_info(self):
        #submit transaction
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 2}
        ]
        change_requirement_method = 'changeRequirement'
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': change_requirement_method,
                            '_params': json.dumps(change_requirement_params),
                            '_description': ''}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)

        # success case: search exist transaction
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionInfo",
                "params": {"_transactionId": "0"}
            }
        }

        actual_transaction_data = self._query(query_request)
        self.assertEqual(0, actual_transaction_data["_executed"])
        self.assertEqual(str(self.multisig_score_addr), actual_transaction_data["_destination"])
        self.assertEqual(change_requirement_method, actual_transaction_data["_method"])

        # failure case: try to search not exist transaction(should return None)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionInfo",
                "params": {"_transactionId":"1"}
            }
        }
        actual_transaction_data = self._query(query_request)
        self.assertEqual({}, actual_transaction_data)

    def test_get_transaction_list_and_get_transaction_count(self):
        # success case: get transaction list
        submit_txs = []
        for idx in range(0, 50):
            change_requirement_params = [
                {'name': '_required',
                 'type': 'int',
                 'value': 2}
            ]
            submit_tx_params = {'_destination': str(self.multisig_score_addr),
                                '_method': 'changeRequirement',
                                '_params': json.dumps(change_requirement_params),
                                '_description': f'get transaction test id:{idx}'}

            submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                 addr_to=self.multisig_score_addr,
                                                 method='submitTransaction',
                                                 params=submit_tx_params
                                                 )
            submit_txs.append(submit_tx)

        prev_block, tx_results = self._make_and_req_block(submit_txs)
        self._write_precommit_state(prev_block)

        # check wallet_owner who has confirmed transaction
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionList",
                "params": {"_offset": "0", "_count": "10"}
            }
        }
        actual_tx_list = self._query(query_request)
        for idx, actual_tx in enumerate(actual_tx_list):
            if actual_tx["_transaction_id"] == idx:
                self.assertEqual(0, actual_tx["_executed"])
                self.assertEqual(str(self.multisig_score_addr), actual_tx["_destination"])
                self.assertEqual(f'get transaction test id:{idx}', actual_tx["_description"])

        # failure case: request more than 50 list
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionList",
                "params": {"_offset": "0", "_count": "51"}
            }
        }

        expected_massage = "requests that exceed the allowed amount"
        try:
            actual_massage = self._query(query_request)
        except RevertException as e:
            actual_massage = e.message
            pass
        self.assertEqual(expected_massage, actual_massage)

        # success case: get pending transaction list
        confirm_txs = []
        for idx in range(0, 50, 2):
            confirm_tx_params = {'_transactionId': f'{idx}'}
            confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                                  addr_to=self.multisig_score_addr,
                                                  method='confirmTransaction',
                                                  params=confirm_tx_params
                                                  )
            confirm_txs.append(confirm_tx)
        prev_block, tx_results = self._make_and_req_block(confirm_txs)
        self._write_precommit_state(prev_block)
        for result in tx_results:
            self.assertEqual(result.status, int(True))

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionList",
                "params": {"_offset": "0", "_count": "10", "_executed": "0"}
            }
        }
        actual_tx_list = self._query(query_request)
        idx = 1
        for actual_tx in actual_tx_list:
            if actual_tx["_transaction_id"] == idx:
                self.assertEqual(0, actual_tx["_executed"])
                self.assertEqual(str(self.multisig_score_addr), actual_tx["_destination"])
                self.assertEqual(f'get transaction test id:{idx}', actual_tx["_description"])
                idx += 2

        # success case: get executed transaction list
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionList",
                "params": {"_offset": "0", "_count": "10", "_pending": "0"}
            }
        }
        actual_tx_list = self._query(query_request)
        idx = 0
        for actual_tx in actual_tx_list:
            if actual_tx["_transaction_id"] == idx:
                self.assertEqual(1, actual_tx["_executed"])
                self.assertEqual(str(self.multisig_score_addr), actual_tx["_destination"])
                self.assertEqual(f'get transaction test id:{idx}', actual_tx["_description"])
                idx += 2

        # success case: get exceed transaction list
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionList",
                "params": {"_offset": "45", "_count": "10"}
            }
        }
        actual_tx_list = self._query(query_request)
        self.assertEqual(5, len(actual_tx_list))

        # success case: test getTransactionCount(should pending transaction: 25, executed transaction: 50)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionCount",
                "params": {"_pending": "1", "_executed": "1"}
            }
        }
        actual_tx_count = self._query(query_request)
        self.assertEqual(50, actual_tx_count)

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionCount",
                "params": {"_pending": "1", "_executed": "0"}
            }
        }
        actual_pending_tx_count = self._query(query_request)
        self.assertEqual(25, actual_pending_tx_count)

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionCount",
                "params": {"_pending": "0", "_executed": "1"}
            }
        }
        actual_executed_tx_count = self._query(query_request)
        self.assertEqual(25, actual_executed_tx_count)

    def test_get_wallet_owners(self):
        owners = [str(create_address()) for x in range(0, 50)]

        # deploy multisig wallet which has 50 wallet owners.
        tx1 = self._make_deploy_tx("",
                                   "multisig_wallet",
                                   self._addr_array[0],
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"_walletOwners": ','.join(owners),
                                       "_required": "2"})

        prev_block, tx_results = self._make_and_req_block([tx1])
        self._write_precommit_state(prev_block)

        self.assertEqual(int(True), tx_results[0].status)
        multisig_score_addr = tx_results[0].score_address

        # success case: get wallet owners 0 ~ 9, 10 ~ 19, 20 ~ 29, 30 ~ 39, 40 ~ 49
        for x in range(1, 5):
            query_request = {
                "version": self._version,
                "from": self._admin,
                "to": multisig_score_addr,
                "dataType": "call",
                "data": {
                    "method": "getWalletOwners",
                    "params": {"_offset": f"{10*x}", "_count": "10"}
                }
            }
            expected_owners = owners[10 * x: 10 + 10 * x]
            actual_owners = self._query(query_request)
            self.assertEqual(expected_owners, actual_owners)

        # success case: exceed owner list(should return owners that does not exceed)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_offset": "45", "_count": "30"}
            }
        }
        expected_owners = owners[45:50]
        actual_owners = self._query(query_request)
        self.assertEqual(expected_owners, actual_owners)

    def test_get_confirmations_and_get_confirmation_count(self):
        # success case: get owner list of confirmed transaction
        owners = [str(create_address()) for x in range(0, 50)]

        # deploy multisig wallet which has 50 wallet owners.
        tx1 = self._make_deploy_tx("",
                                   "multisig_wallet",
                                   self._addr_array[0],
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"_walletOwners": ','.join(owners),
                                                  "_required": "50"})

        prev_block, tx_results = self._make_and_req_block([tx1])
        self._write_precommit_state(prev_block)

        self.assertEqual(int(True), tx_results[0].status)
        multisig_score_addr = tx_results[0].score_address

        # submit transaction
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 2}
        ]
        submit_tx_params = {'_destination': str(multisig_score_addr),
                            '_method': 'changeRequirement',
                            '_params': json.dumps(change_requirement_params),
                            '_description': ""}

        submit_tx = self._make_score_call_tx(addr_from=Address.from_string(owners[0]),
                                             addr_to=multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)

        # getConfirmationCount should be 1
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {"_transactionId":"0"}
            }
        }
        actual_confirmation_count = self._query(query_request)
        self.assertEqual(1, actual_confirmation_count)

        # confirm transaction(odd owners confirm, even owners not confirm)
        confirm_txs = []
        for idx, owner in enumerate(owners):
            if idx % 2 == 0:
                continue
            confirm_tx_params = {'_transactionId': '0x00'}
            confirm_tx = self._make_score_call_tx(addr_from=Address.from_string(owner),
                                                  addr_to= multisig_score_addr,
                                                  method='confirmTransaction',
                                                  params=confirm_tx_params
                                                  )
            confirm_txs.append(confirm_tx)
        prev_block, tx_results = self._make_and_req_block(confirm_txs)
        self._write_precommit_state(prev_block)
        for tx_result in tx_results:
            self.assertEqual(int(True), tx_result.status)

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_offset": "0", "_count": "50", "_transactionId":"0"}
            }
        }
        expected_owners = [owner for idx, owner in enumerate(owners) if idx % 2 == 1]
        expected_owners.insert(0, owners[0])

        actual_owners = self._query(query_request)
        self.assertEqual(expected_owners, actual_owners)

        # getConfirmationCount should be 26(submit wallet owner 1 + confirm wallet owner 25)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {"_transactionId":"0"}
            }
        }
        actual_confirmation_count = self._query(query_request)
        self.assertEqual(26, actual_confirmation_count)

    def test_get_total_number_of_wallet_owner(self):
        # success case: get total number of wallet owner (should be 3 as default deployed wallet is 2 to 3)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwnerCount",
                "params": {}
            }
        }
        actual_executed_tx_count = self._query(query_request)
        self.assertEqual(3, actual_executed_tx_count)

        # success case: after add owner, try get total number of wallet owner (should be 4)
        add_wallet_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner4)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "addWalletOwner",
                            "_params": json.dumps(add_wallet_owner_params),
                            "_description": "add owner4 in wallet"}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=self.multisig_score_addr,
                                                       method="submitTransaction",
                                                       params=submit_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # confirm transaction
        confirm_tx_params = {"_transactionId": "0x00"}
        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner2,
                                                       addr_to=self.multisig_score_addr,
                                                       method="confirmTransaction",
                                                       params=confirm_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwnerCount",
                "params": {}
            }
        }
        actual_executed_tx_count = self._query(query_request)
        self.assertEqual(4, actual_executed_tx_count)

        # success case: after remove owner, try get total number of wallet owner (should be 3)
        remove_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner3)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "removeWalletOwner",
                            "_params": json.dumps(remove_owner_params),
                            "_description": "remove wallet owner3 in wallet"}

        remove_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                          addr_to=self.multisig_score_addr,
                                                          method="submitTransaction",
                                                          params=submit_tx_params
                                                          )
        prev_block, tx_results = self._make_and_req_block([remove_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x01'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwnerCount",
                "params": {}
            }
        }
        actual_executed_tx_count = self._query(query_request)
        self.assertEqual(3, actual_executed_tx_count)

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

from tests.test_integrate_base import TestIntegrateBase


class TestIntegrateRevokeTransaction(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_revoke_transaction(self):
        # submit transaction
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 3}
        ]
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': 'changeRequirement',
                            '_params': json.dumps(change_requirement_params),
                            '_description': 'change requirements 2 to 3'}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )
        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # success case: revoke using confirmed wallet owner
        confirmed_owner1 = self._owner1
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=confirmed_owner1,
                                              addr_to=self.multisig_score_addr,
                                              method='revokeTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check wallet_owners who has confirmed transaction(should be none)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_offset": "0", "_count": "10", "_transactionId": "0x00"}
            }
        }

        expected_confirm_owners = []
        actual_confirm_owners = self._query(query_request)
        self.assertEqual(expected_confirm_owners, actual_confirm_owners)

        # failure case: revoke using not confirmed wallet owner
        not_confirmed_owner = self._owner1
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=not_confirmed_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='revokeTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(False, tx_results[0].status)

        expected_revert_massage = f"{self._owner1} has not confirmed to the transaction id '0' yet"
        actual_revert_massage = tx_results[0].failure.message
        self.assertEqual(expected_revert_massage, actual_revert_massage)

        # failure case: try revoke transaction which is already executed

        # confirm transaction using owner1, 2
        confirmed_owner1 = self._owner1
        confirmed_owner2 = self._owner2
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx1 = self._make_score_call_tx(addr_from=confirmed_owner1,
                                               addr_to=self.multisig_score_addr,
                                               method='confirmTransaction',
                                               params=confirm_tx_params
                                               )
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx2 = self._make_score_call_tx(addr_from=confirmed_owner2,
                                               addr_to=self.multisig_score_addr,
                                               method='confirmTransaction',
                                               params=confirm_tx_params
                                               )
        prev_block, tx_results = self._make_and_req_block([confirm_tx1, confirm_tx2])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)
        self.assertEqual(True, tx_results[1].status)

        # check transaction executed.
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionsExecuted",
                "params": {"_transactionId": "0x00"}
            }
        }
        response = self._query(query_request)
        self.assertEqual(True, response)

        # try to revoke confirmation of the transaction which is already executed
        confirmed_owner1 = self._owner1
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=confirmed_owner1,
                                              addr_to=self.multisig_score_addr,
                                              method='revokeTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        expected_revert_massage = "Transaction ID(0) has already been executed"
        actual_revert_massage = tx_results[0].failure.message
        self.assertEqual(expected_revert_massage, actual_revert_massage)

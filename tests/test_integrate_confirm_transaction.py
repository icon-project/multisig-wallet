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


class TestIntegrateConfirmTransaction(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_confirm_transaction_validate_wallet_owner(self):
        # submit transaction
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 3}
        ]
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': 'changeRequirement',
                            '_params': json.dumps(change_requirement_params),
                            '_description': 'change requirements from 2 to 3'}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check confirmation count(should be 1)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transactionId': "0x00"}
            }
        }
        actual_confirm_count = self._query(query_request)
        expected_confirm_count = 1
        self.assertEqual(expected_confirm_count, actual_confirm_count)

        # check wallet_owner who has confirmed transaction
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_from": "0", "_to": "10", "_transactionId": "0x00"}
            }
        }

        actual_confirm_count = self._query(query_request)
        expected_confirm_owner = self._owner1
        actual_confirm_owner = actual_confirm_count[0]
        self.assertEqual(expected_confirm_owner, actual_confirm_owner)

        # failure case: confirm transaction with invalid owner
        not_included_owner = self._owner4
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=not_included_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        expected_revert_massage = f"{str(self._owner4)} is not an owner of wallet"
        actual_revert_massage = tx_results[0].failure.message
        self.assertEqual(expected_revert_massage, actual_revert_massage)

        # success case: confirm transaction with valid owner(_owner2)
        valid_owner = self._owner2
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=valid_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check wallet_owners who has confirmed transaction(should be owner1, owner2)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_from": "0", "_to": "10", "_transactionId": "0x00"}
            }
        }

        expected_confirm_owners = [self._owner1, self._owner2]
        actual_confirm_owners = self._query(query_request)
        self.assertEqual(expected_confirm_owners, actual_confirm_owners)

        # check if transaction executed successfully
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getRequirements",
                "params": {}
            }
        }
        expected_requirements = 3
        actual_requirements = self._query(query_request)
        self.assertEqual(expected_requirements, actual_requirements)

        # check event log
        expected_execution_event_log = 'Execution(int)'
        actual_execution_event_log = tx_results[0].event_logs[2].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

    def test_confirm_transaction_validate_confirms(self):
        # submit transaction
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 3}
        ]
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': 'changeRequirement',
                            '_params': json.dumps(change_requirement_params),
                            '_description': 'change requirements from 2 to 3'}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check confirmation count(should be 1)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transactionId': "0x00"}
            }
        }
        actual_confirm_count = self._query(query_request)
        expected_confirm_count = 1
        self.assertEqual(expected_confirm_count, actual_confirm_count)

        # failure case: try to confirm using already confirmed owner(owner1)
        confirmed_owner = self._owner1
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=confirmed_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(False, tx_results[0].status)

        # check confirmation count(should be 1)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transactionId': "0x00"}
            }
        }

        expected_confirm_count = 1
        actual_confirm_count = self._query(query_request)
        self.assertEqual(expected_confirm_count, actual_confirm_count)

        # check wallet_owner who has confirmed transaction
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_from": "0", "_to": "10", "_transactionId": "0x00"}
            }
        }

        expected_confirm_owner = [self._owner1]
        actual_confirm_owner = self._query(query_request)
        self.assertEqual(expected_confirm_owner, actual_confirm_owner)

    def test_confirm_transaction_validate_transaction(self):
        change_requirement_params = [
            {'name': '_required',
             'type': 'int',
             'value': 3}
        ]
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': 'changeRequirement',
                            '_params': json.dumps(change_requirement_params),
                            '_description': 'change requirements from 2 to 3'}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # failure case: confirming transaction on not existing transaction id
        confirmed_owner = self._owner1
        confirm_tx_params = {'_transactionId': '0x01'}
        confirm_tx = self._make_score_call_tx(addr_from=confirmed_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(False, tx_results[0].status)

        expected_revert_message = "transaction id '1' is not exist"
        actual_revert_message = tx_results[0].failure.message
        self.assertEqual(expected_revert_message, actual_revert_message)

    def test_confirm_transaction_execute_transaction_failure(self):
        # failure case: if confirmed transaction is not valid(e.g. invalid method name),
        # should be failed but confirm count should be 2.

        # submit invalid transaction(invalid method name)
        invalid_method_name = 'invalid_method_name'
        params = [
            {'name': '_required',
             'type': 'int',
             'value': 3}
        ]
        submit_tx_params = {'_destination': str(self.multisig_score_addr),
                            '_method': invalid_method_name,
                            '_params': json.dumps(params),
                            '_description': 'invalid_method_name'}

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params
                                             )

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        #confirm transaction
        valid_owner = self._owner2
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=valid_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check wallet_owners who has confirmed transaction(should be owner1, owner2)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmations",
                "params": {"_from": "0", "_to": "10", "_transactionId": "0x00"}
            }
        }

        expected_confirm_owners = [self._owner1, self._owner2]
        actual_confirm_owners = self._query(query_request)
        self.assertEqual(expected_confirm_owners, actual_confirm_owners)

        # check if transaction is not executed
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionsExecuted",
                "params": {"_transactionId": "0"}
            }
        }
        expected_value = False
        actual_value = self._query(query_request)
        self.assertEqual(expected_value, actual_value)

        # check event log
        expected_execution_event_log = 'ExecutionFailure(int)'
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)
        pass


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
from iconservice import IconScoreException

class TestIntegrateReadOnly(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_get_transaction_ids(self):
        # success case: get transaction ids
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
                "method": "getTransactionIds",
                "params": {"_offset": "0", "_count": "10"}
            }
        }

        expected_ids_list = [x for x in range(0,10)]
        actual_ids_list = self._query(query_request)
        self.assertEqual(expected_ids_list, actual_ids_list)

        # failure case: request more than 50 ids
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionIds",
                "params": {"_offset": "0", "_count": "51"}
            }
        }

        expected_massage = "Requests that exceed the allowed amount"
        try:
            actual_massage = self._query(query_request)
        except IconScoreException as e:
            actual_massage = e.message
            pass
        self.assertEqual(expected_massage, actual_massage)

        # success case: get pending transaction ids
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
                "method": "getTransactionIds",
                "params": {"_offset": "0", "_count": "10", "_executed": "0"}
            }
        }
        expected_massage = [x for x in range(1,10,2)]
        actual_massage = self._query(query_request)
        self.assertEqual(expected_massage, actual_massage)

        # success case: get executed transaction ids
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionIds",
                "params": {"_offset": "0", "_count": "10", "_pending": "0"}
            }
        }
        expected_massage = [x for x in range(0, 10, 2)]
        actual_massage = self._query(query_request)
        self.assertEqual(expected_massage, actual_massage)

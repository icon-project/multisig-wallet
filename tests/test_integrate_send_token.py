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

from tests.test_integrate_base import TestIntegrateBase

import json


class TestIntegrateSendToken(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr, self.token_score_addr = \
            self._deploy_multisig_wallet_and_token_score(token_total_supply=10000, token_owner=self._owner1)

    def test_send_token(self):
        # success case: send 500 token to owner4
        # deposit owner1's 1000 token to multisig wallet score
        transfer_tx_params = {'_to': str(self.multisig_score_addr), '_value': str(hex(1000))}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner1,
                                              addr_to=self.token_score_addr,
                                              method='transfer',
                                              params=transfer_tx_params)

        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check multisig wallet score's token amount(should be 1000)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self.multisig_score_addr)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(1000, response)

        # check owner4's token amount(should be 0)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(0, response)

        # make transaction which send 500 token to owner4
        transfer_token_params = [
            {'name': '_to',
             'type': 'Address',
             'value': str(self._owner4)},
            {'name': '_value',
             'type': 'int',
             'value': 500}
        ]

        # submit transaction
        submit_tx_params = {'_destination': str(self.token_score_addr),
                            '_method': 'transfer',
                            '_params': json.dumps(transfer_token_params),
                            '_description': 'send 500 token to owner4'}

        confirm_tx = self._make_score_call_tx(addr_from=self._owner1,
                                              addr_to=self.multisig_score_addr,
                                              method='submitTransaction',
                                              params=submit_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
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
        response = self._query(query_request)
        expected_confirm_count = 1
        self.assertEqual(response, expected_confirm_count)

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check confirmation count(should be 2)
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
        response = self._query(query_request)
        self.assertEqual(2, response)

        # check owner4's token amount(should be 500)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(500, response)

        # check multisig wallet's token amount(should be 500)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self.multisig_score_addr)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(500, response)

    def test_send_token_revert(self):
        # failure case: raise revert while sending 500 token to owner4.(500 token should not be sended)
        # deposit owner1's 1000 token to multisig wallet score
        transfer_tx_params = {'_to': str(self.multisig_score_addr), '_value': str(hex(1000))}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner1,
                                              addr_to=self.token_score_addr,
                                              method='transfer',
                                              params=transfer_tx_params)

        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check multisig wallet score's token amount(should be 1000)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self.multisig_score_addr)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(1000, response)

        # check owner4's token amount(should be 0)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(0, response)

        # make transaction which send 500 token to owner4(call revert_check method)
        revert_check_params = [
            {'name': '_to',
             'type': 'Address',
             'value': str(self._owner4)},
            {'name': '_value',
             'type': 'int',
             'value': 500}
        ]

        # submit transaction
        submit_tx_params = {'_destination': str(self.token_score_addr),
                            '_method': 'revert_check',
                            '_params': json.dumps(revert_check_params),
                            '_description': 'send 500 token to owner4'}

        confirm_tx = self._make_score_call_tx(addr_from=self._owner1,
                                              addr_to=self.multisig_score_addr,
                                              method='submitTransaction',
                                              params=submit_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check confirmation count(should be 2)
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
        response = self._query(query_request)
        self.assertEqual(2, response)

        # check transaction executed count(should be False)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getTransactionsExecuted",
                "params": {'_transactionId': "0x00"}
            }
        }
        response = self._query(query_request)
        self.assertEqual(False, response)

        # check owner4's token amount(should be 0)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(0, response)

        # check multisig wallet's token amount(should be 1000)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self.multisig_score_addr)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(1000, response)
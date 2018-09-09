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

import unittest

from iconservice.base.address import ZERO_SCORE_ADDRESS
from tests.test_integrate_base import TestIntegrateBase
from iconservice.base.address import Address


import json

class TestIntegrateMultiSigWallet(TestIntegrateBase):

    def test_multisig_wallet(self):
        #deploy multisig wallet score(2to3 multisig)
        tx1 = self._make_deploy_tx("",
                                   "multisig_wallet",
                                   self._addr_array[0],
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"owners": str(
                                       "%s,%s,%s" % (str(self._owner1), str(self._owner2), str(self._owner3))),
                                                  "required": "0x02"})


        prev_block, tx_results = self._make_and_req_block([tx1])
        self._write_precommit_state(prev_block)

        self.assertEqual(tx_results[0].status, int(True))
        multisig_score_addr = tx_results[0].score_address

        # 3명의 owner가 정상적으로 들어갔는지 확인(get_owners)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getOwners",
                "params": {}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner3]
        self.assertEqual(response, expected_owners)

        # requirements가 정상적으로 들어갔는 지 확인(get_requirements)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getRequirements",
                "params": {}
            }
        }
        response = self._query(query_request)
        expected_requirements = 2
        self.assertEqual(response, expected_requirements)

        # owner가 정상적으로 입력되었는지 확인
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getOwners",
                "params": {}
            }
        }
        response = self._query(query_request)

        # 해당 contract에 일정량의 icx 예치한 후 및 예치된 금액 확인
        send_icx_value = 10000
        icx_send_tx = self._make_icx_send_tx(self._genesis,
                                               multisig_score_addr,
                                               send_icx_value)

        prev_block, tx_results = self._make_and_req_block([icx_send_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))
        query_request = {
            "address": multisig_score_addr
        }

        response = self._query(query_request, 'icx_getBalance')
        self.assertEqual(response, send_icx_value)

        ## owner1을 이용하여 submitTransaction을 진행(add owner), 실제 add owner가 처리되었는 지 체크
        add_owner_params = [
            {'name': '_owner',
             'type': 'Address',
             'value': str(self._owner4)}
        ]
        submit_tx_params = {'_destination':str(multisig_score_addr),
                            '_method':'_add_owner',
                            '_params': json.dumps(add_owner_params),
                            '_description': 'add owner4 in wallet'}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=multisig_score_addr,
                                                       method='submitTransaction',
                                                       params= submit_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # 정상 등록되었는지 getConfirmationCount를 실행하여 체크(should be 1)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transaction_id': "0x00"}
            }
        }
        response = self._query(query_request)
        expected_confirm_count = 1
        self.assertEqual(response, expected_confirm_count)

        ## owner2를 이용하여 confirm transaction 생성
        confirm_tx_params = {'_transaction_id': '0x00'}
        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner2,
                                                       addr_to=multisig_score_addr,
                                                       method='confirmTransaction',
                                                       params=confirm_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # 정상 등록되었는지 getConfirmationCount를 실행하여 체크(should be 2)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transaction_id': "0x00"}
            }
        }
        response = self._query(query_request)
        expected_confirm_count = 2
        self.assertEqual(response, expected_confirm_count)

        # 정상 처리되었는지 getOwners를 실행하여 체크(4개의 address가 등록되어야 한다)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getOwners",
                "params": {}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner3, self._owner4]
        self.assertEqual(response, expected_owners)

        ## owner1를 이용하여 submitTransaction 실행(send ICX)
        submit_tx_params = {'_destination': str(multisig_score_addr),
                            '_method': 'send_icx',
                            '_params': json.dumps(add_owner_params),
                            '_description': 'send_icx to owner4',
                            '_value': 100}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=multisig_score_addr,
                                                       addr_to=self._owner4,
                                                       method='submitTransaction',
                                                       params=submit_tx_params,
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        #TODO: 여기까지 완성시킨 후 code refactoring 및 unit test 나누는 작업 진행

        ## owner1를 이용하여 submitTransaction 실행(send Token)


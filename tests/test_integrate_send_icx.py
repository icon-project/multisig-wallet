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


class TestIntegrateSendIcx(TestIntegrateBase):

    def test_send_icx(self):
        ## 시나리오.1 send icx to owner4 500 t
        # deploy multisig wallet score(2to3 multisig)
        tx1 = self._make_deploy_tx("",
                                   "multisig_wallet",
                                   self._addr_array[0],
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"owners": str(
                                       "%s,%s,%s" % (str(self._owner1), str(self._owner2), str(self._owner3))),
                                       "required": "0x02"})

        # deploy token score for receive icx
        token_total_supply = 10000
        tx2 = self._make_deploy_tx("",
                                   "standard_token",
                                   self._owner1,
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"initialSupply": str(hex(token_total_supply)), "decimals": str(hex(0))})

        prev_block, tx_results = self._make_and_req_block([tx1, tx2])
        self._write_precommit_state(prev_block)

        self.assertEqual(tx_results[0].status, int(True))
        self.assertEqual(tx_results[1].status, int(True))
        multisig_score_addr = tx_results[0].score_address
        token_score_addr = tx_results[1].score_address

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

        # 해당 contract에 10000 icx를 예치한 후 및 예치된 금액 확인
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

        # 현재 owner4의 잔액 확인 (should be 0)
        query_request = {
            "address": self._owner4
        }

        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 0)

        # owner1을 이용하여 submitTransaction을 진행(send 10 icx to SCORE)
        submit_tx_params = {'_destination': str(token_score_addr),
                            '_method': "",
                            '_params': "",
                            '_description': 'send 10 icx to token score',
                            '_value': '0x0a'}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=multisig_score_addr,
                                                       method='submitTransaction',
                                                       params=submit_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # token score의 icx 잔액 확인(should be 0)
        query_request = {
            "address": token_score_addr
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 0)

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

        query_request = {
            "address": token_score_addr
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 10)

        # multisig wallet score의 icx 잔액 확인(should be 9990)
        query_request = {
            "address": multisig_score_addr
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 9990)

        ############################send icx to EOA###########################

        ## owner1을 이용하여 submitTransaction을 진행(send 10 icx to owner4)
        submit_tx_params = {'_destination': str(self._owner4),
                            '_method': '',
                            '_params': '',
                            '_description': 'send 10 icx to owner4 ',
                            '_value': '0x0a'}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=multisig_score_addr,
                                                       method='submitTransaction',
                                                       params=submit_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # owner4의 icx 잔액 확인(should be 0)
        query_request = {
            "address": self._owner4
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 0)

        # 정상 등록되었는지 getConfirmationCount를 실행하여 체크(should be 1)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getConfirmationCount",
                "params": {'_transaction_id': "0x01"}
            }
        }
        response = self._query(query_request)
        expected_confirm_count = 1
        self.assertEqual(response, expected_confirm_count)

        ## owner2를 이용하여 confirm transaction 생성
        confirm_tx_params = {'_transaction_id': '0x01'}
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
                "params": {'_transaction_id': "0x01"}
            }
        }
        response = self._query(query_request)
        expected_confirm_count = 2
        self.assertEqual(response, expected_confirm_count)

        # owner4의 icx 잔액 확인(should be 10)
        query_request = {
            "address": self._owner4
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 10)

        # multisig wallet score의 icx 잔액 확인(should be 9980)
        query_request = {
            "address": multisig_score_addr
        }
        response = self._query(query_request, "icx_getBalance")
        self.assertEqual(response, 9980)

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

class TestIntegrateSendToken(TestIntegrateBase):

    def test_send_token(self):
        # deploy multisig wallet score(2to3 multisig)
        tx1 = self._make_deploy_tx("",
                                   "multisig_wallet",
                                   self._addr_array[0],
                                   ZERO_SCORE_ADDRESS,
                                   deploy_params={"owners": str(
                                       "%s,%s,%s" % (str(self._owner1), str(self._owner2), str(self._owner3))),
                                       "required": "0x02"})

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

        # 토큰 supply 확인
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner1)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(response, token_total_supply)

        # owner1이 소유한 토큰 중 1000token을 multisig wallet score로 전송
        transfer_tx_params = {'_to': str(multisig_score_addr), '_value': str(hex(1000))}
        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=token_score_addr,
                                                       method='transfer',
                                                       params=transfer_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)


        # multisig wallet에 1000 token이 정상 예치되었는지 확인
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(multisig_score_addr)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(response, 1000)

        # owner4의 token 보유량이 0 인지 확인
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(response, 0)


        # 예치된 1000토큰 중 500토큰을 owner4에게 보내는 submit transaction 생성
        transfer_token_params = [
            {'_name': '_to',
             '_type': 'Address',
             '_value': str(self._owner4)},
            {'_name': '_value',
             '_type': 'int',
             '_value': str(hex(500))}
        ]
        ## owner1을 이용하여 submitTransaction을 진행(icx_send)
        submit_tx_params = {'_destination': str(token_score_addr),
                            '_method': 'transfer',
                            '_params': json.dumps(transfer_token_params),
                            '_description': 'send 500 token to owner4'}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=multisig_score_addr,
                                                       method='submitTransaction',
                                                       params=submit_tx_params
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

        # owner4에 500 token이 정상 예치되었는지 확인
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": token_score_addr,
            "dataType": "call",
            "data": {
                "method": "balanceOf",
                "params": {'_owner': str(self._owner4)}
            }
        }
        response = self._query(query_request)
        self.assertEqual(response, 500)

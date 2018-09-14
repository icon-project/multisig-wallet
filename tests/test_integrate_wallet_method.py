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


class TestIntegrateWalletMethod(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_only_wallet_execute_method(self):
        # failure case: call method using normal owner
        # all external method which change the state of wallet(e.g. requirement) should be called by own wallet
        change_requirement_params = {"_required": "3"}

        change_requirement_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                         addr_to=self.multisig_score_addr,
                                                         method="changeRequirement",
                                                         params=change_requirement_params
                                                         )
        add_wallet_owner_params = {"_walletOwner": str(self._owner4)}
        add_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=self.multisig_score_addr,
                                                       method="addWalletOwner",
                                                       params=add_wallet_owner_params
                                                       )
        replace_wallet_owner_params = {"_walletOwner": str(self._owner1), "_newWalletOwner": str(self._owner4)}

        replace_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                           addr_to=self.multisig_score_addr,
                                                           method="replaceWalletOwner",
                                                           params=replace_wallet_owner_params
                                                           )
        remove_wallet_owner_params = {"_walletOwner": str(self._owner1)}
        remove_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                          addr_to=self.multisig_score_addr,
                                                          method="addWalletOwner",
                                                          params=remove_wallet_owner_params
                                                          )


        prev_block, tx_results = self._make_and_req_block([change_requirement_tx,
                                                           add_wallet_owner_tx,
                                                           replace_wallet_owner_tx,
                                                           remove_wallet_owner_tx])

        self._write_precommit_state(prev_block)
        self.assertEqual(int(False), tx_results[0].status)
        self.assertEqual(int(False), tx_results[0].status)
        self.assertEqual(int(False), tx_results[0].status)
        self.assertEqual(int(False), tx_results[0].status)

    def test_add_wallet_owner(self):
        # success case: add wallet owner4 successfully
        add_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner4)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "addWalletOwner",
                            "_params": json.dumps(add_owner_params),
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

        # check wallet owners(owner4 should be added)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0","_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner3, self._owner4]
        self.assertEqual(response, expected_owners)

        # failure case: add already exist wallet owner
        add_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner1)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "addWalletOwner",
                            "_params": json.dumps(add_owner_params),
                            "_description": "add already exist wallet owner"}

        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                       addr_to=self.multisig_score_addr,
                                                       method="submitTransaction",
                                                       params=submit_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # confirm transaction
        confirm_tx_params = {"_transactionId": "0x01"}
        add_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner2,
                                                       addr_to=self.multisig_score_addr,
                                                       method="confirmTransaction",
                                                       params=confirm_tx_params
                                                       )
        prev_block, tx_results = self._make_and_req_block([add_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check wallet owners
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0", "_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner3, self._owner4]
        self.assertEqual(response, expected_owners)

    def test_replace_wallet_owner(self):
        # success case: replace owner successfully(owner3 -> owner4)
        replace_wallet_owner_params = [
            {'name': '_walletOwner',
             'type': 'Address',
             'value': str(self._owner3)},
            {'name': '_newWalletOwner',
             'type': 'Address',
             'value': str(self._owner4)}
        ]
        replace_tx_params = {'_destination': str(self.multisig_score_addr),
                             '_method': 'replaceWalletOwner',
                             '_params': json.dumps(replace_wallet_owner_params),
                             '_description': 'replace wallet owner'}

        replace_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                           addr_to=self.multisig_score_addr,
                                                           method="submitTransaction",
                                                           params=replace_tx_params
                                                           )
        prev_block, tx_results = self._make_and_req_block([replace_wallet_owner_tx])

        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        #confirm transaction
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check the wallet owner list(should be owner1, owner2, owner4)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0","_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner4]
        self.assertEqual(expected_owners, response)

        # failure case: try replace wallet owner who is not listed
        replace_wallet_owner_params = [
            {'name': '_walletOwner',
             'type': 'Address',
             'value': str(self._owner5)},
            {'name': '_newWalletOwner',
             'type': 'Address',
             'value': str(self._owner6)}
        ]
        replace_tx_params = {'_destination': str(self.multisig_score_addr),
                             '_method': 'replaceWalletOwner',
                             '_params': json.dumps(replace_wallet_owner_params),
                             '_description': 'replace wallet owner'}

        replace_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                           addr_to=self.multisig_score_addr,
                                                           method="submitTransaction",
                                                           params=replace_tx_params
                                                           )
        prev_block, tx_results = self._make_and_req_block([replace_wallet_owner_tx])

        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # confirm transaction
        valid_owner = self._owner2
        confirm_tx_params = {'_transactionId': '0x01'}
        confirm_tx = self._make_score_call_tx(addr_from=valid_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check if the wallet owner list is not changed(should be owner1, owner2, owner4)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0","_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner4]
        self.assertEqual(expected_owners, response)

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # failure case: new wallet owner is already listed
        replace_wallet_owner_params = [
            {'name': '_walletOwner',
             'type': 'Address',
             'value': str(self._owner1)},
            {'name': '_newWalletOwner',
             'type': 'Address',
             'value': str(self._owner4)}
        ]
        replace_tx_params = {'_destination': str(self.multisig_score_addr),
                             '_method': 'replaceWalletOwner',
                             '_params': json.dumps(replace_wallet_owner_params),
                             '_description': 'replace wallet owner'}

        replace_wallet_owner_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                           addr_to=self.multisig_score_addr,
                                                           method="submitTransaction",
                                                           params=replace_tx_params
                                                           )
        prev_block, tx_results = self._make_and_req_block([replace_wallet_owner_tx])

        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # confirm transaction
        valid_owner = self._owner2
        confirm_tx_params = {'_transactionId': '0x02'}
        confirm_tx = self._make_score_call_tx(addr_from=valid_owner,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check if the wallet owner list is not changed(should be owner1, owner2, owner4)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0","_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner4]
        self.assertEqual(expected_owners, response)

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

    def test_remove_wallet_owner(self):
        # failure case: try to remove wallet owner who is not listed
        remove_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner4)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "removeWalletOwner",
                            "_params": json.dumps(remove_owner_params),
                            "_description": "remove wallet owner4 in wallet"}

        remove_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                          addr_to=self.multisig_score_addr,
                                                          method="submitTransaction",
                                                          params=submit_tx_params
                                                          )
        prev_block, tx_results = self._make_and_req_block([remove_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check the wallet owner list(should be owner1, owner2, owner3)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0", "_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2, self._owner3]
        self.assertEqual(expected_owners, response)

        # success case: remove wallet owner successfully(remove owner3)
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
                "method": "getTransactionsExecuted",
                "params": {"_transactionId": "1"}
            }
        }
        response = self._query(query_request)
        self.assertEqual(True, response)

        # check execution success
        expected_execution_event_log = "Execution(int)"
        actual_execution_event_log = tx_results[0].event_logs[2].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check the wallet owner list(should be owner1, owner2)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0", "_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2]
        self.assertEqual(expected_owners, response)

        # check the wallet owner3 is not wallet owner
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "checkIsWalletOwner",
                "params": {"_walletOwner": str(self._owner3)}
            }
        }
        expected_owners = False
        response = self._query(query_request)
        self.assertEqual(expected_owners, response)

        # failure case: try to remove wallet owner when owner's count is same as requirement
        # (should not be removed)
        remove_owner_params = [
            {"name": "_walletOwner",
             "type": "Address",
             "value": str(self._owner2)}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "removeWalletOwner",
                            "_params": json.dumps(remove_owner_params),
                            "_description": "remove wallet owner2 in wallet"}

        remove_owner_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                          addr_to=self.multisig_score_addr,
                                                          method="submitTransaction",
                                                          params=submit_tx_params
                                                          )
        prev_block, tx_results = self._make_and_req_block([remove_owner_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x02'}
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
                "method": "getTransactionsExecuted",
                "params": {"_transactionId": "2"}
            }
        }
        response = self._query(query_request)
        self.assertEqual(False, response)

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[1].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check the wallet owner list(should be owner1, owner2)
        query_request = {
            "version": self._version,
            "from": self._admin,
            "to": self.multisig_score_addr,
            "dataType": "call",
            "data": {
                "method": "getWalletOwners",
                "params": {"_from": "0", "_to": "10"}
            }
        }
        response = self._query(query_request)
        expected_owners = [self._owner1, self._owner2]
        self.assertEqual(expected_owners, response)


    def test_change_requirement(self):
        # success case: change requirement 2 to 1
        change_requirement_params = [
            {"name": "_required",
             "type": "int",
             "value": 1}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "changeRequirement",
                            "_params": json.dumps(change_requirement_params),
                            "_description": "change requirement 2 to 1"}

        change_requirement_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                                addr_to=self.multisig_score_addr,
                                                                method="submitTransaction",
                                                                params=submit_tx_params
                                                                )
        prev_block, tx_results = self._make_and_req_block([change_requirement_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # confirm transaction
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=self._owner2,
                                              addr_to=self.multisig_score_addr,
                                              method='confirmTransaction',
                                              params=confirm_tx_params
                                              )
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # check the requirement(should be 1)
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
        expected_requirement = 1
        actual_requiremnt = self._query(query_request)
        self.assertEqual(expected_requirement, actual_requiremnt)

        # failure case: change requirement to 0
        change_requirement_params = [
            {"name": "_required",
             "type": "int",
             "value": 0}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "changeRequirement",
                            "_params": json.dumps(change_requirement_params),
                            "_description": "change requirement 1 to 0"}

        change_requirement_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                                addr_to=self.multisig_score_addr,
                                                                method="submitTransaction",
                                                                params=submit_tx_params
                                                                )
        prev_block, tx_results = self._make_and_req_block([change_requirement_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[2].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check the requirement(should be 1)
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
        expected_requirement = 1
        actual_requiremnt = self._query(query_request)
        self.assertEqual(expected_requirement, actual_requiremnt)

        # failure case: try to set requirement more than owners
        change_requirement_params = [
            {"name": "_required",
             "type": "int",
             "value": 4}
        ]
        submit_tx_params = {"_destination": str(self.multisig_score_addr),
                            "_method": "changeRequirement",
                            "_params": json.dumps(change_requirement_params),
                            "_description": "change requirement 1 to 4"}

        change_requirement_submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                                                addr_to=self.multisig_score_addr,
                                                                method="submitTransaction",
                                                                params=submit_tx_params
                                                                )
        prev_block, tx_results = self._make_and_req_block([change_requirement_submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(tx_results[0].status, int(True))

        # check execution failure
        expected_execution_event_log = "ExecutionFailure(int)"
        actual_execution_event_log = tx_results[0].event_logs[2].indexed[0]
        self.assertEqual(expected_execution_event_log, actual_execution_event_log)

        # check the requirement(should be 1)
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
        expected_requirement = 1
        actual_requiremnt = self._query(query_request)
        self.assertEqual(expected_requirement, actual_requiremnt)
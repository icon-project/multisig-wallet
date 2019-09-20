import json

from tests.test_integrate_base import TestIntegrateBase


class TestIntegrateCancelTransaction(TestIntegrateBase):
    def setUp(self):
        super().setUp()
        self.multisig_score_addr = self._deploy_multisig_wallet()

    def test_cancel_transaction(self):
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
                                             params=submit_tx_params)

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        # Revoke transaction
        confirmed_owner1 = self._owner1
        confirm_tx_params = {'_transactionId': '0x00'}
        confirm_tx = self._make_score_call_tx(addr_from=confirmed_owner1,
                                              addr_to=self.multisig_score_addr,
                                              method='revokeTransaction',
                                              params=confirm_tx_params)
        prev_block, tx_results = self._make_and_req_block([confirm_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(True, tx_results[0].status)

        # success case: get exceed transaction list
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
        self.assertEqual(1, len(actual_tx_list))

        cancel_tx_params = {'_transactionId': '0x00'}
        cancel_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='cancelTransaction',
                                             params=cancel_tx_params)

        prev_block, tx_results = self._make_and_req_block([cancel_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        actual_tx_list = self._query(query_request)
        self.assertEqual(0, len(actual_tx_list))

        submit_tx = self._make_score_call_tx(addr_from=self._owner1,
                                             addr_to=self.multisig_score_addr,
                                             method='submitTransaction',
                                             params=submit_tx_params)

        prev_block, tx_results = self._make_and_req_block([submit_tx])
        self._write_precommit_state(prev_block)
        self.assertEqual(int(True), tx_results[0].status)

        actual_tx_list = self._query(query_request)
        self.assertEqual(1, actual_tx_list[0]['_transaction_id'])
        self.assertEqual(1, len(actual_tx_list))

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
        actual_tx_count = self._query(query_request)
        self.assertEqual(1, actual_tx_count)

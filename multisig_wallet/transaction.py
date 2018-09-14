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

from iconservice import *

from struct import pack, unpack

DEFAULT_VALUE_BYTES = 32
DATA_BYTE_ORDER = 'big'


class Transaction:
    def __init__(self,
                 destination: Address,
                 method: str,
                 params: str,
                 value: int,
                 description: str,
                 executed: bool=False):

        self._executed = executed
        self._destination = destination
        # as None type can't be converted to bytes, must be changed to ""
        self._method = "" if method is None else method
        self._params = "" if params is None else params
        self._value = value
        self._description = description
        # struct_format will be used when decode serialized transaction data
        self._struct_format = self._make_sturct_format()

    def _make_sturct_format(self):
        #todo: check length of each params, in this method, restrict length of data
        destination_len = len(self._destination.to_bytes())
        method_len = len(self._method.encode())
        params_len = len(self._params.encode())
        value_len = DEFAULT_VALUE_BYTES
        description_len = len(self._description.encode())

        return f'>x{destination_len}sx{method_len}sx{params_len}sx{value_len}sx{description_len}s'

    @property
    def executed(self) -> bool:
        return self._executed

    @executed.setter
    def executed(self, executed: bool):
        self._executed = executed

    @property
    def destination(self) -> Address:
        return self._destination

    @property
    def method(self) -> str:
        return self._method

    @property
    def params(self) -> str:
        return self._params

    @property
    def value(self) -> int:
        return self._value

    @property
    def description(self) -> str:
        return self._description

    @staticmethod
    def from_bytes(buf: bytes):
        transaction_executed = buf[0]
        struct_format_len = buf[1]
        struct_format = buf[2:struct_format_len + 2].decode()

        destination, method, params, value, description = unpack(struct_format, buf[struct_format_len + 2:])

        return Transaction(executed=transaction_executed,
                           destination=Address.from_bytes(destination),
                           method=method.decode(encoding="utf-8"),
                           params=params.decode(encoding="utf-8"),
                           value=int.from_bytes(value, DATA_BYTE_ORDER),
                           description=description.decode(encoding="utf-8"))

    def to_bytes(self) -> bytes:
        struct_format_bytes = self._struct_format.encode()
        struct_format_len = len(struct_format_bytes)
        if struct_format_len > 256:
            raise IconScoreException("too long parameters")

        packed_variables = pack(
            self._struct_format,
            self._destination.to_bytes(),
            self._method.encode(encoding="utf-8"),
            self._params.encode(encoding="utf-8"),
            self._value.to_bytes(DEFAULT_VALUE_BYTES, DATA_BYTE_ORDER),
            self._description.encode(encoding="utf-8"))

        transaction = self.executed.to_bytes(1, DATA_BYTE_ORDER) + \
                      struct_format_len.to_bytes(1, DATA_BYTE_ORDER) + \
                      struct_format_bytes + packed_variables

        return transaction
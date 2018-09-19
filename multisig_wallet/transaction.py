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

from struct import Struct, pack, unpack

from iconservice import *

# addr, value fix
ADDRESS_BYTE_LEN = 21
DEFAULT_VALUE_BYTES = 16
DATA_BYTE_ORDER = "big"

MAX_METHOD_LEN = 100
MAX_PARAMS_LEN = 1000
MAX_DESCRIPTION_LEN = 1000

class Transaction:
    # executed flag 1bytes + address 21bytes + value 16bytes + format length 1bytes
    _fixed_struct = Struct(f">Bx{ADDRESS_BYTE_LEN}sx{DEFAULT_VALUE_BYTES}sxB")

    def __init__(self,
                 destination: Address,
                 method: str,
                 params: str,
                 value: int,
                 description: str,
                 executed: bool=False):

        # as None type can't be converted to bytes, must be changed to ""
        method = "" if method is None else method
        params = "" if params is None else params
        # struct_format will be used when decode serialized transaction data(method, params, description)
        self._flexible_struct_format = self._make_struct_format(method, params, description)
        self._executed = executed
        self._method = method
        self._params = params
        self._destination = destination
        self._value = value
        self._description = description

    def _make_struct_format(self, method, params, description):
        method_len = len(method.encode())
        params_len = len(params.encode())
        description_len = len(description.encode())
        if method_len > MAX_METHOD_LEN \
                or params_len > MAX_PARAMS_LEN \
                or description_len > MAX_DESCRIPTION_LEN:
            revert("too long variable length")

        return f'>x{method_len}sx{params_len}sx{description_len}s'

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
        fixed_variables_total_len = Transaction._fixed_struct.size
        transaction_executed, destination, value, flexible_struct_format_len = \
            Transaction._fixed_struct.unpack(buf[:fixed_variables_total_len])

        flexible_struct_format = \
            buf[fixed_variables_total_len: fixed_variables_total_len + flexible_struct_format_len].decode()
        method, params, description = unpack(flexible_struct_format,
                                             buf[fixed_variables_total_len + flexible_struct_format_len:])

        return Transaction(executed=transaction_executed,
                           destination=Address.from_bytes(destination.strip(b'\x00')),
                           method=method.decode(encoding="utf-8"),
                           params=params.decode(encoding="utf-8"),
                           value=int.from_bytes(value, DATA_BYTE_ORDER),
                           description=description.decode(encoding="utf-8"))

    def to_bytes(self) -> bytes:
        flexible_struct_format_bytes = self._flexible_struct_format.encode()
        flexible_struct_format_len = len(flexible_struct_format_bytes)
        if flexible_struct_format_len > 255:
            revert("too long parameters")

        packed_fixed_variables = self._fixed_struct.pack(
            self.executed,
            self.destination.to_bytes(),
            self._value.to_bytes(DEFAULT_VALUE_BYTES, DATA_BYTE_ORDER),
            flexible_struct_format_len
        )

        packed_flexible_variables = pack(
            self._flexible_struct_format,
            self._method.encode(encoding="utf-8"),
            self._params.encode(encoding="utf-8"),
            self._description.encode(encoding="utf-8"))

        transaction = packed_fixed_variables + \
                      flexible_struct_format_bytes + \
                      packed_flexible_variables

        return transaction
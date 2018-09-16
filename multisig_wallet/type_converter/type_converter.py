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


def params_type_converter(param_type: str, value: any):
    if param_type == "int":
        param = _convert_value_int(value) if isinstance(value, str) else value
    elif param_type == "str":
        param = _convert_value_string(value) if isinstance(value, str) else value
    elif param_type == "bool":
        param = _convert_value_bool(value) if isinstance(value, str) else value
    elif param_type == "Address":
        param = _convert_value_address(value) if isinstance(value, str) else value
    elif param_type == "bytes":
        param = _convert_value_bytes(value) if isinstance(value, str) else value
    else:
        raise IconScoreException\
            (f"{param_type} is not supported type(only int, str, bool, Address, bytes are supported)")
    return param

#Todo: builtin
def _convert_value_int(value: str) -> int:
    if value.startswith('0x') or value.startswith('-0x'):
        return int(value, 16)
    else:
        return int(value)


def _convert_value_string(value: str) -> str:
    return value


def _convert_value_bool(value: str) -> bool:
    return bool(_convert_value_int(value))


def _convert_value_address(value: str) -> 'Address':
    return Address.from_string(value)


def _convert_value_bytes(value: str) -> bytes:
    if value.startswith('0x'):
        return bytes.fromhex(value[2:])
    else:
        return bytes.fromhex(value)

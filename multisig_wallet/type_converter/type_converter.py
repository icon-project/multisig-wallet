from iconservice import *


def params_type_converter(param_type: str, value: any):
    param = None

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
            (f"{type} is not supported type(only int, str, bool, Address, bytes are supported)")
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

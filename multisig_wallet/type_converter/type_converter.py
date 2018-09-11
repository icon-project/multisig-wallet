from iconservice import *

def params_type_converter(_type: str, _value: str):
    param = None
    if _type == "int":
        param = _convert_value_int(_value)
    elif _type == "str":
        param = _convert_value_string(_value)
    elif _type == "bool":
        param = _convert_value_bool(_value)
    elif _type == "Address":
        param = _convert_value_address(_value)
    elif _type == "bytes":
        param = _convert_value_bytes(_value)
    else:
        raise IconScoreException\
            (f"{_type} is not supported type(only int, str, bool, Address, bytes are supporteds)")
    return param


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

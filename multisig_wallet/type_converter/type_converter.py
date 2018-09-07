from iconservice.base.address import Address


def params_type_converter(_type: str, _value: str):
    if _type is "int":
        param = _convert_value_int(_value)
    elif _type is "str":
        param = _convert_value_string(_value)
    elif _type is "bool":
        param = _convert_value_bool(_value)
    elif _type is "Address":
        param = _convert_value_address(_value)
    elif _type is "bytes":
        param = _convert_value_bytes(_value)
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

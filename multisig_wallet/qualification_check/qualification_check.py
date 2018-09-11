from iconservice import *
from functools import wraps


def only_wallet(func):
    if not isfunction(func):
        raise IconScoreException(f"{func} isn't function.")

    @wraps(func)
    def __wrapper(calling_obj: object, *args, **kwargs):
        if calling_obj.msg.sender != calling_obj.address:
            raise IconScoreException(
                f"{func} method only can be called by wallet SCORE(address: {calling_obj.address})")

        return func(calling_obj, *args, **kwargs)
    return __wrapper





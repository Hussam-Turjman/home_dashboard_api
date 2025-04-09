from .errors import ManagerErrors, translate_manager_error
import typing


def return_wrapper() -> typing.Callable:
    """
    Decorator to wrap a function and handle its return value.
    Returns
    -------

    """
    def wrapper(func) -> typing.Callable:
        def wrapped(*args, **kwargs) -> dict:
            res = func(*args, **kwargs)
            if isinstance(res, ManagerErrors):
                return {
                    "error": True,
                    "message": translate_manager_error(res),
                    "exception": ValueError(translate_manager_error(res)),
                }
            return {
                "error": False,
                "payload": res,
                "exception": None,
            }

        return wrapped

    return wrapper


__all__ = ["return_wrapper"]

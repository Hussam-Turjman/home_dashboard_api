from enum import Enum


class ManagerErrors(Enum):
    SUCCESS = 0
    NOT_FOUND = 1
    NOT_VERIFIED = 2
    INVALID_PASSWORD = 3


def translate_manager_error(error: ManagerErrors) -> str:
    if error == ManagerErrors.SUCCESS:
        return "Success"
    if error == ManagerErrors.NOT_FOUND:
        return "Not found"
    if error == ManagerErrors.NOT_VERIFIED:
        return "Not verified"
    if error == ManagerErrors.INVALID_PASSWORD:
        return "Invalid password"
    raise ValueError(f"Unknown manager error: {error}")


__all__ = ["ManagerErrors", "translate_manager_error"]

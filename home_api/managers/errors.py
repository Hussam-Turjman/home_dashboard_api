from enum import Enum


class ManagerErrors(Enum):
    SUCCESS = 0
    NOT_FOUND = 1
    NOT_VERIFIED = 2
    INVALID_PASSWORD = 3
    INVALID_IP_ADDRESS = 4
    EXPIRED = 5
    VALUE_ERROR = 6
    MULTIPLE_ENTRIES_FOUND = 7
    ENTRY_EXISTS = 8
    USER_ALREADY_LOGGED_IN = 9
    USER_NOT_FOUND = 10


def translate_manager_error(error: ManagerErrors) -> str:
    if error == ManagerErrors.SUCCESS:
        return "Success"
    if error == ManagerErrors.NOT_FOUND:
        return "Not found"
    if error == ManagerErrors.NOT_VERIFIED:
        return "Not verified"
    if error == ManagerErrors.INVALID_PASSWORD:
        return "Invalid password"
    if error == ManagerErrors.INVALID_IP_ADDRESS:
        return "Invalid IP address"
    if error == ManagerErrors.EXPIRED:
        return "Expired"
    if error == ManagerErrors.VALUE_ERROR:
        return "Value error"
    if error == ManagerErrors.MULTIPLE_ENTRIES_FOUND:
        return "Multiple entries found"
    if error == ManagerErrors.ENTRY_EXISTS:
        return "Entry exists"
    if error == ManagerErrors.USER_ALREADY_LOGGED_IN:
        return "User already logged in"
    if error == ManagerErrors.USER_NOT_FOUND:
        return "User not found"
    raise ValueError(f"Unknown manager error: {error}")


__all__ = ["ManagerErrors", "translate_manager_error"]

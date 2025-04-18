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
    SESSION_NOT_FOUND = 11
    INVALID_DATE = 12
    INVALID_AMOUNT = 13
    ENTRY_NOT_FOUND = 14
    NO_ENTRIES_FOUND = 15
    ENERGY_COUNTER_NOT_FOUND = 16
    DUPLICATE_ENERGY_COUNTER = 17
    ENERGY_COUNTER_INVALID_FREQUENCY = 18
    ENERGY_COUNTER_INVALID_READING_DATE = 19
    ENERGY_COUNTER_INVALID_READING = 20
    NOT_ENOUGH_ENERGY_COUNTER_READINGS = 21
    FEATURE_NOT_IMPLEMENTED = 22
    INVALID_MONTH_FREQUENCY = 23


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
    if error == ManagerErrors.SESSION_NOT_FOUND:
        return "Session not found"
    if error == ManagerErrors.INVALID_DATE:
        return "Invalid date"
    if error == ManagerErrors.INVALID_AMOUNT:
        return "Invalid amount"
    if error == ManagerErrors.ENTRY_NOT_FOUND:
        return "Entry not found"
    if error == ManagerErrors.NO_ENTRIES_FOUND:
        return "No entries found"
    if error == ManagerErrors.ENERGY_COUNTER_NOT_FOUND:
        return "Energy counter not found"
    if error == ManagerErrors.DUPLICATE_ENERGY_COUNTER:
        return "Duplicate energy counter"
    if error == ManagerErrors.ENERGY_COUNTER_INVALID_FREQUENCY:
        return "Energy counter invalid frequency. Valid values are ['daily', 'monthly', 'yearly']"
    if error == ManagerErrors.ENERGY_COUNTER_INVALID_READING_DATE:
        return "Energy counter invalid reading date. Reading date must be between start date and end date and greater than previous reading date"

    if error == ManagerErrors.ENERGY_COUNTER_INVALID_READING:
        return "Energy counter invalid reading. Reading must be greater than previous reading"

    if error == ManagerErrors.NOT_ENOUGH_ENERGY_COUNTER_READINGS:
        return "Not enough energy counter readings. At least two readings are required to calculate the consumption"

    if error == ManagerErrors.FEATURE_NOT_IMPLEMENTED:
        return "Feature not implemented"

    if error == ManagerErrors.INVALID_MONTH_FREQUENCY:
        return "Invalid month frequency. Valid values are between 1 and 12"

    raise ValueError(f"Unknown manager error: {error}")


__all__ = ["ManagerErrors", "translate_manager_error"]

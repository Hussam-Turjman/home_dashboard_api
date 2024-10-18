import re

from uuid import UUID


def is_valid_uuid(uuid_to_test, version=4):
    """
    Check if uuid_to_test is a valid UUID.

     Parameters
    ----------
    uuid_to_test : str
    version : {1, 2, 3, 4}

     Returns
    -------
    `True` if uuid_to_test is a valid UUID, otherwise `False`.

     Examples
    --------
    >>> is_valid_uuid('c9bf9e57-1685-4c89-bafb-ff5af830be8a')
    True
    >>> is_valid_uuid('c9bf9e58')
    False
    """

    try:
        uuid_obj = UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def is_valid_email(email: str) -> bool:
    # Define the regular expression pattern for a valid email
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    # Use re.match to check if the email matches the pattern
    if re.match(email_pattern, email):
        return True
    else:
        return False


def contains_numbers(s: str) -> bool:
    return not (not re.search(r'[0-9]', s))


def contains_special_characters(s: str) -> bool:
    return any(not c.isalnum() for c in s)


def contains_whitespace(s: str) -> bool:
    # Define a regular expression for white spaces
    whitespace_regex = r'\s'

    # Use the regular expression to check if the string contains white spaces
    return re.search(whitespace_regex, s) is not None


def is_strong_password(password: str) -> bool:
    # Check the length of the password
    if len(password) < 8:
        print("Password must be at least 8 characters long.")
        return False

    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        print("Password must contain at least one uppercase letter.")
        return False

    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        print("Password must contain at least one lowercase letter.")
        return False

    # Check for digit
    if not re.search(r'[0-9]', password):
        print("Password must contain at least one digit.")
        return False

    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        print("Password must contain at least one special character.")
        return False

    # If all checks pass, the password is strong
    return True


__all__ = ["is_strong_password",
           "is_valid_email",
           "contains_whitespace",
           "contains_numbers",
           "contains_special_characters",
           "is_valid_uuid"]

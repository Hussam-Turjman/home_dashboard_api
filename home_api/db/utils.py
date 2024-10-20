import secrets
import string


def generate_password(length: int = 20, fixed=False):
    if fixed:
        return "sf923_rFfs;@e3f"
    # Define the alphabet to contain all printable characters except whitespaces
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def create_username(first_name: str, last_name: str, last_id: int):
    username = f"{first_name.lower()[:2]}{last_name.lower()[:2]}{last_id + 1}"
    return username


__all__ = ["generate_password", "create_username"]

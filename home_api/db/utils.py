import secrets
import string


def generate_password(length: int = 20):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


def create_username(first_name: str, last_name: str, last_id: int):
    username = f"{first_name.lower()[:2]}{last_name.lower()[:2]}{last_id + 1}"
    return username


__all__ = ["generate_password", "create_username"]

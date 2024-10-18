import secrets
import string


def generate_password(length: int = 20):
    alphabet = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password


__all__ = ["generate_password"]

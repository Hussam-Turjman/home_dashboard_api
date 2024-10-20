import os
import secrets
from dotenv import load_dotenv, find_dotenv, set_key


def update_secret_key():
    load_dotenv(find_dotenv())
    secret_key = secrets.token_urlsafe(32)
    set_key(find_dotenv(), "JWT_SECRET_KEY", secret_key)


def run():
    update_secret_key()


if __name__ == "__main__":
    run()

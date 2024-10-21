from dotenv import load_dotenv
import os
import yaml
from .etc import PARENT_DIR
import datetime
from passlib.context import CryptContext


class EntryPoint(object):

    def __init__(self):
        self.access_config = None
        self.load()

    def load(self):
        load_dotenv()
        with open(os.path.join(PARENT_DIR, "utils", "access_config.yml"), "r") as f:
            self.access_config = yaml.safe_load(f)

    @property
    def port(self):
        return int(os.getenv("ENDPOINT_PORT", 8000))

    @property
    def host(self):
        return os.getenv("ENDPOINT", "localhost")

    @property
    def db_hostname(self):
        return os.getenv("DB_HOSTNAME", "localhost")

    @property
    def db_user(self):
        return os.getenv("DB_USER")

    @property
    def db_user_password(self):
        return os.getenv("DB_USER_PASSWORD")

    @property
    def db_name(self):
        return os.getenv("DB_NAME")

    @property
    def jwt_config(self):
        try:
            return self.access_config["JWT"]
        except KeyError:
            return None

    @property
    def jwt_algorithm(self):
        try:
            return self.jwt_config["ALGORITHM"]
        except KeyError:
            return None

    @property
    def access_token_expiration(self):
        try:
            return datetime.timedelta(minutes=self.jwt_config["ACCESS_TOKEN_EXPIRE_MINUTES"])
        except KeyError:
            return None

    @property
    def crypt_context(self):
        try:
            return self.access_config["CRYPT_CONTEXT"]
        except KeyError:
            return None

    @property
    def crypt_context_schemes(self):
        try:
            return self.crypt_context["SCHEMES"]
        except KeyError:
            return None

    @property
    def pwd_context(self):
        return CryptContext(schemes=self.crypt_context_schemes,
                            deprecated="auto")

    @property
    def secret_key(self):
        return os.getenv("JWT_SECRET_KEY")

    def check_all(self, missing_res=None):
        # check and return missing environment variables
        missing = []
        if not self.port:
            missing.append("PORT")
        if not self.host:
            missing.append("HOST")
        if not self.db_user:
            missing.append("DB_USER")
        if not self.db_user_password:
            missing.append("DB_USER_PASSWORD")
        if not self.db_name:
            missing.append("DB_NAME")
        if not self.secret_key:
            missing.append("JWT_SECRET")
        if not self.jwt_algorithm:
            missing.append("JWT_ALGORITHM")
        if not self.access_token_expiration:
            missing.append("ACCESS_TOKEN")
        if not self.crypt_context_schemes:
            missing.append("CRYPT_SCHEMES")
        if not self.secret_key:
            missing.append("SECRET_KEY")
        if not self.db_hostname:
            missing.append("DB_HOSTNAME")

        if missing_res is not None:
            missing_res.extend(missing)

        return len(missing) == 0

    def __repr__(self):
        return f"EntryPoint(port={self.port}, host={self.host}, db_hostname={self.db_hostname}, db_user={self.db_user}, db_user_password={self.db_user_password}, db_name={self.db_name}, jwt_config={self.jwt_config}, jwt_algorithm={self.jwt_algorithm}, access_token_expiration={self.access_token_expiration}, crypt_context={self.crypt_context}, crypt_context_schemes={self.crypt_context_schemes}, pwd_context={self.pwd_context}, secret_key={self.secret_key})"


entry_point = EntryPoint()

__all__ = ["EntryPoint", "entry_point"]

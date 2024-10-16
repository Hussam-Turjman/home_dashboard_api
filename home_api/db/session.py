import sqlalchemy
from sqlalchemy.orm import sessionmaker
from ..entrypoint import entry_point


def get_session(db_user, db_user_password, db_name: str, hostname: str, d_Base=None):
    engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{db_user}:{db_user_password}@{hostname}/{db_name}")
    if d_Base:
        d_Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class Session(object):
    def __init__(self, db_user, db_user_password, db_name: str, hostname: str):
        self.db_name = db_name
        self.hostname = hostname
        self.db_user = db_user
        self.db_user_password = db_user_password
        self.session = None

    @classmethod
    def create(cls):
        return cls(db_name=entry_point.db_name,
                   hostname=entry_point.db_hostname,
                   db_user=entry_point.db_user,
                   db_user_password=entry_point.db_user_password)

    def __enter__(self):
        self.session = get_session(db_name=self.db_name,
                                   hostname=self.hostname,
                                   db_user=self.db_user,
                                   db_user_password=self.db_user_password)
        return self.session

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.session.close()

    def __repr__(self):
        return f"Session(db_name={self.db_name}, hostname={self.hostname}, db_user={self.db_user}, db_user_password={self.db_user_password})"


__all__ = ["Session"]

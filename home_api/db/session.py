import sqlalchemy
from sqlalchemy.orm import sessionmaker
from ..entrypoint import entry_point


class Session(object):
    instance: sqlalchemy.orm.Session | None
    engine: sqlalchemy.engine.base.Engine | None

    def __init__(self, db_user, db_user_password,
                 db_name: str, hostname: str,
                 d_Base=None, auto_commit=True):
        self.db_name = db_name
        self.hostname = hostname
        self.db_user = db_user
        self.db_user_password = db_user_password
        self.instance = None
        self.engine = None
        self.d_Base = d_Base
        self.auto_commit = auto_commit

    @property
    def is_connected(self):
        return self.instance is not None

    def init(self):
        self.cleanup()
        self.instance = self.get_session()
        return self

    def cleanup(self):
        if self.instance is not None:
            if self.auto_commit:
                self.instance.commit()
            self.instance.close()
            self.engine.dispose()
            self.instance = None
            self.engine = None
        return self

    def drop_all(self):
        self.d_Base.metadata.drop_all(self.engine)
        return self

    def create_all(self):
        self.d_Base.metadata.create_all(self.engine)
        return self

    def drop_table(self, table):
        table.__table__.drop(self.engine)
        return self

    def create_table(self, table):
        table.__table__.create(self.engine)
        return self

    @classmethod
    def create(cls, d_Base=None, auto_commit=True, **kwargs):
        db_name = kwargs.get("db_name", entry_point.db_name)
        hostname = kwargs.get("hostname", entry_point.db_hostname)
        db_user = kwargs.get("db_user", entry_point.db_user)
        db_user_password = kwargs.get(
            "db_user_password", entry_point.db_user_password)
        return cls(db_name=db_name, hostname=hostname,
                   db_user=db_user,
                   db_user_password=db_user_password,
                   d_Base=d_Base,
                   auto_commit=auto_commit).init()

    def get_session(self):
        self.engine = sqlalchemy.create_engine(
            f"postgresql+psycopg2://{self.db_user}:{self.db_user_password}@{self.hostname}/{self.db_name}")
        if self.d_Base:
            self.d_Base.metadata.create_all(self.engine)
        return sessionmaker(bind=self.engine)()

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cleanup()

    def __repr__(self):
        return f"Session(db_name={self.db_name}, hostname={self.hostname}, db_user={self.db_user}, db_user_password={self.db_user_password})"

    def __del__(self):
        self.cleanup()


__all__ = ["Session"]

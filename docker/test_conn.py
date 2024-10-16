import os
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from sqlalchemy.orm import declarative_base
from sqlalchemy import (Column, Integer, String, Date, DateTime,
                        ForeignKey, Boolean, Float)

Base = declarative_base()

# read environment variables


# from dotenv import load_dotenv
# load_dotenv()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, name="id",
                unique=True, autoincrement=True)
    username = Column(String, name="username", nullable=False, unique=True)


def get_session(db_user, db_user_password, db_name: str, hostname: str):
    engine = sqlalchemy.create_engine(
        f"postgresql+psycopg2://{db_user}:{db_user_password}@{hostname}/{db_name}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class Session(object):
    def __init__(self, db_user, db_user_password, db_name: str, hostname: str):
        self.db_name = db_name
        self.hostname = hostname
        self.db_user = db_user
        self.db_user_password = db_user_password
        self.session = None

    def __enter__(self):
        self.session = get_session(db_name=self.db_name,
                                   hostname=self.hostname,
                                   db_user=self.db_user,
                                   db_user_password=self.db_user_password)
        return self.session

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.session.close()


def run():
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    HOSTNAME = "localhost"
    with Session(db_name=DB_NAME, hostname=HOSTNAME,
                 db_user=DB_USER,
                 db_user_password=DB_PASS) as db_session:
        user = User(username="test")
        db_session.add(user)
        db_session.commit()

    print("Successfully connected to the database")


if __name__ == "__main__":
    run()

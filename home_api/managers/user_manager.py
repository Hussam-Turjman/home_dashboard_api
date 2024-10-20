from passlib.context import CryptContext

from ..db.user import User
from ..db.session import Session
from sqlalchemy.orm.session import Session as SQLSession
from ..entrypoint import entry_point
from .errors import ManagerErrors


class UserManager(object):
    db_session: SQLSession
    pwd_context: CryptContext

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session
        self.pwd_context = entry_point.pwd_context

    def create_user(self, first_name: str, last_name: str, email: str, password: str) -> User:
        user = User.create(session=self.db_session,
                           first_name=first_name,
                           last_name=last_name,
                           email=email,
                           password=password,
                           hash_func=self.pwd_context.hash)
        self.db_session.add(user)
        self.db_session.commit()
        return user

    def delete_user_by_email(self, email: str):
        user = self.db_session.query(User).filter_by(email=email).first()
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
        else:
            return ManagerErrors.NOT_FOUND
        return user

    def delete_user_by_username(self, username: str):
        user = self.db_session.query(User).filter_by(username=username).first()
        if user:
            self.db_session.delete(user)
            self.db_session.commit()
        else:
            return ManagerErrors.NOT_FOUND
        return user

    def verify_user(self, email: str, username: str):
        user = self.db_session.query(User).filter_by(
            email=email).filter_by(username=username).first()
        if not user:
            return ManagerErrors.NOT_FOUND
        user.verified = True
        self.db_session.commit()
        return user

    def _check_user_login(self, user: User | None, password: str):
        if not user:
            return ManagerErrors.NOT_FOUND
        if not user.verified:
            return ManagerErrors.NOT_VERIFIED
        if not self.pwd_context.verify(password, user.password):
            return ManagerErrors.INVALID_PASSWORD
        return user

    def login_email(self, email: str, password: str):
        user = self.db_session.query(User).filter_by(email=email).first()
        return self._check_user_login(user, password)

    def login_username(self, username: str, password: str):
        user = self.db_session.query(User).filter_by(username=username).first()
        return self._check_user_login(user, password)


__all__ = ["UserManager"]

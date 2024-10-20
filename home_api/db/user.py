from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey
from typing import Callable
from .checks import is_valid_email, is_strong_password, contains_whitespace, contains_numbers, \
    contains_special_characters
from .utils import create_username
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import datetime


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, name="id",
                unique=True, autoincrement=True)
    username = Column(String, name="username", nullable=False, unique=True)
    password = Column(String, name="password", nullable=False)
    email = Column(String, name="email", unique=True, nullable=False)
    first_name = Column(String, name="first_name", nullable=False)
    last_name = Column(String, name="last_name", nullable=False)
    verified = Column(Boolean, name="verified", nullable=False, default=False)

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return (f"<User(id={self.id}, "
                f"username={self.username}, "
                f"password={self.password}, "
                f"email={self.email}, "
                f"first_name={self.first_name}, "
                f"last_name={self.last_name}, "
                f"time_created={self.time_created}, "
                f"time_updated={self.time_updated}, "
                f"verified={self.verified}>")

    @classmethod
    def create(cls, session, first_name: str, last_name: str, email: str, password: str,
               hash_func: Callable[[str], str]):
        # Get the last user id
        last_user = session.query(User).order_by(User.id.desc()).first()
        if last_user:
            last_id = last_user.id
        else:
            last_id = 0
        # Generate pseudo username based on the first name and last name and the last user id
        username = create_username(first_name, last_name, last_id)
        # Check if the email is already in use
        if session.query(User).filter_by(email=email).first():
            raise ValueError(f"Email {email} already in use")
        # Check if the email is valid
        if not is_valid_email(email):
            raise ValueError("Invalid email")
        # Check if the password is strong
        if not is_strong_password(password):
            raise ValueError(
                "Weak password. Password must at least be 8 characters long, contain at least one uppercase "
                "letter, one lowercase letter, one digit, and one special character")
        # Check if the first name contains white spaces
        if contains_whitespace(first_name):
            raise ValueError("First name cannot contain white spaces")
        # Check if the first name contains numbers
        if contains_numbers(first_name):
            raise ValueError("First name cannot contain numbers")

        # Check if the first name contains special characters
        if contains_special_characters(first_name):
            raise ValueError("First name cannot contain special characters")

        # Check if the last name contains white spaces
        if contains_whitespace(last_name):
            raise ValueError("Last name cannot contain white spaces")

        # Check if the last name contains numbers
        if contains_numbers(last_name):
            raise ValueError("Last name cannot contain numbers")

        # Check if the last name contains special characters
        if contains_special_characters(last_name):
            raise ValueError("Last name cannot contain special characters")

        # Create the user
        hashed_password = hash_func(password)

        user = User(username=username, first_name=first_name, last_name=last_name, email=email,
                    password=hashed_password)
        return user


class UserSession(Base):
    __tablename__ = "user_session"
    id = Column(UUID(as_uuid=True), primary_key=True,
                name="id", unique=True, default=uuid.uuid4)

    user_id = Column(Integer, ForeignKey("user.id"),
                     name="user_id", nullable=False)
    token = Column(String, name="token", nullable=False)
    expires_at = Column(DateTime, name="expires_at", nullable=False)
    active = Column(Boolean, name="active", nullable=False, default=True)
    created_at = Column(DateTime, name="created_at", nullable=False)
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    ip = Column(String, name="ip", nullable=False)
    location = Column(String, name="location", nullable=False)
    agent = Column(String, name="agent", nullable=False)

    user = relationship("User", backref="user_session")

    def __repr__(self):
        return (f"<UserSession(id={self.id}, "
                f"user_id={self.user_id}, "
                f"token={self.token}, "
                f"expires_at={self.expires_at}, "
                f"active={self.active}, "
                f"ip={self.ip}, "
                f"location={self.location}, "
                f"created_at={self.created_at}, "
                f"time_updated={self.time_updated}, "
                f"agent={self.agent}>")

    @classmethod
    def create_empty(cls, user_id: int):
        return cls(
            token="",
            ip="",
            location="",
            agent="",
            created_at=datetime.datetime.now(),
            expires_at=datetime.datetime.now() + datetime.timedelta(days=1),
            user_id=user_id,
        )


__all__ = ["User", "UserSession"]

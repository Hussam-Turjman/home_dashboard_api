from .base import Base

from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from typing import Callable
from .checks import is_valid_email, is_strong_password, contains_whitespace, contains_numbers, \
    contains_special_characters


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
        username = f"{first_name.lower()[:2]}{last_name.lower()[:2]}{last_id + 1}"
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

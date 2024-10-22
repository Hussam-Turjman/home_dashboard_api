import datetime
import uuid
from typing import Callable

from sqlalchemy import Boolean
from sqlalchemy import Column, Float, Date, func, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .checks import is_valid_email, is_strong_password, contains_whitespace, contains_numbers, \
    contains_special_characters
from .utils import create_username
from sqlalchemy.orm import declarative_base

Base = declarative_base()


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

    account_entries = relationship(
        "AccountEntry", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", cascade="all, delete-orphan")
    energy_counters = relationship(
        "EnergyCounter", cascade="all, delete-orphan")

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

    token = Column(String, name="token", nullable=False)
    expires_at = Column(DateTime, name="expires_at", nullable=False)
    active = Column(Boolean, name="active", nullable=False, default=True)
    created_at = Column(DateTime, name="created_at", nullable=False)
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    ip = Column(String, name="ip", nullable=False)
    location = Column(String, name="location", nullable=False)
    agent = Column(String, name="agent", nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"),
                     name="user_id", nullable=False)

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


class AccountEntry(Base):
    __tablename__ = "account_entry"
    id = Column(UUID(as_uuid=True), primary_key=True,
                name="id", unique=True, default=uuid.uuid4)

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    start_date = Column(Date, name="start_date", nullable=False)
    end_date = Column(Date, name="end_date", nullable=False)
    # Add field for month count between start_date and end_date
    months_count = Column(Integer, name="months_count", nullable=False,
                          default=0)

    amount = Column(Float, name="amount")
    # Total amount for the entry
    total_amount = Column(Float, name="total_amount",
                          nullable=False, default=0)

    name = Column(String, name="name", unique=False, nullable=False)

    tag = Column(String, name="tag")

    user_id = Column(Integer, ForeignKey("user.id"),
                     name="user_id", nullable=False)

    # user = relationship("User", backref=backref("account_entries", cascade="all, delete-orphan"))

    @classmethod
    def create_empty(cls, user_id):
        return cls(
            start_date=datetime.datetime.now().date(),
            end_date=(datetime.datetime.now() +
                      datetime.timedelta(days=1)).date(),
            amount=0.0,
            name="name",
            tag="tag",
            user_id=user_id
        )

    def __repr__(self):
        return (f"<AccountEntry(id={self.id}, "
                f"start_date={self.start_date}, "
                f"end_date={self.end_date}, "
                f"amount={self.amount}, "
                f"name={self.name}, "
                f"tag={self.tag}, "
                f"user_id={self.user_id}>")


class EnergyCounter(Base):
    __tablename__ = "energy_counter"
    id = Column(UUID(as_uuid=True), primary_key=True,
                name="id", unique=True, default=uuid.uuid4)

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    counter_id = Column(String, name="counter_id", nullable=False)
    counter_type = Column(String, name="counter_type", nullable=False)

    base_price = Column(Float, name="base_price", nullable=False)
    price = Column(Float, name="price", nullable=False)
    energy_unit = Column(String, name="energy_unit", nullable=False)
    frequency = Column(String, name="frequency",
                       nullable=False)  # Monthly, yearly, etc
    start_date = Column(Date, name="start_date", nullable=False)
    first_reading = Column(Float, name="first_reading", nullable=False)

    user_id = Column(Integer, ForeignKey("user.id"),
                     name="user_id", nullable=False)
    counter_readings = relationship(
        "EnergyCounterReading", cascade="all, delete-orphan")

    def __repr__(self):
        return (f"<EnergyCounter(id={self.id}, "
                f"counter_id={self.counter_id}, "
                f"counter_type={self.counter_type}, "
                f"energy_unit={self.energy_unit}, "
                f"frequency={self.frequency}, "
                f"user_id={self.user_id}, "
                f"base_price={self.base_price}, "
                f"price={self.price}, "
                f"start_date={self.start_date}, "
                f"first_reading={self.first_reading}")

    @classmethod
    def create_empty(cls, user_id: int):
        return cls(
            counter_id="123456",
            counter_type="counter_type",
            base_price=0.0,
            price=0.0,
            energy_unit="unit",
            frequency="day",
            start_date=datetime.datetime.now().date(),
            first_reading=0.0,
            user_id=user_id
        )


class EnergyCounterReading(Base):
    __tablename__ = "energy_counter_reading"
    id = Column(UUID(as_uuid=True), primary_key=True,
                name="id", unique=True, default=uuid.uuid4)

    time_created = Column(DateTime(timezone=True), server_default=func.now())
    time_updated = Column(DateTime(timezone=True), onupdate=func.now())

    # Reading must be greater than max_reading

    reading = Column(Float, name="reading", nullable=False)
    reading_date = Column(Date, name="reading_date", nullable=False)

    counter_id = Column(UUID(as_uuid=True), ForeignKey(
        "energy_counter.id"), name="counter_id", nullable=False)

    def convert_to_dict(self, counter_id, counter_type):
        return {
            "id": self.id,
            "reading": self.reading,
            "reading_date": self.reading_date,
            "counter_id": counter_id,
            "counter_type": counter_type
        }

    def __repr__(self):
        return (f"<EnergyCounterReading(id={self.id}, "
                f"reading={self.reading}, "
                f"reading_date={self.reading_date}, "
                f"counter_id={self.counter_id}>")

    @classmethod
    def create_empty(cls, counter_id: str):
        return cls(
            reading=0.0,
            reading_date=datetime.datetime.now().date(),
            counter_id=counter_id
        )


__all__ = ["User", "UserSession", "AccountEntry",
           "EnergyCounter", "EnergyCounterReading", "Base"]

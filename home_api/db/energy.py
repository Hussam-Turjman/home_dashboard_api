from .base import Base
from sqlalchemy import Column, Float, Date, func, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime


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
    user = relationship("User", backref="energy_counter")

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
    counter = relationship("EnergyCounter", backref="energy_counter_reading")

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


__all__ = ["EnergyCounter", "EnergyCounterReading"]

from sqlalchemy import Column, Integer, String, Float, DateTime
from .base import Base


class Dummy(Base):
    __tablename__ = "dummy"
    id = Column(Integer, primary_key=True, name="id",
                unique=True, autoincrement=True)
    name = Column(String, name="name", nullable=False, unique=False)
    value = Column(Float, name="value", nullable=False)


__all__ = ["Dummy"]

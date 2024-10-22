import datetime
from pydantic import BaseModel
from uuid import UUID


class EnergyCounterModel(BaseModel):
    id: str | UUID
    counter_id: str
    counter_type: str
    energy_unit: str
    frequency: str
    user_id: int
    base_price: float
    price: float
    start_date: datetime.date | str
    first_reading: float

    class Config:
        from_attributes = True


class EnergyCounterReadingModel(BaseModel):
    id: str | UUID
    counter_id: str
    counter_type: str
    reading: float
    reading_date: datetime.date | str

    class Config:
        from_attributes = True


__all__ = ["EnergyCounterModel", "EnergyCounterReadingModel"]

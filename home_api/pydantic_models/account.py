from pydantic import BaseModel
import datetime
from uuid import UUID


class AccountEntryModel(BaseModel):
    id: str | UUID
    start_date: datetime.date | str
    end_date: datetime.date | str
    amount: float
    name: str
    tag: str
    months_count: int = 0
    total_amount: float = 0.0

    class Config:
        from_attributes = True


class MonthExpensesTagModel(BaseModel):
    id: int
    value: float
    label: str


__all__ = ["AccountEntryModel", "MonthExpensesTagModel"]

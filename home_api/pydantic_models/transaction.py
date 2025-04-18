from pydantic import BaseModel
import datetime
from uuid import UUID


class BankTransactionModel(BaseModel):
    id: str | UUID
    booking_date: datetime.date | str
    value_date: datetime.date | str
    amount: float
    description: str
    currency: str
    category: str
    subcategory: str
    keyword: str

    class Config:
        from_attributes = True


__all__ = ['BankTransactionModel']

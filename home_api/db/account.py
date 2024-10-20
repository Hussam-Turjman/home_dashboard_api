import uuid

from sqlalchemy import (Column, Integer, String, DateTime,
                        Float, Date, func, ForeignKey)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base
import datetime


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
    user = relationship("User", backref="account_entry")

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


__all__ = ["AccountEntry"]

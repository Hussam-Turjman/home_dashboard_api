import datetime

from sqlalchemy.orm.session import Session as SQLSession

from .errors import ManagerErrors, translate_manager_error
from ..db.tables import AccountEntry, User

from ..db.utils import diff_month


class ExpenseManager(object):
    db_session: SQLSession

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session

    def _add_account_entry(self, user_id, entry_id, start_date: datetime.date,
                           end_date: datetime.date, amount: float, name: str,

                           tag: str) -> AccountEntry | ManagerErrors:
        user_exists = (self.db_session.query(User).
                       filter(User.id == user_id).
                       first())
        if not user_exists:
            return ManagerErrors.USER_NOT_FOUND
        if end_date < start_date:
            return ManagerErrors.INVALID_DATE
        if amount == 0:
            return ManagerErrors.INVALID_AMOUNT
        months_count = diff_month(end_date, start_date)
        if months_count < 0:
            return ManagerErrors.INVALID_DATE

        # Check if entry_id exists
        entry_exists = (self.db_session.query(AccountEntry).
                        filter(AccountEntry.id == entry_id).
                        first())
        if entry_exists:
            account_entry = entry_exists
            account_entry.start_date = start_date
            account_entry.end_date = end_date
            account_entry.amount = amount
            account_entry.name = name
            account_entry.tag = tag
            account_entry.months_count = months_count + 1
            account_entry.total_amount = amount * account_entry.months_count
        else:
            months_count = diff_month(end_date, start_date) + 1
            total_amount = amount * months_count
            account_entry = AccountEntry(start_date=start_date,
                                         end_date=end_date,
                                         months_count=months_count,
                                         total_amount=total_amount,
                                         amount=amount,
                                         name=name,
                                         user_id=user_id,
                                         tag=tag,
                                         id=entry_id)
            self.db_session.add(account_entry)

        self.db_session.commit()
        return account_entry

    def _delete_account_entry(self, user_id, entry_id):
        entry = (self.db_session.query(AccountEntry).
                 filter(AccountEntry.id == entry_id).
                 filter(AccountEntry.user_id == user_id).
                 first())
        if not entry:
            return ManagerErrors.ENTRY_NOT_FOUND
        self.db_session.delete(entry)
        self.db_session.commit()
        return entry

    def add_account_entry(self, user_id, entry_id, start_date: datetime.date,
                          end_date: datetime.date, amount: float, name: str,
                          tag: str) -> dict:
        account_entry = self._add_account_entry(user_id=user_id,
                                                entry_id=entry_id,
                                                start_date=start_date,
                                                end_date=end_date,
                                                amount=amount,
                                                name=name,
                                                tag=tag)
        if isinstance(account_entry, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(account_entry),
                "exception": ValueError(translate_manager_error(account_entry)),
            }
        return {
            "error": False,
            "payload": account_entry,
        }

    def delete_account_entry(self, user_id, entry_id) -> dict:
        res = self._delete_account_entry(user_id=user_id, entry_id=entry_id)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

    def create_dummy_account_entry(self, user_id):
        entry = AccountEntry(start_date=datetime.date(2021, 1, 1),
                             end_date=datetime.date(2021, 10, 1),
                             months_count=10,
                             total_amount=100,
                             amount=100,
                             name="Dummy",
                             user_id=user_id,
                             tag="Dummy")
        self.db_session.add(entry)
        self.db_session.commit()
        return entry


__all__ = ["ExpenseManager"]

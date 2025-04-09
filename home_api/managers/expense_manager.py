import datetime
from typing import List

from sqlalchemy.orm.session import Session as SQLSession

from .errors import ManagerErrors, translate_manager_error
from ..db.tables import AccountEntry, User
from sqlalchemy import func
from ..pydantic_models.account import MonthExpensesTagModel
from ..db.utils import diff_month, create_dates_labels
from dateutil.relativedelta import relativedelta
import numpy as np
from .return_wrapper import return_wrapper


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

    @return_wrapper()
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
        return account_entry

    @return_wrapper()
    def delete_account_entry(self, user_id, entry_id) -> dict:
        res = self._delete_account_entry(user_id=user_id, entry_id=entry_id)
        return res

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

    def get_account_entries(self, user_id):
        entries = (self.db_session.query(AccountEntry).
                   filter(AccountEntry.user_id == user_id).
                   all())
        return entries

    def get_month_expenses(self, user_id, month, year):
        results = []
        date = datetime.date(year, month, 1)

        # Group by tag and sum amount
        query = (self.db_session.query(AccountEntry.tag.label("label"), func.sum(AccountEntry.amount).label("value")).
                 filter(AccountEntry.user_id == user_id).
                 # Date between start and end
                 filter(AccountEntry.start_date <= date).
                 filter(AccountEntry.end_date >= date).
                 group_by(AccountEntry.tag).
                 all())
        idx = 0
        for tag, value in query:
            if value >= 0:
                continue
            results.append(MonthExpensesTagModel(
                id=idx, value=abs(value), label=tag))
            idx += 1
        return results

    def get_month_expenses_and_savings(self, user_id, month, year,
                                       ignore_invalid_income=True,
                                       allow_all_zeros=True) -> List[
            MonthExpensesTagModel]:
        expenses = self.get_month_expenses(user_id, month, year)
        total_expenses = sum([expense.value for expense in expenses])
        date = datetime.date(year, month, 1)
        results = []
        # Get income
        income = (self.db_session.query(func.sum(AccountEntry.amount).label("income")).
                  filter(AccountEntry.user_id == user_id).
                  filter(AccountEntry.start_date <= date).
                  filter(AccountEntry.end_date >= date).
                  filter(AccountEntry.amount > 0).
                  first())
        if income and income[0] is not None:
            total_income = income[0]
            # max(total_income - total_expenses, 0)
            savings = total_income - total_expenses
            results.append(MonthExpensesTagModel(
                id=0, value=savings, label="Savings"))
            results.append(MonthExpensesTagModel(
                id=1, value=total_expenses, label="Expenses"))
            results.append(MonthExpensesTagModel(
                id=2, value=total_income, label="Income"))
        elif ignore_invalid_income:
            results.append(MonthExpensesTagModel(
                id=0, value=-total_expenses, label="Savings"))
            results.append(MonthExpensesTagModel(
                id=1, value=total_expenses, label="Expenses"))
            results.append(MonthExpensesTagModel(
                id=2, value=0, label="Income"))
        if not allow_all_zeros:
            results = [result for result in results if result.value != 0]
        return results

    @return_wrapper()
    def get_overview_chart(self, user_id,
                           start_month=None,
                           start_year=None,
                           end_month=None,
                           end_year=None,
                           include_last_month=False,
                           apply_cumulative_on_expenses=True,
                           apply_cumulative_on_income=True,
                           apply_cumulative_on_savings=True
                           ):
        res = self._get_overview_chart(user_id=user_id,
                                       start_month=start_month,
                                       start_year=start_year,
                                       end_month=end_month,
                                       end_year=end_year,
                                       include_last_month=include_last_month,
                                       apply_cumulative_on_expenses=apply_cumulative_on_expenses,
                                       apply_cumulative_on_income=apply_cumulative_on_income,
                                       apply_cumulative_on_savings=apply_cumulative_on_savings
                                       )
        return res

    def _get_overview_chart(self, user_id,
                            start_month=None,
                            start_year=None,
                            end_month=None,
                            end_year=None,
                            include_last_month=False,
                            apply_cumulative_on_expenses=True,
                            apply_cumulative_on_income=True,
                            apply_cumulative_on_savings=True):
        min_start_date = self.db_session.query(func.min(AccountEntry.start_date)).filter(
            AccountEntry.user_id == user_id).first()[0]
        if min_start_date is None:
            return ManagerErrors.NO_ENTRIES_FOUND

        min_start_month = min_start_date.month
        min_start_year = min_start_date.year
        if start_month is None:
            now = datetime.datetime.now()
            start_month = now.month
            start_year = now.year
            end_month = (now + relativedelta(years=1)).month
            end_year = (now + relativedelta(years=1)).year
        start_date = datetime.date(start_year, start_month, 1)
        if start_date < min_start_date:
            # min_start_date = start_date
            min_start_year = start_year
            min_start_month = start_month
        end_date = datetime.date(end_year, end_month, 1)
        if start_date >= end_date:
            return ManagerErrors.INVALID_DATE

        # month_diff = diff_month(end_date, min_start_date)

        x_labels = create_dates_labels(
            start_date=datetime.date(min_start_year, min_start_month, 1),
            end_date=datetime.date(end_year, end_month, 1),
            include_last_month=include_last_month,
            to_dates=False
        )
        # convert labels to dates
        x_labels_dates = [datetime.datetime.strptime(
            label, "%b %Y").date() for label in x_labels]
        cumulative_savings = []
        cumulative_expenses = []
        cumulative_income = []
        to_remove_idxes = []
        for idx, date in enumerate(x_labels_dates):
            current_date = datetime.date(date.year, date.month, 1)
            if current_date < start_date:
                to_remove_idxes.append(idx)
            res = self.get_month_expenses_and_savings(user_id=user_id,
                                                      month=date.month,
                                                      year=date.year,
                                                      ignore_invalid_income=True)
            if len(res) == 0:
                cumulative_savings.append(0)
                cumulative_expenses.append(0)
                cumulative_income.append(0)
            for item in res:
                if item.label == "Savings":
                    cumulative_savings.append(item.value)
                elif item.label == "Expenses":
                    cumulative_expenses.append(item.value)
                elif item.label == "Income":
                    cumulative_income.append(item.value)

        if apply_cumulative_on_savings:
            cumulative_savings = np.cumsum(cumulative_savings).tolist()
        if apply_cumulative_on_expenses:
            cumulative_expenses = np.cumsum(cumulative_expenses).tolist()
        if apply_cumulative_on_income:
            cumulative_income = np.cumsum(cumulative_income).tolist()

        x_labels = np.delete(x_labels, to_remove_idxes).tolist()
        cumulative_income = np.delete(
            cumulative_income, to_remove_idxes).tolist()
        cumulative_expenses = np.delete(
            cumulative_expenses, to_remove_idxes).tolist()
        cumulative_savings = np.delete(
            cumulative_savings, to_remove_idxes).tolist()

        return {
            "x_labels": x_labels,
            "cumulative_savings": cumulative_savings,
            "cumulative_expenses": cumulative_expenses,
            "cumulative_income": cumulative_income,
            "start_month": start_month,
            "start_year": start_year,
            "end_month": end_month,
            "end_year": end_year

        }


__all__ = ["ExpenseManager"]

import datetime

from fastapi import Depends, HTTPException, status, APIRouter, Body, Request

from .user import validate_user
from ..managers.expense_manager import ExpenseManager
from ..pydantic_models.account import AccountEntryModel, MonthExpensesTagModel
from ..pydantic_models.session import UserSessionModel
from ..runtime import db_session
from typing import Annotated, List

expense_manager = ExpenseManager(db_session=db_session)

URL_BASE = "/api/expenses"
router = APIRouter(
    prefix=URL_BASE,
    tags=["expenses"],
    dependencies=[Depends(validate_user)]
)


@router.put("/add_account_entry/{session_id}", response_model=AccountEntryModel)
async def add_account_entry(user: Annotated[UserSessionModel, Depends(validate_user)],
                            entry: AccountEntryModel = Body(...)):
    entry.start_date = datetime.datetime.strptime(
        entry.start_date, "%m/%Y").date().replace(day=1)
    entry.end_date = datetime.datetime.strptime(
        entry.end_date, "%m/%Y").date().replace(day=1)

    res = expense_manager.add_account_entry(user_id=user.user_id,
                                            start_date=entry.start_date,
                                            end_date=entry.end_date,
                                            amount=entry.amount,
                                            name=entry.name,
                                            tag=entry.tag,
                                            entry_id=entry.id)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )

    payload = res["payload"]
    return AccountEntryModel.model_validate(payload).model_dump()


@router.delete("/delete_account_entry/{session_id}/{entry_id}", response_model=AccountEntryModel)
async def delete_account_entry(user: Annotated[UserSessionModel, Depends(validate_user)],
                               entry_id: str):
    res = expense_manager.delete_account_entry(
        user_id=user.user_id, entry_id=entry_id)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )
    payload = res["payload"]
    return AccountEntryModel.model_validate(payload).model_dump()


@router.get("/account_entries/{session_id}", response_model=List[AccountEntryModel])
async def account_entries(user: Annotated[UserSessionModel, Depends(validate_user)]):
    entries = [AccountEntryModel.model_validate(entry).model_dump() for entry in
               expense_manager.get_account_entries(user_id=user.user_id)]

    # Set floating point precision to 2
    for entry in entries:
        entry["amount"] = round(entry["amount"], 2)
        entry["total_amount"] = round(entry["total_amount"], 2)
    return entries


@router.get("/month_expenses/{session_id}", response_model=List[MonthExpensesTagModel])
async def get_month_expenses(user: Annotated[UserSessionModel, Depends(validate_user)],
                             month: int, year: int):
    res = expense_manager.get_month_expenses(
        user_id=user.user_id, month=month, year=year)

    return res


@router.get("/month_expenses_and_savings/{session_id}", response_model=List[MonthExpensesTagModel])
async def get_month_expenses_and_savings(user: Annotated[UserSessionModel, Depends(validate_user)],
                                         month: int, year: int):
    res = expense_manager.get_month_expenses_and_savings(user_id=user.user_id,
                                                         month=month, year=year,
                                                         allow_all_zeros=False)

    return res


@router.get("/overview_chart/{session_id}", response_model=dict)
async def get_overview_chart(user: Annotated[UserSessionModel, Depends(validate_user)],
                             start_month: int, start_year: int,
                             end_month: int, end_year: int, request: Request):
    if start_month == 0 and start_year == 0 and end_month == 0 and end_year == 0:
        start_month = None
        start_year = None
        end_month = None
        end_year = None
    res = expense_manager.get_overview_chart(user_id=user.user_id,
                                             start_month=start_month,
                                             start_year=start_year,
                                             end_month=end_month,
                                             end_year=end_year,
                                             include_last_month=True,
                                             apply_cumulative_on_expenses=False,
                                             apply_cumulative_on_income=False,
                                             apply_cumulative_on_savings=True
                                             )
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )

    payload = res["payload"]
    return payload

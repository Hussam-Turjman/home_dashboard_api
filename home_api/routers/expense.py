import datetime

from fastapi import Depends, HTTPException, status, APIRouter, Body

from .user import validate_user
from ..managers.expense_manager import ExpenseManager
from ..pydantic_models.account import AccountEntryModel
from ..pydantic_models.session import UserSessionModel
from ..runtime import db_session
from typing import Annotated
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

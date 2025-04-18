from typing import Annotated, List, Dict

from fastapi import Depends, HTTPException, status, APIRouter, Request, UploadFile

from .user import validate_user
from ..logger import logger
from ..managers.transactions_manager import TransactionsManager
from ..pydantic_models.account import MonthExpensesTagModel
from ..pydantic_models.session import UserSessionModel
from ..pydantic_models.transaction import BankTransactionModel
from ..runtime import db_session

transactions_manager = TransactionsManager(
    db_session=db_session
)
URL_BASE = "/api/transactions"
router = APIRouter(
    prefix=URL_BASE,
    tags=["transactions"],
    dependencies=[Depends(validate_user)]
)


# add endpoint to upload transactions file
@router.post("/upload/{session_id}", response_model=dict)
async def upload_transactions_file(
        user: Annotated[UserSessionModel, Depends(validate_user)],
        file: UploadFile,

):
    max_size = 100 * 1024 * 1024  # 100 MB
    filetype = file.content_type
    # filesize in mb
    filesize = file.size
    logger.info(f"filesize={file.size} Bytes")
    if filesize == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is empty. Filesize={file.size} Bytes",
        )
    if filetype.lower() != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only CSV files are allowed.",
        )
    if filesize > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 100 MB.",
        )
    content = await file.read()
    try:
        transactions_manager.parse_file(
            filename=file.filename,
            content=content,
            filetype=filetype,
            filesize=file.size,
            user_id=user.user_id,
        )
    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing file: {e}",
        )
    logger.info(
        f"Filename: {file.filename}, filetype: {file.content_type}, filesize: {file.size}")
    return {"message": "File uploaded successfully", "filename": file.filename}


@router.get("/transactions/{session_id}", response_model=List[BankTransactionModel])
async def get_transactions(
        user: Annotated[UserSessionModel, Depends(validate_user)],
):
    all_bank_transactions = transactions_manager.get_bank_transactions(
        user_id=user.user_id)
    all_bank_transactions = [BankTransactionModel.model_validate(
        transaction).model_dump() for transaction in all_bank_transactions]
    return all_bank_transactions


@router.get("/overview_chart/{session_id}", response_model=dict)
async def get_overview_chart(user: Annotated[UserSessionModel, Depends(validate_user)],
                             start_month: int, start_year: int,
                             end_month: int, end_year: int, request: Request):
    if start_month == 0 and start_year == 0 and end_month == 0 and end_year == 0:
        start_month = None
        start_year = None
        end_month = None
        end_year = None
    res = transactions_manager.get_overview_chart(user_id=user.user_id,
                                                  start_month=start_month,
                                                  start_year=start_year,
                                                  end_month=end_month,
                                                  end_year=end_year,
                                                  include_last_month=True,
                                                  apply_cumulative_on_expenses=False,
                                                  apply_cumulative_on_income=False,
                                                  apply_cumulative_on_savings=False
                                                  )
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )

    payload = res["payload"]
    return payload


@router.get("/total_expenses_and_savings/{session_id}", response_model=List[MonthExpensesTagModel])
async def get_total_expenses_and_savings(user: Annotated[UserSessionModel, Depends(validate_user)]):
    res = transactions_manager.get_total_expenses_and_savings(
        user_id=user.user_id)

    return res


@router.get("/category_expenses_and_savings/{session_id}", response_model=List[MonthExpensesTagModel])
async def get_category_expenses_and_savings(user: Annotated[UserSessionModel, Depends(validate_user)]):
    res = transactions_manager.get_category_expenses_and_savings(
        user_id=user.user_id)

    return res


@router.get("/subcategory_expenses_and_savings/{session_id}", response_model=List[dict])
async def get_subcategory_expenses_and_savings(user: Annotated[UserSessionModel, Depends(validate_user)]):
    res = transactions_manager.get_subcategory_expenses_and_savings(
        user_id=user.user_id)

    return res

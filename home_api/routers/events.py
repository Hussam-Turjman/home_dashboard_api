import datetime

from fastapi import Depends, HTTPException, status, APIRouter, Body, Request

from .user import validate_user
from ..managers.expense_manager import ExpenseManager
from ..pydantic_models.account import AccountEntryModel
from ..pydantic_models.session import UserSessionModel
from ..runtime import db_session
from typing import Annotated
from sse_starlette.sse import EventSourceResponse
import json
import asyncio

MESSAGE_STREAM_RETRY_TIMEOUT = 15000  # millisecond
MESSAGE_STREAM_DELAY = 60  # second

URL_BASE = "/api/events"
router = APIRouter(
    prefix=URL_BASE,
    tags=["events"],
    dependencies=[Depends(validate_user)]
)


@router.get("/{session_id}", response_class=EventSourceResponse)
async def get_events(request: Request, user: Annotated[UserSessionModel, Depends(validate_user)]):
    async def event_generator():
        counter = 0
        while True:
            if await request.is_disconnected():
                break
            user_data = UserSessionModel.model_validate(user).model_dump()
            user_data = json.dumps(user_data)
            message = {
                "event": "new_message",
                "id": f"message_id_{counter}",
                "retry": MESSAGE_STREAM_RETRY_TIMEOUT,
                "data": user_data,
            }

            yield message
            await asyncio.sleep(delay=MESSAGE_STREAM_DELAY)
            counter += 1

    return EventSourceResponse(event_generator())

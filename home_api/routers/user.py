from typing import Annotated
from ..db.checks import is_valid_uuid
from fastapi import Depends, HTTPException, status, APIRouter, Request
from ..auth import OAuth2PasswordBearerWithCookie
from ..entrypoint import entry_point
from ..managers.user_manager import UserManager
from ..runtime import db_session
from ..pydantic_models.session import UserSessionModel, SessionPayloadModel
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

URL_BASE = "/api/user"
TOKEN_URL = f"{URL_BASE}/authenticate"
oauth2_scheme = OAuth2PasswordBearerWithCookie(
    token_url=TOKEN_URL)  # OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

user_manager = UserManager(db_session=db_session)
router = APIRouter()


async def validate_user(session_id: str, token: Annotated[str, Depends(oauth2_scheme)]):
    if not is_valid_uuid(session_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session_id",
        )

    res = user_manager.verify_token(token=token, session_id=session_id)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=res["message"],
        )
    else:
        payload = res["payload"]
        payload: UserSessionModel
    payload.token = "********"

    return payload


@router.post(TOKEN_URL, response_model=SessionPayloadModel)
async def authenticate_user(response: JSONResponse, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                            request: Request):
    ip = request.client.host

    agent = request.headers["user-agent"]
    location = "Unknown"
    username = form_data.username
    password = form_data.password
    res = user_manager.login(username=username,
                             password=password,
                             ip=ip,
                             location=location,
                             agent=agent)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password. " + res["message"],
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        session = res["payload"]
        session: SessionPayloadModel

        response.set_cookie(key="access_token",
                            value=f"Bearer {session.token}",
                            httponly=True,
                            max_age=entry_point.access_token_expiration.total_seconds() // 60)

        session.token = "********"
    return session


__all__ = ["router", "validate_user"]

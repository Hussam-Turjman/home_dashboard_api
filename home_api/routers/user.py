from typing import Annotated

from fastapi import Depends, HTTPException, status, APIRouter, Request
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import JSONResponse

from ..auth import OAuth2PasswordBearerWithCookie
from ..db.checks import is_valid_uuid
from ..debug import DEBUG_MODE
from ..entrypoint import entry_point
from ..managers.user_manager import UserManager
from ..pydantic_models.session import UserSessionModel, SessionPayloadModel
from ..runtime import db_session

URL_BASE = "/api/user"
TOKEN_URL = "/authenticate"
oauth2_scheme = OAuth2PasswordBearerWithCookie(
    token_url=URL_BASE + TOKEN_URL)  # OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

user_manager = UserManager(db_session=db_session)
router = APIRouter(
    prefix=URL_BASE,
)


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
    if not DEBUG_MODE:
        payload.token = "********"
        # payload.user_id = -1
        payload.ip = "********"
        payload.agent = "********"
        payload.location = "********"

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

        if not DEBUG_MODE:
            session.token = "********"
    return session


@router.get("/is_session_active/{session_id}", response_model=UserSessionModel)
async def is_session_active(user: Annotated[UserSessionModel, Depends(validate_user)]):
    # today = datetime.datetime.now().date()
    return user


@router.post("/logout/{session_id}")
async def logout_user(session_id: str, token: Annotated[str, Depends(oauth2_scheme)]):
    if not is_valid_uuid(session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session_id",
        )
    res = user_manager.logout(session_id=session_id, token=token)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        pass
    return JSONResponse(content={"message": "Logged out successfully"})


@router.get("/{session_id}", response_model=UserSessionModel)
async def get_user(user: Annotated[UserSessionModel, Depends(validate_user)]):
    user.networth = user_manager.get_networth(user_id=user.user_id)
    user.networth_development_percentage = user_manager.get_networth_development_percentage(
        user_id=user.user_id)
    if not DEBUG_MODE:
        user.user_id = -1
    return user


__all__ = ["router", "validate_user"]

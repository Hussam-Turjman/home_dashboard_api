from pydantic import BaseModel


class SessionPayloadModel(BaseModel):
    session_id: str
    token: str
    token_type: str
    message: str = ''


class UserSessionModel(BaseModel):
    session_id: str
    user_id: int
    token: str
    token_type: str
    message: str = ''
    email: str = ''
    username: str = ''
    first_name: str = ''
    last_name: str = ''
    ip: str
    location: str
    agent: str
    expires_at: str
    active: bool
    networth: float = 0.0


__all__ = ["SessionPayloadModel", "UserSessionModel"]

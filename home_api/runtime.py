from .db.session import Session
from .db.base import Base

db_session = Session.create(d_Base=Base).instance
DEBUG_MODE = True

__all__ = ["db_session", "DEBUG_MODE"]

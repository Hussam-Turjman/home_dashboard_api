from .db.session import Session
from .db.tables import Base

db_session = Session.create(d_Base=Base).instance

__all__ = ["db_session"]

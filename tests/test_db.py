import sys
import os

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.entrypoint import entry_point
from home_api.db.session import Session
from home_api.db.base import Base
# fmt: on

session = Session.create(d_Base=Base)


def test_entry_point():
    assert entry_point.check_all()


def test_session_connection():
    assert session.is_connected

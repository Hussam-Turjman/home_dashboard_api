from home_api.db.base import Base
from home_api.db.session import Session
from home_api.entrypoint import entry_point
import sys
import os
import pytest

cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append("/__w/home_dashboard_final/home_dashboard_final")


session = Session.create(d_Base=Base)


def test_entry_point():
    assert entry_point.check_all()


def test_session_connection():
    assert session.is_connected

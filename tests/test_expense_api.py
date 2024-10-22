import os
import sys
import datetime
import uuid

from fastapi.testclient import TestClient


# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.app import app
from home_api.managers.user_manager import UserManager
from home_api.managers.expense_manager import ExpenseManager
from home_api.runtime import db_session
from home_api.db.utils import generate_password
from home_api.pydantic_models.account import AccountEntryModel

# fmt: on

client = TestClient(app)
user_manager = UserManager(db_session=db_session)
expense_manager = ExpenseManager(db_session=db_session)


def create_user():
    user = user_manager.create_verified_dummy_user()
    return user


def delete_user():
    user_manager.delete_user_by_email("John.Doe@gmail.com")


def create_account_entry():
    now = datetime.datetime.now()
    end = now + datetime.timedelta(days=30)
    entry = AccountEntryModel(
        start_date=now.strftime("%m/%Y"),
        end_date=end.strftime("%m/%Y"),
        amount=100.00,
        name="Test Entry",
        tag="Test Tag",
        id=str(uuid.uuid4())
    )
    return entry


def login_user():
    url = "/api/user/authenticate"
    user = create_user()
    password = generate_password(fixed=True)
    # authenticate the user
    response = client.post(
        url, data={"username": user.username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    session_id = payload["session_id"]
    access_token = payload["token"]
    auth_headers = {"cookie": f"access_token=\"Bearer {access_token}\""}
    return auth_headers, session_id, user


def test_add_account_entry_failure():
    # auth_headers, session_id, user = login_user()
    user = create_user()
    url = "/api/expenses/add_account_entry/0"
    now = datetime.datetime.now()
    end = now + datetime.timedelta(days=30)
    entry = AccountEntryModel(
        start_date=now.strftime("%m/%Y"),
        end_date=end.strftime("%m/%Y"),
        amount=100.00,
        name="Test Entry",
        tag="Test Tag",
        id=uuid.uuid4()
    )
    response = client.put(url,
                          json=entry.model_dump_json())
    assert response.status_code == 401

    delete_user()


def test_add_account_entry_success():
    auth_headers, session_id, user = login_user()

    url = f"/api/expenses/add_account_entry/{session_id}"
    entry = create_account_entry()
    dumped = entry.model_dump()

    # dumped["start_date"] = datetime.datetime.strptime(dumped["start_date"], "%m/%Y").date()
    # dumped["end_date"] = datetime.datetime.strptime(dumped["end_date"], "%m/%Y").date()
    response = client.put(url,
                          json=dumped,
                          headers=auth_headers)
    payload = response.json()
    assert response.status_code == 200

    assert "id" in payload.keys()
    assert "start_date" in payload.keys()
    assert "end_date" in payload.keys()
    assert "amount" in payload.keys()
    assert "name" in payload.keys()
    assert "tag" in payload.keys()
    assert "months_count" in payload.keys()
    assert "total_amount" in payload.keys()
    # res = expense_manager.delete_account_entry(
    #     user_id=user.id, entry_id=entry.id
    # )
    # assert not res["error"]
    delete_user()


def test_delete_account_entry():
    auth_headers, session_id, user = login_user()
    entry = create_account_entry()
    res = expense_manager.add_account_entry(
        user_id=user.id,
        entry_id=entry.id,
        start_date=datetime.datetime.strptime(
            entry.start_date, "%m/%Y").date(),
        end_date=datetime.datetime.strptime(entry.end_date, "%m/%Y").date(),
        amount=entry.amount,
        name=entry.name,
        tag=entry.tag
    )
    assert not res["error"]
    url = f"/api/expenses/delete_account_entry/{session_id}/{entry.id}"
    response = client.delete(url, headers=auth_headers)
    assert response.status_code == 200
    delete_user()

# def run():
#     test_add_account_entry_success()
#     test_add_account_entry_failure()
#     test_delete_account_entry()
#     pass
#
# if __name__ == "__main__":
#     run()

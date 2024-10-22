import sys
import os
import datetime

from debugpy.adapter import access_token
from fastapi.testclient import TestClient

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.app import app
from home_api.managers.user_manager import UserManager
from home_api.runtime import db_session
from home_api.db.utils import generate_password

# fmt: on
client = TestClient(app)
user_manager = UserManager(db_session=db_session)


def create_user():
    # create a user
    first_name = "John"
    last_name = "Doe"
    email = f"{first_name}.{last_name}@gmail.com"
    password = generate_password(fixed=True)
    user_manager.delete_user_by_email(email)
    user = user_manager.create_user(first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password)
    user_manager._verify_user(email=user.email, username=user.username)
    return user


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_authenticate_user():
    url = "/api/user/authenticate"
    user = create_user()
    password = generate_password(fixed=True)
    # authenticate the user
    response = client.post(
        url, data={"username": user.username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    assert "token" in payload.keys()
    assert "session_id" in payload.keys()
    assert "token_type" in payload.keys()
    user_manager.delete_user_by_email(user.email)


def test_is_session_active():
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

    url = f"/api/user/is_session_active/{session_id}"
    response = client.get(url,
                          headers=auth_headers,
                          )
    payload = response.json()
    assert response.status_code == 200, payload

    user_manager.delete_user_by_email(user.email)

# def run():
#     user_manager.delete_user_by_username(username="jodo2")
#     test_is_session_active()
#     # test_authenticate_user()
#     pass
# if __name__ == "__main__":
#      run()

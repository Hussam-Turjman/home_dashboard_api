import sys
import os
import datetime
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


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_authenticate_user():
    url = "/api/user/authenticate"
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
    # set client ip address

    # authenticate the user
    response = client.post(
        url, data={"username": user.username, "password": password})
    assert response.status_code == 200
    payload = response.json()
    assert "token" in payload.keys()
    assert "session_id" in payload.keys()
    assert "token_type" in payload.keys()
    user_manager.delete_user_by_email(email)

# def run():
#     test_authenticate_user()
#
# if __name__ == "__main__":
#     run()

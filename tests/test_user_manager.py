import sys
import os
import datetime

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.entrypoint import entry_point
from home_api.db.utils import generate_password
from home_api.db.session import Session
from home_api.db.base import Base
from home_api.managers.user_manager import UserManager
from home_api.managers.errors import ManagerErrors

# fmt: on

session = Session.create(d_Base=Base)


def create_user(first_name, last_name, email, password):
    user_manager = UserManager(db_session=session.instance)
    user = user_manager.create_user(first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password)
    return user


def test_create_user():
    first_name = "John"
    last_name = "Doe"
    email = f"{first_name}.{last_name}@gmail.com"
    password = generate_password(fixed=True)
    user_manager = UserManager(db_session=session.instance)
    user = create_user(first_name=first_name,
                       last_name=last_name, email=email, password=password)
    assert user.first_name == first_name
    assert user.last_name == last_name
    assert user.email == email
    assert not user.verified
    assert entry_point.pwd_context.verify(password, user.password)

    user_manager.delete_user_by_email(email)
    error = user_manager.delete_user_by_email(email)
    assert error == ManagerErrors.USER_NOT_FOUND
    error = user_manager.delete_user_by_username(user.username)
    assert error == ManagerErrors.USER_NOT_FOUND


def test_login_internal():
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_manager = UserManager(db_session=session.instance)
    password = generate_password(fixed=True)
    query_user = user_manager._login_email(user.email, password)
    assert query_user == ManagerErrors.NOT_VERIFIED
    # verify user
    user = user_manager._verify_user(user.email, user.username)
    query_user = user_manager._login_username(user.username, password)
    assert query_user == user
    session.instance.delete(user)
    session.instance.commit()


def test_delete_user():
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_manager = UserManager(db_session=session.instance)
    error = user_manager.delete_user_by_email(user.email)
    assert user == error
    error = user_manager.delete_user_by_username(user.username)
    assert error == ManagerErrors.USER_NOT_FOUND


def test_verify_user():
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_manager = UserManager(db_session=session.instance)
    user = user_manager._verify_user(user.email, user.username)
    assert user.verified
    session.instance.delete(user)
    session.instance.commit()


def test_invalid_internal_login():
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_manager = UserManager(db_session=session.instance)
    # verify user
    user = user_manager._verify_user(user.email, user.username)
    assert user.verified
    query_user = user_manager._login_email(user.email, "invalid_password")
    assert query_user == ManagerErrors.INVALID_PASSWORD
    query_user = user_manager._login_username(
        user.username, "invalid_password")
    assert query_user == ManagerErrors.INVALID_PASSWORD
    session.instance.delete(user)
    session.instance.commit()


def test_login():
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_manager = UserManager(db_session=session.instance)
    # verify user
    user = user_manager._verify_user(user.email, user.username)
    assert user.verified
    payload = user_manager.login(
        password=generate_password(fixed=True),
        ip="127.0.0.1",
        location="Lagos",
        agent="Mozilla",
        username=user.username,
        email=None,
    )
    assert not payload["error"]
    token_payload = payload["payload"]
    token = token_payload.token
    session_id = token_payload.session_id
    assert token
    assert session_id
    verification_payload = user_manager.verify_token(
        token=token, session_id=session_id)
    assert not verification_payload["error"]
    user_query = user_manager.delete_user_by_email(user.email)
    assert user_query == user

# if __name__ == "__main__":
#     manager = UserManager(db_session=session.instance)
#     o = manager.delete_user_by_username(username="jodo2")
#     print(o)
#     test_login()

import sys
import os

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.entrypoint import entry_point
from home_api.db.session import Session
from home_api.db.base import Base
from home_api.db.user import User
from home_api.db.utils import generate_password, create_username

# fmt: on

session = Session.create(d_Base=Base)


def test_entry_point():
    assert entry_point.check_all()


def test_session_connection():
    assert session.is_connected


def test_create_user():
    instance = session.instance
    password = generate_password()
    first_name = "John"
    last_name = "Doe"
    email = f"{first_name}.{last_name}@gmail.com"
    hash_func = entry_point.pwd_context.hash

    user = User.create(session=instance,
                       first_name=first_name,
                       last_name=last_name,
                       email=email,
                       password=password,
                       hash_func=hash_func
                       )

    instance.add(user)
    instance.commit()
    # Query the user and compare it with the created user
    user_query = (instance.query(User).filter(User.first_name == first_name).filter(
        User.last_name == last_name).filter(User.email == email
                                            ).first())

    assert user_query.first_name == first_name
    assert user_query.last_name == last_name
    assert user_query.email == email
    assert entry_point.pwd_context.verify(password, user_query.password)
    assert not user_query.verified

    # Delete the user
    instance.delete(user_query)
    instance.commit()


# if __name__ == "__main__":
#     test_create_user()

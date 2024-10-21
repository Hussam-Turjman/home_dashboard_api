from home_api.db.base import Base
from home_api.db.dummy import Dummy
from home_api.db.session import Session
from home_api.db.user import User
from home_api.db.utils import create_username, generate_password
from home_api.db.checks import is_valid_ip_address
from home_api.managers.errors import translate_manager_error
from home_api.managers.user_manager import UserManager


def run():
    session_creator = Session.create(d_Base=Base)
    user_manager = UserManager(db_session=session_creator.instance)
    # out = user_manager.login(
    #     password=generate_password(fixed=True),
    #     ip="127.0.0.1",
    #     location="Lagos",
    #     agent="Mozilla",
    #     username="jodo2",
    #     email="John.Doe@gmail.com",
    # )
    # print(out)
    out = user_manager.delete_user_by_email(email="John.Doe@gmail.com")
    # print(out)


if __name__ == "__main__":
    run()

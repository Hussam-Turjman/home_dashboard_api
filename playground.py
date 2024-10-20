from home_api.db.base import Base
from home_api.db.dummy import Dummy
from home_api.db.session import Session
from home_api.db.user import User
from home_api.db.utils import create_username, generate_password


def run():
    session_creator = Session.create(d_Base=Base)
    session = session_creator.instance
    # session.add(Dummy(name="dummy", value=401.0))
    # query all the data from the table
    query = session.query(User)
    for user in query:
        print(user)


if __name__ == "__main__":
    run()

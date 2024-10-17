from home_api.db.base import Base
from home_api.db.dummy import Dummy
from home_api.db.session import Session


def run():
    session_creator = Session.create(d_Base=Base).init()
    session = session_creator.instance
    # session.add(Dummy(name="dummy", value=401.0))
    # query all the data from the table
    query = session.query(Dummy)
    for instance in query:
        print(instance.name, instance.value)


if __name__ == "__main__":
    run()

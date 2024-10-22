from home_api.db.tables import Base, EnergyCounter, EnergyCounterReading
from home_api.db.session import Session
from home_api.managers.expense_manager import ExpenseManager
from home_api.managers.user_manager import UserManager


def run():
    session_creator = Session.create(d_Base=Base)  # .drop_all().create_all()
    user_manager = UserManager(db_session=session_creator.instance)
    expense_manager = ExpenseManager(db_session=session_creator.instance)

    user = user_manager.create_verified_dummy_user()
    for i in range(100):
        counter = EnergyCounter.create_empty(user.id)
        session_creator.instance.add(counter)
    session_creator.instance.commit()
    user_manager.delete_user_by_username(user.username)


if __name__ == "__main__":
    run()

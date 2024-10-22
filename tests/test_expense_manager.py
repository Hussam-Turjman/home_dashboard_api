import datetime
import os
import sys
import uuid

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.db.utils import generate_password
from home_api.db.session import Session
from home_api.db.tables import Base
from home_api.managers.user_manager import UserManager
from home_api.managers.expense_manager import ExpenseManager
# fmt: on

session = Session.create(d_Base=Base)
user_manager = UserManager(db_session=session.instance)
expense_manager = ExpenseManager(db_session=session.instance)


def create_user(first_name, last_name, email, password):
    user = user_manager.create_user(first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    password=password)
    return user


def create_account_entry():
    first_name = "John"
    last_name = "Doe"
    email = f"{first_name}.{last_name}@gmail.com"
    password = generate_password(fixed=True)
    user = create_user(first_name=first_name,
                       last_name=last_name, email=email, password=password)
    user_manager._verify_user(email=user.email, username=user.username)
    user_id = user.id
    entry_id = str(uuid.uuid4())
    start_date = datetime.date.today()
    end_date = datetime.date.today() + datetime.timedelta(days=30)
    amount = 100.00
    name = "Test Entry"
    tag = "Test Tag"
    account_entry = expense_manager._add_account_entry(user_id=user_id,
                                                       entry_id=entry_id,
                                                       start_date=start_date,
                                                       end_date=end_date,
                                                       amount=amount,
                                                       name=name,
                                                       tag=tag)
    return user, account_entry


def test_add_and_delete_account_entry():
    user, account_entry = create_account_entry()
    ret = expense_manager.delete_account_entry(
        user_id=user.id, entry_id=account_entry.id)
    assert not ret["error"]
    user_manager.delete_user_by_email(user.email)

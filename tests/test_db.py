import sys
import os

# fmt: off
cwd = os.path.join(os.path.dirname(__file__))
parent_dir = os.path.join(cwd, "..")
sys.path.append(parent_dir)
from home_api.entrypoint import entry_point
from home_api.db.session import Session
from home_api.db.tables import Base, User, UserSession, EnergyCounter, EnergyCounterReading, AccountEntry

from home_api.db.utils import generate_password

# fmt: on

session = Session.create(d_Base=Base)


def test_entry_point():
    assert entry_point.check_all()


def test_session_connection():
    assert session.is_connected


def create_user(first_name, last_name, email, password):
    user = User.create(session=session.instance,
                       first_name=first_name,
                       last_name=last_name,
                       email=email,
                       password=password,
                       hash_func=entry_point.pwd_context.hash
                       )
    # Add the user to the session
    session.instance.add(user)
    # Commit the changes
    session.instance.commit()
    return user


def test_create_user(delete_user=True):
    instance = session.instance
    password = generate_password(fixed=True)
    first_name = "John"
    last_name = "Doe"
    email = f"{first_name}.{last_name}@gmail.com"

    user = create_user(first_name=first_name,
                       last_name=last_name, email=email, password=password)

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
    if delete_user:
        instance.delete(user_query)
        instance.commit()


def test_create_user_session():
    instance = session.instance
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    user_session = UserSession.create_empty(user_id=user.id)
    instance.add(user_session)
    instance.commit()
    # Query the user session and compare it with the created user session
    user_session_query = instance.query(UserSession).filter(
        UserSession.id == user_session.id).first()
    assert user_session_query.user_id == user.id
    assert user_session_query.active
    assert user_session_query.token == user_session.token
    assert user_session_query.expires_at == user_session.expires_at
    assert user_session_query.created_at == user_session.created_at
    assert user_session_query.ip == user_session.ip
    assert user_session_query.location == user_session.location
    assert user_session_query.agent == user_session.agent

    # Delete the user session
    instance.delete(user_session_query)

    # Delete the user
    instance.delete(user)

    # Commit the changes
    instance.commit()


def test_create_energy_counter():
    instance = session.instance
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    energy_counter = EnergyCounter.create_empty(user_id=user.id)
    instance.add(energy_counter)
    instance.commit()
    # Query the energy counter and compare it with the created energy counter
    energy_counter_query = instance.query(EnergyCounter).filter(
        EnergyCounter.id == energy_counter.id).first()
    assert energy_counter_query.user_id == user.id
    assert energy_counter_query.counter_id == energy_counter.counter_id
    assert energy_counter_query.counter_type == energy_counter.counter_type
    assert energy_counter_query.energy_unit == energy_counter.energy_unit
    assert energy_counter_query.frequency == energy_counter.frequency
    assert energy_counter_query.base_price == energy_counter.base_price
    assert energy_counter_query.price == energy_counter.price
    assert energy_counter_query.start_date == energy_counter.start_date
    assert energy_counter_query.first_reading == energy_counter.first_reading

    # Delete the energy counter
    instance.delete(energy_counter_query)

    # Delete the user
    instance.delete(user)

    # Commit the changes
    instance.commit()


def test_create_energy_counter_reading():
    instance = session.instance
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    energy_counter = EnergyCounter.create_empty(user_id=user.id)
    instance.add(energy_counter)
    instance.commit()
    reading = EnergyCounterReading.create_empty(counter_id=energy_counter.id)
    instance.add(reading)
    instance.commit()
    query = instance.query(EnergyCounterReading).filter(
        EnergyCounterReading.id == reading.id).first()

    assert query.reading == reading.reading
    assert query.reading_date == reading.reading_date
    assert query.counter_id == reading.counter_id

    # Deletion
    instance.delete(reading)
    instance.delete(energy_counter)
    instance.delete(user)

    instance.commit()


def test_create_account_entry():
    instance = session.instance
    user = create_user(first_name="John", last_name="Doe", email="John.Doe@gmail.com",
                       password=generate_password(fixed=True))

    entry = AccountEntry.create_empty(user_id=user.id)
    instance.add(entry)
    instance.commit()
    query = instance.query(AccountEntry).filter(
        AccountEntry.id == entry.id).first()
    assert query.start_date == entry.start_date
    assert query.end_date == entry.end_date
    assert query.amount == entry.amount
    assert query.name == entry.name
    assert query.tag == entry.tag
    assert query.months_count == entry.months_count
    assert query.total_amount == entry.total_amount

    # Deletion
    instance.delete(entry)
    instance.delete(user)
    instance.commit()

# if __name__ == "__main__":
#     test_create_user_session()

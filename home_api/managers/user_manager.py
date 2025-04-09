from passlib.context import CryptContext

from ..db.tables import User, UserSession, AccountEntry

from sqlalchemy.orm.session import Session as SQLSession
from ..entrypoint import entry_point
from .errors import ManagerErrors, translate_manager_error
from ..db.checks import is_valid_ip_address
import datetime
from ..pydantic_models.session import SessionPayloadModel, UserSessionModel
import jwt
from ..db.utils import generate_password
from ..db.utils import diff_month, create_dates_labels
from dateutil.relativedelta import relativedelta


class UserManager(object):
    db_session: SQLSession
    pwd_context: CryptContext

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session
        self.pwd_context = entry_point.pwd_context

    def _verify_user(self, email: str, username: str):
        user = self.db_session.query(User).filter_by(
            email=email).filter_by(username=username).first()
        if not user:
            return ManagerErrors.USER_NOT_FOUND
        user.verified = True
        self.db_session.commit()
        return user

    def _check_user_login(self, user: User | None, password: str):
        if not user:
            return ManagerErrors.USER_NOT_FOUND
        if not user.verified:
            return ManagerErrors.NOT_VERIFIED
        if not self.pwd_context.verify(password, user.password):
            return ManagerErrors.INVALID_PASSWORD
        return user

    def _login_email(self, email: str, password: str):
        user = self.db_session.query(User).filter_by(email=email).first()
        return self._check_user_login(user, password)

    def _login_username(self, username: str, password: str):
        user = self.db_session.query(User).filter_by(username=username).first()
        return self._check_user_login(user, password)

    def _create_user_session(self, password, ip,
                             location, agent, token,
                             expires_at: datetime.datetime, created_at: datetime.datetime,
                             email=None, username=None,
                             force_new_session=False, return_existing_session=False):
        if email is None and username is None:
            return ManagerErrors.VALUE_ERROR
        if created_at >= expires_at:
            return ManagerErrors.VALUE_ERROR
        if expires_at < datetime.datetime.now():
            return ManagerErrors.EXPIRED
        if not is_valid_ip_address(ip):
            return ManagerErrors.INVALID_IP_ADDRESS

        if email is not None:
            user_or_error = self._login_email(email, password)
        else:
            user_or_error = self._login_username(username, password)

        if isinstance(user_or_error, ManagerErrors):
            return user_or_error
        user = user_or_error
        if not force_new_session:
            existing_sessions = (self.db_session.query(User, UserSession).
                                 filter(User.id == UserSession.user_id).
                                 filter(User.id == user.id).
                                 filter(UserSession.expires_at > created_at).
                                 filter(UserSession.ip == ip).
                                 filter(UserSession.location == location).
                                 filter(UserSession.agent == agent).
                                 filter(UserSession.active).
                                 all())
            if len(existing_sessions) > 0:
                if return_existing_session:
                    if len(existing_sessions) > 1:
                        return ManagerErrors.MULTIPLE_ENTRIES_FOUND
                    return existing_sessions[0][1]
                return ManagerErrors.USER_ALREADY_LOGGED_IN

        user_session = UserSession(user_id=user.id, token=token,
                                   expires_at=expires_at,
                                   created_at=created_at, ip=ip,
                                   location=location, agent=agent)
        self.db_session.add(user_session)
        self.db_session.commit()
        return user_session

    def _get_session(self, token, session_id, username=None, email=None) -> UserSession | ManagerErrors:
        if username is None and email is None:
            raise RuntimeError("Either username or email must be provided")
        session = (self.db_session.query(UserSession, User).
                   join(User, User.id == UserSession.user_id).
                   filter(User.email == email if email is not None else User.username == username).
                   filter(UserSession.id == session_id).
                   filter(UserSession.token == token).
                   first())
        if session:
            session = session[0]
            if not session.active:
                return ManagerErrors.EXPIRED
            else:
                now = datetime.datetime.now()
                if session.expires_at < now:
                    session.active = False
                    self.db_session.commit()
                    return ManagerErrors.EXPIRED
        return session

    def _set_expired_sessions_inactive(self, invalidate_all=False) -> ManagerErrors:
        if invalidate_all:
            self.db_session.query(UserSession).update(
                {UserSession.active: False})
            self.db_session.commit()
            return ManagerErrors.SUCCESS
        now = datetime.datetime.now()
        self.db_session.query(UserSession).filter(UserSession.expires_at < now).update(
            {UserSession.active: False})
        self.db_session.commit()
        return ManagerErrors.SUCCESS

    def _delete_user(self, user):
        self.db_session.delete(user)
        self.db_session.commit()
        return ManagerErrors.SUCCESS

    def _logout(self, session_id, token) -> ManagerErrors:
        now = datetime.datetime.now()
        user_session = (self.db_session.query(UserSession)
                        .filter(UserSession.id == session_id)
                        .filter(UserSession.active)
                        .filter(UserSession.expires_at > now)
                        .filter(UserSession.token == token)
                        .first())
        if user_session:
            user_session.active = False
            self.db_session.commit()
            return ManagerErrors.SUCCESS
        return ManagerErrors.SESSION_NOT_FOUND

    def _get_user_from_session(self, session):
        return self.db_session.query(User).filter_by(id=session.user_id).first()

    def create_user(self, first_name: str, last_name: str, email: str, password: str) -> User:
        user = User.create(session=self.db_session,
                           first_name=first_name,
                           last_name=last_name,
                           email=email,
                           password=password,
                           hash_func=self.pwd_context.hash)
        self.db_session.add(user)
        self.db_session.commit()
        return user

    def delete_user_by_email(self, email: str):
        user = self.db_session.query(User).filter_by(email=email).first()
        if user:
            self._delete_user(user)
        else:
            return ManagerErrors.USER_NOT_FOUND
        return user

    def delete_user_by_username(self, username: str):
        user = self.db_session.query(User).filter_by(username=username).first()
        if user:
            # delete all sessions
            self._delete_user(user)
        else:
            return ManagerErrors.USER_NOT_FOUND
        return user

    def login(self, password, ip, location, agent, email=None, username=None) -> dict:
        login_input = "None"
        input_type = "None"
        if email:
            login_input = email
            input_type = "email"
        elif username:
            login_input = username
            input_type = "username"

        created_at = datetime.datetime.now()
        expires_at = created_at + entry_point.access_token_expiration
        payload = {
            "sub": login_input,
            "exp": expires_at,
            "type": input_type,

        }
        access_token = jwt.encode(
            payload, entry_point.secret_key, algorithm=entry_point.jwt_algorithm)

        session_or_error = self._create_user_session(
            password=password,
            ip=ip,
            location=location,
            agent=agent,
            token=access_token,
            expires_at=expires_at,
            created_at=created_at,
            email=email,
            username=username,
            force_new_session=False,
            return_existing_session=True
        )

        if isinstance(session_or_error, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(session_or_error),
                "exception": ValueError(translate_manager_error(session_or_error)),
            }
        return {
            "payload": SessionPayloadModel(
                token=session_or_error.token,
                token_type="bearer",
                session_id=str(session_or_error.id),
            ),
            "error": False}

    def logout(self, session_id, token) -> dict:
        res = self.verify_token(token=token, session_id=session_id)
        if res["error"]:
            return res
        res = self._logout(session_id=session_id, token=token)
        return {
            "error": True if res is not ManagerErrors.SUCCESS else False,
            "message": translate_manager_error(res),
            "exception": ValueError(translate_manager_error(res)),
        }

    def verify_token(self, token, session_id) -> dict:
        try:
            payload = jwt.decode(token, entry_point.secret_key, algorithms=[
                entry_point.jwt_algorithm])
            input_type = payload["type"]
            sub = payload["sub"]
            if input_type == "email":
                session = self._get_session(
                    token=token, email=sub, session_id=session_id)
            elif input_type == "username":
                session = self._get_session(
                    token=token, username=sub, session_id=session_id)
            else:
                return {
                    "error": True,
                    "message": "Session not found",
                    "exception": ValueError("Invalid token"),
                }
            if isinstance(session, ManagerErrors):
                return {
                    "error": True,
                    "message": translate_manager_error(session),
                    "exception": ValueError(translate_manager_error(session)),
                }
            else:
                user = self._get_user_from_session(session)
                return {
                    "error": False,
                    "payload": UserSessionModel(
                        user_id=session.user_id,
                        session_id=str(session.id),
                        token=session.token,
                        token_type="bearer",
                        expires_at=str(session.expires_at),
                        ip=session.ip,
                        location=session.location,
                        agent=session.agent,
                        active=session.active,
                        first_name=user.first_name,
                        email=user.email,
                        username=user.username,
                        last_name=user.last_name,
                    ),

                }
        except jwt.ExpiredSignatureError as e:
            self._set_expired_sessions_inactive(invalidate_all=False)
            return {
                "error": True,
                "message": "Token has expired",
                "exception": e,
            }
        except jwt.InvalidTokenError as e:
            return {
                "error": True,
                "message": "Invalid token. Failed to decode token.",
                "exception": e,
            }

    def create_verified_dummy_user(self, first_name="John", last_name="Doe", password=generate_password(fixed=True)):
        email = f"{first_name}.{last_name}@gmail.com"
        # check if user exists
        user = self.db_session.query(User).filter_by(email=email).first()
        if user:
            return user
        user = self.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )
        user = self._verify_user(email=user.email, username=user.username)
        return user

    def try_delete_dummy_user(self):
        user = self.db_session.query(User).filter_by(
            email="John.Doe@gmail.com").first()
        if user:
            self._delete_user(user)
            return True
        return False

    def create_dummy_user_session(self, user_id):
        now = datetime.datetime.now()
        end = now + datetime.timedelta(days=30)
        session = UserSession(user_id=user_id, token="dummy",
                              expires_at=end,
                              created_at=now, ip="testclient",
                              location="testlocation", agent="testagent")
        self.db_session.add(session)
        self.db_session.commit()
        return session

    def get_networth(self, user_id: int, date: datetime.date = None):
        if date is None:
            today = datetime.datetime.now().date().replace(day=1)
        else:
            today = date.replace(day=1)
        # Get income
        income = (self.db_session.query(AccountEntry).
                  filter(AccountEntry.user_id == user_id).
                  filter(AccountEntry.start_date <= today).
                  filter(AccountEntry.amount > 0).
                  order_by(AccountEntry.start_date).
                  all())

        income = self.sum_amount_until_date(income, today)

        # Get expenses ordered by start date
        expenses = (self.db_session.query(AccountEntry).
                    filter(AccountEntry.user_id == user_id).
                    filter(AccountEntry.start_date <= today).
                    filter(AccountEntry.amount < 0).
                    order_by(AccountEntry.start_date).
                    all())
        expenses = self.sum_amount_until_date(expenses, today)

        for key in expenses.keys():
            if key not in income.keys():
                income[key] = 0
        for key in income.keys():
            if key not in expenses.keys():
                expenses[key] = 0
        monthly_savings = {}
        for key in income.keys():
            monthly_savings[key] = round(income[key] + expenses[key], 2)

        total_networth = sum([value for value in monthly_savings.values()])
        total_networth = round(total_networth, 2)
        return total_networth

    def sum_amount_until_date(self, account_entries, end_date):
        res = {}
        if len(account_entries) > 0:
            start_date = account_entries[0].start_date

            total_months = diff_month(end_date, start_date) + 1
            for month in range(total_months):
                month_amount = 0
                current_month = start_date + relativedelta(months=month)
                for entry in account_entries:

                    if entry.start_date <= current_month <= entry.end_date:
                        month_amount += entry.amount
                # key is month and year only
                key = current_month.strftime("%m-%Y")
                res[key] = month_amount
        return res

    def first_account_entry_date(self, user_id):
        first_entry = (self.db_session.query(AccountEntry).
                       filter(AccountEntry.user_id == user_id).
                       order_by(AccountEntry.start_date).
                       first())
        if first_entry:
            return datetime.date(first_entry.start_date.year, first_entry.start_date.month, first_entry.start_date.day)
        return None

    def get_networth_development_percentage(self, user_id):
        today = datetime.datetime.now().date().replace(day=1)
        # today = datetime.date(2024, 10, 1)
        previous_month = today - relativedelta(months=1)
        # print(f"previous month: {previous_month}")
        # print(f"today: {today}")
        first_date = self.first_account_entry_date(user_id=user_id)
        average_networth = 0.0
        if first_date is None:
            return 0.0
        dates = create_dates_labels(
            start_date=first_date,
            end_date=previous_month,
            include_last_month=True,
            to_dates=True
        )
        for date in dates:
            month_networth = self.get_networth(
                user_id=user_id,
                date=date
            )
            # print(date,month_networth)
            average_networth += month_networth

        average_networth = average_networth / len(dates)
        # print(f"average networth: {average_networth}")
        current_networth = self.get_networth(
            user_id=user_id,
            date=today
        )
        # print(f"current networth: {current_networth}")
        # calculate percentage change
        if average_networth == 0:
            return 0.0
        percentage_change = (
            (current_networth - average_networth) / average_networth) * 100
        return round(percentage_change, 2)


__all__ = ["UserManager"]

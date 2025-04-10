from dateutil.relativedelta import relativedelta
from sqlalchemy.orm.session import Session as SQLSession

from .errors import ManagerErrors, translate_manager_error
from ..db.tables import EnergyCounter, EnergyCounterReading, User
import datetime
from ..db.utils import diff_day, create_dates_labels, to_month_year_str, diff_month
from sqlalchemy import func
from calendar import monthrange
import numpy as np
from ..logger import logger
from .return_wrapper import return_wrapper


class EnergyManager(object):
    db_session: SQLSession

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session

    def _add_energy_counter(self, user_id, counter_id_db, counter_id, counter_type, energy_unit,
                            frequency, base_price, price, start_date, end_date, first_reading):
        if frequency not in ["daily", "monthly", "yearly"]:
            return ManagerErrors.ENERGY_COUNTER_INVALID_FREQUENCY

        user = (self.db_session.query(User).filter(User.id == user_id)).first()
        if not user:
            return ManagerErrors.USER_NOT_FOUND
        # maybe_duplicate = (self.db_session.query(EnergyCounter).
        #                    filter(EnergyCounter.counter_id == counter_id).
        #                    filter(EnergyCounter.user_id == user_id).
        #                    filter(EnergyCounter.counter_type == counter_type)).first()
        # if maybe_duplicate:
        #     return ManagerErrors.DUPLICATE_ENERGY_COUNTER

        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.id == counter_id_db)).first()
        if counter:
            counter.counter_id = counter_id
            counter.counter_type = counter_type
            counter.energy_unit = energy_unit
            counter.frequency = frequency
            counter.base_price = base_price
            counter.price = price
            counter.start_date = start_date
            counter.end_date = end_date
            counter.first_reading = first_reading
        else:
            counter = EnergyCounter(user_id=user_id,
                                    counter_id=counter_id,
                                    counter_type=counter_type,
                                    energy_unit=energy_unit,
                                    frequency=frequency,
                                    base_price=base_price,
                                    price=price,
                                    start_date=start_date,
                                    end_date=end_date,
                                    first_reading=first_reading)
            self.db_session.add(counter)
        self.db_session.commit()
        return counter.convert_to_dict()

    @return_wrapper()
    def add_energy_counter(self, user_id, counter_id_db, counter_id, counter_type, energy_unit,
                           frequency, base_price, price, start_date, end_date, first_reading):
        res = self._add_energy_counter(user_id=user_id,
                                       counter_id=counter_id,
                                       counter_id_db=counter_id_db,
                                       counter_type=counter_type,
                                       energy_unit=energy_unit,
                                       frequency=frequency,
                                       base_price=base_price,
                                       price=price,
                                       start_date=start_date,
                                       end_date=end_date,
                                       first_reading=first_reading)
        return res

    def _delete_energy_counter(self, user_id, counter_id_db):
        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.id == counter_id_db)).first()
        if not counter:
            return ManagerErrors.ENTRY_NOT_FOUND
        self.db_session.delete(counter)
        self.db_session.commit()
        return counter.convert_to_dict()

    @return_wrapper()
    def delete_energy_counter(self, user_id, counter_id_db):
        res = self._delete_energy_counter(user_id=user_id,
                                          counter_id_db=counter_id_db)
        return res

    def get_energy_counters(self, user_id):
        counters = (self.db_session.query(EnergyCounter).
                    filter(EnergyCounter.user_id == user_id).
                    all())
        return counters

    def get_energy_counter_readings(self, user_id):
        readings = (self.db_session.query(EnergyCounterReading, EnergyCounter.counter_id, EnergyCounter.counter_type)
                    .join(EnergyCounter).filter(
            EnergyCounter.user_id == user_id).all())
        # Sort by date
        readings = sorted(readings, key=lambda x: x[0].reading_date)
        tmp = []
        for reading in readings:
            counter_id = reading[1]
            counter_type = reading[2]
            r = reading[0]
            tmp.append(r.convert_to_dict(
                counter_id=counter_id,
                counter_type=counter_type
            ))
        readings = tmp
        return readings

    @return_wrapper()
    def add_energy_counter_reading(self, user_id, entry_id: str, counter_id, counter_type,
                                   reading, reading_date):
        res = self._add_energy_counter_reading(user_id=user_id,
                                               entry_id=entry_id,
                                               counter_id=counter_id,
                                               counter_type=counter_type,
                                               reading=reading,
                                               reading_date=reading_date)
        return res

    def _add_energy_counter_reading(self, user_id: int, entry_id: str, counter_id: str,
                                    counter_type: str, reading: float,
                                    reading_date: datetime.date):
        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.counter_id == counter_id).
                   filter(EnergyCounter.counter_type == counter_type)).all()
        if not counter:
            return ManagerErrors.ENERGY_COUNTER_NOT_FOUND
        if len(counter) > 1:
            return ManagerErrors.MULTIPLE_ENTRIES_FOUND
        counter = counter[0]
        if reading_date > counter.end_date:
            return ManagerErrors.ENERGY_COUNTER_INVALID_READING_DATE
        if reading_date < counter.start_date:
            return ManagerErrors.ENERGY_COUNTER_INVALID_READING_DATE
        previous_reading_object = (self.db_session.query(EnergyCounterReading).
                                   filter(
            EnergyCounterReading.counter_id == counter.id)
            .order_by(EnergyCounterReading.reading_date.desc()).first())
        if not previous_reading_object:
            previous_reading = counter.first_reading
            previous_reading_date = counter.start_date
        else:
            previous_reading = previous_reading_object.reading
            previous_reading_date = previous_reading_object.reading_date
        logger.info(
            f"previous_reading: {previous_reading}, previous_reading_date: {previous_reading_date}")

        if str(previous_reading_object.id) != str(entry_id):
            # print(f"entry_id: {entry_id}, previous_reading_object.id: {previous_reading_object.id}")
            if reading_date <= previous_reading_date:
                return ManagerErrors.ENERGY_COUNTER_INVALID_READING_DATE
            if reading < previous_reading:
                return ManagerErrors.ENERGY_COUNTER_INVALID_READING

        entry = (self.db_session.query(EnergyCounterReading).
                 filter(EnergyCounterReading.id == entry_id)
                 ).first()
        if entry:
            entry.reading = reading
            entry.reading_date = reading_date
            entry.counter_id = counter.id
        else:
            entry = EnergyCounterReading(id=entry_id,
                                         counter_id=counter.id,
                                         reading=reading,
                                         reading_date=reading_date)
            self.db_session.add(entry)
        self.db_session.commit()
        return entry.convert_to_dict(counter_id=counter_id, counter_type=counter_type)

    @return_wrapper()
    def delete_energy_counter_reading(self, user_id, reading_id):
        res = self._delete_energy_counter_reading(user_id=user_id,
                                                  reading_id=reading_id)
        return res

    def _delete_energy_counter_reading(self, user_id, reading_id):
        reading = (self.db_session.query(EnergyCounterReading).
                   join(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounterReading.id == reading_id)).first()
        if not reading:
            return ManagerErrors.ENTRY_NOT_FOUND
        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.id == reading.counter_id).
                   first())
        self.db_session.delete(reading)
        self.db_session.commit()
        return reading.convert_to_dict(counter_id=counter.counter_id,
                                       counter_type=counter.counter_type)

    @return_wrapper()
    def get_energy_consumption_overview(self, user_id, start_date,
                                        end_date, include_last_month=True):
        res = self._get_energy_consumption_overview(user_id=user_id,
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    include_last_month=include_last_month)
        return res

    def _get_energy_consumption_overview(self, user_id, start_date,
                                         end_date, include_last_month=True):
        start_date = datetime.date(start_date.year, start_date.month, 1)
        end_date = datetime.date(end_date.year, end_date.month, 1)
        if start_date >= end_date:
            return ManagerErrors.INVALID_DATE
        counters = (self.db_session.query(EnergyCounter).
                    filter(EnergyCounter.user_id == user_id).
                    # filter(EnergyCounter.start_date <= start_date).
                    all())
        if len(counters) == 0:
            return {
                "x_labels": [],
                "consumption": [],
                "start_month": start_date.month,
                "start_year": start_date.year,
                "end_month": end_date.month,
                "end_year": end_date.year
            }

        counters_overview = []
        x_labels = None
        all_data = []
        for counter in counters:
            counter_overview = self._get_energy_consumption_overview_for_counter(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                counter_db_id=counter.id,
                include_last_month=include_last_month
            )
            if isinstance(counter_overview, dict):
                label = counter_overview["label"]
                data = counter_overview["data"]
                counters_overview.append({
                    "label": label,
                    "data": data,
                })
                all_data.append(data)
                if x_labels is None:
                    x_labels = counter_overview["x_labels"]
            else:
                return counter_overview

        # compute the sum of all counters for each month
        total = np.array(all_data)
        total = np.sum(total, axis=0)
        # convert to list
        total = total.tolist()
        # round to 2 decimal places
        total = [round(x, 2) for x in total]
        # convert to dict
        counters_overview.append({
            "label": "Total",
            "data": total,
        })

        res = {
            "x_labels": x_labels,
            "consumption": counters_overview,
            "start_month": start_date.month,
            "start_year": start_date.year,
            "end_month": end_date.month,
            "end_year": end_date.year
        }
        logger.info(res)
        return res

    @return_wrapper()
    def get_energy_consumption_overview_for_counter(self, user_id: int,
                                                    start_date: datetime.date,
                                                    end_date: datetime.date,
                                                    counter_db_id: str,
                                                    include_last_month=False):
        res = self._get_energy_consumption_overview_for_counter(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            counter_db_id=counter_db_id,
            include_last_month=include_last_month
        )
        return res

    @return_wrapper()
    def get_total_consumption(self, user_id: int):
        today = datetime.date.today()
        start_date = datetime.date(
            today.year, today.month, 1) - relativedelta(months=1)
        end_date = start_date + relativedelta(months=1)
        counters = (self.db_session.query(EnergyCounter).
                    filter(EnergyCounter.user_id == user_id).
                    all())
        if len(counters) == 0:
            return {
                "total": 0.0,
                "current_month_str": to_month_year_str(start_date),
                "message": "No counters found",
                "consumption_development_percentage": 0.0,
                "average_consumption_until_previous_month": 0.0,
                "current_month": start_date.month,
                "current_year": start_date.year,
                "start_month": start_date.month,
                "start_year": start_date.year,
                "end_month": end_date.month,
                "end_year": end_date.year
            }
        current_month_total = 0.0
        for counter in counters:
            counter_overview = self._get_energy_consumption_overview_for_counter(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                counter_db_id=counter.id,
                include_last_month=False
            )
            if isinstance(counter_overview, dict):
                data = counter_overview["data"]
                if len(data) != 1:
                    logger.error(
                        f"Invalid data length. start_date={start_date}, end_date={end_date}, data={data}")
                    return ManagerErrors.ENERGY_COUNTER_INVALID_READING_DATE
                current_month_total += sum(data)
            else:
                logger.error(
                    f"Invalid data length. start_date={start_date}, end_date={end_date}, return={counter_overview}")
                return counter_overview

        min_start_date = (self.db_session.query(func.min(EnergyCounter.start_date)).
                          filter(EnergyCounter.user_id == user_id)).first()[0]

        max_end_date = start_date - relativedelta(months=1)
        month_diff = diff_month(max_end_date, min_start_date)

        average_consumption_price = 0.0
        if month_diff <= 1:
            average_consumption_price = 0.0
        else:
            consumption_overview = self._get_energy_consumption_overview(
                user_id=user_id,
                start_date=min_start_date,
                end_date=max_end_date,
                include_last_month=False
            )
            consumption = consumption_overview["consumption"]

            for sample in consumption:
                if sample["label"].lower() == "total":
                    data = sample["data"]
                    average_consumption_price = sum(data) / len(data)
                    break
        if average_consumption_price == 0.0:
            consumption_development_percentage = 0.0
        else:
            average_consumption_price = round(average_consumption_price, 2)
            consumption_development_percentage = ((
                current_month_total - average_consumption_price) / average_consumption_price) * 100
            consumption_development_percentage = round(
                consumption_development_percentage, 2)
            # if positive, then consumption is decreasing
            consumption_development_percentage *= -1
        if consumption_development_percentage > 0:
            message = "Energy consumption is decreasing"
        elif consumption_development_percentage == 0:
            message = "Energy consumption is stable"
        else:
            message = "Energy consumption is increasing"
        res = {
            "total": current_month_total,
            "current_month_str": to_month_year_str(start_date),
            "current_month": start_date.month,
            "current_year": start_date.year,
            "message": message,
            "average_consumption_until_previous_month": average_consumption_price,
            "consumption_development_percentage": consumption_development_percentage,
            "start_month": min_start_date.month,
            "start_year": min_start_date.year,
            "end_month": max_end_date.month,
            "end_year": max_end_date.year
        }
        logger.info(res)
        return res

    def _get_energy_consumption_overview_for_counter(self, user_id: int,
                                                     start_date: datetime.date,
                                                     end_date: datetime.date,
                                                     counter_db_id: str,
                                                     include_last_month=True):
        start_date = datetime.date(start_date.year, start_date.month, 1)
        end_date = datetime.date(end_date.year, end_date.month, 1)

        if start_date >= end_date:
            return ManagerErrors.INVALID_DATE

        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.id == counter_db_id)).first()

        if not counter:
            return ManagerErrors.ENERGY_COUNTER_NOT_FOUND

        frequency = counter.frequency
        if frequency not in ["daily", "monthly", "yearly"]:
            return ManagerErrors.ENERGY_COUNTER_INVALID_FREQUENCY
        if frequency != "monthly":
            return ManagerErrors.FEATURE_NOT_IMPLEMENTED

        first_reading = EnergyCounterReading(
            counter_id=counter.id,
            reading=counter.first_reading,
            reading_date=counter.start_date
        )
        base_price = counter.base_price
        price = counter.price
        previous_reading = (self.db_session.query(EnergyCounterReading).
                            filter(EnergyCounterReading.counter_id == counter.id).
                            filter(EnergyCounterReading.reading_date < start_date).order_by(
            EnergyCounterReading.reading_date.desc()).first()
        )
        if not previous_reading:
            previous_reading = first_reading
        readings = (self.db_session.query(EnergyCounterReading).
                    filter(EnergyCounterReading.counter_id == counter.id).
                    filter(EnergyCounterReading.reading_date >= start_date).
                    filter(EnergyCounterReading.reading_date <= end_date).
                    order_by(EnergyCounterReading.reading_date).all())
        # set reading_date to last day of month
        # for reading in readings:
        #     reading.reading_date = datetime.date(
        #         reading.reading_date.year, reading.reading_date.month, monthrange(reading.reading_date.year,
        #                                                                            reading.reading_date.month)[1])
        # return

        # add previous reading to readings
        readings = [previous_reading] + readings
        dates = create_dates_labels(
            start_date=start_date,
            end_date=end_date,
            include_last_month=include_last_month,
            to_dates=False
        )
        consumption_map = {date: 0.0 for date in dates}

        for idx in range(len(readings) - 1):
            current_reading = readings[idx]
            next_reading = readings[idx + 1]
            current_reading_date = datetime.date(
                current_reading.reading_date.year,
                current_reading.reading_date.month,
                1
            )
            next_reading_date = datetime.date(
                next_reading.reading_date.year,
                next_reading.reading_date.month,
                monthrange(next_reading.reading_date.year,
                           next_reading.reading_date.month)[
                    1] if next_reading.reading_date.year == current_reading.reading_date.year and next_reading.reading_date.month == current_reading.reading_date.month else 1
            )
            diff_days = diff_day(next_reading_date,
                                 current_reading_date)
            if frequency == "monthly":
                if diff_days not in [28, 29, 30, 31]:
                    print(
                        f"Should skip reading "
                        f"{current_reading_date}"
                        f" to {next_reading_date}"
                        f" due to invalid diff_days: {diff_days}")
                    # continue
            current_month = to_month_year_str(next_reading.reading_date)
            consumption = base_price + \
                (price * (next_reading.reading - current_reading.reading))
            consumption_map[current_month] = round(consumption, 2)

        res = {
            "label": f"{counter.counter_type[:3]}-{counter.counter_id[:3]}",
            "counter_id": counter.counter_id,
            "counter_type": counter.counter_type,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "x_labels": dates,
            "data": [consumption_map[date] for date in dates],
        }
        return res

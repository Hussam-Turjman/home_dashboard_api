from sqlalchemy.orm.session import Session as SQLSession

from .errors import ManagerErrors, translate_manager_error
from ..db.tables import EnergyCounter, EnergyCounterReading, User
import datetime
from ..db.utils import diff_month, create_dates_labels, find_invoice_by_counter_id
from sqlalchemy import func
from calendar import monthrange
import numpy as np
from ..logger import logger


class EnergyManager(object):
    db_session: SQLSession

    def __init__(self, db_session: SQLSession):
        self.db_session = db_session

    def _add_energy_counter(self, user_id, counter_id_db, counter_id, counter_type, energy_unit,
                            frequency, base_price, price, start_date, first_reading):
        user = (self.db_session.query(User).filter(User.id == user_id)).first()
        if not user:
            return ManagerErrors.USER_NOT_FOUND
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
                                    first_reading=first_reading)
            self.db_session.add(counter)
        self.db_session.commit()
        return counter.convert_to_dict()

    def add_energy_counter(self, user_id, counter_id_db, counter_id, counter_type, energy_unit,
                           frequency, base_price, price, start_date, first_reading):
        res = self._add_energy_counter(user_id=user_id,
                                       counter_id=counter_id,
                                       counter_id_db=counter_id_db,
                                       counter_type=counter_type,
                                       energy_unit=energy_unit,
                                       frequency=frequency,
                                       base_price=base_price,
                                       price=price,
                                       start_date=start_date,
                                       first_reading=first_reading)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

    def _delete_energy_counter(self, user_id, counter_id_db):
        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.id == counter_id_db)).first()
        if not counter:
            return ManagerErrors.ENTRY_NOT_FOUND
        self.db_session.delete(counter)
        self.db_session.commit()
        return counter.convert_to_dict()

    def delete_energy_counter(self, user_id, counter_id_db):
        res = self._delete_energy_counter(user_id=user_id,
                                          counter_id_db=counter_id_db)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

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

    def add_energy_counter_reading(self, user_id, entry_id: str, counter_id, counter_type,
                                   reading, reading_date):
        res = self._add_energy_counter_reading(user_id=user_id,
                                               entry_id=entry_id,
                                               counter_id=counter_id,
                                               counter_type=counter_type,
                                               reading=reading,
                                               reading_date=reading_date)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

    def _add_energy_counter_reading(self, user_id: int, entry_id: str, counter_id: str,
                                    counter_type: str, reading: float,
                                    reading_date: datetime.date):
        counter = (self.db_session.query(EnergyCounter).
                   filter(EnergyCounter.user_id == user_id).
                   filter(EnergyCounter.counter_id == counter_id).
                   filter(EnergyCounter.counter_type == counter_type)).all()
        if not counter:
            return ManagerErrors.ENTRY_NOT_FOUND
        if len(counter) > 1:
            return ManagerErrors.MULTIPLE_ENTRIES_FOUND
        counter = counter[0]
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

    def delete_energy_counter_reading(self, user_id, reading_id):
        res = self._delete_energy_counter_reading(user_id=user_id,
                                                  reading_id=reading_id)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

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

    def get_energy_consumption_overview(self, user_id, start_date,
                                        end_date, include_last_month=True):
        res = self._get_energy_consumption_overview(user_id=user_id,
                                                    start_date=start_date,
                                                    end_date=end_date,
                                                    include_last_month=include_last_month)
        if isinstance(res, ManagerErrors):
            return {
                "error": True,
                "message": translate_manager_error(res),
                "exception": ValueError(translate_manager_error(res)),
            }
        return {
            "error": False,
            "payload": res,
        }

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
        if not counters:
            return {
                "x_labels": [],
                "invoices": [],
                "start_month": start_date.month,
                "start_year": start_date.year,
                "end_month": end_date.month,
                "end_year": end_date.year
            }

        counters = sorted(counters, key=lambda x: x.start_date)
        counters = list(counters)
        if len(counters) == 0:
            return ManagerErrors.NO_ENTRIES_FOUND

        original_start_date = start_date
        # Get readings
        # FIXME: get min_start_date for each counter
        # min_start_date = datetime.date(2024, 9, 1)
        # get min_start_date of all counters
        min_start_date = self.db_session.query(func.min(EnergyCounter.start_date)).filter(
            EnergyCounter.user_id == user_id).first()
        if not isinstance(min_start_date, datetime.date):
            min_start_date = min_start_date[0]
        # logger.info(f"min_start_date: {type(min_start_date)}")
        # logger.info(f"min_start_date: {min_start_date}")
        start_date = min_start_date
        month_diff = diff_month(end_date, start_date)
        min_start_month = start_date.month
        min_start_year = start_date.year
        end_month = end_date.month
        end_year = end_date.year
        x_labels = create_dates_labels(
            min_start_year=min_start_year,
            min_start_month=min_start_month,
            month_diff=month_diff,
            end_month=end_month,
            end_year=end_year,
            include_last_month=include_last_month,
            to_dates=False
        )
        # convert labels to dates
        x_labels_dates = [datetime.datetime.strptime(
            label, "%b %Y").date() for label in x_labels]
        invoices = []

        for counter in counters:
            label = f"{counter.counter_type}-{counter.counter_id}"
            data = []
            base_price = counter.base_price

            first_reading = counter.first_reading
            previous_reading = first_reading
            for idx, date in enumerate(x_labels_dates):
                price = counter.price
                last_day = monthrange(date.year, date.month)[1]
                current_date = datetime.date(date.year, date.month, last_day)
                if current_date < counter.start_date:
                    data.append(0)
                    continue

                max_reading = (self.db_session.query(func.max(EnergyCounterReading.reading)).
                               join(EnergyCounter).
                               filter(EnergyCounter.user_id == user_id).
                               filter(EnergyCounter.id == counter.id).
                               filter(EnergyCounterReading.reading_date <= current_date).
                               first())

                max_reading = max_reading[0] if max_reading else None

                if max_reading:
                    price *= (max_reading - previous_reading)
                    previous_reading = max_reading
                else:
                    price = 0.0
                data.append(base_price + price)
            invoice_idx = find_invoice_by_counter_id(
                invoices=invoices, counter_id_in=counter.counter_id)
            if invoice_idx is not None:
                new_label = invoices[invoice_idx]["label"].split("-")[0]
                new_label = f"{new_label}-{label}"
                invoices[invoice_idx]["label"] = new_label
                invoices[invoice_idx]["data"] = [invoices[invoice_idx]["data"][i] + data[i] for i in
                                                 range(len(data))]

            else:
                invoices.append(
                    {
                        "data": data,
                        "label": label
                    }
                )

        # Add extra label for total sum for each month
        total_sum = []
        for idx in range(len(x_labels_dates)):
            t_sum = 0.0
            for invoice in invoices:
                t_sum += invoice["data"][idx]
            total_sum.append(t_sum)
        invoices.append(
            {
                "data": total_sum,
                "label": "Total"
            })
        # filter results to only include dates starting from original_start_date

        to_remove_indexes = []
        for idx, date in enumerate(x_labels_dates):
            if date < original_start_date:
                to_remove_indexes.append(idx)
        x_labels = np.delete(x_labels, to_remove_indexes).tolist()
        for record in invoices:
            record["data"] = np.delete(
                record["data"], to_remove_indexes).tolist()
        start_date = original_start_date

        return {
            "x_labels": x_labels,
            "invoices": invoices,
            "start_month": start_date.month,
            "start_year": start_date.year,
            "end_month": end_date.month,
            "end_year": end_date.year
        }

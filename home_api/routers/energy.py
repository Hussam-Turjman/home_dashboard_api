import datetime

from fastapi import Depends, HTTPException, status, APIRouter, Body, Request

from .user import validate_user
from ..managers.energy_manager import EnergyManager
from ..pydantic_models.energy import EnergyCounterModel, EnergyCounterReadingModel
from ..pydantic_models.session import UserSessionModel
from ..runtime import db_session
from typing import Annotated, List
from ..logger import logger
from dateutil.relativedelta import relativedelta

energy_manager = EnergyManager(db_session=db_session)

URL_BASE = "/api/energy"
router = APIRouter(
    prefix=URL_BASE,
    tags=["energy"],
    dependencies=[Depends(validate_user)]
)


@router.get("/energy_counters/{session_id}", response_model=List[EnergyCounterModel])
async def energy_counters(user: Annotated[UserSessionModel, Depends(validate_user)]):
    counters = energy_manager.get_energy_counters(user_id=user.user_id)
    counters = [EnergyCounterModel.model_validate(
        counter).model_dump() for counter in counters]
    return counters


@router.get("/energy_counter_readings/{session_id}", response_model=List[EnergyCounterReadingModel])
async def energy_counter_readings(user: Annotated[UserSessionModel, Depends(validate_user)]):
    readings = energy_manager.get_energy_counter_readings(user_id=user.user_id)
    readings = [EnergyCounterReadingModel.model_validate(
        reading).model_dump() for reading in readings]
    return readings


@router.put("/add_energy_counter/{session_id}", response_model=EnergyCounterModel)
async def add_energy_counter(user: Annotated[UserSessionModel, Depends(validate_user)],
                             counter: EnergyCounterModel = Body(...)):
    counter.start_date = datetime.datetime.strptime(
        counter.start_date, "%Y-%m-%d").date()
    res = energy_manager.add_energy_counter(user_id=user.user_id,
                                            counter_id=counter.counter_id,
                                            counter_id_db=counter.id,
                                            counter_type=counter.counter_type,
                                            energy_unit=counter.energy_unit,
                                            frequency=counter.frequency,
                                            base_price=counter.base_price,
                                            price=counter.price,
                                            start_date=counter.start_date,
                                            end_date=counter.end_date,
                                            first_reading=counter.first_reading)
    if res["error"]:
        logger.error(res["message"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )
    payload = res["payload"]
    res = EnergyCounterModel.model_validate(payload).model_dump()
    logger.info(f"Added energy counter: {res}")
    return res


@router.delete("/delete_energy_counter/{session_id}/{counter_id_db}", response_model=EnergyCounterModel)
async def delete_energy_counter(user: Annotated[UserSessionModel, Depends(validate_user)],
                                counter_id_db: str):
    res = energy_manager.delete_energy_counter(
        user_id=user.user_id, counter_id_db=counter_id_db)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )
    payload = res["payload"]
    return EnergyCounterModel.model_validate(payload).model_dump()


@router.put("/add_energy_counter_reading/{session_id}", response_model=EnergyCounterReadingModel)
async def add_energy_counter_reading(user: Annotated[UserSessionModel, Depends(validate_user)],
                                     reading: EnergyCounterReadingModel = Body(...)):
    reading.reading_date = datetime.datetime.strptime(
        reading.reading_date, "%Y-%m-%d").date()
    res = energy_manager.add_energy_counter_reading(user_id=user.user_id,
                                                    entry_id=reading.id,
                                                    counter_id=reading.counter_id,
                                                    counter_type=reading.counter_type,
                                                    reading=reading.reading,
                                                    reading_date=reading.reading_date)
    if res["error"]:
        logger.error(res["message"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )
    payload = res["payload"]
    res = EnergyCounterReadingModel.model_validate(payload).model_dump()
    logger.info(f"Added energy counter reading: {res}")
    return res


@router.delete("/delete_energy_counter_reading/{session_id}/{reading_id}", response_model=EnergyCounterReadingModel)
async def delete_energy_counter_reading(user: Annotated[UserSessionModel, Depends(validate_user)],
                                        reading_id: str):
    res = energy_manager.delete_energy_counter_reading(
        user_id=user.user_id, reading_id=reading_id)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )
    payload = res["payload"]
    return EnergyCounterReadingModel.model_validate(payload).model_dump()


@router.get("/energy_consumption_overview/{session_id}", response_model=dict)
async def get_energy_consumption_overview(user: Annotated[UserSessionModel, Depends(validate_user)],
                                          start_month: int, start_year: int,
                                          end_month: int, end_year: int, request: Request
                                          ):
    if start_month == 0 and start_year == 0 and end_month == 0 and end_year == 0:
        now = datetime.datetime.now()
        start_month = now.month
        start_year = now.year
        end_month = (now + relativedelta(years=1)).month
        end_year = (now + relativedelta(years=1)).year
        start_date = datetime.date(start_year, start_month, 1)
        end_date = datetime.date(end_year, end_month, 1)
    else:
        start_date = datetime.date(start_year, start_month, 1)
        end_date = datetime.date(end_year, end_month, 1)
    res = energy_manager.get_energy_consumption_overview(user_id=user.user_id,
                                                         start_date=start_date,
                                                         end_date=end_date,
                                                         include_last_month=True)
    if res["error"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res["message"],
        )

    payload = res["payload"]
    return payload

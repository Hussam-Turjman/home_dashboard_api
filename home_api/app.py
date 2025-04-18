from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .logger import init_logger, logger
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.requests import Request
import datetime
from .entrypoint import entry_point
from .routers.user import router as user_router
from .routers.expense import router as expense_router
from .routers.events import router as events_router
from .routers.energy import router as energy_router
from .routers.transactions import router as transactions_router


@asynccontextmanager
async def lifespan(app_in: FastAPI):
    # on_startup
    init_logger()
    missing = []
    if entry_point.check_all(missing_res=missing):
        logger.info("All environment variables are set.")
    else:
        logger.error("Some environment variables are not set.")
        logger.error(f"Missing: {missing}")

    yield
    # on_shutdown
    logger.info(f"API stopped at {datetime.datetime.now()}")


app = FastAPI(title="Home Dashboard",
              description="DESC:TODO",
              summary="SUMMARY:TODO",
              version="0.0.0",
              terms_of_service="https://hussam-turjman.de/terms/",
              contact={
                  "name": "Hussam Turjman",
                  "url": "https://hussam-turjman.de/contact/",
                  "email": "hussam.turjman@gmail.com",
              },
              # openapi_url=None,
              lifespan=lifespan,
              )

origins = [
    "https://hussam-turjman.de",
    f"http://{entry_point.host}:{entry_point.port}",
    "http://localhost:3000",
    "http://localhost",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers here
app.include_router(router=user_router)
app.include_router(router=expense_router)
app.include_router(router=events_router)
app.include_router(router=energy_router)
app.include_router(router=transactions_router)

# Order matters


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    # or logger.error(f'{exc}')
    msg = f"{exc_str} {request}"
    logger.error(msg)

    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


@app.get("/")
async def root():
    return {"message": "Hello World"}


__all__ = ["app"]

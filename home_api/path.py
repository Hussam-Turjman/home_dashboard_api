import os
import pathlib
import datetime

PARENT_DIR = os.path.join(pathlib.Path(__file__).parent.resolve(), '..')
LOGS_DIR = os.path.join(PARENT_DIR, "logs")
NOW = datetime.datetime.now()
LOG_FILENAME = f"api_{NOW}.log"

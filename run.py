#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from home_api.app import app
from home_api.entrypoint import entry_point
import uvicorn
from home_api.logger import logger


def run():
    uvicorn.run(app,
                host=entry_point.host,
                port=entry_point.port,
                proxy_headers=True,
                log_level="info",
                # workers=8,
                )


if __name__ == "__main__":
    run()

# -*- coding: utf-8 -*-
"""
********************************
reslib.data.sources.utilities
********************************

Util functions for data source functionality, such as WRDS downloader.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

# STDlib imports
import os
import logging
# import datetime as dt

# 3rd party package imports
import pandas as pd
from urllib.parse import quote_plus
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
try:
    import psycopg
    PSYCOPG = "psycopg"
except ImportError:
    PSYCOPG = "psycopg2"

# project imports
# from src import constants as CONST
from src import globals as GLOB


# Local logger
_logger = logging.getLogger(__name__)


class wrds_connection(object):
    """Connect to WRDS (could be replaced with the wrds package).

    Either pass in wrds_user and wrds_password, or set the WRDS_USER and WRDS_PASSWORD environment variables.

    Example:
    ```
    with wrds_connection() as wrds:
        df = wrds.read_sql("SELECT * FROM crsp.dsf LIMIT 10")
    ```
    """
    db_url = "wrds-pgdata.wharton.upenn.edu"
    db_port = 9737
    db_table = "wrds"
    db_conargs = {"sslmode": "require", "application_name": "win32 python 3.10.0/wrds 3.2.0"}

    engine = None
    connection = None

    def __init__(self, wrds_user=None, wrds_password=None):
        self._usr = wrds_user or os.environ.get("WRDS_USER", None)
        self._pass = wrds_password or os.environ.get("WRDS_PASSWORD", None)
        # [DB_FLAVOR]+[DB_PYTHON_LIBRARY]://[USERNAME]:[PASSWORD]@[DB_HOST]:[PORT]/[DB_NAME]
        self._url = (
            f"postgresql+{PSYCOPG}://{self._usr}:{quote_plus(self._pass)}@{self.db_url}:{self.db_port}/{self.db_table}"
        )

    def __enter__(self):
        self.engine = sa.create_engine(self._url, isolation_level="AUTOCOMMIT", connect_args=self.db_conargs)
        self.connection = self.engine.connect()
        return self

    def __exit__(self, *args, **kwargs):
        try:
            # Wrap in exception so engine disposes even if connection close fails
            self.connection.close()
        except Exception as e:
            _logger.error(f"wrds_connection connection.close() error: {e}")
        self.engine.dispose()
        self.engine = None

    def read_sql(self, sql_statement, *args, chunksize=500000, **kwargs):
        if isinstance(sql_statement, str):
            sql_statement = sa.text(sql_statement)
        try:
            df = pd.read_sql_query(sql_statement, self.connection, *args, chunksize=chunksize, **kwargs)
            if chunksize is None:
                return df
            else:
                return pd.concat(df)
        except DBAPIError as e:
            _logger.error(f"wrds_connection read_sql error: {e}")
            raise

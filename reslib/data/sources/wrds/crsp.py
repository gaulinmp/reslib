# -*- coding: utf-8 -*-

"""
*************************************
reslib.data.sources.wrds.crsp
*************************************

This module contains code to download and cache CRSP data from WRDS.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

# STDlib imports
import logging as _logging

# 3rd party package imports
import numpy as _np
import pandas as _pd

# project imports
from reslib.data.cache import _DataFrameCache
from reslib.data.sources.utilities import wrds_connection as _wrds_connection


# Local logger
# _logger = _logging.getLogger(__name__)


class CRSPYearly(_DataFrameCache):
    """
    Read Compustat data from cache if it exists,
    or read from WRDS Postrgres server, and write out to
    `interim` cache folder.
    """
    file_format = 'tab'
    read_args = {'parse_dates': 'datadate lag_datadate'.split()}

    def make_dataset(self):
        # Build sub-queries
        sql_comp_dates = """
            SELECT a1.*, b1.datadate, b1.fyear
                ,make_date(CAST(extract(year from b1.datadate) - 1 AS INTEGER),
                        CAST(extract(month from b1.datadate) AS INTEGER),
                        CAST(extract(day from b1.datadate) AS INTEGER) - 1 ) + 2 AS lag_datadate
            FROM (SELECT * FROM crsp.ccm_lookup WHERE lpermno IS NOT NULL) AS a1
            INNER JOIN (SELECT gvkey, datadate, fyear FROM comp.funda
                        WHERE datadate > '1990-01-01'::date
                        AND INDFMT = 'INDL' AND DATAFMT = 'STD' AND POPSRC = 'D' AND CONSOL = 'C') AS b1
                ON a1.gvkey = b1.gvkey
                AND b1.datadate BETWEEN a1.linkdt AND COALESCE(a1.linkenddt, CURRENT_DATE)
            WHERE a1.gvkey IS NOT NULL
                AND a1.lpermno IS NOT NULL
                AND b1.datadate IS NOT NULL
        """

        sql_msf = f"""
            SELECT b2.gvkey, b2.datadate, b2.lag_datadate, b2.fyear
                , a2.permno, a2.permco, a2.date, a2.ret, ABS(a2.prc) AS prc, a2.vol/1000000 AS vol
            FROM crsp.dsf AS a2
            INNER JOIN ({sql_comp_dates}) AS b2
                ON a2.permno = b2.lpermno
                AND a2.date BETWEEN b2.lag_datadate AND b2.datadate
        """

        sql_crsp = f"""
            SELECT DISTINCT gvkey, datadate, lag_datadate, fyear, permno, permco
                ,SUM(vol) AS total_vol
                ,EXP(SUM(LOG(ret + 1)))-1 as cum_ret
                ,AVG(ret) as ave_ret
                ,STDDEV_SAMP(ret) as stddev_ret
            FROM ({sql_msf}) AS a3
            GROUP BY gvkey, datadate, lag_datadate, fyear, permno, permco
            ORDER BY gvkey, datadate, lag_datadate, fyear, permno, permco
        """

        with wrds_connection() as conn:
            df = conn.read_sql(sql_crsp, parse_dates='datadate lag_datadate'.split())

        return df

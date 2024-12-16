"""
********************************
reslib.data.io
********************************

This module contains the basic functionality for reading/writing data.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

# STDlib imports
import logging as __logging

# 3rd party imports
import numpy as __np

# current module imports

# Local logger
__logger = __logging.getLogger(__name__)

def write_stata_file(df: "DataFrame", filepath: str, **write_kwargs) -> str:
    """
    Write a pandas DataFrame to a Stata file. Handle common issues like string length, missing values, and date columns.

    Attributes:
        df (DataFrame): pandas DataFrame to save to `filepath` in Stata .dta format.
        filepath (str): path to save the file to.
        write_kwargs (dict): additional keyword arguments to pass to `pandas.DataFrame.to_stata`. Default is
            `write_index=False, version=117, convert_dates={k: 'td' for k in df.select_dtypes(include='datetime64').columns}`.

    Returns:
        str: path of the saved file
    """
    df=df.copy()
    for c in df.select_dtypes(include=['object', 'bool']).columns:
        if not (set(df[c].unique()) - {True, False}):
            __logger.info("reslib.data.io.reslib.data.io.write_stata_file: %s is True/False column. Making 0/1.", c)
            df[c] = df[c].astype(int)
        elif not (set(df[c].unique()) - {True, False, __np.nan}):
            __logger.info("reslib.data.io.write_stata_file: %s is True/False/Null column. Making 0/1.", c)
            df[c] = df[c].astype(float)
        elif not (set(df[c].fillna(False).unique()) - {True, False}):
            __logger.info("reslib.data.io.write_stata_file: %s is True/False/Null filled column. Making 0/1.", c)
            df[c] = df[c].astype(float)
        elif not (set(df[c].fillna(False).unique()) - {True, False, __np.nan}):
            __logger.info("reslib.data.io.write_stata_file: %s is True/False/Null filled column nan. Making 0/1.", c)
            df[c] = df[c].astype(float)

        try:
            max_len = max(df.loc[df[c].notnull(), c].apply(len))
            if max_len > 1023:
                __logger.warning("Column %s has max string len == %d, dropping", c, max_len)
                del df[c]
        except Exception:
            # len didn't work? Ignore. Probably bigger problems waiting below.
            pass

    date_cols = {k: 'td' for k in df.select_dtypes(include='datetime64').columns}

    for c in df.select_dtypes(include='object').columns:
        try:
            df[c].str.encode('latin-1')
            __logger.info("write_stata_file: %s is a string column, filling missing with ''", c)
            df[c] = df[c].fillna('')
        except AttributeError:
            pass
        except UnicodeEncodeError:
            __logger.warning("write_stata_file: %s has non latin-1 encodable characters", c)
            df[c] = df[c].str.encode('latin-1', errors='ignore').str.decode('latin-1', errors='ignore').fillna('')

    if "write_index" not in write_kwargs:
        write_kwargs["write_index"] = False
    if "version" not in write_kwargs:
        write_kwargs["version"] = 117
    if "convert_dates" not in write_kwargs:
        write_kwargs["convert_dates"] = date_cols

    df.to_stata(filepath, **write_kwargs)

    return filepath

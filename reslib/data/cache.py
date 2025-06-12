# -*- coding: utf-8 -*-

"""
********************************
reslib.data.cache
********************************

This module contains the DatasetCache object for reading/writing cached datasets to disk.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# STDlib imports
import os
import logging
import datetime as dt
from pathlib import Path
from typing import Union

# 3rd party package imports
# import numpy as np
import pandas as pd

# project imports
from reslib.config import Config


# Local _logger
_logger = logging.getLogger(__name__)


class ReadWriteArgCopyToDescendants(type):
    """
    Make read_args and write_args inheret from parent without super() init code.
    I know about dangerous mutable properties, but doubt it will apply much.
    This is about useage by research academics, not massively parallel projects.
    Citation: https://stackoverflow.com/a/42036304/1959876

    Example::

        class Gramma(metaclass=ReadWriteArgCopyToDescendants):
            read_args = {'sep': '\t'} # Let's say we just want a read_args at first

        class Mom(Gramma):
            read_args = {'parse_dates': ['datadate', ]}
            pass

        assert Mom().read_args == {'sep': '\t', 'parse_dates': ['datadate', ]}
        assert Mom().write_args == {}

        class Kid(Mom):
            write_args = {'sep': ','}
            pass

        assert Kid().read_args == {'sep': '\t', 'parse_dates': ['datadate', ]}
        assert Kid().write_args == {'sep': ','}
    """

    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)

        # Add one of these for each 'dict' you want to copy up the tree
        base_read_args = [getattr(bc, "read_args", {}) for bc in bases + (new_class,)]

        new_class.read_args = {}
        for read_args in base_read_args:
            new_class.read_args.update(read_args)

        # Add one of these for each 'dict' you want to copy up the tree
        base_write_args = [getattr(bc, "write_args", {}) for bc in bases + (new_class,)]

        new_class.write_args = {}
        for write_args in base_write_args:
            new_class.write_args.update(write_args)

        return new_class


class DataFrameCache(metaclass=ReadWriteArgCopyToDescendants):
    """
    Base class for caching intermediate files.

    Defaults to reading/writing dataset cache with pandas to_csv.
    Default write args: sep="\t", index=False
    Default read args: sep="\t"

    Suggested subclassing::

        class CompustatFUNDA(DataFrameCache):
            override_directory = '~/project/data/comp/'
            filename 'funda'

            def make_dataset():
                # Download funda, return it as dataframe
                pass
    """

    # Resultant path of the file
    path: Union[str, Path] = None
    #: Override directory to store the dataset in.
    override_directory: Union[str, Path] = None
    #: Override filename to name the dataset.
    filename: str = None
    #: DataFrame of the data
    df: "pd.DataFrame" = None

    # These arguments are copied to all children, so manually overwrite
    # in a child class if they don't apply there.
    file_format: str = "csv"
    write_func: callable = None
    read_func: callable = None
    write_args: dict = {"index": False}
    read_args: dict = {}

    def __init__(self, override_filename: str = None, delete_cache: Union[bool, str] = False, file_format: str = "csv"):
        """
        Create new cache object. Sets the following attributes:

          * `filename`: Name of the dataset file. Takes first non-missing from:
            1. `override_filename` argument
            2. `self.filename`
            3. `self.__class__.__name__`
          * `path`: Full path to save dataset at. Takes first non-missing from:
            1. `self.override_directory`
            2. `Config().get('DATA_DIR_INTERIM')`
            3. `.`

        Note: setting `override_filename` may be useful for temporarily
        creating a new file, e.g. testing out data changes in `make_dataset()`
        before overwriting an old version of the cache.
        However because the dataset cache location should rarely change, no such
        equivalent override is provided for the dataset location.
        The location for cache files is best set in the project config file.

        The default constructor sets the extension, according to the compression
        setting, then sets the full path with extension based on compression
        and separator type (`sep` argument in `write_args`).

        The following config options are searched for:

        `DATA_DIR_INTERIM`: Path to the interim data directory, where the cached
            dataset will be stored. This is overridden by `override_directory`
            if that attribute is not `None`.

        `COMPRESSION`: What compression to use, if any, for the cached dataset.
            This is overridden by `write_args` and `read_args` if `compression`
            is specified in either of them.

        Args:
            override_filename (str): Filename to write the dataset to,
                overriding the default. Ignored if equal to `None`.
            delete_cache (bool | str): Flag to delete cache, if it exists. Can pass in string to add to the old cache file as backup, or 'date' to add the modified date to the old cache file.
            file_format (str): File format to use from {'csv', 'tab', 'tsv',
                'h5', 'hdf', 'hdf5', 'stata', 'parquet'}. Default: csv
        """
        # compression = None means no compression.
        # So figuring out the preferred compression is a bit verbose below.
        compression = Config().get("COMPRESSION", None)
        self.compression: dict = {**self.write_args, **self.read_args}.get("compression", compression)

        # Set extension based on write_args separator, default = ','/.csv
        if self.file_format in ["h5", "hdf5", "hdf"]:
            self.write_func = pd.DataFrame.to_hdf
            self.read_func = pd.read_hdf
            if "key" not in self.write_args:
                self.write_args["key"] = "data"
            if "key" not in self.read_args:
                self.read_args["key"] = "data"
            self.extension = "h5"

        elif self.file_format in ["stata", "dta"]:
            self.write_func = pd.DataFrame.to_stata
            self.read_func = pd.read_stata
            self.extension = "dta"
            if "index" in self.write_args:
                del self.write_args["index"]
            if "write_index" not in self.write_args:
                self.write_args["write_index"] = False

        elif self.file_format in ["parquet"]:
            self.write_func = pd.DataFrame.to_parquet
            self.read_func = pd.read_parquet
            self.extension = "parquet"

        elif self.file_format in ["csv", "tab", "tsv"]:
            self.write_func = pd.DataFrame.to_csv
            self.read_func = pd.read_csv

            self.extension = self.file_format

            if self.extension in ["tab", "tsv"]:
                self.write_args["sep"] = "\t"
                self.read_args["sep"] = "\t"
            elif self.write_args.get("sep", ",") == "\t":
                self.extension = "tab"
                self.read_args["sep"] = "\t"

            # If there's compression set, add the right extension
            if self.compression == "gzip":
                self.extension += ".gz"
            elif self.compression in ("bz2", "zip", "xz"):
                self.extension += "." + self.compression
        else:
            if self.write_func is None or self.read_func is None:
                _logger.error("Unknown file format %r, and write/read functions are null", self.file_format)
            else:
                _logger.warning(
                    "Unknown file format %r, but write/read functions set so hopefully this is planned behavior",
                    self.file_format,
                )

        if override_filename is not None:
            self.filename = override_filename
        if not self.filename:
            self.filename = self.__class__.__name__

        # Set the path, based on Config.DATA_DIR_INTERIM (else .)
        if self.override_directory:
            data_dir = self.override_directory
        else:
            data_dir = Config().get("DATA_DIR_INTERIM", ".")
        self.path = os.path.join(data_dir, f"{self.filename}.{self.extension}")

        _logger.debug("file_format: %r, path: %r", self.file_format, self.path)
        _logger.debug("write_func: %r", self.write_func)
        _logger.debug("write_args: %r", self.write_args)
        _logger.debug("read_func: %r", self.read_func)
        _logger.debug("read_args: %r", self.read_args)

        if delete_cache:
            self.delete_cache(backup=delete_cache)

    def make_dataset(self) -> "pd.DataFrame":
        """
        Make dataset to be saved to cache.

        Should return a dataframe.
        """
        raise NotImplementedError

    @property
    def data(self) -> "pd.DataFrame":
        """
        Property accessor for the underlying dataframe.
        Loads cached dataframe into memory, calling
        `make_dataset()` if no cache is available.
        """
        if not self.is_cached:
            _logger.debug("Cached file not found, creating new dataset.")
            self.write(self.make_dataset())

        if self.df is None:
            _logger.debug("Cached file found, reading dataset.")
            self.df = self.read()

        return self.df

    def read(self, read_args=None) -> "pd.DataFrame":
        """
        Read df from cache, returning 'cleaned' df.

        Calls: _pre_read_hook() before, and _post_read_hook(read_df) after.

        Args:
            read_args (dict): Dictionary of read-args to be passed to the `read`
                function, overriding those specified in `self.read_args`.

        Returns:
            pandas.DataFrame: DataFrame which is passed through
                `_post_read_hook(df)`.
        """
        preread = self._pre_read_hook()

        read_df = self._read(preread=preread)

        return self._post_read_hook(read_df)

    def write(self, df, overwrite_cache=False, write_args=None) -> "pd.DataFrame":
        """
        Write df to cache, returning 'cleaned' df.

        Args:
            df (pandas.DataFrame): DataFrame to be written to disk, using the
                `self.write_args` and any override `write_args` if provided.
            write_args (dict): Dictionary of any `write_args` which will
                override `self.write_args`
        """
        if df is None:
            raise ValueError(f"{self.__class__}.write: Requires df input as first argument.")

        if self.is_cached and not overwrite_cache:
            _logger.debug("Not writing Data Frame to disk as it already exists.")
            return df

        prewrite = self._pre_write_hook(df, overwrite_cache=overwrite_cache)

        write_df = self._write(prewrite, original_df=df)

        return self._post_write_hook(write_df)

    def _pre_read_hook(self):
        """
        Used for setting variables/verifying paths etc.
        """
        # kwargs = {**self.read_args, **kwargs}
        return None

    def _read(self, **kwargs) -> "pd.DataFrame":
        """
        Inner read function.
        Can take data from _pre_read_hook via 'preread' argument.
        """
        preread = kwargs.pop("preread", None)

        # Add passed in kwargs to the default read_args.
        kwargs = {**self.read_args, **kwargs}

        return self.read_func(self.path, **kwargs)

    def _post_read_hook(self, df: "pd.DataFrame", **kwargs) -> "pd.DataFrame":
        # kwargs = {**self.read_args, **kwargs}
        return df

    def _pre_write_hook(self, df: "pd.DataFrame", **kwargs) -> "pd.DataFrame":
        # kwargs = {**self.prewrite_args, **kwargs}
        return df

    def _write(self, df: "pd.DataFrame", **kwargs) -> "pd.DataFrame":
        """
        Writes DataFrame (`df`) to cache if it is not None,
        otherwise writes original_df= argument.
        """
        odf = kwargs.pop("original_df", None)
        if df is None:
            df = odf

        if df is None:
            raise ValueError(f"{self.__class__}._write: Requires non-null DataFrame input as first argument.")

        # Add passed in kwargs to the default write_args.
        kwargs = {**self.write_args, **kwargs}

        self.write_func(df, self.path, **kwargs)

        return df

    def _post_write_hook(self, df: "pd.DataFrame", **kwargs) -> "pd.DataFrame":
        """
        Runs after _write(), and returns the dataframe.

        Can be changed to just return df if desired. But this might result in
        different DataFrame being returned after the first write versus the
        first read.
        """
        # kwargs = {**self.write_args, **kwargs}
        # return df
        return self.read()

    def delete_cache(self, backup="date") -> None:
        """
        Method for deleting cached file if it exists.

        Args:
            backup (bool | str): Flag to delete cache, if it exists. Can pass in string to add to the old cache file as backup, or 'date' to add the modified date to the old cache file. If False, just deletes the cache file.
        """
        if not backup:
            try:
                _logger.debug("Deleting cache file %r", self.path)
                os.remove(self.path)
            except FileNotFoundError:
                pass
            return
        # Backup the old cache file
        if backup == "date":
            backup = dt.datetime.fromtimestamp(Path(self.path).stats().st_mtime).strftime("%Y-%m-%d")
        elif backup is True:
            backup = "backup"

        _ext = ''.join(Path(self.path).suffixes)
        _newp = str(self.path).replace(_ext, f".{backup}{_ext}")
        try:
            _logger.debug("Backing up cache file %r to %r", self.path, _newp)
            os.rename(self.path, _newp)
        except FileNotFoundError:
            pass

    @property
    def is_cached(self) -> bool:
        """
        Boolean value for whether cached file exists at `path`.
        """
        return os.path.exists(self.path)

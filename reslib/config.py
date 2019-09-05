# -*- coding: utf-8 -*-

"""
********************************
Reslib Config (reslib.config)
********************************

This module facilitates reading configurations from file, and provides some
defaults based on 'best practices' a la
`Cookiecutter Data Science <http://drivendata.github.io/cookiecutter-data-science/>`__.

The Config object contains all the configuration values for a given project.
The values are accessable in python as dictionary objects as well as attributes.
This is to say that the following little example will work::

    config = Config()
    assert(config['DATA_DIR'] == config.DATA_DIR)

NOTE: The config object is a Singleton, and is only ever initialized once.
Subsequent initialization must happen manually, but will propegate across
all instances of the config object. See below for a solution if you do not
want this behavior.


Loading the config file:
------------------------
The config can be loaded two ways (three if you count accepting defaults):

#. The config file can be written as a JSON file, whereby all CAPITAL
    keys will be imported into the Config object.
#. The config file can be written as a Python file, which will be eval-ed
    and then all CAPITAL keys will be imported into the Config object.


Finding the config file:
------------------------
The config file will be searched for by taking the pwd, and looking for the
``file_name`` all the way up the directory tree until it hits the root.
If no ``file_name`` is found, the Config object uses some sane default values.
These defaults can be seen in the code.

The file name of the config file defaults to ``reslib.config.[py|json]``.


Removing the Singleton functionality:
-------------------------------------
The Config object is a singleton, meaning there's only one copy of its data
in memory (effectively). Below is an example of what this means::

    # fileA.py -- runs first
    config = Config('myproject.json')
    config['NEW_VAR'] = 'new value'

    # fileB.py -- runs second
    config = Config('other_name_ignored.py')
    print(config['NEW_VAR'])
    # --> 'new value'

    # other_name_ignored.py -- doesn't run
    NEW_VAR = 'ignored var'

If you wish to have multiple configs for multiple parts of your program,
I suggest two solutions:

    #. Manual prefixing: PARTA_ROOT_PATH = 'folder for part A/data/'
    #. Make your own config object. Inherit this object with just an
        ``def __init__``, but drop the: self.__dict__ = self.__borg_data::

            class MultiConfig(reslib.config.Config):
                def __init__(self, config_name=None, config_path=None, **kwargs):
                    dict.__init__(self, kwargs or {})
                    self.config_path = config_path or self._get_config_path(config_name)
                    self._populate_from_file(self.config_path, **kwargs)

:copyright: (c) 2019 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

# STDlib imports
import os
import logging
import json

# 3rd party package imports


logger = logging.getLogger(__name__)

class Config:
    """
    The config object for a project, which has config values as both
    dictionary objects as well as attributes.
    """

    __borg_data = {} # http://code.activestate.com/recipes/66531/
    __is_initialized = False

    def __init__(self, config_name=None, config_path=None, **kwargs):
        """
        Create config object. Allows for passing additional config objects via
        keyword arguments, which will override the default values or those found
        in the config file.

        Args:
            config_name: name of config file. Name can include or exclude
                ``.json`` or ``.py``, both are tried (in that order)
                if ``config_name`` alone isn't found.
            config_path: Full path of the config file. If this is provided,
                ``config_name`` is ignored.
            **kwargs: Optional additional keyword arguments, for which the
                CAPITAL keys will be added to the config object, overriding the
                config file when keys are present in both.
        """
        # Borg pattern for singletons
        self.__dict__ = self.__borg_data

        if not self.__is_initialized:
            # Set the config_path based on input arguments (or default)
            self.config_path = config_path or self._get_config_path(config_name)

            # Load config file if found
            self._populate_from_file(self.config_path, silent=True)

            # Load overrides (does nothing if none provided)
            self._populate_from_dict(kwargs)

            self.__is_initialized = True


    def __getitem__(self, key):
        return getattr(self, key)


    def __setitem__(self, key, value):
        setattr(self, key, value)


    def __repr__(self):
        return "Config loaded from: {}\nKeys: {}".format(
            self.config_path, [k for k in self.__dict__.keys() if k.isupper()])


    def _get_config_path(self, config_name="reslib.config"):
        """
        Find the config file by name. The config file will be searched for by
        taking the current working directory, and looking for the `config_name`
        all the way up the directory tree until it hits the root.

        If no ``config_name`` is provided, the name defaults to: 'reslib.config'

        Args:
            config_name: name of config file. Name can include or exclude
                ``.json`` or ``.py``, both are tried (in that order)
                if ``config_name`` alone isn't found.

        Returns:
            Path of the found config file, or None.
        """
        if config_name is None:
            config_name="reslib.config"

        extension_order = ("", ".json", ".py")

        last_dir = None
        this_dir = os.path.abspath(config_name)

        while last_dir != this_dir:
            # Search dir for config_name (then plus extensions)
            for ext in extension_order:
                check_path = os.path.join(this_dir, config_name + ext)
                if os.path.exists(check_path):
                    return check_path

            last_dir, this_dir = this_dir, os.path.dirname(this_dir)

    def _get_dict_from_file(self, config_path, **kwargs):
        """
        Make a dictionary from a python or json file, based on extension.
        Only includes keys which are CAPITALIZED.

        NOTE: A python config file is ``eval``-ed, so this is potentially an
        attack vector. Please don't load a python config file you aren't
        completely comfortable with.

        Args:
            config_path: Full path of the config file.
            **kwargs: Optional read-arguments passed to ``open``.
        Returns:
            dict: Dictionary of KEY:value pairs where KEY is all CAPITALIZED
                keys found in the Python/JSON file.
        Raises:
            ValueError: If the config file doesn't have .json or .py extension.
        """
        if config_path is None:
            return {}

        ext = os.path.splitext(config_path)[-1]

        # Load json
        if ext == '.json':
            with open(config_path, mode="r", **kwargs) as fh:
                obj = json.load(fh)
        elif ext == '.py':
            with open(config_path, mode="rb", **kwargs) as fh:
                obj = {}
                exec(compile(fh.read(), config_path, "exec"), obj)
        else:
            raise ValueError("Config file extension unrecognized. Expected "
                             ".json or .py, got %s", ext)

        return {k:v for k,v in obj.items() if k.isupper()}

    def _populate_from_file(self, config_path=None, silent=False, **kwargs):
        """
        Populate the Config from a python or json file, based on extension.
        Only includes keys which are CAPITALIZED.

        NOTE: A python config file is ``eval``-ed, so this is potentially an
        attack vector. Please don't load a python config file you aren't
        completely comfortable with.

        Args:
            config_path: Full path of the config file. Default:
                ``config_path`` from the Config object.
            silent: Boolean flag for whether FileNotFoundError is raised if the
                ``config_path`` doesn't exist.
            **kwargs: Optional read-arguments passed to ``open``.
        Returns:
            dict: Dictionary which was added to the Config object.
        Raises:
            FileNotFoundError: If file isn't found, and ``silent`` is False.
            ValueError: If the config file doesn't have .json or .py extension.
        """
        try:
            obj = self._get_dict_from_file(config_path=config_path, **kwargs)
        except FileNotFoundError:
            logger.warning("Load Config error: file not found: %s", config_path)
            if not silent:
                raise

        return self._populate_from_dict(obj)

    def _populate_from_dict(self, config_dict):
        """
        Populate the Config from a dictionary.

        NOTE: A python config file is ``eval``-ed, so this is potentially an
        attack vector. Please don't load a python config file you aren't
        completely comfortable with.

        Args:
            config_path: Full path of the config file. Default:
                ``config_path`` from the Config object.
            **kwargs: Optional read-arguments passed to ``open``.
        Returns:
            dict: Dictionary which was added to the Config object.
        """
        obj = {}
        for k,v in config_dict.items():
            if k.isupper():
                self[k] = obj[k] = v

        return obj

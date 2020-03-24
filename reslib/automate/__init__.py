# -*- coding: utf-8 -*-

"""
********************************
reslib.automate
********************************

This package facilitates using doit (pydoit.org) to automate data pipelines.

:copyright: (c) 2019 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# Stdlib imports
import os as _os
import re as _re
# import sys
# import inspect
# import pkgutil

# Third party imports
# import pandas as pd

# from doit.task import Task
# from doit.dependency import UptodateCalculator
# from doit.cmd_base import ModuleTaskLoader, NamespaceTaskLoader
# from doit.doit_cmd import DoitMain

# Library imports
# from reslib.config import Config


def cleanpath(path_to_clean, re_pathsep=_re.compile(r"[\\]+"), re_dotstart=_re.compile(r"^./|/$")):
    """Clean a path by replacing ``\\\\`` with ``/``, and removing beginning ``./`` and trailing ``/``"""
    if path_to_clean is None:
        return None
    return re_dotstart.sub("", re_pathsep.sub("/", str(path_to_clean))).strip()


def pathjoin(*paths):
    """Join, normalize, and clean a list of paths, allowing for ``None``s (filtered out)"""
    return cleanpath(_os.path.normpath(_os.path.join(*filter(None, paths))))


# These have to go after cleanpath/pathjoin, because scanner/code_parser use both
from reslib.automate.code_parser import (SAS, Stata, Notebook, Python, Manual)
from reslib.automate.scanner import DependencyScanner

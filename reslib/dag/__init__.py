# -*- coding: utf-8 -*-

"""
********************************
reslib.dag
********************************

This package facilitates evaluating Directed Acyclic Graphs (DAGs).

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""
# Stdlib imports
import os as _os
import re as _re

# Third party imports
# import pandas as pd

# Library imports
# from reslib.config import Config


def cleanpath(path_to_clean, re_pathsep=_re.compile(r"[\\]+"), re_dotstart=_re.compile(r"^./|/$")):
    """Clean a path by replacing ``\\\\`` with ``/``, and removing beginning ``./`` and trailing ``/``"""
    if path_to_clean is None:
        return None
    return re_dotstart.sub("", re_pathsep.sub("/", str(path_to_clean))).strip()


def pathjoin(*paths):
    """Join, normalize, and clean a list of paths, allowing for ``None``s (filtered out)"""
    try:
        return cleanpath(_os.path.normpath(_os.path.join(*filter(None, paths))))
    except TypeError as e:
        # If paths aren't strings, or empty, error out
        raise ValueError(f"All paths must be strings or None, and at least one non-empty: {paths}") from e



# These have to go after cleanpath/pathjoin, because scanner/code_parser use both
from reslib.dag.code_parser import (SAS, Stata, Notebook, Python, Manual, Latex, StataNotebook)
from reslib.dag.scanner import DependencyScanner
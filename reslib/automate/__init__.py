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

# Third party imports

# Library imports



def cleanpath(path_to_clean, re_pathsep=_re.compile(r"[\\]+"), re_dotstart=_re.compile(r"^./|/$")):
    """Clean a path by replacing ``\\\\`` with ``/``, and removing beginning ``./`` and trailing ``/``"""
    if path_to_clean is None:
        return None
    return re_dotstart.sub("", re_pathsep.sub("/", str(path_to_clean)))


def pathjoin(*paths):
    """Join, normalize, and clean a list of paths, allowing for ``None``s (filtered out)"""
    return cleanpath(_os.path.normpath(_os.path.join(*filter(None, paths))))


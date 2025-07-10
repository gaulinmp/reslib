# -*- coding: utf-8 -*-

"""
********************************
reslib.automate
********************************

DEPRECATED: This module has been renamed to reslib.dag.

Please update your imports:
    from reslib.automate import ... -> from reslib.dag import ...

This backwards compatibility shim will be removed in a future version.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "The reslib.automate module has been renamed to reslib.dag. "
    "Please update your imports: 'from reslib.automate import ...' -> 'from reslib.dag import ...'. "
    "This backwards compatibility shim will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2
)

# Import everything from the new dag module for backwards compatibility
from reslib.dag import *
from reslib.dag import cleanpath, pathjoin
from reslib.dag.code_parser import (
    CodeParser, SAS, Stata, Notebook, Python, Manual, Latex, StataNotebook
)
from reslib.dag.scanner import DependencyScanner

# Re-export all public APIs for backwards compatibility
__all__ = [
    'cleanpath',
    'pathjoin', 
    'CodeParser',
    'SAS',
    'Stata', 
    'Notebook',
    'Python',
    'Manual',
    'Latex',
    'StataNotebook',
    'DependencyScanner'
]
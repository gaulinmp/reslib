# -*- coding: utf-8 -*-

"""
********************************
reslib
********************************

This package provides code to facilitate common Accounting/Finance research tasks, such as reading from WRDS or scraping EDGAR data.

:copyright: (c) 2025 by Maclean Gaulin.
:license: MIT, see LICENSE for more details.
"""

from .__version__ import (__title__, __description__, __url__, __version__,
                          __build__, __author__, __author_email__,
                          __license__, __copyright__)


# Add NullHandler default logging handler because Requests says so.
import logging as __log
__log.getLogger(__name__).addHandler(__log.NullHandler())

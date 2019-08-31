.. _quickstart:

Quickstart
=============================

ResLib can be used solely to provide a flexible dependency checking engine.
This usecase is covered in the `Pipelines`_ section.

Additionally, ResLib has functionality to aid a project which uses
Python in some or all of its data-cleaning or analysis, covered in
`Python Library`_.


Pipelines
-----------------------------

Pipelines in ResLib are facilitated by `Doit`_, which is extended herein to
allow for parsing and extracting dependencies from source code in other
languages through the use of specific comment tags.



Python Library
-----------------------------

ResLib provides functionality for downloading data from common sources
(`WRDS`_, `EDGAR`_, etc.), as well as class objects for caching datasets
to disk.




.. _Doit : https://pydoit.org
.. _WRDS : https://wrds-www.wharton.upenn.edu/
.. _EDGAR : https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm

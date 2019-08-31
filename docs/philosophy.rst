.. _philosophy:

Philosophy of ResLib
=============================

ResLib is intended to provide common tools to Accounting and Finance
Researchers, whether they use Python, SAS, Stata, or any other language.
The intent of this library is not solely to provide Python tools, but generic
tools to facilitate reproducible research.

The core of this philosophy is centered around data pipelines.
This is the idea of 'source-to-table', which requires a sequential order
of code which transforms raw data into tables.

Pipelines
-----------------------------

In the software world, Makefiles are often used to achieve this centralization
of process flow, and a key feature in these Makefiles is dependency checking.
Dependency checking in a chaotic data environment like that in which
we research is somewhat harder.

My solution to this is to use a Python package called `Doit`_, which combines
dependency graph creation with automatic running.
In the course of trying to find a solution to this problem, I looked into
the famous alternatives:
`Airflow <https://airflow.apache.org/>`__ and
`Luigi <https://luigi.readthedocs.io/en/stable/index.html>`__.
The decision to go with Doit was based on the specific use case of
Accounting research, in which multiple data sources, languages, and coauthors
were all involved.
Doit seemed to present the most parsimonious way of defining `tasks`, which
represent any atomic step in the pipeline.


In the current implementation, these tasks can be defined simply by adding
comment lines to any source-code, such as SAS or Stata files.
For example:

.. code-block:: stata

   /* INPUT: Data/interim/dataset_from_python.dta */

This would then be picked up by Doit, which would recognize that the file that
created `dataset_from_python.dta` is a dependency of the Stata code,
and make sure that it is run first (but not rerun unnecessarily).


Python
-----------------------------

The rest of the library is aimed at providing beneficial tools for developing
in `Python`_.




.. _Doit : https://pydoit.org

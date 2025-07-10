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

Dependency tracking of pipelines in ResLib is inspired by `Doit`_.
The DependencyScanner allows for parsing and extracting dependencies from
source code through the use of specific comment tags.

There are three such comments tags:

* ``INPUT`` for when reading in a dataset
* ``INPUT_FILE`` for when running another file inline, like a load-function in python or running a do file in Stata
* ``OUTPUT`` for defining which datasets the current file creates.

The DependencyScanner matches inputs to outputs to creat the DAG.
The idea is that if you add ``INPUT``/``OUTPUT`` comments to your existing code,
crating the DAG graph should be trivially easy, as the simple example below shows.

As an example of how to integrate the depenedncy scanning into your project,
assume the following three files exist in the ~/projects/example folder:

.. code-block:: sas
   :caption: code/data.sas

    /* INPUT_DATASET funda.sas7bdat */
    PROC EXPORT DATA=funda OUTFILE= "data/stata_data.dta"; RUN;
    /* OUTPUT: stata_data.dta */


.. code-block:: stata
   :caption: code/load_data.do

    /* INPUT_DATASET stata_data.dta */
    use "data/stata_data.dta", clear


.. code-block:: stata
   :caption: code/analysis.do

    /* INPUT_FILE: load_data.do */
    do "code/load_data.do"


Then the following would create a graph output at ``pipeline.png``:


.. code-block:: python
   :caption: dag.py

    from reslib.dag import DependencyScanner, SAS, Stata

    # Just scan for SAS and Stata code, located in the code directory.
    ds = DependencyScanner(project_root='~/projects/example/',
                           code_path_prefix='code', data_path_prefix='data')
    print(ds)
    ds.DAG_to_file("pipeline.png")

will print the following:

.. code-block:: text
    Stata:: analysis.do
            INPUT FILES (found 1):
                    load_data.do
            INPUT DATASETS (found 0):
            OUTPUT DATASETS (found 0):
            Project Root: ~/projects/example
            Code Prefix: code
            Data Prefix: data
    Stata:: load_data.do
            INPUT FILES (found 0):
            INPUT DATASETS (found 1):
                    stata_data.dta
            OUTPUT DATASETS (found 0):
            Project Root: ~/projects/example
            Code Prefix: code
            Data Prefix: data
    Sas:: data.sas
            INPUT FILES (found 0):
            INPUT DATASETS (found 1):
                    funda.sas7bdat
            OUTPUT DATASETS (found 1):
                    stata_data.dta
            Project Root: ~/projects/example
            Code Prefix: code
            Data Prefix: data

And create ``pipeline.png`` with the DAG graphed:

.. image:: _static/pipeline.png

The colors in the image are intended to be informative at a glance. Yellow
indicates that a dependency doesn't have a parent (only applies to datasets).
Green indicates the files which were scanned, and grey indicates the datasets.
Lastly, if the pipeline isn't a DAG because it is cyclic (File A creates a
dataset for File B, which creates a dataset used in File A), the background will
turn red, for ERROR!!!

Individual files can be omitted from the scan by adding the comment
``RESLIB_IGNORE: True`` (will take ``true``, ``yes``, or ``1``, all case insensitive).


The ``DependencyScanner`` has many settings, the salient ones being:

* ``project_root``: Path to 'root' directory, from which relative paths to input/output file dependencies will be calculated. (Default = ``'.'``)
* ``code_path_prefix``: Path to 'code' directory, which is relative to the ``project_root``. To make the full path to the code file, the prefix will be added to project root, then to the path defined in the INPUT/OUTPUT: comment. (Default = ``None``)
* ``data_path_prefix``: Path to 'data' directory, which is relative to the ``project_root``. To make the full path to the data file, the prefix will be added to project root, then to the path defined in the INPUT/OUTPUT: comment. (Default = ``None``)





Python Library
-----------------------------

ResLib provides functionality for downloading data from common sources
(`WRDS`_, `EDGAR`_, etc.), as well as class objects for caching datasets
to disk.




.. _Doit : https://pydoit.org
.. _NetworkX : http://networkx.github.io
.. _graphviz (Python) : https://github.com/xflr6/graphviz
.. _graphviz : https://www.graphviz.org/
.. _WRDS : https://wrds-www.wharton.upenn.edu/
.. _EDGAR : https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm

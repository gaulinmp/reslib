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

In the software world, Makefiles are often used to achieve automation
of process flow, and a key feature in these Makefiles is dependency checking.
Dependency checking in a chaotic data environment like that in which
we research is somewhat harder.

My first solution to this was to use a Python package called `Doit`_, which combines
dependency graph creation with automatic running.
In the course of trying to find a solution to this problem, I looked into
the popular options like `Airflow`_ and `Luigi`_.
The decision to go with Doit was based on the specific use case of
Accounting research, in which multiple data sources, languages, and coauthors
were all involved.
Doit seemed to present the most parsimonious way of defining `tasks`, which
represent any atomic step in the pipeline.

I quickly ran into limitations with Doit, specifically the graphing of output.
Thus my second iteration was to manually make a parser to create a Directed
Acyclic Graph (DAG) representation of the dependency tree with `NetworkX`_.
I then use `graphviz (Python)`_ to make the plots. This requires the native
`graphviz`_ to be installed, which probably means using Linux (unless you have
mad Windows skills).


The dependencies can be defined simply by adding comment lines to source-code,
such as SAS or Stata files.
For example:

.. code-block:: stata

   /* INPUT_DATASET interim/dataset_from_python.dta */
   use "interim/dataset_from_python.dta"

There are three such comments: ``INPUT`` (for when reading in a dataset),
``INPUT_FILE`` (for when running another file inline, like a load-function in
python or running a do file in Stata), and ``OUTPUT`` for defining which
datasets the current file creates.
The DependencyScanner matches inputs to outputs to creat the DAG.


Python
-----------------------------

The rest of the library is aimed at providing beneficial tools for developing
in `Python`_.




.. _Doit : https://pydoit.org
.. _Airflow : https://airflow.apache.org
.. _Luigi : https://luigi.readthedocs.io/en/stable/index.html
.. _NetworkX : http://networkx.github.io
.. _graphviz (Python) : https://github.com/xflr6/graphviz
.. _graphviz : https://www.graphviz.org/

# Research Library

Research Library (reslib) is a library for facilitating simple, repeatable, and best-practice guided academic research.
It is a hodgepodge of functionality, with the aim of asymptoting to coherence.

This software is provided as is, hopefully it's useful!


## Dependency tracking
One central tenant of good research is that it be repeatable.
To this goal, `reslib` tries to make tracking the data pipeline as simple and useful as possible.
The implementation utilized herein was motivated by [doit](https://pydoit.org/usecases.html), which is like a pythonic Makefile.
I removed the automation part (for now?), and stuck with the dependency tracking.


Assume the following three files exist in the ~/projects/example folder:

``code/data.sas``:

```sas
    /* INPUT_DATASET funda.sas7bdat */
    PROC EXPORT DATA=funda OUTFILE= "data/stata_data.dta"; RUN;
    /* OUTPUT: stata_data.dta */
```

``code/load_data.do``:

```stata
    /* INPUT_DATASET stata_data.dta */
    use "data/stata_data.dta", clear
```

``code/analysis.do``:

```stata
    /* INPUT_FILE: load_data.do */
    do "code/load_data.do"
```

Then the following would create a graph output at ``pipeline.png``::

```python
    from reslib.automate import DependencyScanner, SAS, Stata

    # Just scan for SAS and Stata code, located in the code directory.
    ds = DependencyScanner(project_root='~/projects/example/',
                           code_path_prefix='code', data_path_prefix='data')
    print(ds)
    ds.DAG_to_file("pipeline.png")
```

will print the following:

```txt
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
```

And create ``pipeline.png`` with the DAG graphed:

![pipeline.png](docs/_static/pipeline.png)


Individual files can be omitted from the scan by adding the comment
``RESLIB_IGNORE: True`` (will take ``true``, ``yes``, or ``1``, all case insensitive).


The ``DependencyScanner`` has many settings, the salient ones being:

  - `project_root`: Path to 'root' directory, from which relative paths to input/output file dependencies will be calculated. (Default = ``'.'``)
  - `code_path_prefix`: Path to 'code' directory, which is relative to the `project_root`. To make the full path to the code file, the prefix will be added to project root, then to the path defined in the INPUT/OUTPUT: comment. (Default = ``None``)
  - `data_path_prefix`: Path to 'data' directory, which is relative to the `project_root`. To make the full path to the data file, the prefix will be added to project root, then to the path defined in the INPUT/OUTPUT: comment. (Default = ``None``)

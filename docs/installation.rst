.. _installation:

Installation of ResLib
=============================

This part of the documentation covers the installation of ResLib.
The first step to using any software package is getting it properly installed.
If you don't have Python already, start with `Step 0 <#step-0-install-python>`_
at the bottom, then continue on with the pip install.

$ pip install
-----------------------------

Sorry, ResLib isn't on `Pypi <https://pypi.org/>`__ yet, but probably one day.
For now, use the installation from github method below.

$ pip install from github
-----------------------------

To install ResLib, simply run this simple command in your terminal of choice:


.. code-block:: bash

    $ [if conda env named reslib exists:] conda activate reslib
    $ git clone https://github.com/gaulinmp/reslib.git
    $ cd reslib
    $ pip install -r requirements.txt
    $ pip install .

If you want to be fancy and get all the updates, you can install in
'editable' mode, which links the reslib source code, and allows for git-pull
updates:

.. code-block:: bash

    $ [if conda env named reslib exists:] conda activate reslib
    $ git clone https://github.com/gaulinmp/reslib.git
    $ cd reslib
    $ pip install -r requirements.txt
    $ pip install -e .
    $ git pull

Now, all future updates to the github repository can be retrieved with a
simple `git pull`.

Step 0: Install Python
-----------------------------
If you don't have `Python <https://www.python.org>`_ installed (today's
the day!), I strongly recommend using
`miniconda <https://docs.conda.io/en/latest/miniconda.html>`__.
Once you have Python installed (congrats!) I suggest using conda environments:

.. code-block:: bash

    $ conda create -n reslib

This will create an environment named `reslib`, which is now empty, and ready
to be filled with wonderful python packages.
Congrats! 🍻

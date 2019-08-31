.. _installation:

Installation of ResLib
=============================

This part of the documentation covers the installation of ResLib.
The first step to using any software package is getting it properly installed.


Install Python
-----------------------------
If you don't have `Python <https://www.python.org>`_ installed (today's 
the day!), I strongly recommend using 
`miniconda <https://docs.conda.io/en/latest/miniconda.html>`__.
Once you have Python installed (congrats!) I suggest using conda environments:

    $ conda create -n reslib

This will create an environment named `reslib`, which is now empty, and ready
to be filled with wonderful python packages.
So let's fill it with the packages that will help you do amazing research in
a snap.


$ pip install from source
-----------------------------

To install ResLib, simply run this simple command in your terminal of choice::

    $ [if conda env named reslib exists:] conda activate reslib
    $ git clone https://github.com/gaulinmp/reslib.git
    $ cd reslib
    $ pip install -r requirements.txt
    $ pip install .

If you want to be all fancy and get all the updates, you can install in
'editable' mode, which links the reslib source code, and allows for git-pull
updates:

    $ [if conda env named reslib exists:] conda activate reslib
    $ git clone https://github.com/gaulinmp/reslib.git
    $ cd reslib
    $ pip install -r requirements.txt
    $ pip install -e .
    $ git pull

Now, all future updates to the github repository can be retrieved with a
simple `git pull`.

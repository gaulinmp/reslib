.. reslib documentation master file, created by
   sphinx-quickstart on Fri Aug 30 21:29:42 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

ResLib: Research Library
==================================

Release v\ |version|. (:ref:`installation`)

Research Library is intended to help Accounting and Finance researchers
do efficient, repeatable research.


This documentation provides an overview of ResLib, starting with the
:ref:`philosophy`, and then diving into the nuts and bolts with the
:ref:`installation` and then the :ref:`quickstart`.
The rest of the docs describe each component of ResLib in detail,
with a full reference in the :ref:`api` section.

ResLib relies heavily on `Doit`_ for pipeline automation, and `Pandas`_ for
data wrangling. The documentation for these libraries can be found at:


- `Doit documentation <https://pydoit.org/contents.html>`_
- `Pandas documentation <https://pandas.pydata.org/pandas-docs/stable/index.html>`_

.. _Doit : https://pydoit.org
.. _Pandas : https://pandas.pydata.org


User Guide
------------------

This part of the documentation, which is mostly prose, begins with some
background information about ResLib, then focuses on step-by-step
instructions for project development with ResLib.

.. toctree::
   :maxdepth: 2

   philosophy
   installation
   quickstart


API
-----------------
This part of the documentation dives into the gory detail of ResLib in
all it's paltry equivalent of glory.

.. toctree::
   :maxdepth: 3

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



Thanks to `Requests <https://github.com/psf/requests/tree/master/docs>`__
and `Flask <https://github.com/pallets/flask/tree/1.1.x/docs>`__ for their
wonderful programming and documentation examples. I stole shamelessly from
the examples set by both.

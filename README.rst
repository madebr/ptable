=============
About ptable2
=============

ptable2 is a simple Python library designed to make it quick and easy to
represent tabular data in visually appealing ASCII tables, originally
forked from `PTable <https://github.com/kxxoling/PTable/>`_.

.. image:: https://travis-ci.com/madebr/ptable2.svg
    :target: https://travis-ci.com/madebr/ptable2
    :alt: Build Status

.. image:: https://coveralls.io/repos/github/madebr/ptable2/badge.svg?branch=develop
    :target: https://coveralls.io/github/madebr/ptable2?branch=develop
    :alt: Coverage


Installation
============

As ptable2 is a fork of PrettyTable, and compatible with all its APIs,
so ptable2 is usage is the same as PrettyTable, and the installation
would cover on the original PrettyTable.

As always, you can install ptable2 in 3 ways.

Via pip (recommend)::

    pip install ptable2

From source::

    python setup.py install


Quick start
===========

ptable2 supports two kinds of usage:


As a library
------------

ptable2 library API is almost as PrettyTable, you can import the same API from
``prettytable`` library:

.. code-block:: python

    from prettytable import PrettyTable
    x = PrettyTable()

A better hosted document is hosted on `readthedocs <https://ptable2.readthedocs.io/en/latest//>`_.


As command-line tool
--------------------

This is an original function of ptable2, can be used as ``ptable`` command:

.. code-block:: shell

    ptable --csv somefile.csv

or a Unix style pipe:

.. code-block:: shell

    cat somefile.csv | ptable

Will both print a ASCII table in terminal.



Relative links
==============

* `Source Code (GitHub) <https://github.com/madebr/ptable2>`__
* `RTFD <https://ptable2.readthedocs.io/en/latest/>`__
* `PyPI <https://pypi.python.org/pypi/ptable2/>`__
* `PrettyTable <https://code.google.com/p/prettytable/>`_

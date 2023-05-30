.. upsilonconf documentation master file, created by
   sphinx-quickstart on Sun Mar 19 10:41:09 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=========================
UpsilonConf documentation
=========================

UpsilonConf is a simple configuration library written in Python.
Its main goal is to provide a convenient interface to work with configuration-like objects.
A few handy tools to help with IO are also included.

.. toctree::
   :maxdepth: 2

   usage
   api
   about

Some Features
-------------

UpsilonConf is supposed to be a simple library in terms of code and usability.
Nevertheless, the configuration objects in UpsilonConf come with some useful features:

 - ``dict`` with attribute access
 - ``object`` with indexing
 - ``tuple`` of string for hierarchical indexing
 - ``.``-separated strings for hierarchical indexing
 - flattening of hierarchical configs with ``.``-separated strings as keys
 - properly hashable *frozen* configuration type
 - minimal (i.e. no) requirements for installation
 - readily available conda package
 - ...

Furthermore, the included I/O tools should enable:

 - reading/writing various file formats
 - reading configuration directories
 - retrieving configs from the command line

If you think a particular feature is missing or something is not working as expected,
feel free to let me know by `creating an issue`_.

.. _creating an issue: https://github.com/hoedt/upsilonconf/issues

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

.. _pybacktrack_getting_started:

Getting Started
===============

.. contents::
   :local:
   :depth: 2

Requirements
------------

PyBacktrack depends on:

- `NumPy <http://www.numpy.org/>`_
- `SciPy <https://www.scipy.org/>`_
- `Generic Mapping Tools (GMT) <http://gmt.soest.hawaii.edu/>`_ (>=5.0.0)
- `PyGPlates <http://www.gplates.org/>`_

`NumPy` and `SciPy` are automatically installed by `pip`, however `GMT` (version 5 or above) and `pyGPlates` need to be manually installed.

Installation
------------

To install the latest development version (requires Git), run:
::

  pip install "git+https://github.com/EarthByte/pyBacktrack.git#egg=pybacktrack"

.. note:: | You may need to update your `Git` if you receive an error ending with "*tlsv1 alert protocol version*".
          | This is apparently due to an `update on GitHub <https://blog.github.com/2018-02-23-weak-cryptographic-standards-removed>`_

This will automatically install the `NumPy` and `SciPy` requirements. However `GMT` and `pyGPlates` need to be manually installed.

.. note:: A `PyPi <https://pypi.org/>`_ package, that can be installed with `pip install pybacktrack`, will soon be provided.
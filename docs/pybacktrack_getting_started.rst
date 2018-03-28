.. _pybacktrack_getting_started:

Getting Started
===============

.. contents::
   :local:
   :depth: 2


.. _pybacktrack_requirements:

Requirements
------------

PyBacktrack depends on:

- `NumPy <http://www.numpy.org/>`_
- `SciPy <https://www.scipy.org/>`_
- `Generic Mapping Tools (GMT) <http://gmt.soest.hawaii.edu/>`_ (>=5.0.0)
- `PyGPlates <http://www.gplates.org/>`_

`NumPy` and `SciPy` are automatically installed by `pip` (see :ref:`pyBacktrack installation <pybacktrack_installation>`), however `GMT` (version 5 or above) and `pyGPlates` need to be manually installed.

`GMT` is called via the command-line (shell) and so just needs to be in the PATH in order for `pyBacktrack` to find it.
Also ensure that version 5 or above (supports NetCDF version 4) is installed since the :mod:`bundled grid files in pyBacktrack<pybacktrack.bundle_data>` are in NetCDF4 format.

`pyGPlates` is not currently installable as a package and so needs to be in the python path (sys.path or PYTHONPATH).
Installation instructions are available `here <http://www.gplates.org/docs/pygplates/index.html>`_.


.. _pybacktrack_installation:

Installation
------------

To install the latest development version (requires Git), run:
::

  pip install "git+https://github.com/EarthByte/pyBacktrack.git#egg=pybacktrack"

.. note:: | You may need to update your `Git` if you receive an error ending with ``tlsv1 alert protocol version``.
          | This is apparently due to an `update on GitHub <https://blog.github.com/2018-02-23-weak-cryptographic-standards-removed>`_.

This will automatically install the `NumPy` and `SciPy` requirements. However `GMT` and `pyGPlates` need to be manually installed (see :ref:`pyBacktrack requirements <pybacktrack_requirements>`).

.. note:: A `PyPi <https://pypi.org/>`_ package, that can be installed with ``pip install pybacktrack``, will soon be provided.


.. _pybacktrack_a_backtracking_example:

A Backtracking Example
----------------------

Once :ref:`installed <pybacktrack_installation>` the ``pybacktrack`` Python package is available to:

- use built-in module scripts (inside ``pybacktrack``), or
- ``import pybacktrack`` into your own script.

The following example is used to demonstrate both approaches. It backtracks an ocean drill site and saves the output to a text file by:

- reading the ocean drill site file ``tests/data/ODP-114-699-Lithology.txt``,
- backtracking it using:

  * the ``M2`` dynamic topography model, and
  * the ``Haq87_SealevelCurve_Longterm`` sea-level model,

- writing the amended drill site to ``tests/data/ODP-114-699_backtrack_amended.txt``, and
- writing the following columns to ``tests/data/ODP-114-699_backtrack_decompat.txt``:

  * age
  * compacted_depth
  * compacted_thickness
  * decompacted_thickness
  * decompacted_density
  * water_depth
  * tectonic_subsidence
  * lithology

.. note:: | The input and output filenames specified above are available in the ``tests/data/`` directory of the pyBacktrack source code.
          | This example also uses the :mod:`bundled data<pybacktrack.bundle_data>` internally.

.. _pybacktrack_use_a_builtin_module_script:

Use a built-in module script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since the :mod:`backtrack<pybacktrack.backtrack>` module (inside ``pybacktrack``) can be run as a script,
we can invoke it on the command-line using ``python -m pybacktrack.backtrack`` followed by command line options that are specific to that module.

To see its command-line options, run:

.. code-block:: python

    python -m pybacktrack.backtrack --help

The backtracking example can now be demonstrated by running:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w tests/data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o tests/data/ODP-114-699_backtrack_amended.txt \
        -- \
        tests/data/ODP-114-699_backtrack_decompat.txt

.. _pybacktrack_import_into_your_own_script:

Import into your own script
^^^^^^^^^^^^^^^^^^^^^^^^^^^

An alternative to running a built-in script is to write your own script (using a text editor) that imports ``pybacktrack`` modules and
calls their functions.

The following Python code does the same as the :ref:`built-in script<pybacktrack_use_a_builtin_module_script>` by calling the
:func:`pybacktrack.backtrack.backtrack_and_write_decompacted` function:

.. code-block:: python

    import pybacktrack.backtrack as backtrack
    
    # Input and output filenames (available in 'tests/data/' directory of pyBacktrack source code).
    input_well_filename = 'tests/data/ODP-114-699-Lithology.txt'
    amended_well_output_filename = 'tests/data/ODP-114-699_backtrack_amended.txt'
    decompacted_output_filename = 'tests/data/ODP-114-699_backtrack_decompat.txt'
    
    # Read input well file, and write amended well and decompacted results to output files.
    backtrack.backtrack_and_write_decompacted(
        decompacted_output_filename,
        input_well_filename,
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        # The columns in decompacted output file...
        decompacted_columns=[backtrack.COLUMN_AGE,
                             backtrack.COLUMN_COMPACTED_DEPTH,
                             backtrack.COLUMN_COMPACTED_THICKNESS,
                             backtrack.COLUMN_DECOMPACTED_THICKNESS,
                             backtrack.COLUMN_DECOMPACTED_DENSITY,
                             backtrack.COLUMN_WATER_DEPTH,
                             backtrack.COLUMN_TECTONIC_SUBSIDENCE,
                             backtrack.COLUMN_LITHOLOGY],
        # Might be an extra stratigraphic well layer added from well bottom to ocean basement...
        ammended_well_output_filename=amended_well_output_filename)

If you save the above code to a file called ``my_backtrack_script.py`` then you can run it as:

.. code-block:: python

    python my_backtrack_script.py

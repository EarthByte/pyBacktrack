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

`NumPy` and `SciPy` are automatically installed by `pip` (see :ref:`installation <pybacktrack_install_pybacktrack>`), however `GMT` (version 5 or above) and `pyGPlates` need to be manually installed.

`GMT` is called via the command-line (shell) and so just needs to be in the PATH in order for `pyBacktrack` to find it.
Also ensure that version 5 or above (supports NetCDF version 4) is installed since the :ref:`bundled grid files in pyBacktrack<pybacktrack_bundle_data>` are in NetCDF4 format.

`pyGPlates` is not currently installable as a package and so needs to be in the python path (sys.path or PYTHONPATH).
Installation instructions are available `here <http://www.gplates.org/docs/pygplates/index.html>`_.


.. _pybacktrack_install_pybacktrack:

Install pyBacktrack
-------------------

To install the latest stable version, run:
::

  pip install pybacktrack

.. note:: | This will automatically install the `NumPy` and `SciPy` :ref:`requirements <pybacktrack_requirements>`.
          | However, as mentioned in :ref:`requirements <pybacktrack_requirements>`, `GMT` and `pyGPlates` still need to be manually installed.

To install the latest development version (requires Git on local system), run:
::

  pip install "git+https://github.com/EarthByte/pyBacktrack.git#egg=pybacktrack"

.. note:: | You may need to update your `Git` if you receive an error ending with ``tlsv1 alert protocol version``.
          | This is apparently due to an `update on GitHub <https://blog.github.com/2018-02-23-weak-cryptographic-standards-removed>`_.

...or download the `pyBacktrack source code <https://github.com/EarthByte/pyBacktrack>`_, extract to a local directory and run:
::

  pip install <path-to-local-directory>

.. _pybacktrack_install_example_data:

Install example data
--------------------

Before running the example below, or any of the :ref:`other examples <pygplates_examples>`, you'll also need to install the example data (from the pybacktrack package itself).
This assumes you've already :ref:`installed the pybacktrack package <pybacktrack_install_pybacktrack>`.

The following command installs the example data to a new sub-directory of your *current working directory* called ``pybacktrack_example_data``:

.. code-block:: python

    python -c "import pybacktrack.documentation; pybacktrack.documentation.install_example_data()"

.. note:: The *current working directory* is whatever directory you are in when you run the above command.

.. note:: | Alternatively you can choose a different sub-directory by providing an argument to the ``install_example_data()`` function above.
          | For example, ``python -c "import pybacktrack.documentation; pybacktrack.documentation.install_example_data('pybacktrack/example/data')"``
            creates a new sub-directory of your *current working directory* called ``pybacktrack/example/data``.
          | However the example below assumes the default directory (``pybacktrack_example_data``).

.. _pybacktrack_a_backtracking_example:

A Backtracking Example
----------------------

Once :ref:`installed <pybacktrack_install_pybacktrack>` the ``pybacktrack`` Python package is available to:

- use built-in module scripts (inside ``pybacktrack``), or
- ``import pybacktrack`` into your own script.

The following example is used to demonstrate both approaches. It backtracks an ocean drill site and saves the output to a text file by:

- reading the ocean drill site file ``pybacktrack_example_data/ODP-114-699-Lithology.txt``,

  .. note:: | This file is part of the :ref:`example data <pybacktrack_install_example_data>`.
            | However if you have your own ocean drill site file then you can substitute it in the example below if you want.

- backtracking it using:

  * the ``M2`` dynamic topography model, and
  * the ``Haq87_SealevelCurve_Longterm`` sea-level model,

- writing the amended drill site to ``ODP-114-699_backtrack_amended.txt``, and
- writing the following columns to ``ODP-114-699_backtrack_decompat.txt``:

  * age
  * compacted_depth
  * compacted_thickness
  * decompacted_thickness
  * decompacted_density
  * water_depth
  * tectonic_subsidence
  * lithology

.. _pybacktrack_use_a_builtin_module_script:

Use a built-in module script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Since there is a ``backtrack`` module inside ``pybacktrack`` that can be run as a script,
we can invoke it on the command-line using ``python -m pybacktrack.backtrack`` followed by command line options that are specific to that module.

To see its command-line options, run:

.. code-block:: python

    python -m pybacktrack.backtrack --help

The backtracking example can now be demonstrated by running the script as:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w pybacktrack_example_data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o ODP-114-699_backtrack_amended.txt \
        -- \
        ODP-114-699_backtrack_decompat.txt

.. _pybacktrack_import_into_your_own_script:

Import into your own script
^^^^^^^^^^^^^^^^^^^^^^^^^^^

An alternative to running a built-in script is to write your own script (using a text editor) that imports ``pybacktrack`` and
calls its functions.

The following Python code does the same as the :ref:`built-in script<pybacktrack_use_a_builtin_module_script>` by calling the
:func:`pybacktrack.backtrack_and_write_well` function:

.. code-block:: python

    import pybacktrack
    
    # Input and output filenames.
    input_well_filename = 'pybacktrack_example_data/ODP-114-699-Lithology.txt'
    amended_well_output_filename = 'ODP-114-699_backtrack_amended.txt'
    decompacted_output_filename = 'ODP-114-699_backtrack_decompat.txt'
    
    # Read input well file, and write amended well and decompacted results to output files.
    pybacktrack.backtrack_and_write_well(
        decompacted_output_filename,
        input_well_filename,
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        # The columns in decompacted output file...
        decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE,
                             pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY,
                             pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKTRACK_COLUMN_LITHOLOGY],
        # Might be an extra stratigraphic well layer added from well bottom to ocean basement...
        ammended_well_output_filename=amended_well_output_filename)

If you save the above code to a file called ``my_backtrack_script.py`` then you can run it as:

.. code-block:: python

    python my_backtrack_script.py

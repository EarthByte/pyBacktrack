.. _pygplates_overview:

Overview
========

This document gives a brief overview of the scripts inside the ``pybacktrack`` package.

.. contents::
   :local:
   :depth: 2

Running pyBacktrack
-------------------

Once :ref:`installed <pybacktrack_install_pybacktrack>`, the ``pybacktrack`` Python package is available to:

#. :ref:`run built-in scripts <pybacktrack_running_the_scripts_built_into_pybacktrack>` (inside ``pybacktrack``), or
#. ``import pybacktrack`` :ref:`into your own script <pybacktrack_running_your_own_script_that_imports_pybacktrack>`.

It is generally easier to run the built-in scripts since you only need to specify parameters on the command-line.

However you may need to create your own script if you want to combine ``pybacktrack`` functionality with
other research functionality. In this case it is generally better to ``import pybacktrack``, along with the
other modules, into your own script. This also gives a finer granularity of control compared to the command-line.

The following two sections give an overview of both approaches.

.. note:: | The input files used in the examples below are available in the example data.
          | Please ensure you have :ref:`installed the example data <pybacktrack_install_examples>` before running any of these examples.

.. _pybacktrack_running_the_scripts_built_into_pybacktrack:

Running the scripts built into pyBacktrack
------------------------------------------

PyBacktrack is a Python package containing modules. And each module can be run as a script using
``python -m pybacktrack.<module>`` followed by command line options that are specific to that module.
For example, the ``backtrack`` module can be run as ``python -m pybacktrack.backtrack ...``, or the ``backstrip`` module
can be run as ``python -m pybacktrack.backstrip ...``, with ``...`` replaced by command-line options.

The following sections give an introduction to each module.

.. note:: In each module you can use the ``--help`` option to see all available command-line options for that specific module.
          For example, ``python -m pybacktrack.backtrack --help`` describes all options available to the ``backtrack`` module.

.. _pybacktrack_running_the_backtrack_script:

backtrack
^^^^^^^^^

The ``backtrack`` module is used to find paleo water depths from a tectonic subsidence model
(such as an age-to-depth curve in ocean basins, or rifting near continental passive margins) and sediment decompaction over time.

This example takes an ocean drill site as input and outputs a file containing a backtracked water depth for each age in the drill site:

.. code-block:: python

    python -m pybacktrack.backtrack -w pybacktrack_examples/test_data/ODP-114-699-Lithology.txt -d age water_depth -- ODP-114-699_backtrack_decompat.txt

...where the ``-w`` option specifies the input drill site file ``pybacktrack_examples/test_data/ODP-114-699-Lithology.txt``, the ``-d`` option specifies
the desired columns (``age`` and ``water_depth``) of the output file, and ``ODP-114-699_backtrack_decompat.txt`` is the output file.

There are other command-line options available to the ``backtrack`` module (use the ``--help`` option to list them) but they all have default values and
hence only need to be specified if the default does not suit.

.. _pybacktrack_running_the_backstrip_script:

backstrip
^^^^^^^^^

The ``backstrip`` module is used to find tectonic subsidence (typically due to lithospheric stretching) from paleo water depths and sediment decompaction over time.

This example takes a passive margin site as input and outputs a file containing a backstripped tectonic subsidence for each age in the drill site:

.. code-block:: python

    python -m pybacktrack.backstrip -w pybacktrack_examples/test_data/DSDP-36-327-Lithology.txt -d age average_tectonic_subsidence -- DSDP-36-327_backstrip_decompat.txt

...where the ``-w`` option specifies the input drill site file ``pybacktrack_examples/test_data/ODP-114-699-Lithology.txt``, the ``-d`` option specifies
the desired columns (``age`` and ``average_tectonic_subsidence``) of the output file, and ``DSDP-36-327_backstrip_decompat.txt`` is the output file.

There are other command-line options available to the ``backstrip`` module (use the ``--help`` option to list them) but they all have default values and
hence only need to be specified if the default does not suit.

.. note:: ``average_tectonic_subsidence`` is an *average* of the minimum and maximum tectonic subsidences, that are in turn a result
          of the minimum and maximum water depths specified in the drill site file.

.. _pybacktrack_running_the_age_to_depth_script:

age_to_depth
^^^^^^^^^^^^

The ``age_to_depth`` module is used to convert ocean floor age to ocean basement depth (in ocean basins).

This example takes an input file containing a column of ages, and outputs a file containing two columns (age and depth):

.. code-block:: python

    python -m pybacktrack.age_to_depth -- pybacktrack_examples/test_data/test_ages.txt test_ages_and_depths.txt

Here the input file ``pybacktrack_examples/test_data/test_ages.txt`` contains ages in the first (and only) column.
If they had been in another column, for example if there were other unused columns, then we would need to specify the age column with the ``-a`` option.

The output file ``test_ages_and_depths.txt`` contains ages in the first column and depths in the second column.
To reverse this order you can use the ``-r`` option.

Here the conversion was performed using the *default* age-to-depth ocean model ``GDH1``
(Stein and Stein 1992, "Model for the global variation in oceanic depth and heat flow with lithospheric age")
since the ``-m`` command-line option was not specified. However you can specify the alternate model ``CROSBY_2007``
(Crosby et al. 2006, "The relationship between depth, age and gravity in the oceans") using ``-m CROSBY_2007``.
Or you can specify your own age-to-depth model by specifying a file containing an age column and a depth column
followed by two integers representing the age and depth column indices. For example, if you have your own age-to-depth file
called ``age-depth-model.txt`` where age is in the first column and depth is in the second column then you can specify this
using ``-w age-depth-model.txt 0 1``.

.. note:: Use ``python -m pybacktrack.age_to_depth --help`` to see a description of all command-line options.

.. _pybacktrack_running_the_interpolate_script:

interpolate
^^^^^^^^^^^

The ``interpolate`` module can perform linear interpolation of any piecewise linear function ``y=f(x)``.
As such it can be used for any type of data.

However, for pyBacktrack, it is typically used to interpolate a model where age is a function of depth (``age=function(depth)``).
Here the age-depth model is specified as a file containing a column of depths and a column of ages that forms a piecewise linear function of age with depth.
Then another file specifies the input depths (which are typically stratigraphic layer boundaries).
Finally a third file is created containing the output ages, where each interpolated age is a result of querying the piecewise linear function using a depth:

.. code-block:: python

    python -m pybacktrack.util.interpolate -cx 1 -cy 0 -c pybacktrack_examples/test_data/ODP-114-699_age-depth-model.txt -- pybacktrack_examples/test_data/ODP-114-699_strat_boundaries.txt ODP-114-699_strat_boundaries_depth_age.txt

Here the ``age=function(depth)`` model is specified with the ``-c``, ``-cx`` and ``-cy`` options.
The ``-c`` option specifies the ``pybacktrack_examples/test_data/ODP-114-699_age-depth-model.txt`` file containing a column of ages and a column of depths.
The ``-cx`` and ``-cy`` options specify the *x* and *y* columns of the model function ``y=f(x)``.
These default to ``0`` and ``1`` respectively. However since age (*y*) happens to be in the first column (``0``) and depth (*x*) in the second column (``1``)
we must swap the default order of column indices using ``-cx 1 -cy 0``.

The input depths are in ``pybacktrack_examples/test_data/ODP-114-699_strat_boundaries.txt`` in the first (and only) column.
If they had been in another column, for example if there were other unused columns, then we would need to specify the depth column with the ``-ix`` option.

The output depths and (interpolated) ages are written to the output file ``ODP-114-699_strat_boundaries_depth_age.txt``.
The first column contains depth and the second column contains (interpolated) age. To reverse this order you can use the ``-r`` option.

.. note:: Use ``python -m pybacktrack.util.interpolate --help`` to see a description of all command-line options.

.. _pybacktrack_running_your_own_script_that_imports_pybacktrack:

Running your own script that imports pyBacktrack
------------------------------------------------

An alternative to :ref:`running the built-in scripts <pybacktrack_running_the_scripts_built_into_pybacktrack>`
is to write your own script (using a text editor) that imports ``pybacktrack`` and calls its :ref:`functions <pybacktrack_reference>`.
You might do this if you want to combine pyBacktrack functionality with other research functionality into a single script.

The following shows Python source code that is equivalent to the above :ref:`examples running built-in scripts <pybacktrack_running_the_scripts_built_into_pybacktrack>`.

If you save any of the code examples below to a file called ``my_script.py`` then you can run that example as:

.. code-block:: python

    python my_script.py

backtrack
^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_backtracking>`):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backtrack_and_write_well(
        'ODP-114-699_backtrack_decompat.txt',
        'pybacktrack_examples/test_data/ODP-114-699-Lithology.txt',
        decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE,
                             pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH])

...is equivalent to :ref:`running the backtrack script example <pybacktrack_running_the_backtrack_script>`:

.. code-block:: python

    python -m pybacktrack.backtrack -w pybacktrack_examples/test_data/ODP-114-699-Lithology.txt -d age water_depth -- ODP-114-699_backtrack_decompat.txt

backstrip
^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_backstripping>`):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backstrip_and_write_well(
        'DSDP-36-327_backstrip_decompat.txt',
        'pybacktrack_examples/test_data/DSDP-36-327-Lithology.txt',
        decompacted_columns=[pybacktrack.BACKSTRIP_COLUMN_AGE,
                             pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE])

...is equivalent to :ref:`running the backstrip script example <pybacktrack_running_the_backstrip_script>`:

.. code-block:: python

    python -m pybacktrack.backstrip -w pybacktrack_examples/test_data/DSDP-36-327-Lithology.txt -d age average_tectonic_subsidence -- DSDP-36-327_backstrip_decompat.txt

age_to_depth
^^^^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_converting_age_to_depth>`):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.convert_age_to_depth_files(
        'pybacktrack_examples/test_data/test_ages.txt',
        'test_ages_and_depths.txt')

...is equivalent to :ref:`running the age-to-depth script example <pybacktrack_running_the_age_to_depth_script>`:

.. code-block:: python

    python -m pybacktrack.age_to_depth -- pybacktrack_examples/test_data/test_ages.txt test_ages_and_depths.txt

interpolate
^^^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_utilities>`):

.. code-block:: python

    import pybacktrack
    
    # Read the age-depth function age=function(depth) from age-depth curve file.
    # Ignore the x (depth) and y (age) values read from file by using '_'.
    age_depth_function, _, _ = pybacktrack.read_interpolate_function('pybacktrack_examples/test_data/ODP-114-699_age-depth-model.txt', 1, 0)
    
    # Convert x (depth) values in 1-column input file to x (depth) and y (age) values in 2-column output file.
    pybacktrack.interpolate_file(
        age_depth_function,
        'pybacktrack_examples/test_data/ODP-114-699_strat_boundaries.txt',
        'ODP-114-699_strat_boundaries_depth_age.txt')

...is equivalent to :ref:`running the interpolate script example <pybacktrack_running_the_interpolate_script>`:

.. code-block:: python

    python -m pybacktrack.util.interpolate -cx 1 -cy 0 -c pybacktrack_examples/test_data/ODP-114-699_age-depth-model.txt -- pybacktrack_examples/test_data/ODP-114-699_strat_boundaries.txt ODP-114-699_strat_boundaries_depth_age.txt

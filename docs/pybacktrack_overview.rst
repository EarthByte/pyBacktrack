.. _pybacktrack_overview:

Overview
========

This document gives a brief overview of the scripts inside the ``pybacktrack`` package.

.. contents::
   :local:
   :depth: 2

Running pyBacktrack
-------------------

Once :ref:`installed <pybacktrack_installation>`, the ``pybacktrack`` Python package is available to:

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
``python -m pybacktrack.<module>_cli`` followed by command line options that are specific to that module.
For example, the ``backtrack`` module can be run as ``python -m pybacktrack.backtrack_cli ...``, or the ``backstrip`` module
can be run as ``python -m pybacktrack.backstrip_cli ...``, with ``...`` replaced by command-line options.

The following sections give an introduction to each module.

.. note:: In each module you can use the ``--help`` option to see all available command-line options for that specific module.
          For example, ``python -m pybacktrack.backtrack_cli --help`` describes all options available to the ``backtrack`` module.

.. _pybacktrack_running_the_backtrack_script:

backtrack
^^^^^^^^^

The ``backtrack`` module is used to find paleo water depths from a tectonic subsidence model
(such as an age-to-depth curve in ocean basins, or rifting near continental passive margins) and sediment decompaction over time.

This example takes an ocean drill site as input and outputs a file containing a backtracked water depth for each age in the drill site:

.. code-block:: python

    python -m pybacktrack.backtrack_cli -w pybacktrack_examples/test_data/ODP-114-699-Lithology.txt -d age water_depth -- ODP-114-699_backtrack_decompacted.txt

...where the ``-w`` option specifies the input drill site file ``pybacktrack_examples/test_data/ODP-114-699-Lithology.txt``, the ``-d`` option specifies
the desired columns (``age`` and ``water_depth``) of the output file, and ``ODP-114-699_backtrack_decompacted.txt`` is the output file.

There are other command-line options available to the ``backtrack`` module (use the ``--help`` option to list them) but they all have default values and
hence only need to be specified if the default does not suit.

.. seealso:: :ref:`pybacktrack_backtrack`

.. _pybacktrack_running_the_backstrip_script:

backstrip
^^^^^^^^^

The ``backstrip`` module is used to find tectonic subsidence (typically due to lithospheric stretching) from paleo water depths and sediment decompaction over time.

This example takes a passive margin site as input and outputs a file containing a backstripped tectonic subsidence for each age in the drill site:

.. code-block:: python

    python -m pybacktrack.backstrip_cli -w pybacktrack_examples/test_data/sunrise_lithology.txt -l primary extended -d age average_tectonic_subsidence -- sunrise_backstrip_decompacted.txt

...where the ``-w`` option specifies the input drill site file ``pybacktrack_examples/test_data/sunrise_lithology.txt``, the ``-l`` option specifies the
lithology definitions, the ``-d`` option specifies the desired columns (``age`` and ``average_tectonic_subsidence``) of the output file,
and ``sunrise_backstrip_decompacted.txt`` is the output file.

.. note:: It is necessary to specify the bundled ``primary`` and ``extended`` lithology definitions, with ``-l primary extended``, because the input drill site
          references lithologies in both lithology definition files. See :ref:`pybacktrack_bundled_lithology_definitions`. This is unlike the
          :ref:`backtracking example <pybacktrack_running_the_backtrack_script>` above that only references the ``primary`` lithologies, and hence does not need
          to specify lithology definitions because ``primary`` is the default (when ``-l`` is not specified).

.. note:: ``average_tectonic_subsidence`` is an *average* of the minimum and maximum tectonic subsidences, that are in turn a result
          of the minimum and maximum water depths specified in the drill site file.

There are other command-line options available to the ``backstrip`` module (use the ``--help`` option to list them) but they all have default values and
hence only need to be specified if the default does not suit.

.. seealso:: :ref:`pybacktrack_backstrip`

.. _pybacktrack_running_the_paleo_bathymetry_script:

paleo_bathymetry
^^^^^^^^^^^^^^^^

The ``paleo_bathymetry`` module is used to generate paleo bathymetry grids by reconstructing and backtracking present-day sediment-covered crust through time.

This example generates paleobathymetry grids at 12 minute resolution from 0Ma to 240Ma in 1Myr increments using the ``M7`` :ref:`dynamic topography model <pybacktrack_dynamic_topography>`
and the ``GDH1`` :ref:`oceanic subsidence model <pybacktrack_oceanic_subsidence>`:

.. code-block:: python

    python -m pybacktrack.paleo_bathymetry_cli -gm 12 -ym M7 -m GDH1 --use_all_cpus -- 240 paleo_bathymetry_12m_M7_GDH1

...where the ``-gm`` option specifies the grid spacing (in minutes), the ``-ym`` specifies the dynamic topography model, the ``-m`` option specifies the
oceanic subsidence model, the ``--use_all_cpus`` option uses all CPUs (it also accepts an optional number of CPUs) and
the generated paleobathymetry grid files are named ``paleo_bathymetry_12m_M7_GDH1_<time>.nc``.

There are other command-line options available to the ``paleo_bathymetry`` module (use the ``--help`` option to list them) but they all have default values and
hence only need to be specified if the default does not suit.

.. seealso:: :ref:`pybacktrack_paleo_bathymetry`

.. _pybacktrack_running_the_age_to_depth_script:

age_to_depth
^^^^^^^^^^^^

The ``age_to_depth`` module is used to convert ocean floor age to ocean basement depth (in ocean basins).

This example takes an input file containing a column of ages, and outputs a file containing two columns (age and depth):

.. code-block:: python

    python -m pybacktrack.age_to_depth_cli -- pybacktrack_examples/test_data/test_ages.txt test_ages_and_depths.txt

Here the input file ``pybacktrack_examples/test_data/test_ages.txt`` contains ages in the first (and only) column.
If they had been in another column, for example if there were other unused columns, then we would need to specify the age column with the ``-a`` option.

The output file ``test_ages_and_depths.txt`` contains ages in the first column and depths in the second column.
To reverse this order you can use the ``-r`` option.

There are three built-in age-to-depth ocean models:

* ``RHCW18`` - Richards et al. (2020) `Structure and dynamics of the oceanic lithosphere-asthenosphere system <https://doi.org/10.1016/j.pepi.2020.106559>`_

* ``CROSBY_2007`` - Crosby, A.G., (2007) Aspects of the relationship between topography and gravity on the Earth and Moon, PhD thesis

* ``GDH1`` - Stein and Stein (1992) `Model for the global variation in oceanic depth and heat flow with lithospheric age <https://doi.org/10.1038/359123a0>`_

Here the conversion was performed using the *default* model ``RHCW18`` since the ``-m`` command-line option was not specified.
However you can specify the alternate ``CROSBY_2007`` model using ``-m CROSBY_2007`` (or ``GDH1`` using ``-m GDH1``).

.. note:: The default age-to-depth model was updated in pyBacktrack version 1.4. It is now ``RHCW18``. Previously it was ``GDH1``.

Or you can use your own age-to-depth model by specifying a file containing an age column and a depth column
followed by two integers representing the age and depth column indices. For example, if you have your own age-to-depth file
called ``age-depth-model.txt`` where age is in the first column and depth is in the second column then you can specify this
using ``-w age-depth-model.txt 0 1``.

.. note:: Use ``python -m pybacktrack.age_to_depth_cli --help`` to see a description of all command-line options.

.. _pybacktrack_running_the_stratigraphic_depth_to_age_script:

stratigraphic_depth_to_age
^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``stratigraphic_depth_to_age`` module is used to convert stratigraphic depths to ages using a depth-to-age model.

Here the depth-to-age model is specified as a file containing a column of ages and a column of depths that forms a piecewise linear function of age with depth
(a model where age is a function of depth ``age=function(depth)``).
Then another file specifies the input stratigraphic depths that you wish to convert to ages.
Finally a third file is created containing the input depths and output ages, where each interpolated output age is a result of querying the piecewise linear function using the input depth:

.. code-block:: python

    python -m pybacktrack.stratigraphic_depth_to_age_cli -m pybacktrack_examples/test_data/Site1089B_age_depth.txt -- pybacktrack_examples/test_data/Site1089B_strat_depth.txt Site1089B_age_strat_depth.txt

Here the ``age=function(depth)`` model is specified with the ``-m`` option, where the ``pybacktrack_examples/test_data/Site1089B_age_depth.txt`` file
contains a column of ages and a column of depths (by default age is the first column and depth the second but you can optionally choose any column for either).

The input stratigraphic depths are in ``pybacktrack_examples/test_data/Site1089B_strat_depth.txt`` and must be in the *first* column.
Any text after the depth value in a row (eg, lithologies) is copied to the output file. Also any metadata at the top of the file is copied to the output file.

The interpolated ages and associated depths are written to the output file ``Site1089B_age_strat_depth.txt``.
The first column contains (interpolated) age and the second column contains depth. To reverse this order you can use the ``-r`` option.

.. note:: Use ``python -m pybacktrack.stratigraphic_depth_to_age_cli --help`` to see a description of all command-line options.

.. _pybacktrack_running_the_interpolate_script:

interpolate
^^^^^^^^^^^

The ``interpolate`` module can perform linear interpolation of any piecewise linear function ``y=f(x)``.
As such it can be used for any type of data.

Here the ``y=f(x)`` model is specified as a file containing a column of *x* values and a column of *y* values that forms a piecewise linear function of *y* with *x*.
Then another file specifies the input *x* values. Finally a third file is created containing the input *x* values and the output *y* values,
where each interpolated output *y* value is a result of querying the piecewise linear function using an input *x* value:

.. code-block:: python

    python -m pybacktrack.util.interpolate_cli -cx 1 -cy 0 -c function_y_of_x.txt -- input_x_values.txt output_x_y_values.txt

Here the ``y=f(x)`` model is specified with the ``-c``, ``-cx`` and ``-cy`` options.
The ``-c`` option specifies the file ``function_y_of_x.txt`` containing a column of ``y`` values followed by a column of ``x`` values.
The ``-cx`` and ``-cy`` options specify the *x* and *y* columns of the model function ``y=f(x)``.
These default to ``0`` and ``1`` respectively. However if *y* happens to be in the first column (``0``) and *x* in the second column (``1``)
then you can swap the default order of column indices using ``-cx 1 -cy 0``.

The input ``x`` values are in ``input_x_values.txt`` in the first column (by default).
If they had been in another column, for example if there were other unused columns, then we would need to specify the *x* column with the ``-ix`` option.

The output (interpolated) *y* values (and associated *x* values) are written to the output file ``output_x_y_values.txt``.
The first column contains the *x* values and the second column contains the (interpolated) *y* values. To reverse this order you can use the ``-r`` option.

.. note:: Use ``python -m pybacktrack.util.interpolate_cli --help`` to see a description of all command-line options.

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
        'ODP-114-699_backtrack_decompacted.txt',
        'pybacktrack_examples/test_data/ODP-114-699-Lithology.txt',
        decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE,
                             pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH])

...is equivalent to :ref:`running the backtrack script example <pybacktrack_running_the_backtrack_script>`:

.. code-block:: python

    python -m pybacktrack.backtrack_cli -w pybacktrack_examples/test_data/ODP-114-699-Lithology.txt -d age water_depth -- ODP-114-699_backtrack_decompacted.txt

.. note:: The ``backtrack`` module is covered in more detail :ref:`here <pybacktrack_backtrack>`.

backstrip
^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_backstripping>`):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backstrip_and_write_well(
        'sunrise_backstrip_decompacted.txt',
        'pybacktrack_examples/test_data/sunrise_lithology.txt',
        lithology_filenames=[pybacktrack.PRIMARY_BUNDLE_LITHOLOGY_FILENAME,
                             pybacktrack.EXTENDED_BUNDLE_LITHOLOGY_FILENAME],
        decompacted_columns=[pybacktrack.BACKSTRIP_COLUMN_AGE,
                             pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE])

...is equivalent to :ref:`running the backstrip script example <pybacktrack_running_the_backstrip_script>`:

.. code-block:: python

    python -m pybacktrack.backstrip_cli -w pybacktrack_examples/test_data/sunrise_lithology.txt -l primary extended -d age average_tectonic_subsidence -- sunrise_backstrip_decompacted.txt

.. note:: The ``backstrip`` module is covered in more detail :ref:`here <pybacktrack_backstrip>`.

paleo_bathymetry
^^^^^^^^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_paleobathymetry>`):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.reconstruct_paleo_bathymetry_grids(
        'paleo_bathymetry_12m_M7_GDH1',
        0.2,  # degrees (same as 12 minutes)
        240,
        dynamic_topography_model='M7',
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_MODEL_GDH1,
        use_all_cpus=True)  # can also be an integer (the number of CPUs to use)

...is equivalent to :ref:`running the paleobathymetry script example <pybacktrack_running_the_paleo_bathymetry_script>`:

.. code-block:: python

    python -m pybacktrack.paleo_bathymetry_cli -gm 12 -ym M7 -m GDH1 --use_all_cpus -- 240 paleo_bathymetry_12m_M7_GDH1

.. note:: The ``paleo_bathymetry`` module is covered in more detail :ref:`here <pybacktrack_paleo_bathymetry>`.

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

    python -m pybacktrack.age_to_depth_cli -- pybacktrack_examples/test_data/test_ages.txt test_ages_and_depths.txt

stratigraphic_depth_to_age
^^^^^^^^^^^^^^^^^^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_converting_stratigraphic_depth_to_age>`):

.. code-block:: python

    import pybacktrack
    
    # Read the age=f(depth) function, where 'x' is depth and 'y' is age (in the returned function y=f(x)).
    age_column_index = 0    # age is in the first column
    depth_column_index = 1  # depth is in the second column
    # Ignore the x (depth) and y (age) values read from file by using '_'.
    depth_to_age_model, _, _ = pybacktrack.read_interpolate_function('pybacktrack_examples/test_data/Site1089B_age_depth.txt', depth_column_index, age_column_index)
    
    # Convert depth values in input file to age and depth values in output file.
    pybacktrack.convert_stratigraphic_depth_to_age_files(
        'pybacktrack_examples/test_data/Site1089B_strat_depth.txt',
        'Site1089B_age_strat_depth.txt',
        depth_to_age_model)

...is equivalent to :ref:`running the stratigraphic depth-to-age script example <pybacktrack_running_the_stratigraphic_depth_to_age_script>`:

.. code-block:: python

    python -m pybacktrack.stratigraphic_depth_to_age_cli -m pybacktrack_examples/test_data/Site1089B_age_depth.txt -- pybacktrack_examples/test_data/Site1089B_strat_depth.txt Site1089B_age_strat_depth.txt

interpolate
^^^^^^^^^^^

The following Python source code (using :ref:`these functions <pybacktrack_reference_utilities>`):

.. code-block:: python

    import pybacktrack
    
    # Read the y=f(x) function from a 2-column file.
    # Ignore the x and y values read from file by using '_'.
    function_y_of_x, _, _ = pybacktrack.read_interpolate_function('function_y_of_x.txt', 1, 0)
    
    # Convert x values in a 1-column input file to x and y values in a 2-column output file.
    pybacktrack.interpolate_file(
        function_y_of_x,
        'input_x_values.txt',
        'output_x_y_values.txt')

...is equivalent to :ref:`running the interpolate script example <pybacktrack_running_the_interpolate_script>`:

.. code-block:: python

    python -m pybacktrack.util.interpolate_cli -cx 1 -cy 0 -c function_y_of_x.txt -- input_x_values.txt output_x_y_values.txt

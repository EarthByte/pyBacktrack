.. _pybacktrack_paleo_bathymetry:

Paleobathymetry
===============

.. contents::
   :local:
   :depth: 2

.. _pygplates_paleo_bathymetry_overview:

Overview
--------

The ``paleo_bathymetry`` module is used to generate paleo bathymetry grids by reconstructing and backtracking present-day sediment-covered crust through time.

.. _pygplates_running_paleo_bathymetry:

Running paleobathymetry
-----------------------

You can either run ``paleo_bathymetry`` as a built-in script, specifying parameters as command-line options (``...``):

.. code-block:: python

    python -m pybacktrack.paleo_bathymetry_cli ...

...or ``import pybacktrack`` into your own script, calling its functions and specifying parameters as function arguments (``...``):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.reconstruct_paleo_bathymetry_grids(...)

.. note:: You can run ``python -m pybacktrack.paleo_bathymetry_cli --help`` to see a description of all command-line options available, or
          see the :ref:`paleobathymetry reference section <pybacktrack_reference_paleobathymetry>` for documentation on the function parameters.

.. _pygplates_paleo_bathymetry_example:

Example
^^^^^^^

To generate paleobathymetry grids at 12 minute resolution from 0Ma to 240Ma in 1Myr increments, we can run it from the command-line as:

.. code-block:: python

    python -m pybacktrack.paleo_bathymetry_cli \
        -gm 12 \
        -ym M7 \
        -m GDH1 \
        --use_all_cpus \
        -- \
        240 paleo_bathymetry_12m_M7_GDH1

...where the ``-gm`` option specifies the grid spacing (12 minutes),
the ``-ym`` specifies the ``M7`` :ref:`dynamic topography model <pygplates_dynamic_topography>`,
the ``-m`` option specifies the ``GDH1`` :ref:`oceanic subsidence model <pygplates_oceanic_subsidence>`,
the ``--use_all_cpus`` option uses all CPUs (so it runs faster) and
the generated paleobathymetry grid files are named ``paleo_bathymetry_12m_M7_GDH1_<time>.nc``.

...or write some Python code to do the same thing:

.. code-block:: python

    import pybacktrack
    
    pybacktrack.reconstruct_paleo_bathymetry_grids(
        'paleo_bathymetry_12m_M7_GDH1',
        '0.2',  # degrees (same as 12 minutes)
        240,
        dynamic_topography_model='M7',
        ocean_age_to_depth_model=pybacktrack.AGE_TO_DEPTH_MODEL_GDH1,
        use_all_cpus=True)

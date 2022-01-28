.. _pybacktrack_paleo_bathymetry:

Paleobathymetry
===============

.. contents::
   :local:
   :depth: 2

.. _pybacktrack_paleo_bathymetry_overview:

Overview
--------

The ``paleo_bathymetry`` module is used to generate paleo bathymetry grids by reconstructing and backtracking present-day sediment-covered crust through time.

.. _pybacktrack_running_paleo_bathymetry:

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

.. _pybacktrack_paleo_bathymetry_example:

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
the ``-ym`` specifies the ``M7`` :ref:`dynamic topography model <pybacktrack_dynamic_topography>`,
the ``-m`` option specifies the ``GDH1`` :ref:`oceanic subsidence model <pybacktrack_oceanic_subsidence>`,
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

.. _pybacktrack_paleo_bathymetry_output:

Paleobathymetry output
----------------------

.. _pybacktrack_paleo_bathymetry_gridding_procedure:

Paleobathymetry gridding procedure
----------------------------------

We use the builtin rift start/end age grids along with the existing rifting model and sediment decompaction functionality in pyBacktrack to generate paleo bathymetry grids (typically in 1 Myr intervals).
The ``paleo_bathymetry`` module has similar options to the ``backtrack`` module (such as options for present-day age/topography/crustal-thickness/sediment-thickness grids, dynamic-topography/sea-level models, etc).
Except, instead of a single point location for a well site, a uniform grid of points containing sediment (inside valid regions of the total sediment thickness grid) are backtracked to obtain gridded paleo water depths through time.
As with regular backtracking, those sediment grid points lying inside the age grid (valid regions) use an oceanic subsidence model and those outside use a continental rifting model.
However, in lieu of explicitly providing the rift start and end ages, as for a 1D well site, each 2D grid point samples the builtin rift start/end age grids.
Each grid point is also assigned a plate ID (using static polygons) and reconstructed back through time.
All grid points have a single lithology, initially of the total sediment thickness (sampled at each grid location) at present day and progressively decompacted back in geological time.
Loading each reconstructed point’s decompacted thickness onto its modelled tectonic subsidence (oceanic or continental) back through time, along with the effects of dynamic topography and sea level models, reveals its history of water depths.
The reconstructed locations of all grid points and their reconstructed bathymetries are combined, at each reconstruction time, to create a history of paleo bathymetry grids.

.. _pybacktrack_builtin_rift_gridding_procedure:

Builtin rift gridding procedure
-------------------------------

PyBacktrack comes with two builtin grids containing rift start and end ages on submerged continental crust at 5 minute resolution.
This is used during paleobathymetry gridding to obtain the rift periods of gridded points on continental crust.
It is also used during regular backtracking to obtain the rift period of a drill site on continental crust (when it is not specified in the drill site file or on the command-line).

The rift grids cover all submerged continental crust, not just those areas that have undergone rifting.
Submerged continental crust is where the total sediment thickness grid contains valid values but the age grid does not (ie, submerged crust that is non oceanic).

The rift grids were generated with ``misc/generate_rift_grids.py`` using the Müller 2019 deforming plate model:

* Müller, R. D., Zahirovic, S., Williams, S. E., Cannon, J., Seton, M., Bower, D. J., Tetley, M. G., Heine, C., Le Breton, E., Liu, S., Russell, S. H. J., Yang, T., Leonard, J., and Gurnis, M. (2019),
  `A global plate model including lithospheric deformation along major rifts and orogens since the Triassic. Tectonics, vol. 38, <https://doi.org/10.1029/2018TC005462>`_.

This paragraph gives a brief overview of rift gridding...
First, grid points on continental crust that have undergone *extensional* deformation (rifting) during their most recent deformation period have their rift start and end ages calculated
as the start and end of that most recent deformation period (for each grid point).
Next, grid points on continental crust that have undergone *contractional* deformation during their most recent deformation period have their rift periods set to default values (currently 200 to 0 Ma)
to model these complex areas with simple rifting (despite a rifting model no longer strictly applying).
Next, the non-deforming grid points on continental crust obtain their rift period from the nearest grid deforming grid points.
This ensures all continental crust contains a rift period and hence can be used to generate paleobathymetry grids from all present day continental crust.
Finally, only those continental grid points that are submerged are stored in the final rift grids since we only need to backtrack submerged crust.

This paragraph gives a more detailed explanation of how deformation is used in ``misc/generate_rift_grids.py``...
The script allows one to specify a total sediment thickness grid and an age grid (defaulting to those included with pyBacktrack).
Grid points are uniformly generated in longitude/latitude space on continental crust.
Next pyGPlates is used to load the Müller 2019 topological plate model (containing rigid plate polygons and deforming networks) and reconstruct these continental grid points on back through geological time.
Note that plate IDs do not need to be explicitly assigned in order to be able to reconstruct because recent functionality in pyGPlates, known as *reconstructing by topologies*, essentially continually assigns plate IDs
using the topological plate polygons and deforming networks while each grid point is reconstructed back through time.
During this reconstruction each grid point is queried (at 1Myr intervals) whether it passes through a deforming network.
The time at which a reconstructed grid point first encounters a deforming network (going backward in time) becomes its potential rift end time.
Following that point further back in time we find when it first exits a deforming network (again going backward in time), which becomes its potential rift start time.
We also keep track of a crustal stretching factor through time for each grid point so we can distinguish between extensional and contractional deformation.

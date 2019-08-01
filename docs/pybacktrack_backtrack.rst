.. _pygplates_backtrack:

Backtrack
=========

.. contents::
   :local:
   :depth: 2

.. _pygplates_backtrack_overview:

Overview
--------

The ``backtrack`` module is used to find paleo water depths from a tectonic subsidence model, and sediment decompaction over time.
The tectonic subsidence model is either an age-to-depth curve (in ocean basins) or rifting (near continental passive margins).

.. _pygplates_running_backtrack:

Running backtrack
-----------------

You can either run ``backtrack`` as a built-in script, specifying parameters as command-line options (``...``):

.. code-block:: python

    python -m pybacktrack.backtrack ...

...or ``import pybacktrack`` into your own script, calling its functions and specifying parameters as function arguments (``...``):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backtrack_and_write_well(...)

.. note:: You can run ``python -m pybacktrack.backtrack --help`` to see a description of all command-line options available, or
          see the :ref:`backtracking reference section <pybacktrack_reference_backtracking>` for documentation on the function parameters.

.. _pygplates_backtrack_example:

Example
^^^^^^^

For example, revisiting our :ref:`backtracking example <pybacktrack_a_backtracking_example>`, we can run it from the command-line as:

.. code-block:: python

    python -m pybacktrack.backtrack \
        -w pybacktrack_examples/test_data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o ODP-114-699_backtrack_amended.txt \
        -- \
        ODP-114-699_backtrack_decompat.txt

...or write some Python code to do the same thing:

.. code-block:: python

    import pybacktrack
    
    # Input and output filenames.
    input_well_filename = 'pybacktrack_examples/test_data/ODP-114-699-Lithology.txt'
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

.. note:: The drill site file ``pybacktrack_examples/test_data/ODP-114-699-Lithology.txt`` is part of the :ref:`example data <pybacktrack_install_examples>`.

.. _pygplates_backtrack_output:

Backtrack output
----------------

For each stratigraphic layer in the input drill site file, ``backtrack`` can write one or more parameters to an output file.

For example, if we run the :ref:`above example <pygplates_backtrack_example>` on ODP drill site 699:

.. include:: ../pybacktrack/test_data/ODP-114-699-Lithology.txt
   :literal:

...then we will get the following amended drill site output file:

.. include:: ../pybacktrack/test_data/ODP-114-699_backtrack_amended.txt
   :literal:

.. note:: The extra :ref:`base sediment layer <pygplates_base_sediment_layer>`.

...as well as the following decompacted output file:

.. include:: ../pybacktrack/test_data/ODP-114-699_backtrack_decompat.txt
   :literal:

.. note:: The *age*, *compacted_depth* and *lithology* columns are the same as the *bottom_age*,
          *bottom_depth* and *lithology* columns in the input drill site (except there is also a row associated with the surface age).

The *compacted_thickness* column is the total sediment thickness (601 metres - see :ref:`base sediment layer <pygplates_base_sediment_layer>`
of amended drill site above) minus *compacted_depth*.
The *decompacted_thickness* column is the thickness of all sediment at the associated age. In other words, at each consecutive age
another stratigraphic layer is essentially removed, allowing the underlying layers to expand (due to their porosity). At present day
(or the surface age) the decompacted thickness is just the compacted thickness. The *decompacted_density* is the average density
integrated over the decompacted thickness of the drill site (each stratigraphic layer contains a mixture of water and sediment according
to its porosity at the decompacted depth of the layer).

Finally, *tectonic_subsidence* is the output of the underlying :ref:`tectonic subsidence model <pygplates_backtrack_oceanic_and_continental_subsidence>`,
and *water_depth* is obtained from tectonic subsidence by subtracting an isostatic correction of the decompacted sediment thickness.

.. note:: The output columns are specified using the ``-d`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options), or
          using the *decompacted_columns* argument of the :func:`pybacktrack.backtrack_and_write_well` function.
          By default, only *age* and *decompacted_thickness* are output.

.. _pygplates_backtrack_oceanic_and_continental_subsidence:

Oceanic and continental tectonic subsidence
-------------------------------------------

Tectonic subsidence is modelled separately for ocean basins and continental passive margins.
The subsidence model chosen by the ``backtrack`` module depends on whether the drill site is on oceanic or continental crust.
This is determined by an oceanic age grid. Since the age grid captures only oceanic crust, a drill site inside this region
will automatically use the oceanic subsidence model whereas a drill site outside this region uses the continental subsidence model.

The default present-day age grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
6-minute resolution grid of the age of the world's ocean crust:

* Müller, R.D., Seton, M., Zahirovic, S., Williams, S.E., Matthews, K.J., Wright, N.M., Shephard, G.E., Maloney, K.T., Barnett-Moore, N., Hosseinpour, M., Bower, D.J. & Cannon, J. 2016,
  `Ocean Basin Evolution and Global-Scale Plate Reorganization Events Since Pangea Breakup <https://doi.org/10.1146/annurev-earth-060115-012211>`_,
  Annual Review of Earth and Planetary Sciences, vol. 44, pp. 107 .DOI: 10.1146/annurev-earth-060115-012211

.. note:: You can optionally specify your own age grid using the ``-a`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options), or
          using the *age_grid_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. _pygplates_backtrack_oceanic_versus_continental_sites:

Oceanic versus continental drill sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ODP drill site 699 is located on deeper *ocean* crust (as opposed to shallower continental crust):

.. include:: ../pybacktrack/test_data/ODP-114-699-Lithology.txt
   :literal:

So it will use the *oceanic* subsidence model.

.. seealso:: :ref:`pygplates_oceanic_subsidence`

In contrast, DSDP drill site 327 is located on shallower *continental* crust (as opposed to deeper ocean crust):

.. include:: ../pybacktrack/test_data/DSDP-36-327-Lithology.txt
   :literal:

So it will use the *continental* subsidence model. Since continental subsidence involves rifting, it requires a rift start and end time.
These extra rift parameters can be specified at the top of the drill site file as ``RiftStartAge`` and ``RiftEndAge`` attributes
(see :ref:`pygplates_continental_subsidence`).

.. seealso:: :ref:`pygplates_continental_subsidence`

If you are not sure whether your drill site lies on oceanic or continental crust then first prepare your drill site assuming it's on
oceanic crust (since this does not need rift start and end ages). If an error message is generated when
:ref:`running backtrack <pygplates_running_backtrack>` then you'll need to determine the rift start and end age, then
add these to your drill site file as ``RiftStartAge`` and ``RiftEndAge`` attributes, and then run backtrack again.

.. _pygplates_present_day_tectonic_subsidence:

Present-day tectonic subsidence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The tectonic subsidence at present day is used in both the oceanic and continental subsidence models.
Tectonic subsidence is unloaded water depth, that is with sediment removed.
So to obtain an accurate value, ``backtrack`` starts with a bathymetry grid to obtain the present-day water depth (the depth of the sediment surface).
Then an isostatic correction of the present-day sediment thickness (at the drill site) takes into account the removal of sediment to reveal
the present-day tectonic subsidence. The isostatic correction uses the average sediment density of the drill site stratigraphy.

The default present-day bathymetry grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
6-minute resolution global grid of the land topography and ocean bathymetry (although only the ocean bathymetry is actually needed):

* Amante, C. and B. W. Eakins, `ETOPO1 1 Arc-Minute Global Relief Model: Procedures, Data Sources and Analysis <http://dx.doi.org/10.7289/V5C8276M>`_.
  NOAA Technical Memorandum NESDIS NGDC-24, 19 pp, March 2009

.. note:: You can optionally specify your own bathymetry grid using the ``-t`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options), or
          using the *topography_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: If you specify your own bathymetry grid, ensure that its ocean water depths are negative.
          It is assumed that elevations in the grid above/below sea level are positive/negative.

.. _pygplates_oceanic_subsidence:

Oceanic subsidence
------------------

Oceanic subsidence is somewhat simpler and more accurately modelled than continental subsidence (due to *no* lithospheric stretching).

The age of oceanic crust at the drill site (sampled from the oceanic age grid) can be converted to tectonic subsidence (depth with sediment removed)
by using an age-to-depth model. There are two models built into ``backtrack``:

* ``GDH1`` - Stein and Stein (1992) `Model for the global variation in oceanic depth and heat flow with lithospheric age <https://doi.org/10.1038/359123a0>`_

* ``CROSBY_2007`` - Crosby et al. (2006) `The relationship between depth, age and gravity in the oceans <https://doi.org/10.1111/j.1365-246X.2006.03015.x>`_

.. note:: These oceanic subsidence models can be specified using the ``-m`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options), or
          using the *ocean_age_to_depth_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function.
          The default model is ``GDH1``.

.. note:: It is also possible to specify your own age-to-depth model. This can be done by providing your own text file containing a column of ages and a
          corresponding column of depths, and specifying the name of this file along with two integers representing the age and depth column indices to the
          ``-m`` command-line option. Or you can pass your own function as the *ocean_age_to_depth_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function,
          where your function should accept a single age (Ma) argument and return the corresponding depth (m).

Since the drill site might be located on anomalously thick or thin ocean crust, a constant offset is added to the age-to-depth model to ensure the model subsidence matches
the :ref:`actual subsidence <pygplates_present_day_tectonic_subsidence>` at present day.

.. _pygplates_continental_subsidence:

Continental subsidence
----------------------

Continental subsidence is somewhat more complex and less accurately modelled than oceanic subsidence (due to lithospheric stretching).

The continental subsidence model has two components of rifting as described in
`PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_.
The first contribution is *initial* subsidence due to lithospheric thinning where low-density crust is thinned and hot asthenosphere rises underneath.
In our model the crust and lithospheric mantle are identically stretched (uniform extension).
The second contribution is thermal subsidence where the lithosphere thickens as it cools due to conductive heat loss.
In our model thermal subsidence only takes place once the stretching stage has ended.
In this way, there is instantaneous stretching from a thermal perspective (in the sense that, although stretching happens over a finite period of time,
the model assumes no cooling during the stretching stage).

.. note:: The tectonic subsidence at the start of rifting is zero. This is because it is assumed that rifting begins at sea level, and begins with a
          sediment thickness of zero (since sediments are yet to be deposited on newly forming ocean crust).

For drill sites on continental crust, the rift *end* time must be provided. However the rift *start* time is optional. If it is not specified then
it is assumed to be equal to the rift *end* time. In other words, lithospheric stretching is assumed to happen immediately at the rift *end* time
(as opposed to happening over a period of time). This is fine for stratigraphic layers deposited after rifting has ended, since the subsidence will be
the same regardless of whether a rift *start* time was specified or not.

.. note:: The rift start and end times can be specified in the drill site file using the ``RiftStartAge`` and ``RiftEndAge`` attributes.
          Or they can be specified directly on the ``backtrack`` command-line using the ``-rs`` and ``-re`` options respectively
          (run ``python -m pybacktrack.backtrack --help`` to see all options). Or using the *rifting_period* argument
          of the :func:`pybacktrack.backtrack_and_write_well` function.

If a rift *start* time is specified, then the stretching factor varies exponentially between the rift *start* and *end* times (assuming a constant strain rate).
The stretching factor at the rift *start* time is ``1.0`` (since the lithosphere has not yet stretched). The stretching factor at the rift *end* time is
estimated such that our model produces a subsidence matching the :ref:`actual subsidence <pygplates_present_day_tectonic_subsidence>` at present day, while
also thinning the crust to match the actual crustal thickness at present day.

.. note:: The crustal thickness at the end of rifting and at present day are assumed to be the same.

.. warning:: If the estimated rift stretching factor (at the rift *end* time) results in a tectonic subsidence inaccuracy
             (at present day) of more than 100 metres, then a warning is emitted to ``standard error`` on the console.
             This can happen if the actual present-day subsidence is quite deep and the stretching factor required to achieve
             this subsidence would be unrealistically large and result in a pre-rift crustal thickness
             (equal to the stretching factor multiplied by the actual present-day crustal thickness) that exceeds
             typical lithospheric thicknesses. In this case the stretching factor is clamped to avoid this but,
             as a result, the modeled subsidence is not as deep as the actual subsidence.

The default present-day crustal thickness grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
1-degree resolution grid of the thickness of the crustal part of the lithosphere:

* Laske, G., Masters., G., Ma, Z. and Pasyanos, M., `Update on CRUST1.0 - A 1-degree Global Model of Earth's Crust <http://igppweb.ucsd.edu/~gabi/crust1.html#download>`_,
  Geophys. Res. Abstracts, 15, Abstract EGU2013-2658, 2013

.. note:: You can optionally specify your own crustal thickness grid using the ``-k`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options), or
          using the *crustal_thickness_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. _pybacktrack_backtrack:

Backtrack
=========

.. contents::
   :local:
   :depth: 2

.. _pybacktrack_backtrack_overview:

Overview
--------

The ``backtrack`` module is used to find paleo water depths from a tectonic subsidence model, and sediment decompaction over time.
The tectonic subsidence model is either an age-to-depth curve (in ocean basins) or rifting (near continental passive margins).

.. _pybacktrack_running_backtrack:

Running backtrack
-----------------

You can either run ``backtrack`` as a built-in script, specifying parameters as command-line options (``...``):

.. code-block:: python

    python -m pybacktrack.backtrack_cli ...

...or ``import pybacktrack`` into your own script, calling its functions and specifying parameters as function arguments (``...``):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backtrack_and_write_well(...)

.. note:: You can run ``python -m pybacktrack.backtrack_cli --help`` to see a description of all command-line options available, or
          see the :ref:`backtracking reference section <pybacktrack_reference_backtracking>` for documentation on the function parameters.

.. _pybacktrack_backtrack_example:

Example
^^^^^^^

For example, revisiting our :ref:`backtracking example <pybacktrack_a_backtracking_example>`, we can run it from the command-line as:

.. code-block:: python

    python -m pybacktrack.backtrack_cli \
        -w pybacktrack_examples/example_data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth dynamic_topography water_depth tectonic_subsidence lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o ODP-114-699_backtrack_amended.txt \
        -- \
        ODP-114-699_backtrack_decompacted.txt

...or write some Python code to do the same thing:

.. code-block:: python

    import pybacktrack
    
    # Input and output filenames.
    input_well_filename = 'pybacktrack_examples/example_data/ODP-114-699-Lithology.txt'
    amended_well_output_filename = 'ODP-114-699_backtrack_amended.txt'
    decompacted_output_filename = 'ODP-114-699_backtrack_decompacted.txt'
    
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
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY,
                             pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKTRACK_COLUMN_LITHOLOGY],
        # Might be an extra stratigraphic well layer added from well bottom to ocean basement...
        ammended_well_output_filename=amended_well_output_filename)

.. note:: The drill site file ``pybacktrack_examples/example_data/ODP-114-699-Lithology.txt`` is part of the :ref:`example data <pybacktrack_install_examples>`.

.. _pybacktrack_backtrack_output:

Backtrack output
----------------

For each stratigraphic layer in the input drill site file, ``backtrack`` can write one or more parameters to an output file.

Running the :ref:`above example <pybacktrack_backtrack_example>` on ODP drill site 699:

.. include:: ../pybacktrack/example_data/ODP-114-699-Lithology.txt
   :literal:

...produces an :ref:`amended drill site output file <pybacktrack_backtrack_output_amended_drill_site>` containing an extra base sediment layer,
and a :ref:`decompacted output file <pybacktrack_backtrack_output_decompacted>` containing the decompacted output parameters like
sediment thickness and water depth.

.. _pybacktrack_backtrack_output_amended_drill_site:

Amended drill site output
^^^^^^^^^^^^^^^^^^^^^^^^^

The amended drill site output file:

.. Note we're using 'test_data' instead of 'example_data' since only the former directory contains output files.
.. include:: ../tests/test_data/ODP-114-699_backtrack_amended.txt
   :literal:

There is an extra :ref:`base sediment layer <pybacktrack_base_sediment_layer>` that extends from the bottom
of the drill site (516.3 metres) to the total sediment thickness (601 metres).
The bottom age of this new base layer (86.79 Ma) is the age of oceanic crust that ODP drill site 699 is on.
If it had been on continental crust (near a passive margin such as DSDP drill site 327) then
the bottom age of this new base layer would have been when rifting started
(since we would have assumed deposition began when continental stretching began).

.. seealso:: :ref:`pybacktrack_base_sediment_layer` and :ref:`pybacktrack_backtrack_oceanic_versus_continental_sites`

.. _pybacktrack_backtrack_output_decompacted:

Decompacted output
^^^^^^^^^^^^^^^^^^

The decompacted output file:

.. Note we're using 'test_data' instead of 'example_data' since only the former directory contains output files.
.. include:: ../tests/test_data/ODP-114-699_backtrack_decompacted.txt
   :literal:

The *age*, *compacted_depth* and *lithology* columns are the same as the *bottom_age*, *bottom_depth* and *lithology* columns
in the input drill site (except there is also a row associated with the surface age).

The *compacted_thickness* column is the total sediment thickness (601 metres - see base sediment layer of
:ref:`amended drill site <pybacktrack_backtrack_output_amended_drill_site>` above) minus *compacted_depth*.
The *decompacted_thickness* column is the thickness of all sediment at the associated age. In other words, at each consecutive age
another stratigraphic layer is essentially removed, allowing the underlying layers to expand (due to their porosity). At present day
(or the surface age) the decompacted thickness is just the compacted thickness. The *decompacted_density* column is the average density
integrated over the decompacted thickness of the drill site (each stratigraphic layer contains a mixture of water and sediment according
to its porosity at the decompacted depth of the layer). The *decompacted_sediment_rate* column is the rate of sediment deposition in units of metres/Ma.
At each time it is calculated as the fully decompacted thickness (ie, using surface porosity only) of the surface stratigraphic layer
(whose deposition ends at the specified time) divided by the layer's deposition time interval. The *decompacted_depth* column is similar to
*decompacted_sediment_rate* in that the stratigraphic layers are fully decompacted (using surface porosity only) as if no portion of any layer had
ever been buried. It is also similar to *compacted_depth* except all effects of compaction have been removed.
The *dynamic_topography* column is the dynamic topography elevation relative to present day (or zero if no dynamic topography model was specified).

Finally, *tectonic_subsidence* is the output of the underlying :ref:`tectonic subsidence model <pybacktrack_backtrack_oceanic_and_continental_subsidence>`,
and *water_depth* is obtained from tectonic subsidence by subtracting an isostatic correction of the decompacted sediment thickness.

.. note:: The output columns are specified using the ``-d`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *decompacted_columns* argument of the :func:`pybacktrack.backtrack_and_write_well` function.
          By default, only *age* and *decompacted_thickness* are output.

.. _pybacktrack_backtrack_sealevel_variation:

Sea level variation
-------------------

A model of the variation of sea level relative to present day can optionally be used when backtracking.
This adjusts the isostatic correction of the decompacted sediment thickness to take into account sea-level variations.

.. _pybacktrack_bundled_sea_level_models:

There are two built-in sea level models :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack``:

* ``Haq87_SealevelCurve`` - `The Phanerozoic Record of Global Sea-Level Change <https://doi.org/10.1126/science.1116412>`_

* ``Haq87_SealevelCurve_Longterm`` - Normalised to start at zero at present-day.

A sea-level model is optional. If one is not specified then sea-level variation is assumed to be zero.

.. note:: A built-in sea-level model can be specified using the ``-slm`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *sea_level_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: It is also possible to specify your own sea-level model. This can be done by providing your own text file containing a column of ages (Ma) and a
          corresponding column of sea levels (m), and specifying the name of this file to the ``-sl`` command-line option or to the *sea_level_model* argument
          of the :func:`pybacktrack.backtrack_and_write_well` function.

.. _pybacktrack_backtrack_oceanic_and_continental_subsidence:

Oceanic and continental tectonic subsidence
-------------------------------------------

Tectonic subsidence is modelled separately for ocean basins and continental passive margins.
The subsidence model chosen by the ``backtrack`` module depends on whether the drill site is on oceanic or continental crust.
This is determined by an oceanic age grid. Since the age grid captures only oceanic crust, a drill site inside this region
will automatically use the oceanic subsidence model whereas a drill site outside this region uses the continental subsidence model.

.. _pybacktrack_bundled_age_grid:

The default present-day age grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a 6-minute resolution grid
of the age of the world's ocean crust that uses the timescale of `Gee and Kent (2007) <https://doi.org/10.1016/B978-044452748-6.00097-3>`_:

* Seton, M., Müller, R. D., Zahirovic, S., Williams, S., Wright, N., Cannon, J., Whittaker, J., Matthews, K., McGirr, R., (2020),
  `A global dataset of present-day oceanic crustal age and seafloor spreading parameters <https://doi.org/10.1029/2020GC009214>`_,
  Geochemistry, Geophysics, Geosystems, doi: 10.1029/2020GC009214

.. note:: The default present-day age grid was updated in pyBacktrack version 1.4.

.. note:: You can optionally specify your own age grid using the ``-a`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *age_grid_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. _pybacktrack_backtrack_oceanic_versus_continental_sites:

Oceanic versus continental drill sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ODP drill site 699 is located on deeper *ocean* crust (as opposed to shallower continental crust):

.. include:: ../pybacktrack/example_data/ODP-114-699-Lithology.txt
   :literal:

So it will use the *oceanic* subsidence model.

.. seealso:: :ref:`pybacktrack_oceanic_subsidence`

In contrast, DSDP drill site 327 is located on shallower *continental* crust (as opposed to deeper ocean crust):

.. include:: ../pybacktrack/example_data/DSDP-36-327-Lithology.txt
   :literal:

So it will use the *continental* subsidence model. Since continental subsidence involves rifting, it requires a rift start and end time.
These extra rift parameters can be specified at the top of the drill site file as ``RiftStartAge`` and ``RiftEndAge`` attributes
(see :ref:`pybacktrack_continental_subsidence`).

.. seealso:: :ref:`pybacktrack_continental_subsidence`

If you are not sure whether your drill site lies on oceanic or continental crust then first prepare your drill site assuming it's on
oceanic crust (since this does not need rift start and end ages). If an error message is generated when
:ref:`running backtrack <pybacktrack_running_backtrack>` then you'll need to determine the rift start and end age, then
add these to your drill site file as ``RiftStartAge`` and ``RiftEndAge`` attributes, and then run backtrack again.

.. note:: In pyBacktrack version 1.4 if the ``RiftStartAge`` and ``RiftEndAge`` attributes are not specified in your drill site file then
          they are obtained implicitly from the builtin rift start/end time grids (see :ref:`pybacktrack_continental_subsidence`), so an
          error message is unlikely to be generated when your drill site file is on *continental* crust.

.. _pybacktrack_present_day_tectonic_subsidence:

Present-day tectonic subsidence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The tectonic subsidence at present day is used in both the oceanic and continental subsidence models.
Tectonic subsidence is unloaded water depth, that is with sediment removed.
So to obtain an accurate value, ``backtrack`` starts with a bathymetry grid to obtain the present-day water depth (the depth of the sediment surface).
Then an isostatic correction of the present-day sediment thickness (at the drill site) takes into account the removal of sediment to reveal
the present-day tectonic subsidence. The isostatic correction uses the average sediment density of the drill site stratigraphy.

.. _pybacktrack_bundled_topography_grid:

The default present-day bathymetry grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
6-minute resolution global grid of the land topography and ocean bathymetry (although only the ocean bathymetry is actually needed):

* Amante, C. and B. W. Eakins, `ETOPO1 1 Arc-Minute Global Relief Model: Procedures, Data Sources and Analysis <https://dx.doi.org/10.7289/V5C8276M>`_.
  NOAA Technical Memorandum NESDIS NGDC-24, 19 pp, March 2009

.. note:: You can optionally specify your own bathymetry grid using the ``-t`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *topography_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: If you specify your own bathymetry grid, ensure that its ocean water depths are negative.
          It is assumed that elevations in the grid above/below sea level are positive/negative.

.. _pybacktrack_oceanic_subsidence:

Oceanic subsidence
------------------

Oceanic subsidence is somewhat simpler and more accurately modelled than continental subsidence (due to *no* lithospheric stretching).

The age of oceanic crust at the drill site (sampled from the oceanic age grid) can be converted to tectonic subsidence (depth with sediment removed)
by using an age-to-depth model. There are three models built into ``backtrack``:

* ``RHCW18`` - Richards et al. (2020) `Structure and dynamics of the oceanic lithosphere-asthenosphere system <https://doi.org/10.1016/j.pepi.2020.106559>`_
  
  The parameters of the preferred RHCW18 Plate Model used in pyBacktrack include a potential mantle temperature of 1333 in °C,
  a plate thickness of 130 km and a zero-age ridge depth of 2500 m, as described in Richards et al. (2020)
  (updated from Richards et al. (2018) and on the `related github repository <https://github.com/freddrichards/RHCW18_Plate_Model>`_).

* ``CROSBY_2007`` - Crosby, A.G., (2007). *Aspects of the relationship between topography and gravity on the Earth and Moon, PhD thesis, University of Cambridge*
  
  The Python source code that implements this age-depth relationship can be found
  `here <https://github.com/EarthByte/pyBacktrack/blob/8e21ec2b49be101e88d80e8ccb18fe736d68a277/pybacktrack/age_to_depth.py#L195-L264>`_.
  And note that additional background information on this model can be found in:
  Crosby, A.G. and McKenzie, D., 2009. `An analysis of young ocean depth, gravity and global residual topography <https://doi.org/10.1111/j.1365-246X.2009.04224.x>`_.

* ``GDH1`` - Stein and Stein (1992) `Model for the global variation in oceanic depth and heat flow with lithospheric age <https://doi.org/10.1038/359123a0>`_

The default model is ``RHCW18``.

.. note:: The default age-to-depth model was updated in pyBacktrack version 1.4. It is now ``RHCW18``. Previously it was ``GDH1``.

.. note:: These oceanic subsidence models can be specified using the ``-m`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *ocean_age_to_depth_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: It is also possible to specify your own age-to-depth model. This can be done by providing your own text file containing a column of ages and a
          corresponding column of depths, and specifying the name of this file along with two integers representing the age and depth column indices to the
          ``-m`` command-line option. Or you can pass your own function as the *ocean_age_to_depth_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function,
          where your function should accept a single age (Ma) argument and return the corresponding depth (m).

Since the drill site might be located on anomalously thick or thin ocean crust, a constant offset is added to the age-to-depth model to ensure the model subsidence matches
the :ref:`actual subsidence <pybacktrack_present_day_tectonic_subsidence>` at present day.

.. _pybacktrack_continental_subsidence:

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
          (run ``python -m pybacktrack.backtrack_cli --help`` to see all options). Or using the *rifting_period* argument
          of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: If the rift end time (and optional start time) is not explicitly specified in the drill site file or explicitly on the ``backtrack`` command-line
          (or explicitly via the :func:`pybacktrack.backtrack_and_write_well` function) then both the rift start and end times are obtained implicitly from the
          builtin rift start/end time grids. If the well location is outside valid regions of the rift start/end time grids then an error is
          generated and you must then explicitly provide the rift end time (and optionally the rift start time). However currently the rift grids cover all
          submerged continental crust (ie, where the total sediment thickness grid contains valid values but the age grid does not) and not just the areas
          that are rifting - see :ref:`rift gridding <pybacktrack_builtin_rift_gridding_procedure>` - so an error is unlikely to be generated.

If a rift *start* time is specified, then the stretching factor varies exponentially between the rift *start* and *end* times (assuming a constant strain rate).
The stretching factor at the rift *start* time is ``1.0`` (since the lithosphere has not yet stretched). The stretching factor at the rift *end* time is
estimated such that our model produces a subsidence matching the :ref:`actual subsidence <pybacktrack_present_day_tectonic_subsidence>` at present day, while
also thinning the crust to match the actual crustal thickness at present day.

.. note:: The crustal thickness at the end of rifting and at present day are assumed to be the same.

.. warning:: If the estimated rift stretching factor (at the rift *end* time) results in a tectonic subsidence inaccuracy
             (at present day) of more than 100 metres, then a warning is emitted to ``standard error`` on the console.
             This can happen if the actual present-day subsidence is quite deep and the stretching factor required to achieve
             this subsidence would be unrealistically large and result in a pre-rift crustal thickness
             (equal to the stretching factor multiplied by the actual present-day crustal thickness) that exceeds
             typical lithospheric thicknesses (125km). In this case the stretching factor is clamped to avoid this but,
             as a result, the modeled subsidence is not as deep as the actual subsidence.

.. _pybacktrack_bundled_crustal_thickness_grid:

The default present-day crustal thickness grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
1-degree resolution grid of the thickness of the crustal part of the lithosphere:

* Laske, G., Masters., G., Ma, Z. and Pasyanos, M., `Update on CRUST1.0 - A 1-degree Global Model of Earth's Crust <http://igppweb.ucsd.edu/~gabi/crust1.html#download>`_,
  Geophys. Res. Abstracts, 15, Abstract EGU2013-2658, 2013

.. note:: You can optionally specify your own crustal thickness grid using the ``-k`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *crustal_thickness_filename* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. _pybacktrack_dynamic_topography:

Dynamic topography
------------------

The effects of dynamic topography can be included in the models of tectonic subsidence (both oceanic and continental).

A dynamic topography model is optional. If one is not specified then dynamic topography is assumed to be zero.

All dynamic topography models consist of a sequence of time-dependent global grids (where each grid is associated with a past geological time).
The grids are in the *mantle* reference frame (instead of the *plate* reference frame) and hence the drill site location must be reconstructed
(back in time) before sampling these grids. To enable this, a dynamic topography model also includes an associated static-polygons
file to assign a reconstruction plate ID to the drill site, and associated rotation file(s) to reconstruct the drill site location.

.. note:: The dynamic topography grids are interpolated at times not coinciding with the grid times.
          The method of interpolation changed in pyBacktrack version 1.4 (as described in the notes of :meth:`pybacktrack.DynamicTopography.sample`) -
          however this change has no effect *at* the grid times (only between grid times).

.. warning:: If the drill site is reconstructed to a time that is older than supported by the dynamic topography model then the oldest dynamic topography grid is used.
             Also note that the drill site can be reconstructed to a time that is older than the age of the crust it is located on if the bottom age
             in the drill site file is older than the basement age.

Dynamic topography is included in the oceanic subsidence model by adjusting the subsidence to account for the change in
dynamic topography at the drill site since present day.

.. seealso:: :ref:`pybacktrack_oceanic_subsidence`

Dynamic topography is included in the continental subsidence model by first removing the effects of dynamic topography (between the start of rifting and present day)
prior to estimating the rift stretching factor. This is because estimation of the stretching factor only considers subsidence due to lithospheric thinning (stretching)
and subsequent thickening (thermal cooling). Once the optimal stretching factor has been estimated, the continental subsidence is adjusted to account for the change in
dynamic topography since the start of rifting.

.. seealso:: :ref:`pybacktrack_continental_subsidence`

.. _pybacktrack_bundled_dynamic_topography_models:

These are the built-in dynamic topography models :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack``:

* *Young et al., 2022* - `Long-term Phanerozoic sea level change from solid Earth processes <https://doi.org/10.1016/j.epsl.2022.117451>`_

  * `gld428 <http://portal.gplates.org/dynamic_topography_cesium/?model=gld428&name=Gld428_250-0Ma>`_

* *Braz et al., 2021* - `Modelling the role of dynamic topography and eustasy in the evolution of the Great Artesian Basin <https://doi.org/10.1111/bre.12606>`_

  * `D10_gmcm9 <http://portal.gplates.org/dynamic_topography_cesium/?model=gmcm9&name=D10_gmcm9>`_

* *Cao et al., 2019* - `The interplay of dynamic topography and eustasy on continental flooding in the late Paleozoic <https://doi.org/10.1016/j.tecto.2019.04.018>`_

  * `AY18 <http://portal.gplates.org/dynamic_topography_cesium/?model=gld324&name=AY18>`_
  * `KM16 <http://portal.gplates.org/dynamic_topography_cesium/?model=gld321&name=KM16>`_

* *Müller et al., 2017* - `Dynamic topography of passive continental margins and their hinterlands since the Cretaceous <https://doi.org/10.1016/j.gr.2017.04.028>`_

  * `M1 <http://portal.gplates.org/dynamic_topography_cesium/?model=M1&name=M1>`_
  * `M2 <http://portal.gplates.org/dynamic_topography_cesium/?model=M2&name=M2>`_
  * `M3 <http://portal.gplates.org/dynamic_topography_cesium/?model=M3&name=M3>`_
  * `M4 <http://portal.gplates.org/dynamic_topography_cesium/?model=M4&name=M4>`_
  * `M5 <http://portal.gplates.org/dynamic_topography_cesium/?model=M5&name=M5>`_
  * `M6 <http://portal.gplates.org/dynamic_topography_cesium/?model=M6&name=M6>`_
  * `M7 <http://portal.gplates.org/dynamic_topography_cesium/?model=M7&name=M7>`_

* *Rubey et al., 2017* - `Global patterns of Earth's dynamic topography since the Jurassic <https://doi.org/10.5194/se-2017-26>`_

  * `terra <http://portal.gplates.org/dynamic_topography_cesium/?model=terra&name=Terra>`_

* *Müller et al., 2008* - `Long-term sea-level fluctuations driven by ocean basin dynamics <https://doi.org/10.1126/science.1151540>`_

  * `ngrand <http://portal.gplates.org/dynamic_topography_cesium/?model=ngrand&name=dynto_ngrand>`_
  * `s20rts <http://portal.gplates.org/dynamic_topography_cesium/?model=s20rts&name=dynto_s20rts>`_
  * `smean <http://portal.gplates.org/dynamic_topography_cesium/?model=smean&name=dynto_smean>`_

.. note:: The above model links reference dynamic topography models that can be visualized in the `GPlates Web Portal <http://portal.gplates.org>`_.

The ``M1`` model is a combined forward/reverse geodynamic model, while models ``M2``-``M7`` are forward models.
Models ``ngrand``, ``s20rts`` and ``smean`` are backward-advection models.
The backward-advection models are generally good for the recent geological past (up to last 70 million years).
While the ``M1``-``M7`` models are most useful when it is necessary to look at times older than 70 Ma
because their oceanic paleo-depths lack the regional detail at more recent times that the backward-advection models capture
(because of their assimilation of seismic tomography).
``M1`` also assimilates seismic tomography but suffers from other shortcomings.

.. note:: A built-in dynamic topography model can be specified using the ``-ym`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options), or
          using the *dynamic_topography_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

.. note:: It is also possible to specify your own dynamic topography model.
          This can be done by providing your own grid list text file with the first column containing a list of the dynamic topography grid filenames
          (where each filename should be relative to the directory on the list file) and the second column containing the associated grid times (in Ma).
          You'll also need the associated static-polygons file, and one or more associated rotation files.
          The grid list filename, static-polygons filename and one or more rotation filenames are then specified using the
          ``-y`` command-line option (run ``python -m pybacktrack.backtrack_cli --help`` to see all options),
          or to the *dynamic_topography_model* argument of the :func:`pybacktrack.backtrack_and_write_well` function.

Geohistory analysis
-------------------

The `Decompacting Stratigraphic Layers <https://github.com/EarthByte/pyBacktrack/blob/master/pybacktrack/notebooks/decompacting_stratigraphy.ipynb>`_
notebook shows how to visualize the decompaction of stratigraphic layers at a drill site.

.. note:: The example notebooks are installed as part of the example data which can be installed by following :ref:`these instructions <pybacktrack_install_examples>`.

Continental subsidence
^^^^^^^^^^^^^^^^^^^^^^

One of the examples in that notebook demonstrates decompaction of a shallow continental drill site using backtracking.
The tectonic subsidence (black dashed line) is from our :ref:`model of continental subsidence <pybacktrack_continental_subsidence>` and
the paleo water depths (blue fill) are backtracked using tectonic subsidence and sediment decompaction.
Note that, unlike backstripping, :ref:`dynamic topography <pybacktrack_dynamic_topography>` *does* affect tectonic subsidence
(because its effects are included in the model of tectonic subsidence).

.. figure:: images/geohistory_DSDP-36-327.png

.. note:: There is a base sediment layer below the drill site (from the bottom of drill site to basement depth) since the drill site does not reach basement depth.
          And for this drill site the base sediment layer is quite thick because the default total sediment thickness grid is not as accurate near continental margins (compared to deeper ocean basins).

Oceanic subsidence
^^^^^^^^^^^^^^^^^^

Another example in that notebook demonstrates decompaction of an oceanic drill site using backtracking.
The tectonic subsidence (black dashed line) is from our :ref:`model of oceanic subsidence <pybacktrack_oceanic_subsidence>` and
the paleo water depths (blue fill) are backtracked using tectonic subsidence and sediment decompaction.
Note that, unlike backstripping, :ref:`dynamic topography <pybacktrack_dynamic_topography>` *does* affect tectonic subsidence
(because its effects are included in the model of tectonic subsidence).

.. figure:: images/geohistory_ODP-114-699.png

.. note:: There is a base sediment layer below the drill site (from the bottom of drill site to basement depth) since the drill site does not reach basement depth.

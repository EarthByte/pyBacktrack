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

The following sections cover the available parameters (where ``...`` is specified above).

.. note:: You can run ``python -m pybacktrack.backtrack --help`` to see a description of all command-line options available, or
          see the :ref:`backtracking reference section <pybacktrack_reference_backtracking>` for documentation on the function parameters.

.. _pygplates_backtrack_output:

Backtrack output
----------------

For each stratigraphic layer in the input drill site file, ``backtrack`` can write one or more parameters to an output file.

For example, ODP drill site 699:

.. include:: ../pybacktrack/test_data/ODP-114-699-Lithology.txt
   :literal:

...generates the following output (if all available parameters are specified):

.. include:: ../pybacktrack/test_data/ODP-114-699_backtrack_decompat.txt
   :literal:

.. note:: The *age*, *compacted_depth* and *lithology* columns are the same as the *bottom_age*,
          *bottom_depth* and *lithology* columns in the input drill site (except there is also a row associated with the surface age).

The *compacted_thickness* column is the total sediment thickness (:ref:`601 metres <pygplates_base_sediment_layer>` for ODP drill site 699 above) minus *compacted_depth*.
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

The default age grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
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

.. seealso:: :ref:`pygplates_oceanic_subsidence`.

In contrast, DSDP drill site 327 is located on shallower *continental* crust (as opposed to deeper ocean crust):

.. include:: ../pybacktrack/test_data/DSDP-36-327-Lithology.txt
   :literal:

So it will use the *continental* subsidence model. Since continental subsidence involves rifting, it requires a rift start and end time.
These extra rift parameters can be specified at the top of the drill site file as ``RiftStartAge`` and ``RiftEndAge`` attributes
(see :ref:`pygplates_continental_subsidence`).

.. note:: If ``RiftStartAge`` and ``RiftEndAge`` are not specified in the drill site file then they must be specified
          directly on the ``backtrack`` command-line using the ``-rs`` and ``-re`` options respectively
          (run ``python -m pybacktrack.backtrack --help`` to see all options), or using the *rifting_period* argument
          of the :func:`pybacktrack.backtrack_and_write_well` function.

.. seealso:: :ref:`pygplates_continental_subsidence`.

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

The default bathymetry grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backtrack`` is a
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

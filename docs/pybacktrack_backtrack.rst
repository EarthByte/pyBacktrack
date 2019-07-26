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

.. _pygplates_backtrack_oceanic_versus_continental_subsidence:

Oceanic versus continental tectonic subsidence
----------------------------------------------

Tectonic subsidence is modelled separately for ocean basins and continental passive margins.
The subsidence model chosen by the ``backtrack`` module depends on whether the drill site is on oceanic or continental crust.
An oceanic age grid is used to determine this. Since the age grid captures only oceanic crust, a drill site inside this region
will automatically use the oceanic subsidence model whereas a drill site outside this region uses the continental subsidence model.

The default age grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``pybacktrack`` is a
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
These extra rift parameters can be specified at the top of the as ``RiftStartAge`` and ``RiftEndAge`` attributes (see :ref:`pygplates_continental_subsidence`).

.. note:: If ``RiftStartAge`` and ``RiftEndAge`` are not specified in the drill site file then they must be specified
          directly on the ``backtrack`` command-line using the ``-rs`` and ``-re`` options respectively
          (run ``python -m pybacktrack.backtrack --help`` to see all options), or using the *rifting_period* argument
          of the :func:`pybacktrack.backtrack_and_write_well` function.

.. seealso:: :ref:`pygplates_continental_subsidence`.

If you are not sure whether your drill site lies on oceanic or continental crust then first prepare your drill site assuming it's on
oceanic crust (since this does not need rift start and end ages). If an error message is generated when
:ref:`running backtrack <pygplates_running_backtrack>` then you'll need to determine the rift start and end age, and
add ``RiftStartAge`` and ``RiftEndAge`` attributes to your drill site file and then run backtrack again.

.. _pygplates_oceanic_subsidence:

Oceanic subsidence
^^^^^^^^^^^^^^^^^^

Oceanic subsidence is somewhat simpler and more accurately modelled than continental subsidence (due to *no* lithospheric stretching).

.. _pygplates_continental_subsidence:

Continental subsidence
^^^^^^^^^^^^^^^^^^^^^^

Continental subsidence is somewhat more complex and less accurately modelled than oceanic subsidence (due to lithospheric stretching).

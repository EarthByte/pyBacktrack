.. _pygplates_backtrack:

Backtrack
=========

.. contents::
   :local:
   :depth: 2

.. _pygplates_backtrack_overview:

Overview
--------

The ``backtrack`` module is used to find paleo water depths from a tectonic subsidence model
(such as an age-to-depth curve in ocean basins, or rifting near continental passive margins) and sediment decompaction over time.

.. _pygplates_running_backtrack:

Running backtrack
-----------------

You can either run ``backtrack`` as a built-in script, and specify parameters as command-line options (``...``):

.. code-block:: python

    python -m pybacktrack.backtrack ...

...or import ``backtrack`` into your own script, and call its functions and specify parameters as function arguments (``...``):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backtrack_and_write_well(...)

The following sections cover the available parameters (where ``...`` is specified above).

.. note:: You can run ``python -m pybacktrack.backtrack --help`` to see a description of all command-line options available.

.. _pygplates_backtrack_oceanic_versus_continental_sites:

Oceanic versus continental tectonic subsidence
----------------------------------------------

Tectonic subsidence is modelled separately for ocean basins and continental passive margins.
So the subsidence model used depends on whether the drill site is on oceanic or continental crust.
The ``backtrack`` module uses an age grid to determine this.
The default age grid :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``pybacktrack`` is a
6-minute resolution grid of the age of the world's ocean crust:

* Müller, R.D., Seton, M., Zahirovic, S., Williams, S.E., Matthews, K.J., Wright, N.M., Shephard, G.E., Maloney, K.T., Barnett-Moore, N., Hosseinpour, M., Bower, D.J. & Cannon, J. 2016,
  `Ocean Basin Evolution and Global-Scale Plate Reorganization Events Since Pangea Breakup <https://doi.org/10.1146/annurev-earth-060115-012211>`_,
  Annual Review of Earth and Planetary Sciences, vol. 44, pp. 107 .DOI: 10.1146/annurev-earth-060115-012211

.. note:: You can optionally specify your own age grid using the ``-a`` command-line option (run ``python -m pybacktrack.backtrack --help`` to see all options).

Since the age grid captures only oceanic crust, a drill site that is inside this region will automatically
use the oceanic subsidence model whereas a drill site outside this region uses the continental subsidence model.
However, continental subsidence involves rifting which is more complex and requires a rift start and end time.
These extra rift parameters can be specified at the top of the :ref:`drill site file <pygplates_stratigraphy_oceanic_versus_continental_sites>`
as ``RiftStartAge`` and ``RiftEndAge`` attributes (see :ref:`pygplates_continental_subsidence`).

.. note:: If ``RiftStartAge`` and ``RiftEndAge`` are not specified in the drill site file then they must be specified
          directly on the ``backtrack`` command-line using the ``-rs`` and ``-re`` options respectively
          (run ``python -m pybacktrack.backtrack --help`` to see all options).

If you are not sure whether your drill site lies on oceanic or continental crust then first prepare your drill site assuming it's on
oceanic crust (since this does not need rift start and end ages). If an error message is generated when
:ref:`running backtrack <pygplates_running_backtrack>` then you'll need to determine the rift start and end age,
then add ``RiftStartAge`` and ``RiftEndAge`` attributes to your :ref:`drill site file <pygplates_stratigraphy_oceanic_versus_continental_sites>`
and then run backtrack again.

.. _pygplates_oceanic_subsidence:

Oceanic subsidence
^^^^^^^^^^^^^^^^^^



.. _pygplates_continental_subsidence:

Continental subsidence
^^^^^^^^^^^^^^^^^^^^^^


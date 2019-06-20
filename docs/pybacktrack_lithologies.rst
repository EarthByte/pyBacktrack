.. _pygplates_lithologies:

Lithologies
===========

.. contents::
   :local:
   :depth: 2

Drill sites
-----------

The main input file for backtracking and backstripping is an ocean drill site.
It provides a record of the present-day lithostratigraphy of the sedimentation sitting on top
of the submerged oceanic or continental crust.

The following is the content of the drill site file associated with ODP site 699:
::

  # SiteLongitude = -30.677
  # SiteLatitude = -51.542
  # SurfaceAge = 0 
  
  ## bottom_age bottom_depth lithology
     18.7       85.7         Diatomite 0.7 Clay 0.3
     25.0       142.0        Coccolith_ooze 0.3 Diatomite 0.5 Mud 0.2
     31.3       233.6        Coccolith_ooze 0.3 Diatomite 0.7
     31.9       243.1        Sand 1
     36.7       335.4        Coccolith_ooze 0.8 Diatomite 0.2
     40.8       382.6        Chalk 1
     54.5       496.6        Chalk 1
     55.3       516.3        Chalk 0.5 Clay 0.5

It consists of two main sections. The top section specifies the *attributes* of the drill site,
and the bottom section specifies the *stratigraphic layers*.

The attributes ``SiteLongitude`` and ``SiteLatitude`` specify the drill site location (in degrees).

.. note:: If ``SiteLongitude`` and ``SiteLatitude`` are not specified then they must be specified
          directly in the :ref:`backtrack <pygplates_backtrack>` or :ref:`backstrip <pygplates_backstrip>`
          module using the ``-w`` command-line option.

For each stratigraphic layer in the drill site there is an age (Ma) and a depth (m) representing the bottom of that layer.
The top age and depth of each layer is the bottom age and depth of the layer above. Since the surface (top) layer
has no layer above it, the top age and depth of the surface layer are 0Ma and 0m respectively. However,
if the ``SurfaceAge`` attribute is specified then it replaces the top age of the surface layer.
A non-zero value of ``SurfaceAge`` implies that sediment deposition ended prior to present day.
In other words, it represents the age of the total sediment surface.

.. note:: The ``SurfaceAge`` attribute is optional, and defaults to 0Ma if not specified.

It is also possible that the sediment thickness recorded at the drill site is less than the total sediment
thickness. In this situation a base stratigraphic layer is automatically added during backtracking and backstripping
to represent sediment from the bottom of the drill site down to the base depth of oceanic or continental crust.
By default the base layer lithology is ``Shale``, but can be changed using the ``-b`` command-line option in
the :ref:`backtrack <pygplates_backtrack>` and :ref:`backstrip <pygplates_backstrip>` modules. To determine the
total sediment thickness a grid is sampled at the drill site location. The default grid is
:ref:`bundled <pybacktrack_reference_bundle_data>` inside ``pybacktrack``. However, you can override this with your
own grid by using the ``-s`` command-line option in the :ref:`backtrack <pygplates_backtrack>` and
:ref:`backstrip <pygplates_backstrip>` modules. The default total sediment thickness grid is:

* Wobbe, Florian; Lindeque, Ansa; Gohl, Karsten (2014):
  `Total sediment thickness grid of the Southern Pacific Ocean off West Antarctica, links to NetCDF files <https://doi.org/10.1594/PANGAEA.835589>`_,
  PANGAEA, doi:10.1594/PANGAEA.835589

.. note:: If the drill site thickness happens to exceed the total sediment thickness then no base layer is added,
          and a warning is emitted to standard error on the console.

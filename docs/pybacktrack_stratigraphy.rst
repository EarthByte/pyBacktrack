.. _pygplates_stratigraphy:

Stratigraphy
============

This document covers drill site stratigraphy, and lithology names that reference lithology definitions of density, surface porosity and porosity decay.

.. contents::
   :local:
   :depth: 2

.. _pygplates_drill_site:

Drill site
----------

The main input file for backtracking and backstripping is a drill site.
It provides a record of the present-day lithostratigraphy of the sedimentation sitting on top
of the submerged oceanic or continental crust.

.. _pygplates_stratigraphy_oceanic_versus_continental_sites:

Oceanic versus continental sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ODP drill site 699 is located on deeper *ocean* crust (as opposed to shallower continental crust):

.. include:: ../pybacktrack/test_data/ODP-114-699-Lithology.txt
   :literal:

This site is more suitable for :ref:`backtracking <pygplates_backtrack>` since oceanic subsidence
is somewhat simpler and more accurately modelled (due to no lithospheric stretching).
Backtracking will then find the unknown paleo-water depths.

In contrast, DSDP drill site 327 is located on shallower *continental* crust (as opposed to deeper ocean crust):

.. include:: ../pybacktrack/test_data/DSDP-36-327-Lithology.txt
   :literal:

This site is a candidate for :ref:`backstripping <pygplates_backstrip>` since continental subsidence
due to rift stretching is somewhat more complex and less accurately modelled. Note that this site contains two extra
columns, for the minimum and maximum water depths. Backstripping will then use these paleo-water depths,
along with sediment decompaction, to reveal the complex tectonic subsidence of rift stretching at the site location.

Alternatively, the paleo-water depths in the drill site could be ignored (perhaps they weren't recorded in the drill site
and instead were inserted from another simulation). In this case :ref:`backtracking <pygplates_backtrack>` can provide
tectonic subsidence via its built-in model of continental rift stretching. In this case the ``RiftStartAge`` and ``RiftEndAge``
parameters (in the site file) specify when rifting started and when it ended.

.. seealso:: :ref:`Backtrack <pygplates_backtrack>` for more details.

Drill site file format
^^^^^^^^^^^^^^^^^^^^^^

As seen in the :ref:`oceanic and continental sites <pygplates_stratigraphy_oceanic_versus_continental_sites>`,
the file format of drill sites consist of two main sections. The top section specifies the *attributes*
of the drill site, and the bottom section specifies the *stratigraphic layers*.

The attributes ``SiteLongitude`` and ``SiteLatitude`` specify the drill site location (in degrees).

.. note:: If ``SiteLongitude`` and ``SiteLatitude`` are not specified then they must be specified
          directly in the :ref:`backtrack <pygplates_backtrack>` or :ref:`backstrip <pygplates_backstrip>`
          module using the ``-w`` command-line option.

For each stratigraphic layer in the drill site there is a mixture of lithologies representing the
stratigraphic composition of that layer. Each lithology (in a layer) is identified by a lithology name
and the fraction it contributes to the layer (where all the fractions must add up to ``1.0``).
Each lithology name is used to look up a list of :ref:`lithology definitions <pygplates_lithology_definitions>`
to obtain lithology density, surface porosity and porosity decay.

For each stratigraphic layer in the drill site there is also an age (Ma) and a depth (m) representing the bottom of that layer.
The top age and depth of each layer is the bottom age and depth of the layer above. Since the surface (top) layer
has no layer above it, the top age and depth of the surface layer are 0Ma and 0m respectively. However,
if the ``SurfaceAge`` attribute is specified then it replaces the top age of the surface layer.
A non-zero value of ``SurfaceAge`` implies that sediment deposition ended prior to present day.
In other words, it represents the age of the total sediment surface.

.. note:: The ``SurfaceAge`` attribute is optional, and defaults to 0Ma if not specified.

Base sediment layer
^^^^^^^^^^^^^^^^^^^

It is also possible that the sediment thickness recorded at the drill site is less than the total sediment
thickness. This happens when the drill site does not penetrate all the way to the basement depth of oceanic or contintal crust.
In this situation a base stratigraphic layer is automatically added during backtracking and backstripping
to represent sediment from the bottom of the drill site down to the basement depth of oceanic or continental crust.
For backtracking, the bottom age of this new base layer is the age of oceanic crust if drill site is on ocean crust,
or the age that rifting starts if drill site is on continental crust (since it is assumed that deposition began when
continental stretching started) - see :ref:`backtrack <pygplates_backtrack>` for more details.
For backstripping, the bottom age of this new base layer is simply set to the age at the bottom of the drill site
(ie, bottom age of deepest stratigraphic layer).
By default the lithology of the base layer is ``Shale``, but can be changed using the ``-b`` command-line option in
the :ref:`backtrack <pygplates_backtrack>` and :ref:`backstrip <pygplates_backstrip>` modules. To determine the
total sediment thickness, a grid is sampled at the drill site location. The default grid is
:ref:`bundled <pybacktrack_reference_bundle_data>` inside ``pybacktrack``. However, you can override this with your
own grid by using the ``-s`` command-line option in the :ref:`backtrack <pygplates_backtrack>` and
:ref:`backstrip <pygplates_backstrip>` modules. The default total sediment thickness grid is:

* Wobbe, Florian; Lindeque, Ansa; Gohl, Karsten (2014):
  `Total sediment thickness grid of the Southern Pacific Ocean off West Antarctica, links to NetCDF files <https://doi.org/10.1594/PANGAEA.835589>`_,
  PANGAEA, doi:10.1594/PANGAEA.835589

.. note:: If the drill site thickness happens to exceed the total sediment thickness then no base layer is added,
          and a warning is emitted to standard error on the console.

.. _pygplates_lithology_definitions:

Lithology Definitions
---------------------

The stratigraphy layers in a :ref:`drill site <pygplates_drill_site>` contain lithology *names* that reference
lithology *definitions*. Each lithology definition contains a density, a surface porosity and a porosity decay.

These definitions are stored in lithology files. 

Bundled definitions
^^^^^^^^^^^^^^^^^^^

There are two lithology files currently :ref:`bundled <pybacktrack_reference_bundle_data>`
inside ``pybacktrack``, one containing *primary* lithologies and the other *extended* lithologies.

The *primary* lithologies (inside ``pybacktrack``) contains the deep-sea lithologies listed in Table 1 in the pyBacktrack paper:

* Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
  `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
  **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313.

.. include:: ../pybacktrack/bundle_data/lithologies/primary.txt
   :literal:

And the *extended* lithologies (inside ``pybacktrack``) mostly contains shallow-water lithologies:

.. include:: ../pybacktrack/bundle_data/lithologies/extended.txt
   :literal:

.. _pygplates_bundled_lithology_definitions:

Lithology file format
^^^^^^^^^^^^^^^^^^^^^

As seen in the :ref:`bundled lithology definitions <pygplates_bundled_lithology_definitions>`,
the first column is the lithology name. The second column is the lithology's sediment density (kg/m3).
The third column is the surface porosity as a fraction, and fourth column is porosity decay (m).

.. note:: You can also use your own lithology files provided they use this format.

Porosity is the contribution of water to the sediment volume and decays exponentially with depth according to the decay constant
(since sediment compaction increases with depth and squeezes out more water from between the sediment grains).

Specifying definitions
^^^^^^^^^^^^^^^^^^^^^^

Any number of lithology files can be specified. In the :ref:`backtrack <pygplates_backtrack>` and
:ref:`backstrip <pygplates_backstrip>` modules these are specified using the ``-l`` command-line option.
With this option you can specify one or more lithologies files including the :ref:`bundled <pybacktrack_reference_bundle_data>`
lithologies. To specify the bundled *primary* and *extended* lithologies you specify ``primary`` or ``extended``.
And to specify your own lithology files you provide the entire filename as usual. If you don't specify the ``-l`` option
then it defaults to using only the *primary* lithologies.

.. note:: | If you use the ``-l`` option but do not specify ``primary`` then the primary lithologies will not be included.
          | However if you don't use the ``-l`` option then *only* the ``primary`` lithologies will be included (they are the default).

Conflicting definitions
^^^^^^^^^^^^^^^^^^^^^^^

When specifying more than one lithology file it is possible to have conflicting definitions.
This occurs when two or more lithology files contain the same lithology *name* but have different values for its
density, surface porosity or porosity decay. You can actually see this in the :ref:`primary and
extended definitions <pygplates_bundled_lithology_definitions>` (for example the *Basalt* lithology).
When there is a conflict, the lithology *definition* is taken from the last conflicting lithology file specified.
For example, if you specify ``-l primary my_conflicting_lithologies.txt`` then conflicting lithologies in
``my_conflicting_lithologies.txt`` override those in ``primary``. However, specifying
``-l my_conflicting_lithologies.txt primary`` will result in ``primary`` overriding those in ``my_conflicting_lithologies.txt``.

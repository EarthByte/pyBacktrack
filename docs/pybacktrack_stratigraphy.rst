.. _pybacktrack_stratigraphy:

Stratigraphy
============

This document covers drill site stratigraphy, and lithology names that reference lithology definitions of density, surface porosity and porosity decay.

.. contents::
   :local:
   :depth: 2

.. _pybacktrack_drill_site:

Drill site
----------

Both backtracking and backstripping involve sediment decompaction over time.
So the main input file for backtracking and backstripping is a drill site.
It provides a record of the present-day litho-stratigraphy of the sediment sitting on top
of the submerged oceanic or continental crust.

The difference between backtracking and backstripping is whether recorded paleo-water depths are
recorded in the drill site file. When there are no recorded paleo-water depths, :ref:`backtracking <pybacktrack_backtrack>`
uses a known model of tectonic subsidence (oceanic or continental) to determine the unknown paleo-water depths.
Conversely, when there is a record of paleo-water depths, :ref:`backstripping <pybacktrack_backstrip>`
uses these known paleo-water depths to determine the unknown history of tectonic subsidence.

.. _pybacktrack_stratigraphy_backtracking_versus_backstripping_sites:

Backtracking versus backstripping sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

ODP drill site 699 is located on deep *ocean* crust and has no recorded paleo-water depths:

.. include:: ../pybacktrack/example_data/ODP-114-699-Lithology.txt
   :literal:

So it is suitable for :ref:`backtracking <pybacktrack_backtrack>`, to find the unknown paleo-water depths.

In contrast, the sunrise drill site is located on shallower *continental* crust and has a record of paleo-water depths:

.. include:: ../pybacktrack/example_data/sunrise_lithology.txt
   :literal:

So it is suitable for :ref:`backstripping <pybacktrack_backstrip>`, to find the unknown history of tectonic subsidence.
Note that this site records the paleo-water depths as two extra columns, for the minimum and maximum water depths.
Backstripping will then use these paleo-water depths, along with sediment decompaction, to reveal the complex tectonic subsidence
of rift stretching at the site location.

.. note:: It is possible, although perhaps not desirable, to backtrack (instead of backstrip) the sunrise drill site
          to provide simulated paleo-water depths via a built-in model of continental rift stretching.
          This would involve ignoring the recorded paleo-water depth columns (using the ``-c`` option of :ref:`backtrack <pybacktrack_backtrack>`)
          and supplying the start and end times of rifting (using the ``-rs`` and ``-re`` options of :ref:`backtrack <pybacktrack_backtrack>`).

Drill site file format
^^^^^^^^^^^^^^^^^^^^^^

As seen in the :ref:`pybacktrack_stratigraphy_backtracking_versus_backstripping_sites`,
the file format of drill sites consist of two main sections. The top section specifies the *attributes*
of the drill site, and the bottom section specifies the *stratigraphic layers*.

The attributes ``SiteLongitude`` and ``SiteLatitude`` specify the drill site location (in degrees).

.. note:: If ``SiteLongitude`` and ``SiteLatitude`` are not specified then they must be specified
          directly in the :ref:`backtrack <pybacktrack_backtrack>` or :ref:`backstrip <pybacktrack_backstrip>`
          module using the ``-w`` command-line option, or the *well_location* argument of the
          :func:`pybacktrack.backtrack_and_write_well` or :func:`pybacktrack.backstrip_and_write_well` function.

For each stratigraphic layer in the drill site there is a mixture of lithologies representing the
stratigraphic composition of that layer. Each lithology (in a layer) is identified by a lithology name
and the fraction it contributes to the layer (where all the fractions must add up to ``1.0``).
Each lithology name is used to look up a list of :ref:`lithology definitions <pybacktrack_lithology_definitions>`
to obtain lithology density, surface porosity and porosity decay.

For each stratigraphic layer in the drill site there is also an age (Ma) and a depth (m) representing the bottom of that layer.
The top age and depth of each layer is the bottom age and depth of the layer above. Since the surface (top) layer
has no layer above it, the top age and depth of the surface layer are 0Ma and 0m respectively. However,
if the ``SurfaceAge`` attribute is specified then it replaces the top age of the surface layer.
A non-zero value of ``SurfaceAge`` implies that sediment deposition ended prior to present day.
In other words, it represents the age of the total sediment surface.

.. note:: The ``SurfaceAge`` attribute is optional, and defaults to 0Ma if not specified.

.. _pybacktrack_base_sediment_layer:

Base sediment layer
^^^^^^^^^^^^^^^^^^^

It is also possible that the sediment thickness recorded at the drill site is less than the total sediment
thickness. This happens when the drill site does not penetrate all the way to the basement depth of oceanic or continental crust.
In this situation a base stratigraphic layer is automatically added during backtracking and backstripping
to represent sediment from the bottom of the drill site down to the basement depth of oceanic or continental crust.

For backtracking, the bottom age of this new base layer is the age of oceanic crust if the drill site is on ocean crust,
or the age that rifting starts if the drill site is on continental crust (since it is assumed that deposition began when
continental stretching started) - see :ref:`backtrack <pybacktrack_backtrack>` for more details.

For backstripping, the bottom age of this new base layer is simply duplicated from the age at the bottom of the drill site
(ie, bottom age of deepest stratigraphic layer). This is because, unlike backtracking, we don't know the age of the crust.
But this is fine since the decompacted output only uses the top age of each layer.
And the decompacted sediment thickness/density (and hence the tectonic subsidence)
still takes into account the base sediment layer and hence the total sediment thickness.
Also since backstripping requires min/max recorded paleo-water depths for each layer, these are simply duplicated
from the bottom layer of the drill site to the new base layer.

By default the lithology of the base layer is ``Shale``, but can be changed using the ``-b`` command-line option in
the :ref:`backtrack <pybacktrack_backtrack>` and :ref:`backstrip <pybacktrack_backstrip>` modules. To determine the
total sediment thickness, a grid is sampled at the drill site location. The default grid is
:ref:`bundled <pybacktrack_reference_bundle_data>` inside ``pybacktrack``. However, you can override this with your
own grid by using the ``-s`` command-line option in the :ref:`backtrack <pybacktrack_backtrack>` and
:ref:`backstrip <pybacktrack_backstrip>` modules.

.. _pybacktrack_bundled_total_sediment_thickness_grid:

The default total sediment thickness grid is:

* Straume, E.O., Gaina, C., Medvedev, S., Hochmuth, K., Gohl, K., Whittaker, J. M., et al. (2019).
  `GlobSed: Updated total sediment thickness in the world's oceans. <https://doi.org/10.1029/2018GC008115>`_
  Geochemistry, Geophysics, Geosystems, 20. DOI: 10.1029/2018GC008115

.. note:: The default total sediment thickness grid was updated in pyBacktrack version 1.4.

.. warning:: If the drill site thickness happens to exceed the total sediment thickness then no base layer is added,
             and a warning is emitted to ``standard error`` on the console.
             This can happen as a result of uncertainties in the sediment thickness grid.

You can optionally write out an amended drill site file that adds this base sediment layer.
This is useful when you want to know the basement depth at the drill site location.

For example, backtracking the ODP drill site 699 (located on *ocean* crust):

.. include:: ../pybacktrack/example_data/ODP-114-699-Lithology.txt
   :literal:

...generates the following amended drill site file:

.. Note we're using 'test_data' instead of 'example_data' since only the former directory contains output files.
.. include:: ../tests/test_data/ODP-114-699_backtrack_amended.txt
   :literal:

...containing the extra base shale layer with a bottom age equal to the age grid sampled at the drill site
and a bottom depth equal to the total sediment thickness.

.. note:: To output an amended drill site file, specify the amended output filename using the ``-o`` command-line option
          in the :ref:`backtrack <pybacktrack_backtrack>` or :ref:`backstrip <pybacktrack_backstrip>` module.

Geohistory analysis
^^^^^^^^^^^^^^^^^^^

The `Decompacting Stratigraphic Layers <https://github.com/EarthByte/pyBacktrack/blob/master/pybacktrack/notebooks/decompacting_stratigraphy.ipynb>`_
notebook shows how to visualize the decompaction of stratigraphic layers at a drill site.

.. note:: The example notebooks are installed as part of the example data which can be installed by following :ref:`these instructions <pybacktrack_install_examples>`.

That notebook decompacts drill sites in the context of :ref:`backtracking <pybacktrack_backtrack>` and :ref:`backstripping <pybacktrack_backstrip>` (covered in later sections), but
regardless of whether we're backstripping or backtracking we are still decompacting the sediment layers in the same way. The following image (from that notebook)
shows the decompaction of a shallow continental drill site over time.

.. figure:: images/geohistory_sunrise.png

.. _pybacktrack_lithology_definitions:

Lithology Definitions
---------------------

The stratigraphy layers in a :ref:`drill site <pybacktrack_drill_site>` contain lithology *names* that reference
lithology *definitions*. Each lithology definition contains a density, a surface porosity and a porosity decay.

These definitions are stored in lithology files. 

.. _pybacktrack_bundled_lithology_definitions:

Bundled lithology definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two lithology files currently :ref:`bundled <pybacktrack_reference_bundle_data>`
inside ``pybacktrack``, one containing *primary* lithologies and the other *extended* lithologies.

The *primary* lithologies (inside ``pybacktrack``) contains the deep-sea lithologies listed in Table 1 in the pyBacktrack paper:

* Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
  `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
  **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313.

.. include:: ../pybacktrack/bundle_data/lithologies/primary.txt
   :literal:

And the *extended* lithologies (inside ``pybacktrack``) mostly contain shallow-water lithologies:

* Baldwin, S., 1999,
  Quantifying the development of a deep sedimentary basin: the Bonaparte Basin, NW Australia, PhD Thesis, Univ. of Cambridge.

.. Note that some 'extended' lithologies are not documented (requested by Dietmar)...
.. .. include:: ../pybacktrack/bundle_data/lithologies/extended.txt
.. include:: document_extended_lithologies.txt
   :literal:

.. _pybacktrack_lithology_file_format:

Lithology file format
^^^^^^^^^^^^^^^^^^^^^

As seen in the :ref:`bundled lithology definitions <pybacktrack_bundled_lithology_definitions>`,
the first column is the lithology name. The second column is the lithology's sediment density (kg/m3).
The third column is the surface porosity as a fraction, and fourth column is porosity decay (m).

.. note:: You can also use your own lithology files provided they use this format.

Porosity is the contribution of water to the sediment volume and decays exponentially with depth according to the decay constant
(since sediment compaction increases with depth and squeezes out more water from between the sediment grains).

.. _pybacktrack_specifying_lithology_definititions:

Specifying lithology definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any number of lithology files can be specified. In the :ref:`backtrack <pybacktrack_backtrack>` and
:ref:`backstrip <pybacktrack_backstrip>` modules these are specified using the ``-l`` command-line option.
With this option you can specify one or more lithologies files including the :ref:`bundled <pybacktrack_reference_bundle_data>`
lithologies. To specify the bundled *primary* and *extended* lithologies you specify ``primary`` and ``extended``.
And to specify your own lithology files you provide the entire filename as usual. If you don't specify the ``-l`` option
then it defaults to using only the *primary* lithologies (*extended* lithologies are not included by default).

.. note:: | If you don't use the ``-l`` option then *only* the ``primary`` lithologies will be included (they are the default).
          | However if you use the ``-l`` option but do not specify ``primary`` then the primary lithologies will **not** be included.

.. _pybacktrack_conflicting_lithology_definititions:

Conflicting lithology definitions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When specifying more than one lithology file it is possible to have conflicting definitions.
This occurs when two or more lithology files contain the same lithology *name* but have different values for its
density, surface porosity or porosity decay.
When there is a conflict, the lithology *definition* is taken from the last conflicting lithology file specified.
For example, if you specify ``-l primary my_conflicting_lithologies.txt`` then conflicting lithologies in
``my_conflicting_lithologies.txt`` override those in ``primary``. However, specifying the reverse order with
``-l my_conflicting_lithologies.txt primary`` will result in ``primary`` overriding those in ``my_conflicting_lithologies.txt``.

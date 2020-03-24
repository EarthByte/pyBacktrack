.. _pygplates_backstrip:

Backstrip
=========

.. contents::
   :local:
   :depth: 2

.. _pygplates_backstrip_overview:

Overview
--------

The ``backstrip`` module is used to find tectonic subsidence from paleo water depths, and sediment decompaction over time.

.. _pygplates_running_backstrip:

Running backstrip
-----------------

You can either run ``backstrip`` as a built-in script, specifying parameters as command-line options (``...``):

.. code-block:: python

    python -m pybacktrack.backstrip ...

...or ``import pybacktrack`` into your own script, calling its functions and specifying parameters as function arguments (``...``):

.. code-block:: python

    import pybacktrack
    
    pybacktrack.backstrip_and_write_well(...)

.. note:: You can run ``python -m pybacktrack.backstrip --help`` to see a description of all command-line options available, or
          see the :ref:`backstripping reference section <pybacktrack_reference_backstripping>` for documentation on the function parameters.

.. _pygplates_backstrip_example:

Example
^^^^^^^

To backstrip the sunrise drill site (located on shallower *continental* crust), and output all available parameters (via the ``-d`` option), we can run it from the command-line as:

.. code-block:: python

    python -m pybacktrack.backstrip \
        -w pybacktrack_examples/test_data/sunrise_lithology.txt \
        -l primary extended \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density min_tectonic_subsidence max_tectonic_subsidence average_tectonic_subsidence min_water_depth max_water_depth average_water_depth lithology \
        -slm Haq87_SealevelCurve_Longterm \
        -o sunrise_backstrip_amended.txt \
        -- \
        sunrise_backstrip_decompat.txt

...or write some Python code to do the same thing:

.. code-block:: python

    import pybacktrack
    
    # Input and output filenames.
    input_well_filename = 'pybacktrack_examples/test_data/sunrise_lithology.txt'
    amended_well_output_filename = 'sunrise_backstrip_amended.txt'
    decompacted_output_filename = 'sunrise_backstrip_decompat.txt'
    
    # Read input well file, and write amended well and decompacted results to output files.
    pybacktrack.backstrip_and_write_well(
        decompacted_output_filename,
        input_well_filename,
        lithology_filenames=[pybacktrack.PRIMARY_BUNDLE_LITHOLOGY_FILENAME,
                             pybacktrack.EXTENDED_BUNDLE_LITHOLOGY_FILENAME],
        sea_level_model=pybacktrack.BUNDLE_SEA_LEVEL_MODELS['Haq87_SealevelCurve_Longterm'],
        decompacted_columns=[pybacktrack.BACKSTRIP_COLUMN_AGE,
                             pybacktrack.BACKSTRIP_COLUMN_COMPACTED_DEPTH,
                             pybacktrack.BACKSTRIP_COLUMN_COMPACTED_THICKNESS,
                             pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_THICKNESS,
                             pybacktrack.BACKSTRIP_COLUMN_DECOMPACTED_DENSITY,
                             pybacktrack.BACKSTRIP_COLUMN_MIN_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKSTRIP_COLUMN_MAX_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKSTRIP_COLUMN_AVERAGE_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKSTRIP_COLUMN_MIN_WATER_DEPTH,
                             pybacktrack.BACKSTRIP_COLUMN_MAX_WATER_DEPTH,
                             pybacktrack.BACKSTRIP_COLUMN_AVERAGE_WATER_DEPTH,
                             pybacktrack.BACKSTRIP_COLUMN_LITHOLOGY],
        # Might be an extra stratigraphic well layer added from well bottom to ocean basement...
        ammended_well_output_filename=amended_well_output_filename)

.. note:: The drill site file ``pybacktrack_examples/test_data/sunrise_lithology.txt`` is part of the :ref:`example data <pybacktrack_install_examples>`.

.. _pygplates_backstrip_output:

Backstrip output
----------------

For each stratigraphic layer in the input drill site file, ``backstrip`` can write one or more parameters to an output file.

Running the :ref:`above example <pygplates_backstrip_example>` on the sunrise drill site:

.. include:: ../pybacktrack/test_data/sunrise_lithology.txt
   :literal:

...produces an :ref:`amended drill site output file <pygplates_backstrip_output_amended_drill_site>`,
and a :ref:`decompacted output file <pygplates_backstrip_output_decompacted>` containing the decompacted output parameters like
sediment thickness and tectonic subsidence.

.. _pygplates_backstrip_output_amended_drill_site:

Amended drill site output
^^^^^^^^^^^^^^^^^^^^^^^^^

The amended drill site output file:

.. include:: ../pybacktrack/test_data/sunrise_backstrip_amended.txt
   :literal:

.. note:: No extra :ref:`base sediment layer <pygplates_base_sediment_layer>` is added from the bottom of the
          drill site (2311 metres) to the total sediment thickness at the drill site (1298.15 metres),
          because the former (bottom of drill site) is already deeper than the latter (total sediment thickness).
          This happens because the :ref:`default total sediment thickness grid <pygplates_base_sediment_layer>` is not
          as accurate near continental margins (compared to deeper ocean basins).

.. _pygplates_backstrip_output_decompacted:

Decompacted output
^^^^^^^^^^^^^^^^^^

The decompacted output file:

.. include:: ../pybacktrack/test_data/sunrise_backstrip_decompat.txt
   :literal:

The *age*, *compacted_depth*, *min_water_depth*, *max_water_depth* and *lithology* columns are the same as the *bottom_age*, *bottom_depth*,
*min_water_depth*, *max_water_depth* and *lithology* columns in the input drill site (except there is also a row associated with the surface age).

The *compacted_thickness* column is the bottom depth of the drill site (2311 metres - noting that there is no base sediment layer in the
:ref:`amended drill site <pygplates_backstrip_output_amended_drill_site>` above) minus *compacted_depth*.
The *decompacted_thickness* column is the thickness of all sediment at the associated age. In other words, at each consecutive age
another stratigraphic layer is essentially removed, allowing the underlying layers to expand (due to their porosity). At present day
(or the surface age) the decompacted thickness is just the compacted thickness. And note that because no extra
:ref:`base sediment layer <pygplates_base_sediment_layer>` was added to the bottom of the drill site (2311 metres) the thickness and density is zero there.
The *decompacted_density* is the average density integrated over the decompacted thickness of the drill site (each stratigraphic layer contains
a mixture of water and sediment according to its porosity at the decompacted depth of the layer).

Finally, *average_water_depth* is just the average *min_water_depth* and *max_water_depth*. And *min_tectonic_subsidence*, *max_tectonic_subsidence* and
*average_tectonic_subsidence* are obtained from *min_water_depth* and *max_water_depth* and *average_water_depth* by adding an isostatic correction of the
decompacted sediment thickness (to obtain the deeper isostatically compensated, sediment-free water depth also known as tectonic subsidence).

.. note:: The output columns are specified using the ``-d`` command-line option (run ``python -m pybacktrack.backstrip --help`` to see all options), or
          using the *decompacted_columns* argument of the :func:`pybacktrack.backstrip_and_write_well` function.
          By default, only *age* and *decompacted_thickness* are output.

.. _pygplates_backstrip_sealevel_variation:

Sea level variation
-------------------

A model of the variation of sea level relative to present day can optionally be used when backstripping.
This adjusts the isostatic correction of the decompacted sediment thickness to take into account sea-level variations.

There are two built-in sea level models :ref:`bundled <pybacktrack_reference_bundle_data>` inside ``backstrip``:

* ``Haq87_SealevelCurve`` - `The Phanerozoic Record of Global Sea-Level Change <https://doi.org/10.1126/science.1116412>`_

* ``Haq87_SealevelCurve_Longterm`` - Normalised to start at zero at present-day.

A sea-level model is optional. If one is not specified then sea-level variation is assumed to be zero.

.. note:: A built-in sea-level model can be specified using the ``-slm`` command-line option (run ``python -m pybacktrack.backstrip --help`` to see all options), or
          using the *sea_level_model* argument of the :func:`pybacktrack.backstrip_and_write_well` function.

.. note:: It is also possible to specify your own sea-level model. This can be done by providing your own text file containing a column of ages (Ma) and a
          corresponding column of sea levels (m), and specifying the name of this file to the ``-sl`` command-line option or to the *sea_level_model* argument
          of the :func:`pybacktrack.backstrip_and_write_well` function.

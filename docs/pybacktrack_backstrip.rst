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

The following sections cover the available parameters (where ``...`` is specified above).

.. note:: You can run ``python -m pybacktrack.backstrip --help`` to see a description of all command-line options available, or
          see the :ref:`backstripping reference section <pybacktrack_reference_backstripping>` for documentation on the function parameters.

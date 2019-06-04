PyBacktrack
===========

.. image:: https://img.shields.io/pypi/v/pybacktrack.svg
   :target: https://pypi.python.org/pypi/pybacktrack/

.. image:: https://img.shields.io/docker/pulls/earthbyte/pybacktrack.svg
   :target: https://hub.docker.com/r/earthbyte/pybacktrack

A tool for reconstructing paleobathymetry on oceanic and continental crust.

PyBacktrack is a Python package that backtracks the paleo-water depth of ocean drill sites through time
by combining a model of tectonic subsidence with decompaction of the site stratigraphic lithologies.
PyBacktrack can also include the effects of mantle-convection driven dynamic topography on paleo-water depth,
as well as sea-level variations. PyBacktrack provides a model of tectonic subsidence on both oceanic and continental crust.
Ocean crust subsidence is based on a user-selected lithospheric age-depth model and the present-day unloaded basement depth.
Continental crust subsidence is based on syn-rift and post-rift subsidence that is modelled using the total sediment thickness at the site
and the timing of the transition from rifting to thermal subsidence. On sites that did not penetrate to basement,
the age-coded stratigraphy is supplemented with a synthetic stratigraphic section that represents the undrilled section,
whose thickness is estimated using a global sediment thickness map. This is essential for estimating the decompacted thickness
of the total sedimentary section, and thus bathymetry, through time.

Documentation
-------------

.. image:: https://readthedocs.org/projects/pybacktrack/badge
   :target: http://pybacktrack.readthedocs.io

Documentation can be found at http://pybacktrack.readthedocs.io and covers installation, examples and an API reference.

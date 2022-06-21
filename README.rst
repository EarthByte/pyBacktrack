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
and the timing of the transition from rifting to thermal subsidence. At drill sites that did not penetrate to basement,
the age-coded stratigraphy is supplemented with a synthetic stratigraphic section that represents the undrilled section,
whose thickness is estimated using a global sediment thickness map. This is essential for estimating the decompacted thickness
of the total sedimentary section, and thus bathymetry, through time.
At drill sites on stretched continental crust where the paleo-water depth is known from benthic fossil assemblages,
tectonic subsidence can be computed via backstripping. The workflow is similar to backtracking, but paleo-water depths and
their uncertainties need to be supplied as part of the input.
In addition to individual 1D drill sites, all submerged present-day crust (assigned a single lithology) can be backtracked and reconstructed to
generate 2D paleobathymetry grids through time.

Documentation
-------------

.. image:: https://readthedocs.org/projects/pybacktrack/badge
   :target: http://pybacktrack.readthedocs.io

The `documentation <http://pybacktrack.readthedocs.io>`_ covers the pyBacktrack Python package. It includes installation, examples and an API reference.

Reference
---------

The following paper covers the theory and algorithms of pyBacktrack:

* Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
  `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
  **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313

It can be downloaded either at `Geochemistry, Geophysics, Geosystems <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2017GC007313>`_ or `ResearchGate <https://www.researchgate.net/publication/325045269_PyBacktrack_10_A_Tool_for_Reconstructing_Paleobathymetry_on_Oceanic_and_Continental_Crust>`_.

.. pyBacktrack documentation master file, created by
   sphinx-quickstart on Thu Mar 15 13:17:25 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. _pybacktrack_index:

PyBacktrack documentation
=========================

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

Reference
---------

The following paper covers the theory and algorithms of pyBacktrack:

* Müller, R. D., Cannon, J., Williams, S. and Dutkiewicz, A., 2018,
  `PyBacktrack 1.0: A Tool for Reconstructing Paleobathymetry on Oceanic and Continental Crust <https://doi.org/10.1029/2017GC007313>`_,
  **Geochemistry, Geophysics, Geosystems,** 19, 1898-1909, doi: 10.1029/2017GC007313

.. note:: It can be downloaded either at `Geochemistry, Geophysics, Geosystems <https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2017GC007313>`_ or
          `ResearchGate <https://www.researchgate.net/publication/325045269_PyBacktrack_10_A_Tool_for_Reconstructing_Paleobathymetry_on_Oceanic_and_Continental_Crust>`_.

Contents
========

.. toctree::
   :maxdepth: 3

   pybacktrack_getting_started
   pybacktrack_overview
   pybacktrack_stratigraphy
   pybacktrack_backtrack
   pybacktrack_backstrip
   pybacktrack_reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



#
# Copyright (C) 2017 The University of Sydney, Australia
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License, version 2, as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

"""A Python package for reconstructing paleobathymetry on oceanic and continental crust.

The ``pybacktrack`` package has the ``__version__`` attribute:
::

    import pybacktrack
    
    pybacktrack.__version__

The following ``pybacktrack`` modules are available:

- :mod:`pybacktrack.backtrack_bundle`
- :mod:`pybacktrack.bundle_data`
- :mod:`pybacktrack.backtrack`
- :mod:`pybacktrack.backstrip`
- :mod:`pybacktrack.age_to_depth`
- :mod:`pybacktrack.util.interpolate`
"""

from pybacktrack.version import __version__, VERSION

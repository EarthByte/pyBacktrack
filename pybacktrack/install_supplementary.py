
#
# Copyright (C) 2022 The University of Sydney, Australia
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

import os.path
import pkg_resources
from distutils import dir_util


def install(
        dest_path="./pybacktrack_supplementary"):
    """Install supplementary scripts in the given location.

    Supplementary scripts are pre/post processing, conversion and test scripts that are not necessary for running the pyBacktrack module.

    WARNING: If the path exists, the example data files will be written into the path
    and will overwrite any existing files with which they collide. The default path
    is chosen to make collision less likely / problematic.
    """

    supplementary_src_path = pkg_resources.resource_filename('pybacktrack', 'supplementary')
    supplementary_dest_path = dest_path

    # The distutils.dir_util.copy_tree function works very similarly to shutil.copytree except that
    # dir_util.copy_tree will just overwrite a directory that exists instead of raising an exception.
    dir_util.copy_tree(supplementary_src_path, supplementary_dest_path, preserve_mode=1, preserve_times=1, preserve_symlinks=1, update=0, verbose=1, dry_run=0)

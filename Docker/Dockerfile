##
#

FROM ubuntu:18.04

RUN apt-get update -y

# Install Python and PIP.
RUN apt-get install -y --no-install-recommends python3 python3-pip
RUN pip3 install --upgrade pip

# Install GMT5.
RUN apt-get install -y --no-install-recommends gmt

RUN apt-get update -y
RUN pip3 install --upgrade pip

# Install Cartopy and its dependencies is rather troublesome.
# Seems need to first install GEOS and PROJ (>= 4.9.0).
# Also need to install 'proj-data' and 'proj-bin' to avoid error "Proj 4.9.0 must be installed".
# 'g++' is required since 'pip3 install cartopy' attempts to build a wheel.
# 'libpython3-dev' is required to avoid missing 'Python.h' when wheel is compiled.
RUN apt-get install -y --no-install-recommends libproj-dev proj-data proj-bin libgeos++-dev libpython3-dev g++
RUN pip3 install -U setuptools  # To avoid error in 'pip3 install cartopy'.
# Also need to install cython, numpy and pyshp before cartopy.
RUN pip3 install --upgrade cython numpy pyshp
# Apparently shapely needs to be built from source to link to geos (before installing cartopy).
RUN pip3 install shapely --no-binary shapely
RUN pip3 install cartopy

# Install matplotlib, jupyter, numpy and netCDF4 for the example notebooks.
RUN pip3 install matplotlib jupyter numpy netCDF4

WORKDIR /usr/src/pybacktrack

# Install pygplates for Python 3.
RUN apt-get install -y --no-install-recommends wget
# Download pyGPlates 0.36 for Ubuntu 18.04 ("pygplates_0.36.0_py36_ubuntu-18.04-amd64.deb").
# This unique link was obtained from the pyGPlates 0.36 download page (https://www.earthbyte.org/download-pygplates-0-36/ ).
# Each download link provided (after entering user information) is a unique link (but it's a permanent link).
RUN wget https://www.earthbyte.org/download/9081/?uid=46bef20416 -O pygplates_0.36.0_py36_ubuntu-18.04-amd64.deb
RUN apt-get install -y --no-install-recommends /usr/src/pybacktrack/pygplates_0.36.0_py36_ubuntu-18.04-amd64.deb
RUN rm pygplates_0.36.0_py36_ubuntu-18.04-amd64.deb
# Tell Python where to find pyGPlates.
ENV PYTHONPATH ${PYTHONPATH}:/usr/lib

# Install pybacktrack (either latest public release, or directly from Github repo).
RUN pip3 install pybacktrack
#RUN apt-get update -y
#RUN apt-get install -y --no-install-recommends git
#RUN pip3 install -U setuptools  # Need pkg_resources to install pybacktrack from Github.
#RUN pip3 install --upgrade "git+https://github.com/EarthByte/pyBacktrack.git#egg=pybacktrack"

# Install pybacktrack example data from the pybacktrack package.
RUN pip3 install -U setuptools  # Need pkg_resources to install examples.
RUN python3 -c 'import pybacktrack; pybacktrack.install_examples()'
# Install pybacktrack supplementary scripts from the pybacktrack package.
RUN python3 -c 'import pybacktrack; pybacktrack.install_supplementary()'

# User can run 'notebook.sh' to start jupyter notebook
# (if they want to look at the example notebooks).
COPY notebook.sh /usr/src/pybacktrack/
RUN chmod a+x /usr/src/pybacktrack/notebook.sh

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8888

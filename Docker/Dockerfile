##
#

FROM ubuntu:22.04

RUN apt-get update -y

# Install Python and PIP.
RUN apt-get install -y --no-install-recommends python3 python3-pip
RUN pip3 install --upgrade pip

# Install GMT5.
RUN apt-get install -y --no-install-recommends gmt

RUN apt-get update -y
RUN pip3 install --upgrade pip

# Install Cartopy.
RUN pip3 install cartopy

# Install extra modules for the example notebooks.
RUN pip3 install matplotlib jupyter numpy netCDF4 gplately joblib plate-model-manager moviepy

WORKDIR /usr/src/pybacktrack

# Install pygplates.
RUN pip3 install pygplates
# PyGPlates requires libGL but it is not copied into the pyGPlates wheel (by 'auditwheel')
# since it is expected to be available by default on all Linux distributions.
# However the libGL.so.1 library, which is part of the OpenGL implementation, is not
# included by default in the minimal Ubuntu 22.04 Docker base image.
# So we need to install it.
RUN apt-get install -y libgl1-mesa-glx libglib2.0-0

# Install pybacktrack (either latest public release, or directly from Github repo).
RUN pip3 install pybacktrack
#RUN apt-get update -y
#RUN apt-get install -y --no-install-recommends git
#RUN pip3 install --upgrade "git+https://github.com/EarthByte/pyBacktrack.git"

# Install pybacktrack example data from the pybacktrack package.
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

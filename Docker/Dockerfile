##
#

FROM ubuntu:16.04

RUN apt-get update

# Install Python and PIP.
RUN apt-get install -y --no-install-recommends python python-pip
RUN pip install --upgrade pip

# Install GMT5.
RUN apt-get install -y --no-install-recommends gmt

# Install pygplates.
COPY Docker/pygplates-ubuntu-xenial_2.1_1_amd64.deb /usr/src/install/
RUN apt-get install -y --no-install-recommends /usr/src/install/pygplates-ubuntu-xenial_2.1_1_amd64.deb
RUN cp /usr/lib/pygplates/revision18/pygplates.so /usr/lib/python2.7/dist-packages/

# Install pybacktrack.
RUN pip install pybacktrack

# Copy pybacktrack example data.
COPY pybacktrack/test_data/ /usr/src/pybacktrack/pybacktrack_example_data/

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

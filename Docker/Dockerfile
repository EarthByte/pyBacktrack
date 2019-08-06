##
#

FROM ubuntu:16.04

RUN apt-get update -y

# Install Python and PIP.
RUN apt-get install -y --no-install-recommends python python-pip
RUN pip install --upgrade pip

# Install GMT5.
RUN apt-get install -y --no-install-recommends gmt

WORKDIR /usr/src/pybacktrack

# Install pygplates.
RUN apt-get install -y --no-install-recommends wget
RUN wget http://sourceforge.net/projects/gplates/files/pygplates/beta-revision-18/pygplates-ubuntu-xenial_2.1_1_amd64.deb
RUN apt-get install -y --no-install-recommends /usr/src/pybacktrack/pygplates-ubuntu-xenial_2.1_1_amd64.deb
RUN rm pygplates-ubuntu-xenial_2.1_1_amd64.deb
# Tell Python where to find pyGPlates.
Env PYTHONPATH ${PYTHONPATH}:/usr/lib:/usr/lib/pygplates/revision18/

# Install pybacktrack (either latest public release, or directly from Github repo).
RUN pip install pybacktrack
#RUN apt-get install -y --no-install-recommends git
#RUN pip install "git+https://github.com/EarthByte/pyBacktrack.git#egg=pybacktrack"

# Install pybacktrack example data from the pybacktrack package.
RUN pip install -U setuptools  # Need pkg_resources to install examples.
RUN python -c 'import pybacktrack; pybacktrack.install_examples()'

# Seem to need this to fix install error for matplotlib (involving subprocess32).
RUN apt-get install -y python-subprocess32
# Install matplotlib and jupyter for the example notebooks.
RUN pip install matplotlib jupyter

# User can run 'notebook.sh' to start jupyter notebook
# (if they want to look at the example notebooks).
COPY notebook.sh /usr/src/pybacktrack/
RUN chmod a+x /usr/src/pybacktrack/notebook.sh

# Clean up APT when done.
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 8888

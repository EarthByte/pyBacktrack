To build a Docker image:

First download the run the pyGPlates Ubuntu installation file 'pygplates-ubuntu-xenial_2.1_1_amd64.deb'
from http://www.gplates.org and move it to this directory ('Docker/').

Then run the following command in Docker in the parent (pyBacktrack) directory:

  docker build -f Docker/Dockerfile --tag=pybacktrack .
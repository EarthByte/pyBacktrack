# PyBacktrack Documentation

The generated documentation can be found at http://pybacktrack.readthedocs.io

## Generating documentation

[Read the Docs](https://readthedocs.org) has been set up via [web hooks](https://docs.readthedocs.io/en/latest/guides/setup/git-repo-manual.html) to automatically generate documentation whenever a commit is made to this GitHub repository.
It does this by reading and processing our *docs* directory using Sphinx.
Our *conf.py* Sphinx configuration file specifies the *autodoc* extension which searches the module/class/function docstrings in our *PyBacktrack* Python package and parses the reStructuredText (reST) contained within to provide the reference API part of the documentation.

**Note:** Since we haven't (yet) configured "Read the Docs" to install pygplates (a dependency of pybacktrack) we mock it out to avoid import errors when Sphinx builds documentation (see *conf.py*).

**Note:** We use [numpydoc](http://numpydoc.readthedocs.io) style docstrings since it is easier to read directly in the Python source code than reST.
The Sphinx extension *napoleon* enables conversion of numpydoc and google style docstrings to reST during the documentation build phase.
The docstrings in the *pybacktrack* Python package use the numpydoc style.
The *napoleon* extension is included with Sphinx >= 1.3 (so we make that our Sphinx requirement).

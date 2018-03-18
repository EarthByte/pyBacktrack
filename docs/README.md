# PyBacktrack Documentation

The generated documentation can be found at http://pybacktrack.readthedocs.io

## Generating documentation

[Read the Docs](https://readthedocs.org) has been set up via [web hooks](https://docs.readthedocs.io/en/latest/webhooks.html) to automatically generate documentation whenever a commit is made to this GitHub repository.
It does this by reading and processing our *docs* directory using Sphinx.
Our *conf.py* Sphinx configuration file specifies the *autodoc* extension which searches the module/class/function docstrings in our *PyBacktrack* Python package and parses the reStructuredText (reST) contained within to provide the reference API part of the documentation.

**Note:** In the [advanced settings](https://readthedocs.org/dashboard/pybacktrack/advanced) of the *PyBacktrack* project in the *Read the Docs*, accessible by *PyBacktrack* project maintainers, the check box *Use system packages* should be checked.
This is needed because C extension modules like *numpy* are installed in the global site-packages directory but not in the virtual environment.

**Note:** *Read the Docs* does not have *pygplates* (a C extension) installed in its build system.
So we mock out *pygplates* to avoid an import error during the Sphinx documentation build phase.
This is done using the technique prescribed in the [Read the Docs FAQ](http://docs.readthedocs.io/en/latest/faq.html) which requires the *mock* module (see *conf.py*).

**Note:** We use [numpydoc](http://numpydoc.readthedocs.io) style docstrings since it is easier to read directly in the Python source code than reST.
The Sphinx extension *napoleon* enables conversion of numpydoc and google style docstrings to reST during the documentation build phase.
The docstrings in the *pybacktrack* Python package use the numpydoc style.
Also note that "Read the Docs" uses a version of Sphinx >= 1.3 (these versions include napoleon as a bundled extension).
However version < 1.3 requires you to install 'sphinxcontrib.napoleon', so if you are building documentation locally (via 'make html', or 'python setup.py build_sphinx', for example),
and you are using Sphinx < 1.3, then you'll need to 'pip install sphinxcontrib.napoleon'.

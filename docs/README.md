# PyBacktrack Documentation

The generated documentation can be found at http://pybacktrack.readthedocs.io

## Generating documentation

[Read the Docs](https://readthedocs.org) has been set up via [web hooks](https://docs.readthedocs.io/en/latest/webhooks.html) to automatically generate documentation whenever a commit is made to this GitHub repository.
It does this by reading and processing our *docs* directory using Sphinx.
Our *conf.py* Sphinx configuration file specifies the *autodoc* extension which searches the module/class/function docstrings in our *PyBacktrack* Python package and parses the reStructuredText (reST) contained within to provide the reference API part of the documentation.

Note: In the *advanced settings* of the *PyBacktrack* in the *Read the Docs* project, the check box *Use system packages* should be checked.
This is needed because C extension modules like *numpy* are installed in the global site-packages directory but not in the virtual environment.

Note: *Read the Docs* does not have pygplates (a C extension) installed in its build system.
So we mock out *pygplates* to avoid an import error during the Sphinx documentation build phase.
This is done using the technique prescribed in the [Read the Docs FAQ](http://docs.readthedocs.io/en/latest/faq.html) which requires the *mock* module (see *conf.py*).

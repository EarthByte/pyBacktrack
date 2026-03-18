.. _pybacktrack_getting_started:

Getting Started
===============

.. contents::
   :local:
   :depth: 3


.. _pybacktrack_installation:

Installation
++++++++++++

.. _pybacktrack_install_pybacktrack:

Install pybacktrack
-------------------

You can install ``pybacktrack`` in *one* of the following ways:

#. :ref:`Using conda <pybacktrack_install_using_conda>`:

   This is recommended, since it installs **all** dependencies of ``pybacktrack``.

#. :ref:`Using pip <pybacktrack_install_using_pip>`:

   This will install all dependencies except ``gmt`` (which must be installed manually).

#. :ref:`Using Docker <pybacktrack_install_using_docker>`:

   This might be less familiar, but does come with all the dependencies pre-installed.

.. _pybacktrack_install_using_conda:

Using conda
^^^^^^^^^^^

PyBacktrack can be installed using the `conda package manager <https://docs.conda.io/projects/conda/en/latest/user-guide/index.html>`__.

.. note:: We recommend installing `Miniconda <https://www.anaconda.com/docs/getting-started/miniconda/main>`__.

To install the latest *stable* version of ``pybacktrack``, type the following in a terminal or command window:
::

  conda install -c conda-forge pybacktrack

.. note:: On macOS and Ubuntu this is done in a *Terminal* window, and on Windows you'll need to open an *Anaconda prompt* from the Start menu.

We recommend installing pyBacktrack into a *new* conda environment.
For example, the following creates and activates a Python 3.13 environment named ``pybacktrack_py313`` containing pyBacktrack and all its dependencies:
::

  conda create -n pybacktrack_py313 -c conda-forge python=3.13 pybacktrack
  conda activate pybacktrack_py313

You can then use pyBacktrack. For example, to see the pyBacktrack version:
::

  python -c "import pybacktrack; print(pybacktrack.__version__)"

.. _pybacktrack_install_using_pip:

Using pip
^^^^^^^^^

PyBacktrack can be installed using `pip (the package installer for Python) <https://pip.pypa.io/en/stable/>`__.

This will install all dependencies except ``gmt``, which must be installed manually.

The following sections demonstrate how to first install ``gmt`` and then install ``pybacktrack``.

.. contents::
   :local:
   :depth: 2

.. _pybacktrack_requirements:

Requirements
************

PyBacktrack depends on:

- `NumPy <http://www.numpy.org/>`__
- `SciPy <https://www.scipy.org/>`__
- `PyGPlates <http://www.gplates.org/>`__
- `Generic Mapping Tools (GMT) <https://www.generic-mapping-tools.org/>`__ (>=5.0.0)

``numpy``, ``scipy`` and ``pygplates`` are automatically installed by pip when ``pybacktrack`` is installed.

However ``gmt`` (version 5 or above) needs to be installed manually.
GMT is called via the command-line (shell) and so it just needs to be in the ``PATH`` in order for pyBacktrack to find it.

.. note:: | Ensure GMT version 5 or above is installed.
          | This is required to support the NetCDF4 format of the :ref:`grid files bundled in pyBacktrack<pybacktrack_reference_bundle_data>`.

The following sections show how to install GMT and Python, on Ubuntu and macOS.

.. _pybacktrack_install_requirements_ubuntu:

Install GMT and Python/pip on Ubuntu
""""""""""""""""""""""""""""""""""""

This example assumes you are using a *Ubuntu* Linux operating system.

First install GMT 5:
::

  sudo apt install gmt

Then install Python 3 (and pip):
::

  sudo apt update
  
  sudo apt install python3 python3-pip
  sudo pip3 install --upgrade pip

.. note:: This will later require typing ``python3`` on the command-line (instead of ``python``) to use Python.

.. _pybacktrack_install_requirements_mac:

Install GMT and Python/pip on macOS
"""""""""""""""""""""""""""""""""""

This example uses the `Macports package manager <https://www.macports.org/>`__ for macOS.

First install GMT 5:
::

  sudo port install gmt5

.. note:: | You will likely need to add ``/opt/local/lib/gmt5/bin/`` to your ``PATH`` environment variable.
          | You can do this in your ``~/.bashrc``, ``~/.bash_profile`` or ``~/.zprofile`` file so that ``PATH``
            is automatically set each time you open a new terminal window.

| Then install Python 3 (and Pip).
| For example, if you want Python 3.13:

  ::

    sudo port install python313
    sudo port install py313-pip

Then point the default ``python3`` to the newly installed Python 3.13:
::

  sudo port select --set python3 python313

.. note:: | This means when you type ``python3`` you will use Python 3.13.
          | If you prefer to type ``python`` (instead of ``python3``) then you can instead run:

            ::
          
              sudo port select --set python python313

.. _pybacktrack_pip_install_pybacktrack:

Install pybacktrack
*******************

This section demonstrates how to install pyBacktrack into the **global** Python installation.

.. warning:: | We **highly** recommend :ref:`installing pyBacktrack into a virtual environment <pybacktrack_getting_started_install_into_a_venv>`.
             | This can avoid unintended side effects on other projects or the global Python installation.

On **macOS** and **Linux**, to install the latest stable version of pyBacktrack type the following in a terminal:
::

  python3 -m pip install pybacktrack

.. note:: If ``python3`` doesn't work then try ``python``.

On **Windows**, to install the latest stable version of pyBacktrack type the following in a command window:
::

  py -m pip install pybacktrack

.. note:: On the Windows platform, ``py`` installs into the *default* version of Python (if you have multiple Python installations).
          However you can install into a specific Python version. For example, to install into Python 3.13 replace ``py`` with ``py -3.13``.

.. _pybacktrack_getting_started_install_into_a_venv:

Install into a virtual environment
""""""""""""""""""""""""""""""""""

This section demonstrates how to install the latest *stable* version of pyBacktrack into a new `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_.

In the following example, we create and *activate* a Python environment named ``pybacktrack_venv`` that will contain pyBacktrack (and all its dependencies except ``gmt``).
This will create a sub-directory called ``pybacktrack_venv`` in the current directory.

On **macOS** and **Linux**:
::

  python3 -m venv pybacktrack_venv
  source pybacktrack_venv/bin/activate

.. note:: If ``python3`` doesn't work then try ``python``.

On **Windows**:
::
  
  py -m venv pybacktrack_venv
  pybacktrack_venv\Scripts\activate.bat

.. note:: On the Windows platform, ``py`` creates a virtual environment that uses the *default* version of Python (if you have multiple Python installations).
  However you can create an environment with a specific Python version. For example, for Python 3.13 replace ``py`` with ``py -3.13``.

Then you can install pyBacktrack into the *activated* environment with:
::

  python -m pip install pybacktrack

...or if you have an older version of ``pybacktrack`` already installed, then use the ``--upgrade`` flag to get the latest version:
::

  python -m pip install --upgrade pybacktrack

.. note:: Once a virtual environment has been *activated* you can use ``python`` on **all** platforms.
  In other words, you do **not** need to use ``python3`` on macOS and Linux, or ``py`` on Windows.

| Now you can use pyBacktrack.
| For example, to see the pyBacktrack version:

::

  python -c "import pybacktrack; print(pybacktrack.__version__)"

.. _pybacktrack_getting_started_install_latest_dev_version:

Install latest *development* version
""""""""""""""""""""""""""""""""""""

Up until now, we've been installing the latest *stable* version of pyBacktrack.
There is also the latest *development* version that contains any updates since the latest *stable* version.
These updates are in development, and have not necessarily been tested or documented.

To install the latest *development* version, run:
::

  python -m pip install "git+https://github.com/EarthByte/pyBacktrack.git"

.. note:: You'll first need to `install git <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_ (if you don't already have it).

          If you already have it, but are getting an error ending with "*tlsv1 alert protocol version*", then you may need to update your ``git``
          (this is apparently due to an `update on GitHub <https://blog.github.com/2018-02-23-weak-cryptographic-standards-removed>`__).

...or you can download the `pyBacktrack source code <https://github.com/EarthByte/pyBacktrack>`__, extract it to a local directory, and run:
::

  python -m pip install <path-to-local-directory>

.. note:: This assumes a virtual environment has already been *activated* as described in :ref:`pybacktrack_getting_started_install_into_a_venv`.
          Otherwise you might need to replace ``python`` with ``python3`` (on macOS and Linux) or ``py`` (on Windows).

.. _pybacktrack_install_using_docker:

Using Docker
^^^^^^^^^^^^

This method of running ``pybacktrack`` relies on `Docker <https://www.docker.com/>`__, so before installing
the ``pybacktrack`` docker image, ensure you have installed Docker.

.. note:: | On Windows platforms you can install `Docker Desktop for Windows <https://docs.docker.com/docker-for-windows/install/>`__.
            Note that `Docker Toolbox <https://docs.docker.com/toolbox/overview/>`__ has been deprecated (and now *Docker Desktop for Windows* is recommended).
          | A similar situation applies on Mac platforms where you can install
            `Docker Desktop for Mac <https://docs.docker.com/docker-for-mac/install/>`__ (with *Docker Toolbox* being deprecated).

Once Docker is installed, open a terminal (command-line interface).

.. note:: | For `Docker Desktop for Windows <https://docs.docker.com/docker-for-windows/install/>`__ and
            `Docker Desktop for Mac <https://docs.docker.com/docker-for-mac/install/>`__ this a regular command-line terminal.
          | And on Linux systems this also is a regular command-line terminal.

To install the ``pybacktrack`` docker image, type:

.. code-block:: none

    docker pull earthbyte/pybacktrack

To run the docker image, type:

.. code-block:: none

    docker run -it --rm -p 18888:8888 -w /usr/src/pybacktrack earthbyte/pybacktrack

| This should bring up a command prompt **inside** the running docker container.
| The current working directory should be ``/usr/src/pybacktrack/``.
| It should have a ``pybacktrack_examples`` sub-directory containing example data.

.. note:: On Linux systems you may have to use `sudo` when running `docker` commands. For example:
          ::
          
            sudo docker pull earthbyte/pybacktrack
            sudo docker run -it --rm -p 18888:8888 -w /usr/src/pybacktrack earthbyte/pybacktrack

From the current working directory you can run the :ref:`backtracking example <pybacktrack_a_backtracking_example>` below,
or any :ref:`other examples <pybacktrack_overview>` in this documentation. For example, you could run:

.. code-block:: python

    python3 -m pybacktrack.backtrack_cli -w pybacktrack_examples/example_data/ODP-114-699-Lithology.txt -d age water_depth -- ODP-114-699_backtrack_decompacted.txt

If you wish to run the `example notebooks <https://github.com/EarthByte/pyBacktrack/tree/master/pybacktrack/notebooks>`__
then there is a ``notebook.sh`` script to start a Jupyter notebook server in the running docker container:

.. code-block:: none

    ./notebook.sh

Then you can start a web browser on your local machine and type the following in the URL field:

.. code-block:: none

    http://localhost:18888/tree

| This will display the current working directory in the docker container.
| In the web browser, navigate to ``pybacktrack_examples`` and then ``notebooks``.
| Then click on a notebook (such as `backtrack.ipynb <https://github.com/EarthByte/pyBacktrack/blob/master/pybacktrack/notebooks/backtrack.ipynb>`__).
| You should be able to run the notebook, or modify it and then run it.

.. _pybacktrack_install_examples:

Install the examples
--------------------

Before running the example below, or any :ref:`other examples <pybacktrack_overview>`, you'll also need to install the example data (from the pybacktrack package itself).
This assumes you've already :ref:`installed pybacktrack <pybacktrack_install_pybacktrack>`.

The following command installs the examples (example data and notebooks) to a new sub-directory of your *current working directory* called ``pybacktrack_examples``:

.. code-block:: python

    python -c "import pybacktrack; pybacktrack.install_examples()"

.. note:: The *current working directory* is whatever directory you are in when you run the above command.

.. note:: | Alternatively you can choose a different sub-directory by providing an argument to the ``install_examples()`` function above.
          | For example, ``python -c "import pybacktrack; pybacktrack.install_examples('pybacktrack/examples')"``
            creates a new sub-directory of your *current working directory* called ``pybacktrack/examples``.
          | However the example below assumes the default directory (``pybacktrack_examples``).

.. _pybacktrack_install_supplementary:

Install supplementary scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can optionally install supplementary scripts. These are not necessary for running the ``pybacktrack`` module.
They are various pre/post processing, conversion and test scripts that have only been included for reference (for those interested).

The following command installs the supplementary scripts to a new sub-directory of your *current working directory* called ``pybacktrack_supplementary``:

.. code-block:: python

    python -c "import pybacktrack; pybacktrack.install_supplementary()"

.. note:: Similar to :ref:`installing the examples <pybacktrack_install_examples>`, you can specify your own sub-directory (to the ``install_supplementary()`` function).

.. _pybacktrack_a_backtracking_example:

A Backtracking Example
++++++++++++++++++++++

Once :ref:`installed <pybacktrack_installation>`, ``pybacktrack`` is available to:

#. run built-in scripts (inside ``pybacktrack``), or
#. ``import pybacktrack`` into your own script.

The following example is used to demonstrate both approaches. It backtracks an ocean drill site and saves the output to a text file by:

- reading the ocean drill site file ``pybacktrack_examples/example_data/ODP-114-699-Lithology.txt``,

  .. note:: | This file is part of the :ref:`example data <pybacktrack_install_examples>`.
            | However if you have your own ocean drill site file then you can substitute it in the example below if you want.

- backtracking it using:

  * the ``M2`` dynamic topography model, and
  * the ``Haq87_SealevelCurve_Longterm`` sea-level model,

- writing the amended drill site to ``ODP-114-699_backtrack_amended.txt``, and
- writing the following columns to ``ODP-114-699_backtrack_decompacted.txt``:

  * age
  * compacted_depth
  * compacted_thickness
  * decompacted_thickness
  * decompacted_density
  * decompacted_sediment_rate
  * decompacted_depth
  * dynamic_topography
  * water_depth
  * tectonic_subsidence
  * paleo_longitude
  * paleo_latitude
  * lithology

.. _pybacktrack_use_a_builtin_module_script:

Use a built-in module script
----------------------------

Since there is a ``backtrack`` module inside ``pybacktrack`` that can be run as a script,
we can invoke it on the command-line using ``python -m pybacktrack.backtrack_cli`` followed by command line options that are specific to that module.
This is the easiest way to run backtracking.

To see its command-line options, run:

.. code-block:: python

    python -m pybacktrack.backtrack_cli --help

The backtracking example can now be demonstrated by running the script as:

.. code-block:: python

    python -m pybacktrack.backtrack_cli \
        -w pybacktrack_examples/example_data/ODP-114-699-Lithology.txt \
        -d age compacted_depth compacted_thickness decompacted_thickness decompacted_density decompacted_sediment_rate decompacted_depth dynamic_topography water_depth tectonic_subsidence paleo_longitude paleo_latitude compacted_density composite_porosity composite_decay lithology \
        -ym M2 \
        -slm Haq87_SealevelCurve_Longterm \
        -o ODP-114-699_backtrack_amended.txt \
        -- \
        ODP-114-699_backtrack_decompacted.txt

.. _pybacktrack_import_into_your_own_script:

Import into your own script
---------------------------

An alternative to running a built-in script is to write your own script (using a text editor) that imports ``pybacktrack`` and
calls its functions. You might do this if you want to combine pyBacktrack functionality with other research functionality into a single script.

The following Python code does the same as the :ref:`built-in script<pybacktrack_use_a_builtin_module_script>` by calling the
:func:`pybacktrack.backtrack_and_write_well` function:

.. code-block:: python

    import pybacktrack
    
    # Input and output filenames.
    input_well_filename = 'pybacktrack_examples/example_data/ODP-114-699-Lithology.txt'
    amended_well_output_filename = 'ODP-114-699_backtrack_amended.txt'
    decompacted_output_filename = 'ODP-114-699_backtrack_decompacted.txt'
    
    # Read input well file, and write amended well and decompacted results to output files.
    pybacktrack.backtrack_and_write_well(
        decompacted_output_filename,
        input_well_filename,
        dynamic_topography_model='M2',
        sea_level_model='Haq87_SealevelCurve_Longterm',
        # The columns in decompacted output file...
        decompacted_columns=[pybacktrack.BACKTRACK_COLUMN_AGE,
                             pybacktrack.BACKTRACK_COLUMN_COMPACTED_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_COMPACTED_THICKNESS,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_THICKNESS,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DENSITY,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_SEDIMENT_RATE,
                             pybacktrack.BACKTRACK_COLUMN_DECOMPACTED_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_DYNAMIC_TOPOGRAPHY,
                             pybacktrack.BACKTRACK_COLUMN_WATER_DEPTH,
                             pybacktrack.BACKTRACK_COLUMN_TECTONIC_SUBSIDENCE,
                             pybacktrack.BACKTRACK_COLUMN_SEA_LEVEL,
                             pybacktrack.BACKTRACK_COLUMN_PALEO_LONGITUDE,
                             pybacktrack.BACKTRACK_COLUMN_PALEO_LATITUDE,
                             pybacktrack.BACKTRACK_COLUMN_COMPACTED_DENSITY,
                             pybacktrack.BACKTRACK_COLUMN_COMPOSITE_POROSITY,
                             pybacktrack.BACKTRACK_COLUMN_COMPOSITE_DECAY,
                             pybacktrack.BACKTRACK_COLUMN_LITHOLOGY],
        # Might be an extra stratigraphic well layer added from well bottom to basement...
        ammended_well_output_filename=amended_well_output_filename)

If you save the above code to a file called ``my_backtrack_script.py`` then you can run it as:

.. code-block:: python

    python my_backtrack_script.py

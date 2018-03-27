# PyBacktrack Testing

The tests can be run with:

```
  python setup.py test
```

...this will automatically install `pytest` and its plugins `pytest-pep8` and `pytest-runner` (to the local './.eggs' directory) if they are not installed in the system.

Alernatively you can simply run:

```
  pytest
```

...provided `pytest` has been installed (eg, via `pip install pytest`).

In addition to running the tests, you can also check that the code style of `pybacktrack` is compatible with [PEP8](https://www.python.org/dev/peps/pep-0008/) by running:

```
  python setup.py test --addopts="--pep8"
```

...which, as mentioned above, will download the `pytest-pep8` plugin locally (if it's not installed in the system).

Or, if you have `pytest-pep8` installed (eg, via `pip install pytest-pep8`), you can simply run:

```
  pytest --pep8
```

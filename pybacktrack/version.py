from importlib.metadata import version, PackageNotFoundError
from packaging.version import Version

try:
    # Version string satifying PEP 440 (e.g., "1.5.0").
    __version__ = version("pybacktrack")
    VERSION = __version__
    # Version object for querying the version, such as checking if it's a pre-release (with '_version.is_prerelease').
    _version = Version(__version__)
except PackageNotFoundError:
    # Package is not installed (e.g., running from a source checkout).
    pass
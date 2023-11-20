VERSION_MAJOR = 1
VERSION_MINOR = 5
VERSION_PATCH = 0
# Pre-release suffix should follow the PEP440 versioning scheme (https://www.python.org/dev/peps/pep-0440/).
# Note: It should be empty for public releases.
VERSION_PRERELEASE_SUFFIX = '.dev8'

__version__ = '{}.{}.{}{}'.format(VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_PRERELEASE_SUFFIX)
VERSION = __version__

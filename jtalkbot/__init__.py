"""A discord bot talking Japanese. """

from importlib import metadata


__all__ = ['VERSION']


try:
    VERSION = metadata.version(__name__)
except metadata.PackageNotFoundError:
    pass

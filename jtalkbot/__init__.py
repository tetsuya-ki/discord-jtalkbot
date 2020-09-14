"""A discord bot talking Japanese. """

from importlib import metadata


__all__ = ['VERSION', 'get_setting_schema', 'get_settings', 'load_settings']


try:
    VERSION = metadata.version(__name__)
except metadata.PackageNotFoundError:
    pass

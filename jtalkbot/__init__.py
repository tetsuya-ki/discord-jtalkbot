"""A discord bot talking Japanese. """

import os
import sys
from argparse import Namespace
from importlib import metadata
from typing import Optional

from . import settings


__all__ = ['VERSION', 'get_setting_schema', 'get_settings', 'load_settings']


try:
    VERSION = metadata.version(__name__)
except metadata.PackageNotFoundError:
    pass


__setting_schema__ = None
__settings__ = None


def get_setting_schema() -> settings.SettingSchema:
    """retrun global `SettingSchema` object """

    global __setting_schema__
    if __setting_schema__ is None:
        __setting_schema__ = settings.SettingSchema('jtalkbot')
    return __setting_schema__


def get_settings() -> Optional[Namespace]:
    """return global settings namespace object """

    return __settings__


def load_settings() -> None:
    """load settings in specific order and return global namespace object """

    setting_schema = get_setting_schema()

    d_settings = setting_schema.parse_env()
    filename = 'jtalkbot-config.json'
    if os.path.exists(filename):
        with open(filename, encoding='utf-8') as f:
            json_s = f.read()
        d_settings.update(setting_schema.parse_json(json_s))
    d_settings.update(setting_schema.parse_args())

    global __settings__
    __settings__ = Namespace(**d_settings)

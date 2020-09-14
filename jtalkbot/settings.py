"""reginster / load / save settings """


import json
import os
import sys
from argparse import ArgumentParser, Namespace
from typing import Any, Dict, Optional, Sequence, Union


class SettingField(object):
    """registered setting argument """

    __slots__ = ['name', 'type', 'default', 'help']

    def __init__(self, name: str, *,
                 type: type = str,
                 default: Union[str, int, float] = None,
                 help: Optional[str] = None):
        """constructor """

        self.name = name
        self.type = type
        self.default = default
        self.help = help


class SettingSchema(object):
    """setting definition """

    def __init__(self, prefix: str):
        """constructor """

        self.prefix = prefix
        self.fields = {}

    def register(self, name: str, *,
                 type: type = str,
                 default: Union[str, int, float] = None,
                 help: Optional[str] = None):
        """register a setting option """

        field = SettingField(name, type=type, default=default, help=help)
        self.fields[name] = field

    def parse_json(self, json_str: str) -> Dict[str, Any]:
        """parse given json string and return settings dict

        >>> setting_schema = SettingSchema('test')
        >>> setting_schema.register('a', type=int)
        >>> setting_schema.register('b')
        >>> s = '{ "a": 1, "b": "two" }'
        >>> setting_schema.parse_json(s)
        {'a': 1, 'b': 'two'}
        """

        result = json.loads(json_str)
        d = {}
        for name, field in self.fields.items():
            value = result.get(name, field.default)
            if value is not None:
                value = field.type(value)
            d[name] = value
        return d

    def parse_args(self, args: Optional[Sequence[str]] = None
                   ) -> Dict[str, Any]:
        """parse args and return settings dict

        >>> setting_schema = SettingSchema('test')
        >>> setting_schema.register('a', type=int)
        >>> setting_schema.register('b')
        >>> a = ['--a', '1', '--b', 'two']
        >>> setting_schema.parse_args(a)
        {'a': 1, 'b': 'two'}
        """

        parser = ArgumentParser()
        for name, field in self.fields.items():
            parser.add_argument('--' + name, type=field.type,
                                default=field.default, help=field.help)
        namespace = parser.parse_args(args)
        return {k: v for k, v in vars(namespace).items() if v is not None}

    def parse_env(self, env: Optional[Dict[str, str]] = None
                  ) -> Dict[str, Any]:
        """parse environment value and return settings namespace

        >>> setting_schema = SettingSchema('test')
        >>> setting_schema.register('a', type=int)
        >>> setting_schema.register('b')
        >>> env = {'TEST_A': '1', 'TEST_B': 'two'}
        >>> setting_schema.parse_env(env)
        {'a': 1, 'b': 'two'}
        """

        if env is None:
            env = os.environ
        d = {}
        for name, field in self.fields.items():
            key = '_'.join([self.prefix, name]).upper()
            value = env.get(key, field.default)
            if value is not None:
                value = field.type(value)
            d[name] = value
        return d


__setting_schema__ = None
__settings__ = None


def get_setting_schema() -> SettingSchema:
    """retrun global `SettingSchema` object """

    global __setting_schema__
    if __setting_schema__ is None:
        __setting_schema__ = SettingSchema('jtalkbot')
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()

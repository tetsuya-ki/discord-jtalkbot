"""reginster / load / save settings """


import argparse
import json
import os
from typing import Any, Dict, Optional, Sequence


class SettingField(object):
    """registered setting argument """

    __slots__ = ['name', 'type', 'default', 'help']

    def __init__(self, name, *,
                 type: type = str, default: Any = None, help: str = None):
        """constructor """

        self.name = name
        self.type = type
        self.default = default
        self.help = help


class Settings(object):
    """store settings """

    def __init__(self, prefix: str):
        """constructor """

        self.prefix = prefix
        self.fields = {}

    def register(self, name: str, *,
                 type: type = str, default: Any = None, help: str = None):
        """register a setting option """

        field = SettingField(name, type=type, default=default, help=help)
        self.fields[name] = field

    def parse_json(self, json_str: str) -> Dict[str, Any]:
        """parse given json string and return settings dict

        >>> settings = Settings('test')
        >>> settings.register('a', type=int)
        >>> settings.register('b')
        >>> s = '{ "a": 1, "b": "two" }'
        >>> settings.parse_json(s)
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

        >>> settings = Settings('test')
        >>> settings.register('a', type=int)
        >>> settings.register('b')
        >>> a = ['--a', '1', '--b', 'two']
        >>> settings.parse_args(a)
        {'a': 1, 'b': 'two'}
        """

        parser = argparse.ArgumentParser()
        for name, field in self.fields.items():
            parser.add_argument('--' + name, type=field.type,
                                default=field.default, help=field.help)
        namespace = parser.parse_args(args)
        return vars(namespace)

    def parse_env(self, env: Optional[Dict[str, str]] = None
                  ) -> Dict[str, Any]:
        """parse environment value and return settings namespace

        >>> settings = Settings('test')
        >>> settings.register('a', type=int)
        >>> settings.register('b')
        >>> env = {'TEST_A': '1', 'TEST_B': 'two'}
        >>> settings.parse_env(env)
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()

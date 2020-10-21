"""reginster / load / save application environment """


import json
import os
import sys
from argparse import ArgumentParser, Namespace
from typing import (Dict, ItemsView, Iterable, KeysView, Optional, Sequence,
                    Union, ValuesView)


FieldValue = Union[str, int, float]


class EnvField(object):
    """registered environment field """

    __slots__ = ['name', 'type', 'default', 'help']

    def __init__(self, name: str, *,
                 type: type = str,
                 default: Optional[FieldValue] = None,
                 help: Optional[str] = None):
        """constructor """

        self.name = name
        self.type = type
        self.default = default
        self.help = help


class ApplicationEnvironment(object):
    """application environment """

    def __init__(self):
        """constructor """

        self.fields = {}
        self._dict = {}

    def __contains__(self, item: str) -> bool:
        """return whether the object contains `item` """

        return item in self._dict

    def __getitem__(self, key: str) -> FieldValue:
        """return setting field value """

        return self._dict[key]

    def __iter__(self) -> Iterable[str]:
        """return iterator of the keys """

        return iter(self._dict)

    def get(self, key: str, default: Optional[FieldValue] = None
            ) -> Optional[FieldValue]:
        """return setting field value or default if not exists """

        return self._dict.get(key, default)

    def add_field(self, name: str, *,
                  type: type = str,
                  default: Optional[FieldValue] = None,
                  help: Optional[str] = None):
        """add new environment field """

        field = EnvField(name, type=type, default=default, help=help)
        self.fields[name] = field

    def keys(self) -> KeysView[str]:
        """return `dict_view` object of keys for the settings """

        return self._dict.keys()

    def values(self) -> ValuesView[Optional[FieldValue]]:
        """return `dict_view` object of values for the settings """

        return self._dict.values()

    def items(self) -> ItemsView[str, Optional[FieldValue]]:
        """return `dict_view` object of keys and values for the settings """

        return self._dict.items()

    def load_json(self,
                  filename: str
                  ) -> Dict[str, Optional[FieldValue]]:
        """parse given json string, update settings and return result dict

        >>> appenv = ApplicationEnvironment()
        >>> appenv.add_field('a', type=int)
        >>> appenv.add_field('b')
        >>> s = '{ "a": 1, "b": "two" }'
        >>> appenv.load_json(s)
        {'a': 1, 'b': 'two'}
        """

        with open(filename, encoding='utf-8') as fp:
            result = json.load(fp)

        d = {}
        for name, field in self.fields.items():
            default = self._dict.get(name, field.default)
            value = result.get(name, default)
            if value is not None:
                value = field.type(value)
            d[name] = value
        self._dict.update(d)
        return d

    def load_args(self,
                  args: Optional[Sequence[str]] = None,
                  parser: Optional[ArgumentParser] = None
                  ) -> Dict[str, Optional[FieldValue]]:
        """parse args, update settings and return result dict

        >>> appenv = ApplicationEnvironment()
        >>> appenv.add_field('a', type=int)
        >>> appenv.add_field('b')
        >>> a = ['--a', '1', '--b', 'two']
        >>> appenv.load_args(a)
        {'a': 1, 'b': 'two'}
        """

        if args is None:
            args = sys.argv[1:]
        if parser is None:
            parser = ArgumentParser()

        for name, field in self.fields.items():
            default = self._dict.get(name, field.default)
            parser.add_argument('--' + name,
                                type=field.type,
                                default=default,
                                help=field.help)
        namespace = parser.parse_args(args)
        d = {k: v for k, v in vars(namespace).items() if v is not None}
        self._dict.update(d)
        return d

    def load_env(self,
                 env: Optional[Dict[str, str]] = None,
                 prefix: str = '',
                 ) -> Dict[str, Optional[FieldValue]]:
        """parse environment value, update settings and return result dict

        >>> appenv = ApplicationEnvironment()
        >>> appenv.add_field('a', type=int)
        >>> appenv.add_field('b')
        >>> env = {'TEST_A': '1', 'TEST_B': 'two'}
        >>> appenv.load_env(env, 'test')
        {'a': 1, 'b': 'two'}
        """

        if env is None:
            env = os.environ

        d = {}
        for name, field in self.fields.items():
            key = name.upper()
            default = self._dict.get(name, field.default)
            if prefix:
                key = prefix.upper() + '_' + key
            value = env.get(key, default)
            if value is not None:
                value = field.type(value)
            d[name] = value
        self._dict.update(d)
        return d


__appenv__ = None


def get_appenv() -> ApplicationEnvironment:
    """retrun global `SettingSchema` object """

    global __appenv__
    if __appenv__ is None:
        __appenv__ = ApplicationEnvironment()
    return __appenv__


if __name__ == "__main__":
    import doctest
    doctest.testmod()

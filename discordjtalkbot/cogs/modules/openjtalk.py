"""Open JTalk command wrapper """

import asyncio
import io
import os
import shlex
import subprocess
import sys
import tempfile
import wave
import logging
from argparse import ArgumentParser
from typing import Any, List, Optional, Sequence

logging.basicConfig()
LOG = logging.getLogger(__name__)

__all__ = [
    'FREQ_44100HZ', 'FREQ_48000HZ',
    'OpenJTalkError', 'OpenJTalkArgumentParserError',
    'Agent',
    'talk', 'async_talk',
]


ENCODING = sys.getfilesystemencoding()
OPEN_JTALK = 'open_jtalk'
DICT = '/usr/local/opt/open-jtalk/dic' # YOUR_DICT_DIRECTORY
VOICE = '/usr/local/opt/open-jtalk/voice/mei/mei_normal.htsvoice' # YOUR_VOICE

WAVE_OUT = 'a.wav'
TRACE_OUT = 'trace.log'

# pre-defined sampling frequency
FREQ_44100HZ = 44100
FREQ_48000HZ = 48000


class OpenJTalkError(Exception):
    """module exception """
    pass


class OpenJTalkArgumentParserError(OpenJTalkError):
    """error on parsing `open_jtalk` args """
    pass


class _OpenJTalkArgumentParser(ArgumentParser):
    """(internal) option parser for `open_jtalk` command """

    def exit(self, status=0, message=None):
        if status:
            raise OpenJTalkArgumentParserError(message)


class _OptionMapping(object):
    """(internal) mapping entry between a command line option and a
    argument name and its type """

    __slots__ = ['option', 'name', 'type', 'help']

    def __init__(self, *, option: str, name: str, type: type, help: str):
        """constructor """

        self.option = option
        self.name = name
        self.type = type
        self.help = help


OPTION_MAPPINGS = [
    _OptionMapping(option='-x', name='dictionary', type=str,
                help='dictionary directory'),
    _OptionMapping(option='-m', name='voice', type=str,
                help='HTS voice files'),
    _OptionMapping(option='-s', name='sampling', type=int,
                help='sampling frequency'),
    _OptionMapping(option='-p', name='frameperiod', type=int,
                help='frame period (point)'),
    _OptionMapping(option='-a', name='allpass', type=float,
                help='all-pass constant'),
    _OptionMapping(option='-b', name='postfilter', type=float,
                help='postfiltering coefficient'),
    _OptionMapping(option='-r', name='speedrate', type=float,
                help='speech speed rate'),
    _OptionMapping(option='-fm', name='halftone', type=float,
                help='additional half-tone'),
    _OptionMapping(option='-u', name='threshold', type=float,
                help='voiced/unvoiced threshold'),
    _OptionMapping(option='-jm', name='spectrum', type=float,
                help='weight of GV for spectrum'),
    _OptionMapping(option='-jf', name='logf0', type=float,
                help='weight of GV for log F0'),
    _OptionMapping(option='-g', name='volume', type=float,
                help='volume (dB)'),
    _OptionMapping(option='-z', name='buffersize', type=int,
                help='audio buffer size (if i==0, turn off)'),
]
PROP_NAMES_DICT = {m.name: m for m in OPTION_MAPPINGS}
OPTIONS_DICT = {m.option: m for m in OPTION_MAPPINGS}


class Agent(object):
    """Open JTalk command line option set """

    @property
    def dictionary(self) -> str:
        """Path to the dictionary directory """

        return self._dictionary

    @dictionary.setter
    def dictionary(self, value: str):

        self._dictionary = str(value)

    @property
    def voice(self) -> str:
        """Path to the htc_voice file """

        return self._voice

    @voice.setter
    def voice(self, value: str):

        self._voice = str(value)

    @property
    def name(self) -> str:
        """Name of the agent """

        return self._name

    @name.setter
    def name(self, value: str):

        self._name = str(value)

    @property
    def sampling(self) -> Optional[int]:
        """Sampling frequency (`None` for auto) """

        return self._sampling

    @sampling.setter
    def sampling(self, value: Optional[int]):

        if value is not None:
            value = int(value)
            if value < 1:
                raise ValueError(f'sampling must be >= 1: {value}')
        self._sampling = value

    @property
    def frameperiod(self) -> Optional[int]:
        """Frame period (point) (`None` for auto) """

        return self._frameperiod

    @frameperiod.setter
    def frameperiod(self, value: Optional[int]):

        if value is not None:
            value = int(value)
            if value < 1:
                raise ValueError(f'frameperiod must be >= 1: {value}')
        self._frameperiod = value

    @property
    def allpass(self) -> Optional[float]:
        """all-pass constant  (`None` for auto) """

        return self._allpass

    @allpass.setter
    def allpass(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f'allpass is out of range (0.0-1.0): {value!r}')
        self._allpass = value

    @property
    def postfilter(self) -> Optional[float]:
        """Postfiltering coefficient """

        return self._postfilter

    @postfilter.setter
    def postfilter(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f'postfilter is out of range (0.0-1.0): {value}')
        self._postfilter = value

    @property
    def speedrate(self) -> Optional[float]:
        """Speech speed rate """

        return self._speedrate

    @speedrate.setter
    def speedrate(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if value < 0.0:
                raise ValueError(f'speedrate must be > 0.0: {value}')
        self._speedrate = value

    @property
    def halftone(self) -> Optional[float]:
        """Additional half-tone """

        return self._halftone

    @halftone.setter
    def halftone(self, value: Optional[float]):

        if value is not None:
            value = float(value)
        self._halftone = value

    @property
    def threshold(self) -> Optional[float]:
        """voiced/unvoiced threshold """

        return self._threshold

    @threshold.setter
    def threshold(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f'postfilter is out of range (0.0-1.0): {value}')
        self._threshold = value

    @property
    def spectrum(self) -> Optional[float]:
        """Weight of GV for spectrum """

        return self._spectrum

    @spectrum.setter
    def spectrum(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if value < 0.0:
                raise ValueError(f'spectrum must be >= 0.0: {value}')
        self._spectrum = value

    @property
    def logf0(self) -> Optional[float]:
        """Weight of GV for log F0 """

        return self._logf0

    @logf0.setter
    def logf0(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if value < 0.0:
                raise ValueError(f'logf0 must be >= 0.0: {value}')
        self._logf0 = value

    @property
    def volume(self) -> Optional[float]:
        """volume (dB) """

        return self._volume

    @volume.setter
    def volume(self, value: Optional[float]):

        if value is not None:
            value = float(value)
            if value < 0.0:
                raise ValueError(f'volume must be >= 0.0: {value}')
        self._volume = value

    @property
    def buffersize(self) -> Optional[int]:
        """Audio buffer size (if i == 0, turn off) """

        return self._buffersize

    @buffersize.setter
    def buffersize(self, value: Optional[int]):

        if value is not None:
            value = int(value)
            if value < 0:
                raise ValueError(f'buffersize must be >= 0: {value}')
        self._buffersize = value

    def __init__(
            self,
            dictionary: str,
            voice: str,
            name: str = None,
            *,
            sampling: int = None,
            frameperiod: int = None,
            allpass: float = None,
            postfilter: float = None,
            speedrate: float = None,
            halftone: float = None,
            threshold: float = None,
            spectrum: float = None,
            logf0: float = None,
            volume: float = None,
            buffersize: int = None):
        """Constructor. """

        self.dictionary = dictionary
        self.voice = voice
        self.name = name if name else '<unnamed>'
        self.sampling = sampling
        self.frameperiod = frameperiod
        self.allpass = allpass
        self.postfilter = postfilter
        self.speedrate = speedrate
        self.halftone = halftone
        self.threshold = threshold
        self.spectrum = spectrum
        self.logf0 = logf0
        self.volume = volume
        self.buffersize = buffersize

    def __repr__(self) -> str:
        """return `repr(self)` """

        return f'<{__name__}.{__class__.__name__} at {hex(id(self))}' \
            + f' "{self.name}" [{self.build_flags()}]>'

    def build_args(self, *, outwave: str = None, outtrace: str = None,
                   infile: str = None, **kwds) -> List[str]:
        """return a list of command line args for `open_jtalk` command """

        d = {k: getattr(self, k) for k in PROP_NAMES_DICT}
        d.update(kwds)

        args = []
        for prop_name, value in d.items():
            if value is None or prop_name not in PROP_NAMES_DICT:
                continue
            opt = PROP_NAMES_DICT[prop_name].option
            args.append(opt)
            args.append(str(value))
        if outwave is not None:
            args.append('-ow')
            args.append(outwave)
        if outtrace is not None:
            args.append('-ot')
            args.append(outtrace)
        if infile is not None:
            args.append(infile)
        return args

    def build_flags(self, **kwds) -> str:
        """return option flags string for `open_jtalk` command """

        args = self.build_args(**kwds)
        return shlex.join(args)

    def talk(self, text: str, **kwds) -> bytes:
        """Retrun wave data bytes for given text """
        LOG.info('talk')

        for k in kwds:
            if k not in PROP_NAMES_DICT:
                raise ValueError(f'{k!r} is not a valid keyword')

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = [OPEN_JTALK] \
                 + self.build_args(outwave=output, **kwds)
            proc = subprocess.run(args, input=text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return b''

    async def async_talk(self, text: str, **kwds) -> bytes:
        """[Coroutine] Retrun wave data bytes for given text """

        for k in kwds:
            if k not in PROP_NAMES_DICT:
                raise ValueError(f'{k!r} is not a valid keyword')

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = [OPEN_JTALK] \
                 + self.build_args(outwave=output, **kwds)
            proc = await asyncio.create_subprocess_exec(
                *args, stdin=asyncio.subprocess.PIPE)
            await proc.communicate(text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return b''

    @classmethod
    def from_args(cls, args: Sequence[str]) -> 'Agent':
        """return `Agent` instance initialized with `argv` as
        `open_jtalk` option arguments """

        kwds = parse_args(args)
        dictinary = kwds.pop('dictionary', DICT)
        voice = kwds.pop('voice', VOICE)
        path = os.path.join(os.path.dirname(__file__), '..' + os.sep + '..' + os.sep + '..' + os.sep)
        if dictinary.startswith('.'):
            dictinary = path + dictinary
        if voice.startswith('.'):
            voice = path + voice
        return cls(dictinary, voice, **kwds)

    @classmethod
    def from_flags(cls, flags: str) -> 'Agent':
        """return `Agent` instance initialized with `flags` as a
        `open_jtalk` option flags string """

        args = shlex.split(flags)
        return cls.from_args(args)



default_agent = Agent(DICT, VOICE, '<default>')


def talk(text: str, **kwds) -> bytes:
    """Generate wave data bytes for given text with default voice """

    return default_agent.talk(text, **kwds)


async def async_talk(text: str, **kwds) -> bytes:
    """[Coroutine] Generate wave data bytes for given text with default
    voice"""

    return await default_agent.async_talk(text, **kwds)


def mono_to_stereo(file: str) -> bytes:
    """Return stereo converted wave data from a monaural wave file. """

    with io.BytesIO() as stream, \
    wave.open(file, 'rb') as wi, \
    wave.open(stream, 'wb') as wo:
        wo.setnchannels(2)
        wo.setsampwidth(wi.getsampwidth())
        wo.setframerate(wi.getframerate())
        nframes = wi.getnframes()
        wo.setnframes(nframes)
        gen_frames = (wi.readframes(1) for _ in range(nframes))
        [wo.writeframesraw(f * 2) for f in gen_frames]
        return stream.getvalue()


_parser = None

def parse_args(args: Sequence[str]) -> dict:
    """parse `open_jtalk` command args and return them as a `dict` """

    global _parser
    if '_parser' not in globals() or _parser is None:
        _parser = _OpenJTalkArgumentParser(add_help=False)
        for m in OPTION_MAPPINGS:
            _parser.add_argument(m.option, dest=m.name, type=m.type)

    ns_args = _parser.parse_args(args)
    return dict((k, v) for (k, v) in vars(ns_args).items() if v is not None)


def main():
    data = talk('おやすみなさい')
    with open(WAVE_OUT, 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    main()

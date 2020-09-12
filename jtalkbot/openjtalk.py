"""Open JTalk command wrapper """

import asyncio
import io
import os
import shlex
import subprocess
import sys
import tempfile
import wave
from argparse import ArgumentParser
from typing import Any, List, Sequence


__all__ = [
    'FREQ_44100HZ', 'FREQ_48000HZ',
    'OpenJTalkError', 'Agent', 'talk', 'async_talk'
]


ENCODING = sys.getfilesystemencoding()
OPEN_JTALK = 'open_jtalk'
DICT = '/opt/local/lib/open_jtalk/dic'
VOICE = '/opt/local/lib/open_jtalk/voice/nitech/nitech_jp_atr503_m001.htsvoice'

WAVE_OUT = 'a.wav'
TRACE_OUT = 'trace.log'

# pre-defined sampling frequency
FREQ_44100HZ = 44100
FREQ_48000HZ = 48000


class OpenJTalkError(Exception):
    """module exception """
    pass


class _OptionMapping(object):
    """(internal) mapping entry between a command line option and a
    argument name and its type """

    __slots__ = ['option', 'name', 'type']

    def __init__(self, *, option: str, name: str, type: type):
        """constructor """

        self.option = option
        self.name = name
        self.type = type


OPTION_MAPPINGS = [
    _OptionMapping(option='-x', name='dictionary', type=str),
    _OptionMapping(option='-m', name='voice', type=str),
    _OptionMapping(option='-ow', name='_outwave', type=str),
    _OptionMapping(option='-ot', name='_outtrace', type=str),
    _OptionMapping(option='-s', name='sampling', type=int),
    _OptionMapping(option='-p', name='frameperiod', type=int),
    _OptionMapping(option='-a', name='allpass', type=float),
    _OptionMapping(option='-b', name='postfilter', type=float),
    _OptionMapping(option='-r', name='speedrate', type=float),
    _OptionMapping(option='-fm', name='halftone', type=float),
    _OptionMapping(option='-u', name='threshold', type=float),
    _OptionMapping(option='-jm', name='spectrum', type=float),
    _OptionMapping(option='-jf', name='logf0', type=float),
    _OptionMapping(option='-g', name='volume', type=float),
    _OptionMapping(option='-z', name='buffersize', type=int),
    _OptionMapping(option='infile', name='_infile', type=str),
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

        if not os.path.isdir(value):
            raise ValueError(f'{value!r} is not a existing directory')
        self._dictionary = str(value)

    @property
    def voice(self) -> str:
        """Path to the htc_voice file """

        return self._voice

    @voice.setter
    def voice(self, value: str):

        if not os.path.exists(value):
            raise ValueError(f'{value!r} is not a existing file name')
        self._voice = str(value)

    @property
    def name(self) -> str:
        """Name of the agent """

        return self._name

    @name.setter
    def name(self, value: str):

        self._name = str(value)

    @property
    def sampling(self) -> int:
        """Sampling frequency (`None` for auto) """

        return self._sampling

    @sampling.setter
    def sampling(self, value: int):

        if value is None:
            self._sampling = None
            return

        value = int(value)
        if value < 1:
            raise ValueError(f'sampling must be >= 1: {value}')
        self._sampling = value

    @property
    def frameperiod(self) -> int:
        """Frame period (point) (`None` for auto) """

        return self._frameperiod

    @frameperiod.setter
    def frameperiod(self, value: int):

        if value is None:
            self._frameperiod = None
            return

        value = int(value)
        if value < 1:
            raise ValueError(f'frameperiod must be >= 1: {value}')
        self._frameperiod = value

    @property
    def allpass(self) -> float:
        """all-pass constant  (`None` for auto) """

        return self._allpass

    @allpass.setter
    def allpass(self, value: float):

        if value is None:
            self._allpass = None
            return

        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'allpass is out of range (0.0-1.0): {value!r}')
        self._allpass = value

    @property
    def postfilter(self) -> float:
        """Postfiltering coefficient """

        return self._postfilter

    @postfilter.setter
    def postfilter(self, value: float):

        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'postfilter is out of range (0.0-1.0): {value}')
        self._postfilter = value

    @property
    def speedrate(self) -> float:
        """Speech speed rate """

        return self._speedrate

    @speedrate.setter
    def speedrate(self, value: float):

        value = float(value)
        if value < 0.0:
            raise ValueError(f'speedrate must be > 0.0: {value}')
        self._speedrate = value

    @property
    def halftone(self) -> float:
        """Additional half-tone """

        return self._halftone

    @halftone.setter
    def halftone(self, value: float):

        value = float(value)
        self._halftone = value

    @property
    def threshold(self) -> float:
        """voiced/unvoiced threshold """

        return self._threshold

    @threshold.setter
    def threshold(self, value: float):

        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(f'postfilter is out of range (0.0-1.0): {value}')
        self._threshold = value

    @property
    def spectrum(self) -> float:
        """Weight of GV for spectrum """

        return self._spectrum

    @spectrum.setter
    def spectrum(self, value: float):

        value = float(value)
        if value < 0.0:
            raise ValueError(f'spectrum must be >= 0.0: {value}')
        self._spectrum = value

    @property
    def logf0(self) -> float:
        """Weight of GV for log F0 """

        return self._logf0

    @logf0.setter
    def logf0(self, value: float):

        value = float(value)
        if value < 0.0:
            raise ValueError(f'logf0 must be >= 0.0: {value}')
        self._logf0 = value

    @property
    def volume(self) -> float:
        """volume (dB) """

        return self._volume

    @volume.setter
    def volume(self, value: float):

        value = float(value)
        if value < 0.0:
            raise ValueError(f'volume must be >= 0.0: {value}')
        self._volume = value

    @property
    def buffersize(self) -> int:
        """Audio buffer size (if i == 0, turn off) """

        return self._buffersize

    @buffersize.setter
    def buffersize(self, value: int):

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
            postfilter: float = 0.0,
            speedrate: float = 1.0,
            halftone: float = 0.0,
            threshold: float = 0.5,
            spectrum: float = 1.0,
            logf0: float = 1.0,
            volume: float = 0.0,
            buffersize: int = 0):
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

    def build_command_line_args(self, **kwds) -> List[str]:
        """return a list of command line args for `open_jtalk` command """

        d = props(self)
        d.update(kwds)

        opts = []
        for prop_name, value in d.items():
            if prop_name not in PROP_NAMES_DICT or value is None:
                continue
            opt = PROP_NAMES_DICT[prop_name].option
            if opt.startswith('-'):
                opts.append(opt)
            opts.append(str(value))
        return opts


    def talk(self, text: str, **kwds) -> bytes:
        """Retrun wave data bytes for given text """

        for k in kwds:
            if k not in PROP_NAMES_DICT or k.startswith('_'):
                raise ValueError(f'{k!r} is not a valid keyword')

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = [OPEN_JTALK] \
                 + self.build_command_line_args(_outwave=output, **kwds)
            proc = subprocess.run(args, input=text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return b''

    async def async_talk(self, text: str, **kwds) -> bytes:
        """[Coroutine] Retrun wave data bytes for given text """

        for k in kwds:
            if k not in PROP_NAMES_DICT or k.startswith('_'):
                raise ValueError(f'{k!r} is not a valid keyword')

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = [OPEN_JTALK] \
                 + self.build_command_line_args(_outwave=output, **kwds)
            proc = await asyncio.create_subprocess_exec(
                *args, stdin=asyncio.subprocess.PIPE)
            await proc.communicate(text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return b''


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


def parse_args(args: Sequence[str]) -> dict:
    """parse `open_jtalk` command args and return them as a `dict` """

    global _parser
    if '_parser' not in globals():
        _parser = ArgumentParser()
        for m in OPTION_MAPPINGS:
            _parser.add_argument(m.opt, dest=m.name, type=m.type)

    opts = _parser.parse_args(args)
    return dict((k, v) for (k, v) in vars(opts).items() if v is not None)


def parse_flags(flags: str) -> dict:
    """parse flags as `open_jtalk` command line options and return them
    as a `dict` """

    args = shlex.split(flags)
    return vars_from_args(args)


def props(o: Any):
    """return all properties of a given object as a `dict` """

    return {k: getattr(o, k) for k in dir(o.__class__)
            if isinstance(getattr(o.__class__, k), property)}


def main():
    data = talk('おやすみなさい')
    with open(WAVE_OUT, 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    main()

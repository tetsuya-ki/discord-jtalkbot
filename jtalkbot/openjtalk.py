"""Open JTalk command wrapper """

import argparse
import asyncio
import io
import os
import shlex
import subprocess
import sys
import tempfile
import wave
from typing import List, Sequence


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
        self.name = name if name is not None else '<unnamed>'
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

    def build_args(
            self,
            output: str,
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
            buffersize: int = None) -> str:
        """Build command line args """

        ot = None
        s = self.sampling if sampling is None else sampling
        p = self.frameperiod if frameperiod is None else frameperiod
        a = self.allpass if allpass is None else allpass
        b = self.postfilter if postfilter is None else postfilter
        r = self.speedrate if speedrate is None else speedrate
        fm = self.halftone if halftone is None else halftone
        u = self.threshold if threshold is None else threshold
        jm = self.spectrum if spectrum is None else spectrum
        jf = self.logf0 if logf0 is None else logf0
        g = self.volume if volume is None else volume
        z = self.buffersize if buffersize is None else buffersize
        return build_args(
            OPEN_JTALK, self.dictionary, self.voice, output,
            ot=ot, s=s, p=p, a=a, b=b, r=r, fm=fm, u=u, jm=jm, jf=jf, g=g, z=z)

    def talk(
            self,
            text: str,
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
            buffersize: int = None) -> bytes:
        """Generate wave data bytes for given text """

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = self.build_args(output,
                sampling=sampling, frameperiod=frameperiod,
                allpass=allpass, postfilter=postfilter, speedrate=speedrate,
                halftone=halftone, threshold=threshold, spectrum=spectrum,
                logf0=logf0, volume=volume, buffersize=buffersize)
            proc = subprocess.run(args, input=text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return None

    async def async_talk(
            self,
            text: str,
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
            buffersize: int = None) -> bytes:
        """[Coroutine] Generate wave data bytes for given text """

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, WAVE_OUT)
            args = self.build_args(output,
                sampling=sampling, frameperiod=frameperiod,
                allpass=allpass, postfilter=postfilter, speedrate=speedrate,
                halftone=halftone, threshold=threshold, spectrum=spectrum,
                logf0=logf0, volume=volume, buffersize=buffersize)
            proc = await asyncio.create_subprocess_exec(
                *args, stdin=asyncio.subprocess.PIPE)
            await proc.communicate(text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return None


default_agent = Agent(DICT, VOICE, '<default>')


def build_args(
        command: str,
        x: str,
        m: str,
        ow: str,
        *,
        ot: str = None,
        s: int = None,
        p: int = None,
        a: float = None,
        b: float = None,
        r: float = None,
        fm: float = None,
        u: float = None,
        jm: float = None,
        jf: float = None,
        g: float = None,
        z: int = None,
        infile: str = None) -> List[str]:
    """Build open_jtalk command line args. """

    args = [command, '-x', x, '-m', m, '-ow', ow]
    if ot is not None:
        args += ['-ot', ot]
    if s is not None:
        args += ['-s', str(s)]
    if p is not None:
        args += ['-p', str(p)]
    if a is not None:
        args += ['-a', str(a)]
    if b is not None:
        args += ['-b', str(b)]
    if r is not None:
        args += ['-r', str(r)]
    if fm is not None:
        args += ['-fm', str(fm)]
    if u is not None:
        args += ['-u', str(u)]
    if jm is not None:
        args += ['-jm', str(jm)]
    if jf is not None:
        args += ['-jf', str(jf)]
    if g is not None:
        args += ['-g', str(g)]
    if z is not None:
        args += ['-z', str(z)]
    if infile is not None:
        args.append(infile)
    return args


def talk(
        text: str,
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
        buffersize: int = None) -> bytes:
    """Generate wave data bytes for given text """

    return default_agent.talk(text,
        sampling=sampling, frameperiod=frameperiod,
        allpass=allpass, postfilter=postfilter, speedrate=speedrate,
        halftone=halftone, threshold=threshold, spectrum=spectrum,
        logf0=logf0, volume=volume, buffersize=buffersize)


async def async_talk(
        text: str,
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
        buffersize: int = None) -> bytes:
    """[Coroutine] Generate wave data bytes for given text """

    return await default_agent.async_talk(text,
        sampling=sampling, frameperiod=frameperiod,
        allpass=allpass, postfilter=postfilter, speedrate=speedrate,
        halftone=halftone, threshold=threshold, spectrum=spectrum,
        logf0=logf0, volume=volume, buffersize=buffersize)


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


def vars_from_args(args: Sequence[str]) -> dict:
    """parse `open_jtalk` command args and return them as a `dict` """

    global _parser

    if '_parser' not in globals():
        _parser = argparse.Argument_Parser()
        _parser.add_argument('-x', dest='dictionary')
        _parser.add_argument('-m', dest='voice')
        _parser.add_argument('-ow', dest='outfile')
        _parser.add_argument('-ot', dest='trace')
        _parser.add_argument('-s', dest='sampling', type=int)
        _parser.add_argument('-p', dest='frameperiod', type=int)
        _parser.add_argument('-a', dest='allpass', type=float)
        _parser.add_argument('-b', dest='postfilter', type=float)
        _parser.add_argument('-r', dest='speedrate', type=float)
        _parser.add_argument('-fm', dest='halftone', type=float)
        _parser.add_argument('-u', dest='threshold', type=float)
        _parser.add_argument('-jm', dest='spectrum', type=float)
        _parser.add_argument('-jf', dest='logf0', type=float)
        _parser.add_argument('-g', dest='volume', type=float)
        _parser.add_argument('-z', dest='buffersize', type=int)
        _parser.add_argument('infile')

    opts = _parser.parse_args(args)
    return vars(opts)


def vars_from_flags(flags: str) -> dict:
    """parse flags as `open_jtalk` command line options and return them
    as a `dict` """

    args = shlex.split(flags)
    return vars_from_args(args)


def main():
    data = talk('おやすみなさい')
    with open(WAVE_OUT, 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    main()

"""Open JTalk wrapper.

Open JTalk:
    http://open-jtalk.sourceforge.net
"""

import asyncio
import io
import os.path
import sys
import tempfile
import wave
from typing import List


__all__ = ['Agent', 'async_talk']


ENCODING = sys.getfilesystemencoding()
OPEN_JTALK = '/usr/local/bin/open_jtalk'
DICT = '/usr/local/lib/open_jtalk/dic'
VOICE = '/usr/local/lib/open_jtalk/nitech/nitech_jp_atr503_m001.htsvoice'


class Agent(object):
    """Open JTalk command line option wrapper. """

    def __init__(self, command: str, dic: str, voice: str, output: str,
                 trace: str = None,
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
                 buffersize: float = 0,
                 infile: str = None):
        """Constructor. """

        self._command = command
        self._output = output
        self._trace = trace
        self._dic = dic
        self._voice = voice
        self._sampling = sampling
        self._frameperiod = frameperiod
        self._allpass = allpass
        self._postfilter = postfilter
        self._speedrate = speedrate
        self._halftone = halftone
        self._threshold = threshold
        self._spectrum = spectrum
        self._logf0 = logf0
        self._volume = volume
        self._buffersize = buffersize
        self._infile = infile

    @property
    def command(self) -> str:
        """Path to the open_jtalk command """
        return self._command

    @command.setter
    def command(self, value: str):
        self._command = value

    @property
    def dictionary(self) -> str:
        """Path to the dictionary directory """
        return self._dic

    @dictionary.setter
    def dictionary(self, value: str):
        self._dic = value

    @property
    def voice(self) -> str:
        """Path to the htc_voice file """
        return self._voice

    @voice.setter
    def voice(self, value: str):
        self._voice = value

    @property
    def output(self) -> str:
        """Filename of output wav audio (generated speech) """
        return self._output

    @output.setter
    def output(self, value: str):
        self._output = value

    @property
    def trace(self) -> str:
        """Filename of output trace information """
        return self._trace

    @trace.setter
    def trace(self, value: str):
        self._trace = value

    @property
    def sampling(self) -> int:
        """Sampling frequency """
        return self._sampling

    @sampling.setter
    def sampling(self, value: int):
        self._sampling = value

    @property
    def frameperiod(self) -> int:
        """Frame period (point) """
        return self._frameperiod

    @frameperiod.setter
    def frameperiod(self, value: int):
        self._frameperiod = value

    @property
    def allpass(self) -> float:
        """all-pass constant """
        return self._allpass

    @allpass.setter
    def allpass(self, value: float):
        self._allpass = value

    @property
    def postfilter(self) -> float:
        """Postfiltering coefficient """
        return self._postfilter

    @postfilter.setter
    def postfilter(self, value: float):
        self._postfilter = value

    @property
    def speedrate(self) -> float:
        """Speech speed rate """
        return self._speedrate

    @speedrate.setter
    def speedrate(self, value: float):
        self._speedrate = value

    @property
    def halftone(self) -> float:
        """Additional half-tone """
        return self._halftone

    @halftone.setter
    def halftone(self, value: float):
        self._halftone = value

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value

    @property
    def spectrum(self) -> float:
        """Weight of GV for spectrum """
        return self._spectrum

    @spectrum.setter
    def spectrum(self, value: float):
        self._spectrum = value

    @property
    def logf0(self) -> float:
        """Weight of GV for log F0 """
        return self._logf0

    @logf0.setter
    def logf0(self, value: float):
        self._logf0 = value

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def buffersize(self) -> int:
        """Audio buffer size (if i == 0, turn off) """
        return self._buffersize

    @buffersize.setter
    def buffersize(self, value: int):
        self._buffersize = value

    @property
    def infile(self) -> str:
        """Input text file """
        return self._infile

    @infile.setter
    def infile(self, value: str):
        self._infile = value

    def build_args(self,
                   command: str = None,
                   dic: str = None,
                   voice: str = None,
                   output: str = None,
                   trace: str = None,
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
                   buffersize: float = None,
                   infile: str = None) -> str:
        """Build command line args """

        cmd = self.command if command is None else command
        x = self.dictionary if dic is None else dic
        m = self.voice if voice is None else voice
        ow = self.output if output is None else output
        ot = self.trace if trace is None else trace
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
        infile = self.infile if infile is None else infile
        return build_args(
            cmd, x, m, ow, ot=ot, s=s, p=p, a=a, b=b, r=r, fm=fm, u=u, jm=jm,
            jf=jf, g=g, z=z, infile=infile)

    async def async_exec(self,
                         command: str = None,
                         dic: str = None,
                         voice: str = None,
                         output: str = None,
                         trace: str = None,
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
                         buffersize: float = None,
                         infile: str = None) -> int:
        """[Coroutine] Exec open_jtalk command with given args """

        args = self.build_args(
            command=command, dic=dic, voice=voice, output=output,
            trace=trace, sampling=sampling, frameperiod=frameperiod,
            allpass=allpass, postfilter=postfilter, speedrate=speedrate,
            halftone=halftone, threshold=threshold, spectrum=spectrum,
            logf0=logf0, volume=volume, buffersize=buffersize, infile=infile)
        proc = await asyncio.create_subprocess_exec(*args)
        await proc.communicate(text.encode(ENCODING))
        return proc.returncode

    async def async_talk(self, text: str,
                         command: str = None,
                         dic: str = None,
                         voice: str = None,
                         trace: str = None,
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
                         buffersize: float = None) -> bytes:
        """[Coroutine] Generate wave data bytes for given text """

        with tempfile.TemporaryDirectory() as tempdir:
            output = os.path.join(tempdir, 'a.wav')
            args = self.build_args(
                command=command, dic=dic, voice=voice, output=output,
                trace=trace, sampling=sampling, frameperiod=frameperiod,
                allpass=allpass, postfilter=postfilter, speedrate=speedrate,
                halftone=halftone, threshold=threshold, spectrum=spectrum,
                logf0=logf0, volume=volume, buffersize=buffersize)
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.PIPE)
            await proc.communicate(text.encode(ENCODING))
            if proc.returncode == 0:
                return mono_to_stereo(output)
        return None


default_agent = Agent(OPEN_JTALK, DICT, VOICE, 'a.wav')


def build_args(command: str, x: str, m: str, ow: str,
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


async def async_talk(text: str,
                     command: str = None,
                     dic: str = None,
                     voice: str = None,
                     trace: str = None,
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
                     buffersize: float = None) -> bytes:
    """[Coroutine] Generate wave data bytes for given text """

    return await default_agent.async_talk(
        text, command=command, dic=dic, voice=voice,
        trace=trace, sampling=sampling, frameperiod=frameperiod,
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


async def main():
    data = await async_talk('おやすみなさい')
    with open('a.wav', 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    asyncio.run(main())

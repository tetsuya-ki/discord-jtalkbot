# openjtalk.py - Open JTalk wrapper

import io
import os.path
import subprocess
import tempfile
import wave


OPEN_JTALK = '/opt/local/bin/open_jtalk'
DICT = '/opt/local/lib/open_jtalk/dic'
VOICE = '/opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice'


class OpenJTalk(object):

    def __init__(self, path=None, dictdir=None, voice=None):
        """Constructor. """
        self.path = path if path else OPEN_JTALK
        self.dictdir = dictdir if dictdir else DICT
        self.voice = voice if voice else VOICE

    def exec(self, text):
        with tempfile.TemporaryDirectory() as tempdir:
            outname = os.path.join(tempdir, 'a.wav')
            args = [self.path, '-x', self.dictdir,
                    '-m', self.voice, '-ow', outname]
            cp = subprocess.run(
                args, input=text, capture_output=True, encoding='utf-8')
            if cp.returncode == 0:
                data = mono_to_stereo(outname)
        return data


def mono_to_stereo(filename):

    with io.BytesIO() as stream, \
          wave.open(filename, 'rb') as wave_in, \
           wave.open(stream, 'wb') as wave_out:
        wave_out.setnchannels(2)
        wave_out.setsampwidth(wave_in.getsampwidth())
        wave_out.setframerate(wave_in.getframerate())
        nframes = wave_in.getnframes()
        wave_out.setnframes(nframes)
        for _ in range(nframes):
            frame = wave_in.readframes(1)
            wave_out.writeframesraw(frame)  # L
            wave_out.writeframesraw(frame)  # R
        data = stream.getvalue()
    return data


def main():
    agent = OpenJTalk()
    data = agent.exec('はじめまして。')
    with open('a.wav', mode='wb') as f:
        f.write(data)


if __name__ == "__main__":
    main()

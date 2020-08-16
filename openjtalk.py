# openjtalk.py - Open JTalk wrapper

import io
import os.path
import subprocess
import tempfile
import wave


OPEN_JTALK = '/opt/local/bin/open_jtalk'
DIR = '/opt/local/lib/open_jtalk/dic'
VOICE = '/opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice'


def run(text: str):
    with tempfile.TemporaryDirectory() as tempdir:
        outname = os.path.join(tempdir, 'a.wav')
        args = [OPEN_JTALK, '-x', DIR, '-m', VOICE, '-ow', outname]
        cp = subprocess.run(args, input=text, capture_output=True, encoding='utf-8')
        if cp.returncode == 0:
            data = mono_to_stereo(outname)
    return data


def mono_to_stereo(file_in):

    with io.BytesIO() as stream:
        with wave.open(file_in, 'rb') as wave_in, wave.open(stream, 'wb') as wave_out:
            wave_out.setnchannels(2)
            wave_out.setsampwidth(wave_in.getsampwidth())
            wave_out.setframerate(wave_in.getframerate())
            nframes = wave_in.getnframes()
            wave_out.setnframes(nframes)
            for _ in range(nframes):
                frame = wave_in.readframes(1)
                wave_out.writeframesraw(frame)
                wave_out.writeframesraw(frame)
            data = stream.getvalue()
    return data


def main():
    data = run('こんにちは')
    with open('a.wav', mode='wb') as f:
        f.write(data)


if __name__ == "__main__":
    main()

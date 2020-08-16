# openjtalk.py - Open JTalk wrapper

import asyncio
import io
import os.path
import subprocess
import tempfile
import wave


OPEN_JTALK = '/opt/local/bin/open_jtalk'
DICT = '/opt/local/lib/open_jtalk/dic'
VOICE = '/opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice'


async def exec(text):

    with tempfile.TemporaryDirectory() as tempdir:
        outname = os.path.join(tempdir, 'a.wav')
        args = [OPEN_JTALK, '-x', DICT, '-m', VOICE, '-ow', outname]
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE)
        await proc.communicate(text.encode('utf-8'))
        if proc.returncode == 0:
            return mono_to_stereo(outname)
    return None


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
        return stream.getvalue()


async def main():
    data = await exec('おやすみなさい')
    with open('a.wav', 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    asyncio.run(main())

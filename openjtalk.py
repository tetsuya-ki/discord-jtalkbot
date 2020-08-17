# openjtalk.py - Open JTalk wrapper

import asyncio
import io
import os.path
import tempfile
import wave


OPEN_JTALK = '/opt/local/bin/open_jtalk'
DICT = '/opt/local/lib/open_jtalk/dic'
VOICE = '/opt/local/lib/open_jtalk/voice/mei/mei_normal.htsvoice'


async def exec(text: str) -> bytes:

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


def mono_to_stereo(file: str) -> bytes:

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
    data = await exec('おやすみなさい')
    with open('a.wav', 'wb') as f:
        f.write(data)


if __name__ == "__main__":
    asyncio.run(main())

"""openjtalk module command line util """

import io
import wave
from argparse import ArgumentParser
from itertools import chain

import pyaudio

from . import openjtalk


def main():
    parser = ArgumentParser()
    parser.add_argument('-t', '--text')
    for m in openjtalk.OPTION_MAPPINGS:
        parser.add_argument(m.option, type=str, help=m.help)
    ns_args = parser.parse_args()

    d_args = vars(ns_args)
    text = d_args.pop('text')
    agent_args = chain.from_iterable(
        ('-' + k, v) for k, v in d_args.items() if v is not None)
    agent = openjtalk.Agent.from_args(agent_args)
    print(agent)
    pa = pyaudio.PyAudio()
    try:
        wave_bytes = agent.talk(text)
        with io.BytesIO(wave_bytes) as bytes_io:
            with wave.open(bytes_io, 'rb') as wf:
                sampwidth = wf.getsampwidth()
                nchannels = wf.getnchannels()
                rate = wf.getframerate()
                pa_format = pa.get_format_from_width(sampwidth)
                stream = pa.open(rate, nchannels, pa_format, output=True)
                try:
                    chunk = 4096
                    while True:
                        frame_data = wf.readframes(chunk)
                        if not frame_data:
                            break
                        stream.write(frame_data)
                finally:
                    stream.stop_stream()
                    stream.close()
    finally:
        pa.terminate()


if __name__ == "__main__":
    main()

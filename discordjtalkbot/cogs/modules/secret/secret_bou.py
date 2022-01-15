# https://qiita.com/krrka/items/67b9e12b4bfe750cb21a
from ctypes import *
from cffi import FFI
import io, wave, os, sys,librosa,soundfile
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import environ
"""
secret/
┝aq_dic/...→辞書ファイルが配置される
┝aq_dic_large/...→辞書ファイル(大)が配置される
┝AqKanji2Koe.framework/...
┝AquesTalk2.framework/...
┝AquesTalk2Eva.framework/...→評価版の場合
┝output_file/...→出力ファイルが配置される
┗phont/...→phontファイルが配置される
という状態で実行すること
"""

ffi = FFI()
ffi.cdef("""
int AqKanji2Koe_SetDevKey(const char *key);
void * AqKanji2Koe_Create(const char *pathDic, int *pErr);
void * AqKanji2Koe_Create_Ptr(const void *pSysDic, const void *pUserDic, int *pErr);
void AqKanji2Koe_Release(void *hAqKanji2Koe);
int AqKanji2Koe_ConvertW(void *hAqKanji2Koe, const wchar_t *kanji, wchar_t *wKoe, int nBufKoe);
""")
WAVE_OUT = 'a.wav'
CONV_OUT = 'b.wav'
ENCODING = sys.getfilesystemencoding()
path = os.path.dirname(os.path.abspath(__file__)) + os.sep
output_path = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'output_file' + os.sep

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

def conv(file: str) -> bytes:
    # https://note.com/npaka/n/n6f421b546024
    y, sr = librosa.core.load(file, sr=48000, mono=False)
    output = os.path.join(output_path, CONV_OUT)
    soundfile.write(output, y, sr, subtype="PCM_16")
    with io.BytesIO() as stream, \
        wave.open(output, 'rb') as wi, \
        wave.open(stream, 'wb') as wo:
            wo.setnchannels(2)
            wo.setsampwidth(wi.getsampwidth())
            wo.setframerate(wi.getframerate())
            nframes = wi.getnframes()
            wo.setnframes(nframes)
            gen_frames = (wi.readframes(1) for _ in range(nframes))
            [wo.writeframesraw(f * 2) for f in gen_frames]
            return stream.getvalue()

def talk(text: str, file_phont: str) -> bytes:
        """Retrun wave data bytes for given text """

        output = os.path.join(output_path, WAVE_OUT)
        if bouyomi(text=text, speed=100, file_phont=file_phont, output=output) == 0:
            return conv(output)
        return b''

# https://boxheadroom.hatenablog.com/entry/20140414/p1#fn-b5d3d0eb
def kanji2koe_utf8(kanji):
    AqKanji2Koe_path = "AqKanji2Koe.framework/Versions/A/AqKanji2Koe"
    try: 
        AqKanji2Koe = ffi.dlopen(path + AqKanji2Koe_path)
    except:
        raise RuntimeError("ライブラリが読み込めませんでした")

    data = ""
    appenv = environ.get_appenv()
    appenv.load_env(prefix='discordjtalkbot')
    # print("appenv:" + str(appenv.get('aq_dev_key')))
    if appenv.get('aq_dev_key') is not None:
        data = appenv.get('aq_dev_key')
    elif data == "" and os.environ.get("AQ_DEV_KEY") is not None:
        data = os.environ.get("AQ_DEV_KEY")
    # print(data)
    devKey=ffi.new("char []", data.encode('ascii'))
    ret=AqKanji2Koe.AqKanji2Koe_SetDevKey(devKey)

    pathDic=ffi.new("char []", (path + "aq_dic").encode('ascii'))
    pErr=ffi.new("int[1]") 
    hAqKanji2Koe=AqKanji2Koe.AqKanji2Koe_Create(pathDic, pErr)

    if hAqKanji2Koe is None or hAqKanji2Koe ==0:
        return
    nBufKoe=256
    yomi = ""

    for txt2read in kanji.splitlines():
        wKoe=ffi.new("wchar_t [%d]"%nBufKoe)
        txt=ffi.new("wchar_t []",txt2read)

        AqKanji2Koe.AqKanji2Koe_ConvertW(hAqKanji2Koe, txt, wKoe, nBufKoe)
        yomi="".join([c for c in wKoe])
        print(yomi)

    AqKanji2Koe.AqKanji2Koe_Release(hAqKanji2Koe)
    return yomi

def koe2synthe_utf8(text, speed=100, file_phont=None):
    if file_phont is not None:
        file_phont = path + file_phont
        with open(file_phont, 'rb') as f:
            phont = f.read()
    else:
        phont = None

    AquesTalk2_path = "AquesTalk2.framework/Versions/A/AquesTalk2"
    try: 
        aqtk = cdll.LoadLibrary(path + AquesTalk2_path)
    except:
        AquesTalk2_path = AquesTalk2_path.replace("AquesTalk2", "AquesTalk2Eva")
        try:
            aqtk = cdll.LoadLibrary(path + AquesTalk2_path)
        except:
            raise RuntimeError("ライブラリが読み込めませんでした")
    byte_array = (c_ubyte)
    aqtk.AquesTalk2_Synthe_Utf8.restype = POINTER(byte_array)
    size=c_int(0)
    wav_p = aqtk.AquesTalk2_Synthe_Utf8(text.encode('utf-8'), speed, byref(size), phont)
    if not bool(wav_p):
        print("ERR:", size.value)
        return None
    arr = (c_ubyte * size.value)
    wav_p = cast(wav_p,  POINTER(arr))
    wav = bytearray(wav_p.contents)
    aqtk.AquesTalk2_FreeWave(wav_p)
    return wav

def bouyomi(text, speed=100, file_phont=None, output='./default.wav'):
    koe = kanji2koe_utf8(text)
    if koe:
        with open(output, 'wb') as f:
            wav = koe2synthe_utf8(koe, speed,file_phont)
            if wav:
                f.write(wav)
            else:
                print("音がない")
                return 1
        return 0
    else:
        print("声がない")
        return 1

if __name__ == '__main__':
    """
    下記のコマンドでまず音声ファイルが出力されるか確認してください
    poetry run python discordjtalkbot/cogs/modules/secret/secret_bou.py
    """
    output = os.path.join(output_path, WAVE_OUT)

    # test = u"あしたの/て'んきわ、いちにちじゅー/はれ。"
    # with open(output, 'wb') as f:
    #     wav = koe2synthe_utf8(test, speed=100)
    #     f.write(wav)

    test2 = u"""明日の天気は、一日中晴。"""
    koe = kanji2koe_utf8(test2)
    if koe:
        with open(output, 'wb') as f:
            wav = koe2synthe_utf8(koe, speed=100)
            f.write(wav)

    # test2 = u"ゆっくりしていってね"
    # with open(output, 'wb') as f:
    #     wav = koe2synthe_utf8(test2, speed=100, file_phont='phont/aq_yukkuri.phont')
    #     f.write(wav)
    # pass
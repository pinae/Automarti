from pedalboard.io import AudioFile
from pedalboard import Pedalboard
from pedalboard import Compressor, load_plugin


if __name__ == "__main__":
    with AudioFile('samples/budumdumdidum.mp3') as f:
        audio = f.read(f.frames)
    print(type(audio), audio.shape, audio.dtype)

    import pyaudio
    pa = pyaudio.PyAudio()
    pa_strm = pa.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        output=True)
    pa_strm.write(audio)

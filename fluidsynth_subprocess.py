import subprocess
import tempfile
import numpy as np
from typing import Iterator
from numpy.typing import NDArray
from music21.stream import Stream
from music21.midi.translate import streamToMidiFile
from pedalboard.io import AudioFile


def sample_generator(music_stream: Stream, soundfont_filename: str,
                     chunk_size_in_seconds: float = 5.0) -> Iterator[NDArray[np.float32]]:
    midi_file = streamToMidiFile(music_stream)
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=True) as temp_midi, tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_wav:
        midi_file.open(temp_midi.name, "wb")
        midi_file.write()
        midi_file.close()

        # Calling fluidsynth to convert MIDI to wav
        subprocess.run(
            ['fluidsynth', '-ni', soundfont_filename,
             temp_midi.name, '-F', temp_wav.name, '-r', '44100']
        )

        # Load the wav file and yield to a numpy array
        with AudioFile(temp_wav.name) as audio_file:
            chunk_size = int(chunk_size_in_seconds * audio_file.samplerate)
            while audio_file.tell() < audio_file.frames:
                yield audio_file.read(chunk_size)


if __name__ == "__main__":
    from music21.note import Note
    from music21.tempo import MetronomeMark
    from music21.meter import TimeSignature
    strm = Stream([MetronomeMark(number=120, referent=Note(type='quarter')),
                   TimeSignature('4/4'),
                   Note('G4', quarterLength=1),
                   Note('C4', quarterLength=1),
                   Note('A4', quarterLength=2),
                   MetronomeMark(number=70, referent=Note(type='quarter')),
                   TimeSignature('3/4'),
                   Note('G4', quarterLength=1),
                   Note('G4', quarterLength=1),
                   Note('C4', quarterLength=1)])
    sam_gen = sample_generator(strm, 'soundfonts/organ/Aggorg.sf2')
    for audio in sam_gen:
        print(type(audio), audio.dtype, f"Shape: {audio.shape}")
        print(audio)

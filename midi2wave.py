import numpy as np
import pyaudio
import fluidsynth
from music21.note import Note
from music21.tempo import MetronomeMark
from music21.meter import TimeSignature
from music21.stream import Stream
from music21.midi.translate import streamToMidiFile
from music21.midi import MidiEvent, DeltaTime, ChannelVoiceMessages


def create_fluidsynth() -> fluidsynth.Synth:
    # Initialize FluidSynth
    synth = fluidsynth.Synth(gain=1.0, samplerate=44100, channels=1)
    synth.start()
    return synth


def part_to_waveform(melody: Stream, synth: fluidsynth.Synth, soundfont_filename: str, sample_rate: int = 44100):
    """
    Converts a music21 Part object into a waveform represented as a numpy array.

    Parameters:
    - melody: music21.stream.Stream object containing the melody.
    - synth: fluidsynth.Synth object.
    - soundfont_filename: path of a soundfont in .sf2 format.
    - sample_rate: Sampling rate (default is 44100 Hz).

    Returns:
    - A numpy array representing the waveform of the melody.
    """
    # Convert the Part object to MIDI data
    midi_data = streamToMidiFile(melody)

    # Prepare counters for each track
    counters = np.array([0] * len(midi_data.tracks), dtype=int)
    current_time = np.array([0] * len(midi_data.tracks), dtype=int)  # Keep track of the current time in each track
    progressing_time = 0  # Overall time across all tracks

    # Buffer for the waveform data
    waveform = np.array([], dtype=np.float32)

    def next_event():
        current_track = np.argmin(current_time)
        if counters[current_track] >= len(midi_data.tracks[current_track].events):
            found_another_track = False
            for track_skip in range(1, len(midi_data.tracks)):
                i = current_track + track_skip % len(midi_data.tracks)
                if counters[i] >= len(midi_data.tracks[i].events):
                    continue
                else:
                    current_track = i
                    found_another_track = True
                    break
            if not found_another_track:
                return None, None
        focused_event = midi_data.tracks[current_track].events[counters[current_track]]
        counters[current_track] += 1
        if isinstance(focused_event, DeltaTime):
            time_progression = int((focused_event.time / (10080 * 2)) * sample_rate)
            current_time[current_track] += time_progression
            return next_event()
        else:
            return focused_event, current_time[current_track]

    sfid = synth.sfload(soundfont_filename)
    synth.program_select(0, sfid, 0, 0)
    while True:
        event, new_time = next_event()
        if event is None:
            break
        consume_time = new_time - progressing_time
        if consume_time > 0:
            samples = synth.get_samples(int(consume_time))
            waveform = np.append(waveform, samples)
            progressing_time = new_time
        if event.type == ChannelVoiceMessages.NOTE_ON:
            #print(f"Note {event.pitch} on with {event.velocity}!")
            synth.noteon(0, event.pitch, event.velocity)
        elif event.type == ChannelVoiceMessages.NOTE_OFF:
            #print(f"Note {event.pitch} off ...")
            synth.noteoff(0, event.pitch)
        else:
            pass
            #print("Doing nothing for", event)
    synth.all_notes_off(chan=0)
    samples = synth.get_samples(int(sample_rate / 2))
    waveform = np.append(waveform, samples)
    synth.all_sounds_off(chan=0)
    return waveform


if __name__ == "__main__":
    pa = pyaudio.PyAudio()

    # Initial silence is 1 second
    s = np.zeros(44100 * 1, dtype=np.float32)

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

    fl = create_fluidsynth()
    s = np.append(s, part_to_waveform(strm, synth=fl,
                                      soundfont_filename="soundfonts/organ/Aggorg.sf2",
                                      sample_rate=44100))
    fl.delete()
    print(s.shape, s.dtype, type(s), np.min(s), np.max(s))
    print(f"Created a numpy array with shape {s.shape} of type {s.dtype} with values in the range {np.min(s)} to {np.max(s)}.")
    samps = fluidsynth.raw_audio_string(s)
    print('Starting playback')
    pa_strm = pa.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        output=True)
    pa_strm.write(samps)

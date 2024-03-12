from music21.note import Note
from music21.chord import Chord
from music21.interval import Interval
from music21.stream import Stream, Part
from circle_of_fiths import CircleOfFifths, MajorMinor, major, minor
from random import choice, randint


def transpose_to_octave(tone: Note, octave_no: int = 4) -> Note:
    while tone.octave > octave_no:
        tone = tone.transpose('P-8')
    while tone.octave < octave_no:
        tone = tone.transpose('P8')
    return tone


def transpose_chord_to_octave(chord: Chord, octave_no: int = 4) -> Chord:
    while get_lowest_note_of_chord(chord).octave > octave_no:
        chord = chord.transpose('P-8')
    while get_lowest_note_of_chord(chord).octave < octave_no:
        chord = chord.transpose('P8')
    return chord


def build_chord(base_tone: Note, mode: MajorMinor = major, inversion=0):
    intervals = ('M3', 'm3') if mode == major else ('m3', 'M3')
    second_tone = base_tone.transpose(intervals[0])
    third_tone = second_tone.transpose(intervals[1])
    if inversion >= 1:
        base_tone = base_tone.transpose('P8')
    if inversion >= 2:
        second_tone = second_tone.transpose('P8')
    return Chord([base_tone, second_tone, third_tone])


def build_chord_and_select_inversion(base_tone: Note, mode: MajorMinor, prev_base_tone: Note) -> Chord:
    chord = transpose_chord_to_octave(build_chord(base_tone, mode, inversion=0))
    chord6 = transpose_chord_to_octave(build_chord(base_tone, mode, inversion=1))
    chordq6 = transpose_chord_to_octave(build_chord(base_tone, mode, inversion=2))
    return sorted([chord, chord6, chordq6],
                  key=lambda x: Interval(prev_base_tone, get_lowest_note_of_chord(x)).semitones)[0]


def get_lowest_note_of_chord(c: Chord) -> Note:
    return sorted(c.notes, key=lambda x: x.pitch)[0]


def modify_rhythm(melody: Stream) -> Stream:

    def list_available_merges() -> list:
        available_merges = []
        for pos, (n1, n2) in enumerate(zip(melody.notes[:-1], melody.notes[1:])):
            if n1.duration == n2.duration:
                available_merges.append(pos)
        return available_merges

    def list_available_splits():
        return [i for i, n in enumerate(melody.notes) if n.duration.quarterLength >= 0.5]

    available_merges = list_available_merges()
    available_splits = list_available_splits()
    # print(f"There are these {available_merges} merges and these {available_splits} splits available.")

    def do_random_merge(mel: Stream) -> Stream:
        pos = choice(available_merges)
        # print(f"Merging at {pos}.")
        new_melody = Stream()
        for i, tone in enumerate(mel):
            tql = tone.duration.quarterLength
            if i != pos + 1:
                new_melody.append(Note(
                    pitch=tone.pitch,
                    quarterLength=tql * 2 if i == pos else tql))
        return new_melody

    def do_random_split(mel: Stream) -> Stream:
        pos = choice(available_splits)
        # print(f"Splitting at {pos}.")
        new_melody = Stream()
        for i, tone in enumerate(mel):
            tql = tone.duration.quarterLength
            if i == pos:
                tql = 0.5 * tql
                new_melody.append(Note(
                    pitch=tone.pitch,
                    quarterLength=tql))
            new_melody.append(Note(
                pitch=tone.pitch,
                quarterLength=tql))
        return new_melody

    if len(available_merges) >= 1 and len(available_splits) >= 1:
        return choice((do_random_merge, do_random_split))(melody)
    elif len(available_merges) >= 1:
        return do_random_merge(melody)
    else:
        return do_random_split(melody)


def create_rhythm() -> Part:
    part = Part()
    s = Stream([Note('G4', quarterLength=1),
                Note('G4', quarterLength=1),
                Note('G4', quarterLength=1),
                Note('G4', quarterLength=1)])
    s.append(s.transpose(0))
    for _ in range(16):
        s = modify_rhythm(s)
    part.append(s)
    for _ in range(2):
        s = modify_rhythm(s)
    part.append(s)
    return part


class RandomComposer:
    def __init__(self):
        self.cf = CircleOfFifths()

    def create_random_chord_stream(self, note_pattern):
        directions = [(major, -1), (minor, -1),
                      (major, 0), (minor, 0),
                      (major, 1), (minor, 1)]
        mode = choice((major, minor))
        chord_number = randint(0, 11)
        base_note = self.cf.base_note(chord_number)
        base_note.quarterLength = note_pattern[0].quarterLength
        new_chord = build_chord(base_note, mode)
        s = Stream()
        s.append(new_chord)
        for i, pattern_note in enumerate(note_pattern):
            changing_directions = directions.copy()
            changing_directions.pop(directions.index((mode, 0)))
            direction = choice(changing_directions)
            chord_number += direction[1]
            base_note = self.cf.base_note(chord_number % 12)
            base_note.quarterLength = pattern_note.quarterLength
            base_note = transpose_to_octave(base_note, 4)
            new_chord = build_chord(base_note, direction[0])
            s.append(new_chord)
            mode = direction[0]
        return s

    def compose(self):
        rhythm = create_rhythm()
        s = self.create_random_chord_stream(note_pattern=rhythm.notes)




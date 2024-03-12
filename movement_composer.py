from typing import List, Dict
import torch
from torch.distributions import uniform
from emotional_narrative import EmotionSequenceGenerator
from typing import cast
import os


class MusicalModifier(object):
    def __init__(self, emo_vector: torch.Tensor = None):
        if not emo_vector:
            esg = EmotionSequenceGenerator()
            self.emo_vector = torch.nn.Parameter(esg.generate_sequence(1).flatten())
        else:
            self.emo_vector = emo_vector

    @property
    def category(self) -> str:
        raise NotImplementedError("Please instantiate a subclass of MusicalModifier.")


class ChordProgression(MusicalModifier):
    def __init__(self, progression: List[int], emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.progression = progression

    def __str__(self):
        return f"{self.__class__.__name__}-[{','.join([str(c) for c in self.progression])}]"

    @property
    def category(self) -> str:
        return "chord_progression"


class PitchDirection(MusicalModifier):
    def __init__(self, direction: float, emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.dir = direction

    def __str__(self):
        return f"{self.__class__.__name__}{self.dir:+.1f}"

    @property
    def category(self) -> str:
        return "pitch_direction"


class TempoChange(MusicalModifier):
    def __init__(self, direction: float, emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.dir = direction

    def __str__(self):
        return f"{self.__class__.__name__}{self.dir:+.1f}"

    @property
    def category(self) -> str:
        return "tempo_change"


class InstrumentCue(MusicalModifier):
    def __init__(self, instrument_type: str, on_off: int, emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.instrument_type = instrument_type
        self.on_off = on_off

    def __str__(self):
        return f"{self.__class__.__name__}-{self.instrument_type}-{'ON' if self.on_off > 0 else 'OFF'}"

    @property
    def category(self) -> str:
        return "instrument_cue"

    @property
    def on(self) -> bool:
        return self.on_off > 0

    @property
    def off(self) -> bool:
        return not self.on


class KeyChange(MusicalModifier):
    def __init__(self, key: int, emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.new_key = key

    def __str__(self):
        return f"{self.__class__.__name__}To{self.new_key:d}"

    @property
    def category(self) -> str:
        return "key_change"


class EffectChange(MusicalModifier):
    def __init__(self, effect_changes: Dict[str, float], emo_vector: torch.Tensor = None):
        super().__init__(emo_vector)
        self.effect_changes = effect_changes

    def __str__(self):
        return f"{self.__class__.__name__}-{str(self.effect_changes).replace(' ', '')}"

    @property
    def category(self) -> str:
        return "effect_change"


class MovementComposer:
    def __init__(self,
                 emo_sequence: torch.Tensor, emo_sequence_offset: int = 0,
                 emo_state_init: torch.Tensor = torch.zeros(5),
                 key_init: int = torch.randint(-11, 12, [1])):
        self.emo_sequence = emo_sequence
        self.emo_seq_pos = emo_sequence_offset
        self.emo_state = emo_state_init
        self.key = key_init
        self.instrument_tracks: List[InstrumentCue] = []
        self.active_instrument_tracks: List[InstrumentCue] = []
        self.modifiers: List[MusicalModifier] = []
        progressions = [
            [1, 5, -4, 4]
        ]
        self.modifiers += [ChordProgression(p) for p in progressions]
        self.modifiers += [PitchDirection(1.0), PitchDirection(-1.0)]
        self.modifiers += [TempoChange(1.0), TempoChange(-1.0)]
        for instrument_type in os.listdir("soundfonts"):
            self.modifiers += [InstrumentCue(instrument_type, 1), InstrumentCue(instrument_type, 0)]
        self.modifiers += [KeyChange(key_no) for key_no in range(-11, 12)]
        self.modifiers.append(EffectChange({"reverb": +0.5}))
        self.composition: List[List[MusicalModifier]] = [[]]

    def compose_movement(self) -> List[List[MusicalModifier]]:
        next_emo = self.emo_sequence[self.emo_seq_pos]
        emotion_delta = next_emo - self.emo_state
        self.select_modifier(self.filter_modifiers(emotion_delta), emotion_delta, next_emo[4])
        # add to composition
        return self.composition

    def filter_modifiers(self, emotion_delta: torch.Tensor) -> List[MusicalModifier]:
        used_up_categories = set()
        for modifier in self.composition[-1]:
            used_up_categories.add(modifier.category)
        filtered_modifiers = []
        for modifier in self.modifiers:
            if modifier.category in used_up_categories:
                continue
            if type(modifier) is KeyChange and cast(KeyChange, modifier).new_key == self.key:
                continue
            if type(modifier) is InstrumentCue:
                inst_cue = cast(InstrumentCue, modifier)
                if inst_cue.off and inst_cue not in self.active_instrument_tracks:
                    continue
            filtered_modifiers.append(modifier)
        return filtered_modifiers

    def select_modifier(self,
                        filtered_modifiers: List[MusicalModifier],
                        emotion_delta: torch.Tensor,
                        randomness: torch.Tensor):
        offered_emo_matrix = torch.stack([m.emo_vector for m in filtered_modifiers])
        distances = torch.sqrt(torch.sum((offered_emo_matrix - emotion_delta) ** 2, dim=1))
        modifier_id = torch.multinomial(torch.nn.Softmax().forward(distances + randomness), 1, replacement=False)
        # modifier_idx = torch.argmax(torch.dot(delta_emotion, modifier_vectors)).item()


if __name__ == "__main__":
    print("Hello!")

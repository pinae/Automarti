from typing import List, Dict
import torch
from torch.distributions import uniform
from emotional_narrative import EmotionSequenceGenerator
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
                 emo_state_init: torch.Tensor = torch.zeros(5),
                 key_init: int = torch.randint(-11, 12, [1])):
        self.emo_state = emo_state_init
        self.key = key_init
        self.modifiers = []
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

    def compose_movement(self, emotion_sequence: torch.Tensor) -> List[Dict]:
        movement = []
        delta_emotions = emotion_sequence[1:] - emotion_sequence[:-1]
        for delta_emotion in delta_emotions:
            modifiers = self.select_modifiers(delta_emotion)
            movement.append(modifiers)
        return movement

    def select_modifiers(self, delta_emotion: torch.Tensor) -> List[Dict]:
        selected_modifiers = []
        for category, modifier_vectors in self.MODIFIER_VECTORS.items():
            if self.randomness == 0:
                modifier_idx = torch.argmax(torch.dot(delta_emotion, modifier_vectors)).item()
                selected_modifiers.append({category: self.CATEGORIES[category][modifier_idx]})
            else:
                for modifier_idx, modifier_vector in enumerate(modifier_vectors):
                    if torch.dot(delta_emotion, modifier_vector) > 0:
                        selected_modifiers.append({category: self.CATEGORIES[category][modifier_idx]})
        return selected_modifiers


if __name__ == "__main__":
    x = MovementComposer()
    d = {}
    for m in x.modifiers:
        print(m, m.category)
        d[str(m)] = vars(m)
    print(d.keys(), [str(d[g]['emo_vector']) for g in d])

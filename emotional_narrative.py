import torch


class EmotionSequenceGenerator:
    DIMENSIONS = {
        "Tension": {'min': 0.0, 'max': 1.0},
        "Motivation": {'min': -1.0, 'max': 1.0},
        "Playfulness": {'min': -1.0, 'max': 1.0},
        "Happyness": {'min': -1.0, 'max': 1.0},
        "Randomness": {'min': 0.0, 'max': 1.0}
    }

    def generate_sequence(self, seq_len):
        emo_dims = []
        for i, dimension in enumerate(self.DIMENSIONS):
            emo_dims.append(torch.distributions.uniform.Uniform(
                low=self.DIMENSIONS[dimension]['min'],
                high=self.DIMENSIONS[dimension]['max']).sample([seq_len]))
        return torch.stack(emo_dims, dim=1)


if __name__ == "__main__":
    generator = EmotionSequenceGenerator()
    emotions = generator.generate_sequence(10)
    print(emotions)

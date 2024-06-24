from typing import Optional
import numpy as np
from src.xlogomini.emulator.fast_emulator import FastEmulator


class DecisionMaker:
    def binary_decision(self):
        pass

    def pick_int(self, from_, to):
        pass


class RandomDecisionMaker(DecisionMaker):
    def __init__(self, random_generator):
        self.random_generator = random_generator

    @classmethod
    def auto_init(cls):
        return cls(np.random.default_rng())

    def binary_decision(self):
        return self.random_generator.integers(0, 2)

    def pick_int(self, from_, to):
        return int(self.random_generator.integers(from_, to))


class IntelligentDecisionMaker(DecisionMaker):
    def __init__(self, emulator: Optional[FastEmulator] = None):
        self.emulator = emulator

    def binary_decision(self):
        pass

    def pick_int(self, from_, to):
        pass

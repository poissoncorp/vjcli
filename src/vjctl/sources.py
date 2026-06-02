from __future__ import annotations

import random

from .events import SocialIncoming


class SimulatedSocialSource:
    def __init__(self, seed: int = 901507) -> None:
        self.rng = random.Random(seed)
        self.next_at = 0.0

    def poll(self, now: float, cooldown: float) -> list[SocialIncoming]:
        if self.next_at <= 0.0:
            self.next_at = now + self.rng.uniform(5.0, 9.0)
            return []
        if cooldown > 0.7 or now < self.next_at:
            return []

        names = ("null.void", "acid_marta", "909_fever", "redacted", "szum", "warehouse_lena")
        kind = "follow" if self.rng.random() < 0.28 else "like"
        self.next_at = now + self.rng.uniform(7.0, 15.0)
        return [SocialIncoming(self.rng.choice(names), kind)]

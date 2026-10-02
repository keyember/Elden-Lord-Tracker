# SPDX-License-Identifier: GPL-3.0-only
"""Monotonic accumulated time, excluding intervals not authorized by the guard."""
import math

class RunClock:
    def __init__(self, seconds=0):
        if isinstance(seconds, bool):
            raise ValueError('Duree enregistree invalide')
        try:
            self.seconds = float(seconds)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError('Duree enregistree invalide') from exc
        if not math.isfinite(self.seconds) or self.seconds < 0:
            raise ValueError('Duree enregistree invalide')
        self.last = None
        self.previous = False

    def sample(self, now, can_count):
        if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now):
            raise ValueError('Horodatage monotone invalide')
        if type(can_count) is not bool:
            raise ValueError('Autorisation de comptage invalide')
        if self.last is not None:
            delta = now - self.last
            if self.previous and can_count and 0 <= delta < 0.5:
                self.seconds += delta
        self.last = now
        self.previous = can_count
        return self.seconds

    def freeze(self):
        self.last = None
        self.previous = False

    def formatted(self):
        n = int(self.seconds)
        return f'{n//3600:02d}:{n%3600//60:02d}:{n%60:02d}'

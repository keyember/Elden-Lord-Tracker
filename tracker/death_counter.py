# SPDX-License-Identifier: GPL-3.0-only
"""v0.6.0 : compteur racine teste sur executable 2.7.1.0.
Comptabilise uniquement les augmentations unitaires observees dans la session.
Les interruptions et changements de personnage ne sont pas rattrapes.
"""
from .i18n import tr, translate_status
import struct
from .character_guard import NameReader

class DeathReader(NameReader):

    def snapshot(self):
        snap = super().snapshot()
        snap.update(death_total_raw=None, death_error=None)
        if not snap['can_count']:
            return snap
        try:
            root = self.ptr(self.globals['identity_root'])
            player = self.ptr(root + 8)
            total = struct.unpack('<I', self.read(root + 148, 4))[0]
            after = super().snapshot()
            if self.ptr(self.globals['identity_root']) != root or self.ptr(root + 8) != player or (not after['can_count']) or (after.get('observed_character') != self.expected):
                after.update(death_total_raw=None, death_error=tr('Lecture en transition'))
                return after
            snap['death_total_raw'] = total
        except (OSError, ValueError, KeyError, struct.error) as exc:
            snap['death_error'] = str(exc)
        return snap

class DeathSession:

    def __init__(self, count=0):
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(tr('Morts de challenge invalides'))
        self.count = count
        self.last = None
        self.pending = None
        self.repeats = 0
        self.blocked = False
        self.warning = None

    def reset_baseline(self):
        self.last = None
        self.pending = None
        self.repeats = 0

    def observe(self, snap):
        out = dict(deaths_total=None, death_tracking_status=None)
        if self.blocked:
            out['death_tracking_status'] = tr('Morts suspendues : compteur en recul, redemarre apres verification')
            return out
        if not snap.get('can_count'):
            if snap.get('screen_state') != 1 and (not snap.get('blackscreen')):
                self.reset_baseline()
            else:
                self.pending = None
                self.repeats = 0
            return out
        raw = snap.get('death_total_raw')
        if isinstance(raw, bool) or not isinstance(raw, int) or (not 0 <= raw <= 4294967295):
            self.reset_baseline()
            out['death_tracking_status'] = tr('Morts indisponibles : lecture non confirmee')
            return out
        if self.pending == raw:
            self.repeats += 1
        else:
            self.pending = raw
            self.repeats = 1
        if self.repeats < 2:
            return out
        out['deaths_total'] = raw
        if self.last is None:
            self.last = raw
        elif raw < self.last:
            self.blocked = True
            out['deaths_total'] = None
            out['death_tracking_status'] = tr('Morts suspendues : compteur en recul, redemarre apres verification')
        elif raw == self.last + 1:
            self.count += 1
            self.last = raw
        elif raw > self.last + 1:
            self.warning = f"{tr('Ecart de ')}{raw - self.last}{tr(' morts : non attribue au challenge')}"
            self.last = raw
        if self.warning and (not out['death_tracking_status']):
            out['death_tracking_status'] = self.warning
        return out

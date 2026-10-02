# SPDX-License-Identifier: GPL-3.0-only
"""NAME_GUARD_CONSOLIDATED_V1 : nom uniquement, pas une identite durable.
Conserve la restriction a l'executable 2.7.1.0.
"""
from .i18n import tr, translate_status
import struct
import threading
from lecture_directe import LiveReader, PATTERNS
from diagnostic_memoire import version

PATTERN = '48 8b 05 ? ? ? ? 48 8d 4d c0 41 b8 10 00 00 00 48 8b 10 48 83 c2 1c'
_PATTERN_LOCK = threading.RLock()


def expected_name(names, slot):
    if not isinstance(names, (list, tuple)) or len(names) != 10 or type(slot) is not int or not 0 <= slot < 10:
        raise ValueError(tr('Liste des slots invalide'))
    name = names[slot]
    if not isinstance(name, str) or not name:
        raise ValueError(tr('Slot sans nom : suivi refuse'))
    if names.count(name) != 1:
        raise ValueError(tr('Nom present dans plusieurs slots : controle ambigu, suivi refuse'))
    return name


def decode_name(raw):
    if len(raw) != 34:
        raise ValueError(tr('Nom incomplet'))
    end = next((i for i in range(0, 34, 2) if raw[i:i + 2] == b'\x00\x00'), None)
    if end is None:
        raise ValueError(tr('Nom non termine'))
    name = raw[:end].decode('utf-16le', 'strict')
    if not name or not all(c.isprintable() for c in name):
        raise ValueError(tr('Nom invalide'))
    return name


class NameReader(LiveReader):
    def __init__(self, expected):
        if not isinstance(expected, str) or not expected:
            raise ValueError(tr('Slot sans nom : suivi refuse'))
        self.expected = expected
        self.matches = 0
        self._matched_pointers = None
        patterns = dict(PATTERNS)
        patterns['identity_root'] = PATTERN
        super().__init__(patterns=patterns)
        try:
            if version(self.path) != '2.7.1.0':
                raise ValueError(tr('Version executable non validee pour le controle du nom'))
        except Exception:
            self.close()
            raise

    def _reset_confirmation(self):
        self.matches = 0
        self._matched_pointers = None

    def snapshot(self):
        snap = super().snapshot()
        snap.update(observed_character=None, name_match=None, identity_verified=False,
                    identity_mode='name_only', can_count=False)
        if snap['screen_state'] != 0 or snap['blackscreen']:
            self._reset_confirmation()
            snap['guard_status'] = tr('pause automatique')
            return snap
        try:
            root = self.ptr(self.globals['identity_root'])
            player = self.ptr(root + 8)
            name = decode_name(self.read(player + 156, 34))
            if self.ptr(self.globals['identity_root']) != root or self.ptr(root + 8) != player:
                raise ValueError(tr('Personnage en transition'))
            after = super().snapshot()
            if not after['can_count']:
                self._reset_confirmation()
                snap['guard_status'] = tr('pause automatique')
                return snap
            if self.ptr(self.globals['identity_root']) != root or self.ptr(root + 8) != player:
                raise ValueError(tr('Personnage en transition'))
            snap['observed_character'] = name
            snap['name_match'] = name == self.expected
            if not snap['name_match']:
                self._reset_confirmation()
                snap['guard_status'] = f"{tr('PAUSE : personnage charge ')}{name}{tr(', attendu ')}{self.expected}"
            else:
                pointers = (root, player)
                if self._matched_pointers != pointers:
                    self.matches = 0
                    self._matched_pointers = pointers
                self.matches += 1
                snap['can_count'] = self.matches >= 3
                snap['guard_status'] = tr('chrono actif - nom concordant (slot non verifie)') if snap['can_count'] else tr('pause - confirmation du nom')
        except (OSError, ValueError, KeyError, UnicodeError, struct.error) as exc:
            self._reset_confirmation()
            snap['guard_status'] = f"{tr('PAUSE : nom illisible (')}{exc})"
        return snap

# PRIVATE_READER_PATTERNS_V1

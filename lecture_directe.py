# SPDX-License-Identifier: GPL-3.0-only
# Pointer definitions and screen-state logic adapted from SoulMemory/EldenRing.
# Copyright (c) 2022 Frank van der Stam; modifications 2026-10-02.
# Original: https://github.com/FrankvdStam/SoulSplitter
# This test reader excludes ALL writes, injection and no-logo patches.
from tracker.i18n import tr, translate_status
import ctypes as C
import struct
import re
import time
from diagnostic_memoire import api, processes, module
PATTERNS = {'time': '48 8b 05 ? ? ? ? 4c 8b 40 08 4d 85 c0 74 0d 45 0f b6 80 be 00 00 00 e9 13 00 00 00', 'menu': '48 8b 0d ? ? ? ? 48 8b 53 08 48 8b 92 d8 00 00 00 48 83 c4 20 5b'}

def regex(pattern):
    return re.compile(b''.join((b'.' if t == '?' else re.escape(bytes([int(t, 16)])) for t in pattern.split())), re.DOTALL)

def relative_address(address, instruction):
    return address + 7 + struct.unpack_from('<i', instruction, 3)[0]

class LiveReader:

    def __init__(self, patterns=None):
        patterns = dict(PATTERNS if patterns is None else patterns)
        if not {'time', 'menu'} <= patterns.keys():
            raise ValueError('Signatures time/menu manquantes')
        compiled = {key: regex(pattern) for key, pattern in patterns.items()}
        overlap = max(len(pattern.split()) for pattern in patterns.values()) - 1
        self.k = api()
        self.handle = None
        items = processes(self.k)
        if any('easyanticheat' in n.lower() or n.lower() == 'start_protected_game.exe' for _, n in items):
            raise ValueError('Processus EAC detecte : lecture refusee')
        games = [pid for pid, n in items if n.lower() == 'eldenring.exe']
        if len(games) != 1:
            raise ValueError('Lance une seule instance du jeu avec EAC desactive')
        self.pid = games[0]
        self.path, self.base, self.size = module(self.k, self.pid)
        self.handle = self.k.OpenProcess(1024 | 16, False, self.pid)
        if not self.handle:
            raise C.WinError(C.get_last_error())
        try:
            header = self.read(self.base, 4096)
            pe = struct.unpack_from('<I', header, 60)[0]
            if header[pe:pe + 4] != b'PE\x00\x00':
                raise ValueError('Executable PE invalide')
            count = struct.unpack_from('<H', header, pe + 6)[0]
            optional = struct.unpack_from('<H', header, pe + 20)[0]
            table = self.read(self.base + pe + 24 + optional, count * 40)
            matches = {key: [] for key in patterns}
            for i in range(count):
                section = table[i * 40:(i + 1) * 40]
                size, rva = struct.unpack_from('<II', section, 8)
                flags = struct.unpack_from('<I', section, 36)[0]
                if not flags & 536870912:
                    continue
                if size > self.size or rva + size > self.size:
                    raise ValueError('Section PE incoherente')
                previous = b''
                for offset in range(0, size, 1024 * 1024):
                    block = self.read(self.base + rva + offset, min(1024 * 1024, size - offset))
                    chunk = previous + block
                    origin = self.base + rva + offset - len(previous)
                    for key, expression in compiled.items():
                        for match in expression.finditer(chunk):
                            address = origin + match.start()
                            if address not in matches[key]:
                                matches[key].append(address)
                    previous = chunk[-overlap:] if overlap else b''
            self.globals = {}
            for key, addresses in matches.items():
                if len(addresses) != 1:
                    raise ValueError(f'Signature {key} : {len(addresses)} correspondances, lecture refusee')
                self.globals[key] = relative_address(addresses[0], self.read(addresses[0], 7))
        except Exception:
            self.close()
            raise

    def read(self, address, size):
        if not address or address < 65536:
            raise ValueError('Pointeur nul ou invalide')
        buffer = C.create_string_buffer(size)
        read = C.c_size_t()
        if not self.k.ReadProcessMemory(self.handle, address, buffer, size, C.byref(read)) or read.value != size:
            raise C.WinError(C.get_last_error())
        return buffer.raw

    def ptr(self, address):
        return struct.unpack('<Q', self.read(address, 8))[0]

    def integer(self, address):
        return struct.unpack('<i', self.read(address, 4))[0]

    def snapshot(self):
        fd4 = self.ptr(self.globals['time'])
        menu = self.ptr(self.globals['menu'])
        state = self.integer(menu + 1840)
        if state not in (0, 1, 256):
            return {'raw_igt_ms': None, 'screen_state': state, 'screen_name': f"{tr('Etat inconnu (')}{state})", 'blackscreen': False, 'can_count': False}
        flag = self.integer(menu + 24)
        black = state == 0 and flag & 1 == 1 and (flag >> 8 & 1 == 0) and (flag >> 16 & 1 == 1)
        milliseconds = self.integer(fd4 + 160)
        if milliseconds < 0:
            raise ValueError('Temps brut negatif : lecture refusee')
        return {'raw_igt_ms': milliseconds, 'screen_state': state, 'screen_name': {0: tr('En jeu'), 1: tr('Chargement'), 256: tr('Menu principal')}[state], 'blackscreen': black, 'can_count': state == 0 and (not black)}

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None

# PRIVATE_READER_PATTERNS_V1

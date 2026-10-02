# SPDX-License-Identifier: GPL-3.0-only
# Lecture adaptee de SoulMemory, Frank van der Stam ; adaptation Python 2026-10-02.
from .i18n import tr, translate_status
import struct

def locate_flags(reader):
    import re

    def pattern_regex(pattern):
        return re.compile(b''.join((b'.' if token == '?' else re.escape(bytes([int(token, 16)])) for token in pattern.split())), re.DOTALL)
    header = reader.read(reader.base, 4096)
    pe = struct.unpack_from('<I', header, 60)[0]
    if header[pe:pe + 4] != b'PE\x00\x00':
        raise ValueError('Executable PE invalide')
    count = struct.unpack_from('<H', header, pe + 6)[0]
    optional = struct.unpack_from('<H', header, pe + 20)[0]
    if not 1 <= count <= 128:
        raise ValueError('Nombre de sections PE incoherent')
    table = reader.read(reader.base + pe + 24 + optional, count * 40)
    pattern = pattern_regex('44 89 7c 24 28 4c 8b 25 ? ? ? ? 4d 85 e4')
    matches = set()
    for i in range(count):
        section = table[i * 40:(i + 1) * 40]
        size, rva = struct.unpack_from('<II', section, 8)
        flags = struct.unpack_from('<I', section, 36)[0]
        if not flags & 536870912:
            continue
        if rva + size > reader.size:
            raise ValueError('Section executable incoherente')
        previous = b''
        for offset in range(0, size, 1024 * 1024):
            block = reader.read(reader.base + rva + offset, min(1024 * 1024, size - offset))
            chunk = previous + block
            origin = reader.base + rva + offset - len(previous)
            matches.update((origin + match.start() for match in pattern.finditer(chunk)))
            previous = chunk[-64:]
    if len(matches) != 1:
        raise ValueError(f'Signature complete event_flags : {len(matches)} correspondances, lecture refusee')
    address = next(iter(matches))
    instruction = reader.read(address, 12)
    return address + 12 + struct.unpack_from('<i', instruction, 8)[0]

def flag(reader, manager, identifier):
    divisor = reader.integer(manager + 28)
    if not 1 <= divisor <= 1000000:
        raise ValueError('Diviseur de flags invalide ou non initialise')
    category, remainder = divmod(identifier, divisor)
    header = reader.ptr(manager + 56)
    node = reader.ptr(header + 8)
    candidate = header
    seen = set()
    for _ in range(128):
        sentinel = reader.read(node + 25, 1)[0]
        if sentinel == 1:
            break
        if sentinel != 0 or node in seen:
            raise ValueError('Arbre de flags incoherent')
        seen.add(node)
        key = reader.integer(node + 32)
        if key < category:
            node = reader.ptr(node + 16)
        else:
            candidate = node
            node = reader.ptr(node)
    else:
        raise ValueError('Parcours de flags trop long')
    if candidate == header or reader.integer(candidate + 32) != category:
        raise ValueError('Categorie absente : etat inconnu, pas faux')
    mode = reader.integer(candidate + 40)
    if mode == 1:
        stride = reader.integer(manager + 32)
        index = reader.integer(candidate + 48)
        if stride <= 0 or index < 0:
            raise ValueError('Stockage indexe invalide')
        storage = reader.ptr(manager + 40) + stride * index
    elif mode == 2:
        raise ValueError('Categorie sans stockage lisible')
    else:
        storage = reader.ptr(candidate + 48)
    byte = reader.read(storage + (remainder >> 3), 1)[0]
    return bool(byte & 1 << 7 - (remainder & 7))

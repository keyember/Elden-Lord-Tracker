
"""Layout PC teste sur le fichier fourni ; timer non valide dans le jeu."""
from .i18n import tr, translate_status
import hashlib
import shutil
import struct
STRIDE = 2621456
SUMMARY = 26215328
NAME = 26221838

def checksum_section(data, start, size):
    section = data[start:start + size]
    if len(section) != size:
        raise ValueError('Fichier incomplet')
    if hashlib.md5(section[16:]).digest() != section[:16]:
        raise ValueError('Checksum invalide : copie rejetee')

def validate_slot(data, slot):
    if data[:4] != b'BND4' or not 0 <= slot <= 9:
        raise ValueError('Format PC BND4 ou slot invalide')
    checksum_section(data, 768 + slot * STRIDE, STRIDE)

def read_names(data):
    if data[:4] != b'BND4':
        raise ValueError('Format PC BND4 requis')
    checksum_section(data, SUMMARY, 393232)
    names = []
    for slot in range(10):
        address = NAME + slot * 588
        name = data[address:address + 32].decode('utf-16le').split('\x00', 1)[0]
        if any((not ch.isprintable() for ch in name)):
            raise ValueError('Nom non interpretable')
        names.append(name)
    return names

def format_time(seconds):
    hours, rest = divmod(seconds, 3600)
    minutes, sec = divmod(rest, 60)
    return f'{hours:02d}:{minutes:02d}:{sec:02d}'

def read_profile(data, slot):
    validate_slot(data, slot)
    names = read_names(data)
    address = NAME + slot * 588
    level = struct.unpack_from('<I', data, address + 34)[0]
    seconds = struct.unpack_from('<I', data, address + 38)[0]
    if not names[slot] or not 1 <= level <= 713 or seconds > 100000000:
        raise ValueError('Profil vide ou layout non pris en charge')
    return {'slot': slot, 'character_name': names[slot], 'level': level, 'seconds_played': seconds, 'timer': format_time(seconds), 'checksum_valid': True, 'timer_validated': False}

def copy_save(source, target):
    if source.resolve() == target.resolve():
        raise ValueError('Ne selectionne pas la copie temporaire')
    before = source.stat()
    shutil.copy2(source, target)
    after = source.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise OSError('Sauvegarde modifiee pendant la copie')
    return target.read_bytes()

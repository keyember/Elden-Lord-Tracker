
"""Profils explicites : le chemin et le slot ne sont PAS une identite de personnage.
Si une save est remplacee ou un personnage recree, choisir un nouveau challenge.
Les donnees existantes ne sont jamais fusionnees automatiquement.
"""
from .i18n import tr, translate_status
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .paths import DATA
from .storage import write_json
DIRECTORY = DATA / 'profiles'
SELECTION = DATA / 'challenge_selection.json'

def key(source):
    return str(Path(source).resolve())

def list_profiles(source, slot):
    DIRECTORY.mkdir(parents=True, exist_ok=True)
    result = []
    for path in DIRECTORY.glob('*.json'):
        try:
            profile = json.loads(path.read_text(encoding='utf-8'))
            if profile.get('source') == key(source) and profile.get('slot') == slot:
                result.append(profile)
        except (OSError, ValueError, AttributeError):
            continue
    return sorted(result, key=lambda p: p.get('created_at', ''))

def create_profile(source, slot, name):
    name = name.strip()
    if not name or len(name) > 80:
        raise ValueError(tr('Nom requis, 80 caracteres maximum'))
    if not 0 <= slot <= 9:
        raise ValueError(tr('Slot invalide'))
    profile = {'id': uuid.uuid4().hex, 'name': name, 'source': key(source), 'slot': slot, 'created_at': datetime.now(timezone.utc).isoformat(), 'schema_version': 1, 'boss_attempts': {}, 'boss_history': [], 'last_deaths': None, 'status': 'active'}
    write_json(DIRECTORY / (profile['id'] + '.json'), profile)
    return profile

def select_profile(profile):
    write_json(SELECTION, {'profile_id': profile['id'], 'source': profile['source'], 'slot': profile['slot']})

def selected_profile(source, slot):
    try:
        selection = json.loads(SELECTION.read_text(encoding='utf-8'))
        if selection.get('source') != key(source) or selection.get('slot') != slot:
            return None
        identifier = selection['profile_id']
        if not isinstance(identifier, str) or len(identifier) != 32 or any((c not in '0123456789abcdef' for c in identifier)):
            return None
        p = json.loads((DIRECTORY / (identifier + '.json')).read_text(encoding='utf-8'))
        if p.get('source') == key(source) and p.get('slot') == slot:
            return p
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return None

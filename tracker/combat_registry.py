from .boss_catalog import BOSSES, BY_ID


SOURCE_BANK = {
    str(b['flag_id']): dict(
        boss_id=b['id'],  # Utilise b['id'] directement au lieu de BY_ID[b['flag_id']]['id']
        active_flag=b['flag_id'] + 2005,
        repository='soulsmodding.com/doku.php',
        revision='2025-02-27',
        path='tutorial:learning-how-to-use-emevd',
        event='emevd_event_flag_offset',
        parameter='elden_ring_offset_2000_plus',
        validation='documented'
    )
    for b in BOSSES
}


ENABLED_LEVELS = frozenset({'documented', 'user_tested'})


def read_configuration():
    import json
    from pathlib import Path
    CONFIG_PATH = Path(__file__).resolve().parent / 'catalogue_data/combat_catalog.json'
    try:
        doc = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig'))
        if not isinstance(doc, dict) or doc.get('schema_version') != 1 or not isinstance(doc.get('encounters'), dict):
            raise ValueError('Configuration invalide')
        entries = doc['encounters']; seen = {}; enabled = 0
        for key, item in entries.items():
            if key not in BY_ID or not isinstance(item, dict):
                raise ValueError('Rencontre inconnue')
            level = item.get('validation'); active = item.get('active_flag')
            if level not in ('not_configured', 'candidate', 'documented', 'user_tested'):
                raise ValueError('Validation invalide')
            if active is not None and (type(active) is not int or not 0 <= active <= 4294967295 or active == BY_ID[key]['flag_id']):
                raise ValueError('Flag invalide')
            if level == 'documented':
                reference = SOURCE_BANK.get(str(BY_ID[key]['flag_id']))
                source = item.get('source', {})
                if not reference or active != reference['active_flag'] or not isinstance(source, dict) or any(source.get(field) != reference[field] for field in ('repository', 'revision', 'path', 'event', 'parameter')):
                    raise ValueError('Association documentee sans provenance correspondante')
            if level in ENABLED_LEVELS and item.get('enabled', True) is not False:
                if active is None:
                    raise ValueError('Flag de combat manquant')
                if active in seen and seen[active] != key:
                    raise ValueError('Flag actif partage : attribution ambigue')
                seen[active] = key; enabled += 1
        if enabled > len(BOSSES):
            raise ValueError('Suivis actifs au dela du catalogue : configuration refusee')
        return entries, None
    except (OSError, ValueError, TypeError):
        import sys
        return {}, str(sys.exc_info()[1])


def supported_specs(include_disabled=False):
    specs = list(SOURCE_BANK.values())
    if include_disabled:
        return specs
    return [s for s in specs if s.get('validation') in ENABLED_LEVELS]


def supported_spec(boss_id):
    # Cherche par boss_id, pas par flag_id
    for key, spec in SOURCE_BANK.items():
        if spec.get('boss_id') == boss_id:
            return spec
    return None


__all__ = ['SOURCE_BANK', 'supported_specs', 'supported_spec', 'read_configuration']
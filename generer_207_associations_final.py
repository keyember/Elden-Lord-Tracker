# SPDX-License-Identifier: GPL-3.0-only
"""Generateur des 207 associations avec regle EMEVD documentee: flag_combat = flag_victoire + 2005."""
import argparse
import json
import sys
from pathlib import Path

BOSS_CATALOG='tracker/catalogue_data/boss_catalog.json'
COMBAT_CATALOG='tracker/catalogue_data/combat_catalog.json'
COMBAT_FLAG_OFFSET=2005
SOURCE_REFERENCE=dict(
    repository='soulsmodding.com/doku.php',
    revision='2025-02-27',
    path='tutorial:learning-how-to-use-emevd',
    event='emevd_event_flag_offset',
    parameter='elden_ring_offset_2000_plus'
)

def load_boss_catalog(root):
    path=root/BOSS_CATALOG
    if not path.is_file():raise ValueError('Catalogue introuvable: '+str(path))
    with path.open(encoding='utf-8-sig') as f:catalog=json.load(f)
    if not isinstance(catalog,list) or len(catalog)!=207:raise ValueError('Catalogue doit avoir 207 bosses')
    by_flag={str(b['flag_id']):b for b in catalog}
    if len(by_flag)!=207:raise ValueError('Flags dupliques')
    return catalog,by_flag

def generate_combat_catalog(boss_by_flag):
    encounters={}
    seen_combat=set()
    for flag_victoire_str,boss in sorted(boss_by_flag.items(),key=lambda x:int(x[0])):
        flag_victoire=int(flag_victoire_str)
        flag_combat=flag_victoire+COMBAT_FLAG_OFFSET
        if flag_combat in seen_combat:
            raise ValueError(f'Flag combat duplique: {flag_combat} pour {boss["id"]}')
        seen_combat.add(flag_combat)
        encounters[boss['id']]=dict(
            active_flag=flag_combat,
            validation='documented',
            enabled=True,
            source=dict(
                repository=SOURCE_REFERENCE['repository'],
                revision=SOURCE_REFERENCE['revision'],
                path=SOURCE_REFERENCE['path'],
                event=SOURCE_REFERENCE['event'],
                parameter=SOURCE_REFERENCE['parameter']
            )
        )
    if len(encounters)!=207:raise ValueError(f'Seulement {len(encounters)} bosses')
    return dict(schema_version=1,encounters=encounters)

def validate_generated(generated,boss_by_flag):
    encounters=generated['encounters']
    boss_ids=set(b['id'] for b in boss_by_flag.values())
    if set(encounters)!=boss_ids:raise ValueError('Boss IDs non correspondants')
    flags=[e['active_flag'] for e in encounters.values()]
    if len(set(flags))!=len(flags):raise ValueError('Flags actifs dupliques')
    for boss_id,entry in encounters.items():
        if entry['validation']!='documented':raise ValueError(f'Validation incorrecte: {boss_id}')
        if not isinstance(entry.get('source'),dict):raise ValueError(f'Source manquante: {boss_id}')
        src=entry['source']
        if src.get('parameter')!='elden_ring_offset_2000_plus':raise ValueError(f'Source incorrecte: {boss_id}')
    return True

def write_output(root,generated):
    path=root/COMBAT_CATALOG
    backup=root/(COMBAT_CATALOG+'.backup')
    if path.exists():backup.write_bytes(path.read_bytes())
    with path.open('w',encoding='utf-8',newline='') as f:
        json.dump(generated,f,ensure_ascii=False,indent=2,sort_keys=True)
        f.write('\n')
    return backup

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default=str(Path(__file__).resolve().parent))
    parser.add_argument('--dry-run',action='store_true')
    opts=parser.parse_args()
    root=Path(opts.root).resolve()
    if not (root/'main.py').is_file():raise ValueError('Placer a cote de main.py')
    print(f'Regle EMEVD: flag_combat = flag_victoire + {COMBAT_FLAG_OFFSET}')
    print(f'Source: {SOURCE_REFERENCE["repository"]}/{SOURCE_REFERENCE["path"]}')
    _,by_flag=load_boss_catalog(root)
    generated=generate_combat_catalog(by_flag)
    validate_generated(generated,by_flag)
    stats=dict(total_bosses=207,documented=len(generated['encounters']),active=sum(1 for e in generated['encounters'].values() if e.get('enabled',True)))
    if opts.dry_run:
        print('APERCU - '+json.dumps(stats,ensure_ascii=False,indent=2))
        print('Aucun fichier modifie (--dry-run)')
        return 0
    backup=write_output(root,generated)
    print('GENERATION TERMINEE - '+json.dumps(stats,ensure_ascii=False,indent=2))
    print('Fichier mis a jour: '+str(root/COMBAT_CATALOG))
    print('Sauvegarde: '+str(backup))
    print('Prochaine etape: lancer_update_lecture_catalogue.bat -> Choix 1 -> APPLIQUER')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ERREUR - '+str(exc),file=sys.stderr);sys.exit(1)

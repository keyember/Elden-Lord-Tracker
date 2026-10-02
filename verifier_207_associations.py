# SPDX-License-Identifier: GPL-3.0-only
"""Verification que les 207 associations sont correctes et compatibles."""
import json
import sys
from pathlib import Path

COMBAT_CATALOG='tracker/catalogue_data/combat_catalog.json'
BOSS_CATALOG='tracker/catalogue_data/boss_catalog.json'

def verify():
    root=Path(__file__).resolve().parent
    combat_path=root/COMBAT_CATALOG
    boss_path=root/BOSS_CATALOG

    if not combat_path.is_file():
        print(f"ERREUR: {COMBAT_CATALOG} introuvable")
        return 1
    if not boss_path.is_file():
        print(f"ERREUR: {BOSS_CATALOG} introuvable")
        return 1

    with combat_path.open(encoding='utf-8') as f:
        combat=json.load(f)
    with boss_path.open(encoding='utf-8-sig') as f:
        bosses=json.load(f)

    print("VERIFICATION DES 207 ASSOCIATIONS")
    print("="*60)

    # Check 1: Nombre d'encounters
    if len(combat.get('encounters',{}))!=207:
        print(f"ERREUR: {len(combat.get('encounters',{}))} encounters au lieu de 207")
        return 1
    print(f"✓ 207 encounters trouves")

    # Check 2: Tous les bosses sont presents
    boss_ids=set(b['id'] for b in bosses)
    encounter_ids=set(combat['encounters'].keys())
    if boss_ids!=encounter_ids:
        print(f"ERREUR: Boss IDs non correspondants")
        print(f"  Manquants: {boss_ids-encounter_ids}")
        print(f"  En trop: {encounter_ids-boss_ids}")
        return 1
    print(f"✓ Tous les 207 bosses sont presents")

    # Check 3: Toutes les associations sont 'documented'
    not_documented=[k for k,v in combat['encounters'].items() if v.get('validation')!='documented']
    if not_documented:
        print(f"ERREUR: {len(not_documented)} associations non 'documented': {not_documented[:5]}")
        return 1
    print(f"✓ Toutes les associations sont 'documented'")

    # Check 4: Toutes les associations sont 'enabled'
    disabled=[k for k,v in combat['encounters'].items() if v.get('enabled',True)==False]
    if disabled:
        print(f"ERREUR: {len(disabled)} associations desactivees: {disabled[:5]}")
        return 1
    print(f"✓ Toutes les associations sont 'enabled'")

    # Check 5: Source parameter correct
    wrong_source=[k for k,v in combat['encounters'].items() if v.get('source',{}).get('parameter')!='elden_ring_offset_2000_plus']
    if wrong_source:
        print(f"ERREUR: {len(wrong_source)} associations avec source incorrecte: {wrong_source[:5]}")
        return 1
    print(f"✓ Toutes les sources sont correctes (elden_ring_offset_2000_plus)")

    # Check 6: Flags de combat uniques
    flags=[v['active_flag'] for v in combat['encounters'].values()]
    if len(set(flags))!=207:
        print(f"ERREUR: {207-len(set(flags))} flags de combat dupliques")
        return 1
    print(f"✓ 207 flags de combat uniques")

    # Check 7: Offset correct
    boss_by_flag={str(b['flag_id']):b for b in bosses}
    wrong_offset=[]
    for boss_id,enc in combat['encounters'].items():
        boss=boss_by_flag.get(boss_id)
        if boss:
            expected=boss['flag_id']+2005
            if enc['active_flag']!=expected:
                wrong_offset.append((boss_id,enc['active_flag'],expected))
    if wrong_offset:
        print(f"ERREUR: {len(wrong_offset)} associations avec offset incorrect: {wrong_offset[:3]}")
        return 1
    print(f"✓ Toutes les associations utilisent offset +2005")

    # Check 8: Exemples
    print(f"\nEXEMPLES:")
    for i,boss_id in enumerate(sorted(combat['encounters'].keys())[:3]):
        enc=combat['encounters'][boss_id]
        boss=boss_by_flag[boss_id]
        print(f"  {boss_id}:")
        print(f"    flag_victoire: {boss['flag_id']}")
        print(f"    flag_combat: {enc['active_flag']} (offset={enc['active_flag']-boss['flag_id']})")
        print(f"    validation: {enc['validation']}")
        print(f"    enabled: {enc.get('enabled',True)}")

    print(f"\n" + "="*60)
    print(f"VERIFICATION REUSSIE - Les 207 associations sont correctes")
    print(f"Prochaine etape: lancer_update_lecture_catalogue.bat -> Choix 1 -> APPLIQUER")
    return 0

if __name__=='__main__':
    try:sys.exit(verify())
    except Exception as exc:print(f'ERREUR - {exc}',file=sys.stderr);sys.exit(1)

# SPDX-License-Identifier: GPL-3.0-only
"""Generic registry: explicit associations, no numeric suffix inference."""
import json
from pathlib import Path
from .boss_catalog import BOSSES, BY_ID, active_bosses, display_name
from .i18n import get_language,settings,tr
CONFIG_PATH=Path(__file__).resolve().parent/'catalogue_data/combat_catalog.json'
SOURCE_BANK={'1033420800': {'active_flag': 1033422806, 'path': 'eldenring/events/m60_33_42_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1036500800': {'active_flag': 1036502806, 'path': 'eldenring/events/m60_36_50_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1033450800': {'active_flag': 1033452806, 'path': 'eldenring/events/m60_33_45_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1039500800': {'active_flag': 1039502806, 'path': 'eldenring/events/m60_39_50_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1042370800': {'active_flag': 1042372806, 'path': 'eldenring/events/m60_42_37_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1038410800': {'active_flag': 1038412806, 'path': 'eldenring/events/m60_38_41_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1053560800': {'active_flag': 1053562806, 'path': 'eldenring/events/m60_53_56_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1044350800': {'active_flag': 1044352806, 'path': 'eldenring/events/m60_44_35_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1042330800': {'active_flag': 1042332806, 'path': 'eldenring/events/m60_42_33_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1049390850': {'active_flag': 1049392856, 'path': 'eldenring/events/m60_49_39_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}}
UI_KEYS=('Suivi des combats', 'Couverture du catalogue', 'Historique du challenge', 'Catalogue', 'Historique', 'Rencontres du catalogue', 'Rencontres actives', 'Suivis actifs disponibles', 'Validé sur ton PC', 'Non configuré', 'À vérifier', 'Prise en charge', 'Disponible', 'Non pris en charge par ce prototype', 'Boss', 'Contenu', 'Flag de combat', 'Validation', 'Rechercher un boss', 'Actualiser', 'Jeu de base', 'Aucun challenge sélectionné', 'Aucune tentative enregistrée', 'Tentative observée', 'Résultat', 'Début observé', 'Fin observée', 'Durée observée', 'Sans fin enregistrée', 'Temps inconnu', 'Mort', 'Victoire', 'Victoire et mort observées', 'Interrompu - résultat inconnu', 'Résultat incertain', 'Historique enregistré uniquement, sans import des diagnostics.', 'Configurer une rencontre ne suffit pas à valider son suivi.', 'Configuration de combat indisponible', 'Connexion au tracker interrompue', 'Le suivi actif reste limité à Godefroy.', 'Documenté - non testé sur ton PC', 'Disponible - expérimental', 'Le suivi actif dépend des associations configurées.', 'Suivi expérimental', 'Plusieurs signaux de combat actifs - attribution suspendue')
ENABLED_LEVELS=frozenset({'documented','user_tested'})


def ui(language):return {key:tr(key,language) for key in UI_KEYS}


def read_configuration():
    try:
        doc=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        if not isinstance(doc,dict) or doc.get('schema_version')!=1 or not isinstance(doc.get('encounters'),dict):raise ValueError('Configuration invalide')
        entries=doc['encounters'];seen={};enabled=0
        for key,item in entries.items():
            if key not in BY_ID or not isinstance(item,dict):raise ValueError('Rencontre inconnue')
            level=item.get('validation');active=item.get('active_flag')
            if level not in ('not_configured','candidate','documented','user_tested'):raise ValueError('Validation invalide')
            if active is not None and (type(active) is not int or not 0<=active<=4294967295 or active==BY_ID[key]['flag_id']):raise ValueError('Flag invalide')
            if level=='documented':
                reference=SOURCE_BANK.get(str(BY_ID[key]['flag_id']))
                source=item.get('source',{})
                if not reference or active!=reference['active_flag'] or not isinstance(source,dict) or any(source.get(field)!=reference[field] for field in ('repository','revision','path','event','parameter')):raise ValueError('Association documentee sans provenance correspondante')
            if level in ENABLED_LEVELS and item.get('enabled',True) is not False:
                if active is None:raise ValueError('Flag de combat manquant')
                if active in seen and seen[active]!=key:raise ValueError('Flag actif partage : attribution ambigue')
                seen[active]=key;enabled+=1
        if enabled>32:raise ValueError('Plus de 32 suivis actifs : extension a valider avant activation')
        return entries,None
    except (OSError,ValueError,TypeError):
        import sys
        return {},str(sys.exc_info()[1])


def supported_specs(active_only=True):
    entries,error=read_configuration()
    if error:return ()
    allowed={b['id'] for b in active_bosses()} if active_only else set(BY_ID)
    return tuple(dict(boss_id=key,active_flag=item['active_flag'],victory_flag=BY_ID[key]['flag_id'],validation=item['validation'])
                 for key,item in entries.items() if key in allowed and item.get('validation') in ENABLED_LEVELS and item.get('enabled',True) is not False)


def supported_spec(boss_id):return next((spec for spec in supported_specs(False) if spec['boss_id']==boss_id),None)


def catalogue_view():
    language=get_language();entries,error=read_configuration();active_ids={b['id'] for b in active_bosses()};supported={s['boss_id'] for s in supported_specs(False)};rows=[]
    names={'not_configured':'Non configuré','candidate':'À vérifier','documented':'Documenté - non testé sur ton PC','user_tested':'Validé sur ton PC'}
    for boss in BOSSES:
        key=boss['id'];item=entries.get(key,{});level=item.get('validation','not_configured');available=key in supported
        rows.append(dict(boss_id=key,name=display_name(key,language),content=boss.get('content'),content_label=tr('Jeu de base',language) if boss.get('content')=='base_game' else 'DLC',
          active=key in active_ids,active_flag=item.get('active_flag'),validation=level,validation_label=tr(names[level],language),live_supported=available,
          support_label=tr(('Disponible' if level=='user_tested' else 'Disponible - expérimental') if available else 'Non pris en charge par ce prototype',language),source=item.get('source')))
    return dict(language=language,ui=ui(language),rows=rows,configuration_error=error,include_dlc=settings()['include_dlc'],
      summary=dict(catalogue_total=len(rows),active_total=len(active_ids),live_supported_active=sum(r['active'] and r['live_supported'] for r in rows),
                   user_tested=sum(r['validation']=='user_tested' for r in rows),documented=sum(r['validation']=='documented' for r in rows)))
# GENERIC_COMBAT_ENGINE_V1

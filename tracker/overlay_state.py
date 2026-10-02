# SPDX-License-Identifier: GPL-3.0-only
"""Etat OBS : inconnus explicites, derniers etats signales, noms du catalogue."""
import json
import math
import time
from datetime import datetime
from .paths import DATA
from .profiles import selected_profile
from .boss_catalog import BOSS_IDS, normalize_id, display_name, active_bosses
from .i18n import get_language, tr, translate_status


# OVERLAY_I18N_V1
OVERLAY_LABELS = ('CHALLENGE', 'TEMPS DE JEU', 'MORTS', 'BOSS VAINCUS', 'VICTOIRE', 'APERÇU', 'Aperçu de la victoire', 'PRÉVISUALISATION — AUCUNE VICTOIRE ENREGISTRÉE', 'Prévisualisation', 'Boss vaincu', 'Connexion au tracker interrompue', 'Chrono direct non demarre', 'Choisis le challenge puis demarre le chrono', 'Connexion interrompue / chrono non actualise', 'En attente', 'COMBAT EXPÉRIMENTAL', 'TENTATIVES OBSERVÉES', 'Hors combat', 'Combat en cours', 'Combat déjà commencé - début inconnu', 'Lecture du combat indisponible', 'Mort confirmée - attente du retour', 'Attente du retour hors combat', 'Suivi arrêté', 'Dernier résultat', 'Mort', 'Victoire', 'Interrompu - résultat inconnu', 'Résultat incertain', 'Victoire et mort observées', 'Prototype limité à', 'MORTS OBSERVÉES', 'COMBAT EN COURS', 'Aperçu de combat', 'Données fictives - aperçu', 'Documenté - non testé sur ton PC', 'Disponible - expérimental', 'Le suivi actif dépend des associations configurées.', 'Suivi expérimental', 'Plusieurs signaux de combat actifs - attribution suspendue', 'Configuration de combat indisponible')


def progression(raw, ids=None):
    ids = tuple(b['id'] for b in active_bosses()) if ids is None else tuple(ids)
    states = {key: raw.get(key) if isinstance(raw, dict) and type(raw.get(key)) is bool else None for key in ids}
    known = sum(type(value) is bool for value in states.values())
    return dict(states=states, known=known, won=sum(value is True for value in states.values()), total=len(states), unknown=len(states)-known)


def format_timer(seconds):
    """Formate les secondes en HH:MM:SS"""
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return 'N/A'
    n = int(seconds)
    return f'{n//3600:02d}:{n%3600//60:02d}:{n%60:02d}'


def named_history(raw, language):
    if not isinstance(raw, list):
        return []
    result = []
    seen = set()
    for event in raw:
        if not isinstance(event, dict) or event.get('type') != 'boss_victory' or event.get('timing_mode') != 'confirmed_flag_observation':
            continue
        raw_key = event.get('boss_id', event.get('boss'))
        key = normalize_id(raw_key) if isinstance(raw_key, str) else None
        identifier = event.get('id')
        seconds = event.get('run_seconds')
        observed = event.get('observed_at')
        if key not in BOSS_IDS or not isinstance(identifier, str) or not identifier or identifier in seen:
            continue
        if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or not math.isfinite(seconds) or seconds < 0:
            continue
        if not isinstance(observed, str):
            continue
        try:
            date = datetime.fromisoformat(observed.replace('Z', '+00:00'))
            if date.tzinfo is None:
                continue
            timestamp = date.timestamp()
            if not math.isfinite(timestamp):
                continue
        except (ValueError, OverflowError, OSError):
            continue
        item = dict(event)
        item.update(boss_id=key, name=display_name(key, language))
        result.append(item)
        seen.add(identifier)
    return result


def state():
    language = get_language()
    active_ids = tuple(b['id'] for b in active_bosses())
    result = dict(challenge=None, character=None, timer=None, deaths=None, defeated=None, boss_history=[], profile_id=None, stale=True, status=tr('Chrono direct non demarre', language), language=language, boss_states=None, boss_states_stale=True, boss_catalog_count=len(active_ids), boss_known_count=0, boss_unknown_count=len(active_ids), defeated_known_count=None, combat=None)
    result['ui'] = {key: tr(key, language) for key in OVERLAY_LABELS}
    try:
        report = json.loads((DATA/'live_clock.json').read_text(encoding='utf-8'))
        runtime = json.loads((DATA/'runtime.json').read_text(encoding='utf-8'))
        if not isinstance(report, dict) or not isinstance(runtime, dict):
            return result
        source, slot = report.get('source'), report.get('slot')
        if not isinstance(source, str) or type(slot) is not int or not 0 <= slot <= 9:
            return result
        profile = selected_profile(source, slot)
        if not isinstance(profile, dict) or not profile.get('id') or profile['id'] != report.get('profile_id') or runtime.get('source') != source or runtime.get('slot') != slot:
            result['status'] = tr('Choisis le challenge puis demarre le chrono', language)
            return result
        updated = report.get('updated_at')
        valid_date = isinstance(updated, (int, float)) and not isinstance(updated, bool) and math.isfinite(updated)
        age = time.time()-updated if valid_date else float('inf')
        stale = age > 3 or age < -5 or report.get('running') is not True or runtime.get('running') is not True
        status = report.get('status')
        if not isinstance(status, str):
            status = tr('En attente', language)
        if report.get('running') is True and stale:
            status = tr('Connexion interrompue / chrono non actualise', language)
        raw = report.get('boss_states')
        summary = progression(raw, active_ids)
        cached = stale or summary['known'] == 0
        if cached:
            saved = progression(profile.get('boss_states'), active_ids)
            if saved['known']:
                summary = saved
        deaths = report.get('deaths')
        if type(deaths) is not int or deaths < 0:
            deaths = None
        if stale and deaths is None:
            saved_deaths = profile.get('tracked_deaths')
            if type(saved_deaths) is int and saved_deaths >= 0:
                deaths = saved_deaths
        if summary['known']:
            defeated = str(summary['won']) + ' / ' + str(summary['total'])
            notes = []
            if summary['unknown']:
                notes.append(str(summary['unknown']) + (' unknown states' if language == 'en' else ' etats inconnus'))
            if cached:
                notes.append('last recorded reading' if language == 'en' else 'derniere lecture enregistree')
            if notes:
                status += ' | ' + ' ; '.join(notes)
        else:
            defeated = None
            status += ' | ' + ('boss states unavailable' if language == 'en' else 'etats des boss indisponibles')
        status = translate_status(status, language)
        if isinstance(report.get('combat_error'), str) and report['combat_error']:
            status += ' | ' + tr(report['combat_error'], language)
        result.update(challenge=profile.get('name'), character=report.get('character'), timer=report.get('timer'), deaths=deaths, defeated=defeated, boss_history=named_history(profile.get('boss_history'), language), profile_id=profile['id'], stale=stale, status=status, boss_states=summary['states'], boss_states_stale=cached, boss_known_count=summary['known'], boss_unknown_count=summary['unknown'], defeated_known_count=summary['won'] if summary['known'] else None, combat=decorate_combat(report.get('combat'), language))
        
        # Dernière mort
        last_death = None
        boss_history = profile.get('boss_history', [])
        if isinstance(boss_history, list):
            deaths = [e for e in boss_history if isinstance(e, dict) and e.get('type') == 'boss_attempt_end' and e.get('outcome') in ('death', 'victory_and_death')]
            if deaths:
                last = max(deaths, key=lambda d: d.get('observed_at', ''))
                boss_id = last.get('boss_id', '')
                last_death = {
                    'boss_name': display_name(boss_id, language) if boss_id else tr('N/A', language),
                    'timer': format_timer(last.get('run_seconds', 0))
                }
        result.update(last_death=last_death)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        pass
    return result


# ACTIVE_BOSS_SCOPE_V1


def decorate_combat(payload,language,stale=False):
    from .combat_registry import supported_spec
    if not isinstance(payload,dict) or payload.get('mode') not in ('godefroy_active_flag_v1','confirmed_active_flag_v1'):return None
    boss_id=payload.get('boss_id')
    if not isinstance(boss_id,str):return None
    spec=supported_spec(boss_id)
    if spec is None:return None
    count=payload.get('observed_attempts')
    if type(count) is not int or count<0:return None
    phases={'ready':'Hors combat','active':'Combat en cours','active_untracked':'Combat déjà commencé - début inconnu','unknown':'Lecture du combat indisponible','suspended':'Lecture du combat indisponible','wait_reset':'Attente du retour hors combat','defeated':'Boss vaincu','stopped':'Suivi arrêté'}
    phase=payload.get('phase')
    if phase not in phases:return None
    outcomes={'death':'Mort','victory':'Victoire','interrupted':'Interrompu - résultat inconnu','uncertain':'Résultat incertain','victory_and_death':'Victoire et mort observées'}
    status=phases[phase]
    if phase=='wait_reset' and payload.get('last_result')=='death':status='Mort confirmée - attente du retour'
    if stale and phase!='stopped':phase='suspended';status=phases[phase]
    deaths=payload.get('observed_boss_deaths')
    validation='Validé sur ton PC' if spec['validation']=='user_tested' else 'Documenté - non testé sur ton PC'
    result=dict(payload)
    result.update(mode='confirmed_active_flag_v1',phase=phase,active=payload.get('active') is True and not stale,boss_name=display_name(boss_id,language),status=tr(status,language),observed_boss_deaths=deaths if type(deaths) is int and deaths>=0 else None,validation_label=tr(validation,language),result_label=tr(outcomes[payload['last_result']],language) if payload.get('last_result') in outcomes else None)
    return result


# GODEFROY_COMBAT_PROTOTYPE_V1


# COMBAT_CONTEXTUAL_UI_V1


# GENERIC_COMBAT_ENGINE_V1
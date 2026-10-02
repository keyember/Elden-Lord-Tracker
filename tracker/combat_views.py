# SPDX-License-Identifier: GPL-3.0-only
"""Vues en lecture seule : aucune creation, correction ou fusion de profils."""
import json
import math
from .paths import DATA
from .profiles import selected_profile
from .boss_catalog import BY_ID, display_name
from .i18n import get_language, tr
from .overlay_state import state
from .combat_registry import catalogue_view, ui

MODES=frozenset({'godefroy_active_flag_v1','confirmed_active_flag_v1'})
OUTCOMES={'death':'Mort','victory':'Victoire','victory_and_death':'Victoire et mort observées',
          'interrupted':'Interrompu - résultat inconnu','uncertain':'Résultat incertain'}


def valid_seconds(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0


def render_history(history,language):
    starts={};ends={}
    if not isinstance(history,list):return []
    for event in history:
        if not isinstance(event,dict) or event.get('tracking_mode') not in MODES or event.get('boss_id') not in BY_ID:continue
        attempt=event.get('attempt_id')
        if not isinstance(attempt,str) or not attempt:continue
        key=(event['boss_id'],attempt)
        if event.get('type')=='boss_attempt_start' and valid_seconds(event.get('run_seconds')):
            starts.setdefault(key,event)
        elif event.get('type')=='boss_attempt_end' and event.get('outcome') in OUTCOMES:
            ends.setdefault(key,event)
    numbers={};rows=[]
    for key,start in sorted(starts.items(),key=lambda item:item[1]['run_seconds']):
        boss_id,attempt=key;numbers[boss_id]=numbers.get(boss_id,0)+1;end=ends.get(key)
        end_seconds=end.get('run_seconds') if end and valid_seconds(end.get('run_seconds')) else None
        if end_seconds is not None and end_seconds<start['run_seconds']:end_seconds=None
        outcome=end.get('outcome') if end else None
        rows.append(dict(attempt_id=attempt,boss_id=boss_id,name=display_name(boss_id,language),
                         number=numbers[boss_id],start_seconds=start['run_seconds'],end_seconds=end_seconds,
                         duration_seconds=end_seconds-start['run_seconds'] if end_seconds is not None else None,
                         outcome=outcome,result_label=tr(OUTCOMES[outcome] if outcome else 'Sans fin enregistrée',language),
                         reason=end.get('reason') if end else None))
    return list(reversed(rows))


def history_view():
    language=get_language();frame=state()
    result=dict(language=language,ui=ui(language),challenge=frame.get('challenge'),rows=[],
                summary=dict(attempts=0,deaths=0,victories=0,unresolved=0),status=frame.get('status'))
    if not frame.get('profile_id'):return result
    try:
        report=json.loads((DATA/'live_clock.json').read_text(encoding='utf-8'))
        if not isinstance(report,dict):return result
        source,slot=report.get('source'),report.get('slot')
        if not isinstance(source,str) or type(slot) is not int:return result
        profile=selected_profile(source,slot)
        if not profile or profile.get('id')!=frame['profile_id'] or report.get('profile_id')!=profile['id']:return result
        rows=render_history(profile.get('combat_history',[]),language)
        result.update(rows=rows,summary=dict(attempts=len(rows),deaths=sum(r['outcome'] in ('death','victory_and_death') for r in rows),
                      victories=sum(r['outcome'] in ('victory','victory_and_death') for r in rows),
                      unresolved=sum(r['outcome'] in (None,'interrupted','uncertain') for r in rows)))
    except (OSError,ValueError,TypeError,KeyError):pass
    return result

# SPDX-License-Identifier: GPL-3.0-only
"""Dernieres victoires observees du challenge, sans reconstruire les anciennes."""
import math
from datetime import datetime,timezone
from .catalogue_view import decorate_state as base_state
from .boss_catalog import normalize_id,display_name
from .boss_timeline import format_seconds
from .profiles import selected_profile
from .i18n import tr
LABELS=("DERNIÈRES VICTOIRES","Aucune victoire enregistrée","VICTOIRE","APERÇU","Test de l'effet de cendres")

def recent_events(history,language):
    if not isinstance(history,list):return []
    result=[];seen=set()
    for index,event in enumerate(history):
        if not isinstance(event,dict) or event.get("type")!="boss_victory" or event.get("timing_mode")!="confirmed_flag_observation":continue
        raw=event.get("boss_id",event.get("boss"));key=normalize_id(raw) if isinstance(raw,str) else None
        identifier=event.get("id");seconds=event.get("run_seconds");date=event.get("observed_at")
        if key is None or not isinstance(identifier,str) or not identifier or len(identifier)>128 or identifier in seen:continue
        if not isinstance(seconds,(int,float)) or isinstance(seconds,bool) or not math.isfinite(seconds) or seconds<0:continue
        if not isinstance(date,str):continue
        try:
            parsed=datetime.fromisoformat(date.replace("Z","+00:00"))
            if parsed.tzinfo is None:continue
            stamp=parsed.timestamp()
        except (ValueError,OverflowError,OSError):continue
        seen.add(identifier)
        result.append(dict(id=identifier,boss_id=key,name=display_name(key,language),time=format_seconds(seconds),run_seconds=seconds,observed_at=date,_sort=(stamp,index)))
    result.sort(key=lambda e:e["_sort"],reverse=True)
    result=result[:3]
    for event in result:event.pop("_sort",None)
    return result

def decorate_state(state,report=None):
    report=report or {};state=base_state(state,report);language=state.get("language","fr")
    state["ui"].update({key:tr(key,language) for key in LABELS})
    state.update(recent_victories=[],overlay_profile_id=None)
    if not state.get("challenge") or not report.get("profile_id"):return state
    source=report.get("source");slot=report.get("slot")
    if source is None or type(slot) is not int:return state
    profile=selected_profile(source,slot)
    if not profile or profile.get("id")!=report["profile_id"]:return state
    state["overlay_profile_id"]=profile["id"]
    state["recent_victories"]=recent_events(profile.get("boss_history",[]),language)
    return state

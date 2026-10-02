# SPDX-License-Identifier: GPL-3.0-only
from .boss_catalog import active_bosses,display_name
from .boss_timeline import format_seconds
from .i18n import get_language,tr,translate_status

def decorate_state(state,report=None):
    report=report or {};lang=get_language()
    states=report.get("boss_states") if not state.get("stale",True) else None
    times=report.get("boss_times",{});rows=[]
    counts={content:dict(total=0,known=0,defeated=0,unknown=0) for content in ("base_game","dlc")}
    for b in active_bosses():
        key=b["id"];done=states.get(key) if isinstance(states,dict) else None
        if type(done) is not bool:done=None
        seconds=times.get(key) if done is True and isinstance(times,dict) else None
        valid_time=isinstance(seconds,(int,float)) and not isinstance(seconds,bool) and seconds>=0
        label="N/A" if done is None else (tr("Non vaincu",lang) if not done else tr("Vaincu",lang))
        text=label+(" \u00b7 "+(format_seconds(seconds) if valid_time else tr("temps inconnu",lang)) if done is True else "")
        rows.append(dict(id=key,name=display_name(key,lang),place=b["places"][lang],region=b["regions"][lang],content=b["content"],state=done,status=text,time=format_seconds(seconds) if valid_time else None))
        c=counts[b["content"]];c["total"]+=1;c["known"]+=done is not None;c["unknown"]+=done is None;c["defeated"]+=done is True
    total=sum(c["total"] for c in counts.values());known=sum(c["known"] for c in counts.values());defeated=sum(c["defeated"] for c in counts.values())
    keys=("Catalogue des boss","Rechercher un boss ou un lieu","Tous les contenus","Jeu de base","Tous les etats","Vaincu","Non vaincu","Boss","Lieu","Region","Etat","Temps du challenge","Suivis","Vaincus connus","Etats inconnus","Actualisation impossible","CHALLENGE","BOSS SUIVI","TENTATIVES","TEMPS DE JEU","MORTS","BOSS VAINCUS (SUIVIS)","PROGRESSION DES BOSS","Progression indisponible","Connexion au tracker interrompue")
    state.update(language=lang,ui={k:tr(k,lang) for k in keys},bosses=rows,boss_counts=counts,boss_catalog_count=total,
      defeated=(str(defeated)+"/"+str(total)) if known else None,boss_known_count=known,
      status=translate_status(state.get("status",""),lang))
    return state

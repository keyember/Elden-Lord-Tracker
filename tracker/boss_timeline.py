# SPDX-License-Identifier: GPL-3.0-only
import math,uuid
from datetime import datetime,timezone
from .boss_catalog import BOSS_IDS,BY_ID,normalize_id,active_bosses,display_name
from .i18n import get_language,tr

def format_seconds(seconds):
    n=int(seconds);return f"{n//3600:02d}:{n%3600//60:02d}:{n%60:02d}"
class BossTimeline:
    def __init__(self,history):
        if not isinstance(history,list):raise ValueError(tr("Historique de boss invalide"))
        self.existing=list(history);self.events=[];self.last=None;self.times={};self.blocked=set()
        for event in history:
            if not isinstance(event,dict) or event.get("type")!="boss_victory" or event.get("timing_mode")!="confirmed_flag_observation":continue
            raw=event.get("boss_id",event.get("boss"));key=normalize_id(raw) if isinstance(raw,str) else None;seconds=event.get("run_seconds")
            if key is not None and isinstance(seconds,(int,float)) and not isinstance(seconds,bool) and math.isfinite(seconds) and seconds>=0:self.times.setdefault(key,float(seconds))
    def observe(self,snap,seconds):
        states=snap.get("boss_states")
        if states is None:
            transition=snap.get("screen_state")==1 or bool(snap.get("blackscreen"))
            confirming=snap.get("can_count") and snap.get("name_match") is True and not snap.get("boss_error")
            if not transition and not confirming:self.last=None
            if snap.get("boss_error"):self.last=None
            return
        if not isinstance(states,dict):self.last=None;return
        if not isinstance(seconds,(int,float)) or isinstance(seconds,bool) or not math.isfinite(seconds) or seconds<0:raise ValueError(tr("Temps de victoire invalide"))
        valid={key:states.get(key) for key in BOSS_IDS if type(states.get(key)) is bool}
        for key,done in valid.items():
            if not done and key in self.times:self.blocked.add(key)
            if self.last is not None and self.last.get(key) is False and done and key not in self.times and key not in self.blocked:
                value=round(float(seconds),6)
                self.events.append(dict(id=uuid.uuid4().hex,type="boss_victory",boss_id=key,boss=BY_ID[key]["names"]["fr"],run_seconds=value,observed_at=datetime.now(timezone.utc).isoformat(),timing_mode="confirmed_flag_observation",attempts=None))
                self.times[key]=value
        self.last=valid
    def merge(self,current):
        history=current.get("boss_history",[])
        if not isinstance(history,list):raise ValueError(tr("Historique enregistre invalide"))
        ids={e.get("id") for e in history if isinstance(e,dict) and isinstance(e.get("id"),str)}
        current["boss_history"]=history+[dict(e) for e in self.events if e["id"] not in ids]
    def render(self,states):
        lang=get_language();lines=[]
        for boss in active_bosses():
            key=boss["id"];done=states.get(key) if isinstance(states,dict) else None
            if type(done) is not bool:label="N/A"
            elif not done:label=tr("Non vaincu",lang)
            else:
                seconds=self.times.get(key) if key not in self.blocked else None
                label=tr("Vaincu",lang)+" \u00b7 "+(format_seconds(seconds) if seconds is not None else tr("temps inconnu",lang))
            lines.append(display_name(key,lang)+" - "+label)
        return "\n".join(lines)

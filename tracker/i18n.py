# SPDX-License-Identifier: GPL-3.0-only
"""Localisation FR/EN ; donnees de personnage et de challenge non traduites."""
import json,time,threading
from pathlib import Path
from .paths import DATA
from .storage import write_json
ROOT=Path(__file__).resolve().parent
_LOCK=threading.RLock();_stamp=0;_settings={"language":"fr","include_dlc":True}
_EN=json.loads((ROOT/"locales"/"en.json").read_text(encoding="utf-8"))

def settings():
    global _stamp,_settings
    with _LOCK:
        now=time.monotonic()
        if now-_stamp>=0.5:
            try:
                value=json.loads((DATA/"settings.json").read_text(encoding="utf-8"))
                if not isinstance(value,dict):raise ValueError("Invalid settings")
                _settings={"language":value.get("language") if value.get("language") in ("fr","en") else "fr","include_dlc":value.get("include_dlc",True) is True}
            except (OSError,ValueError):pass
            _stamp=now
        return dict(_settings)

def get_language():return settings()["language"]
def set_setting(key,value):
    global _stamp,_settings
    if key=="language" and value not in ("fr","en"):raise ValueError("Invalid language")
    if key=="include_dlc" and type(value) is not bool:raise ValueError("Invalid DLC setting")
    if key not in ("language","include_dlc"):raise ValueError("Invalid setting")
    with _LOCK:
        current=settings();current[key]=value
        path=DATA/"settings.json"
        try:
            previous=json.loads(path.read_text(encoding="utf-8"))
            if isinstance(previous,dict):previous.update(current);current=previous
        except (OSError,ValueError):pass
        write_json(path,current);_settings={k:current[k] for k in ("language","include_dlc")};_stamp=time.monotonic()

def tr(text,language=None):
    language=language or get_language()
    return _EN.get(text,text) if language=="en" else text

def translate_status(text,language=None):
    language=language or get_language()
    if language!="en":return text
    if text in _EN:return _EN[text]
    # Les fragments sont appliques aux seuls messages de statut, pas aux noms.
    for key in sorted(_EN,key=len,reverse=True):
        if len(key)>=12 and key in text:text=text.replace(key,_EN[key])
    return text

# SPDX-License-Identifier: GPL-3.0-only
"""207 rencontres de reference EROverlay ; libelles FR/EN sous licence MIT.
Seuls trois flags ont ete valides individuellement sur le PC utilisateur.
"""
import json
from collections import Counter
from pathlib import Path
from .i18n import get_language,settings
BOSSES=tuple(json.loads((Path(__file__).resolve().parent/"catalogue_data"/"boss_catalog.json").read_text(encoding="utf-8")))
BOSS_IDS=tuple(b["id"] for b in BOSSES)
BY_ID={b["id"]:b for b in BOSSES}
FLAG_IDS={b["id"]:b["flag_id"] for b in BOSSES}
LEGACY_NAMES={"Margit":"margit","Godrick":"godrick","Radahn":"radahn"}
if len(BOSSES)!=207 or len(BY_ID)!=207 or len(set(FLAG_IDS.values()))!=207:raise ValueError("Invalid boss catalogue")
COUNTS={lang:Counter(b["names"][lang] for b in BOSSES) for lang in ("fr","en")}

def normalize_id(value):return value if value in BY_ID else LEGACY_NAMES.get(value)
def active_bosses():
    include=settings()["include_dlc"]
    return tuple(b for b in BOSSES if include or b["content"]=="base_game")
def display_name(boss_id,language=None):
    lang=language or get_language();b=BY_ID[boss_id];name=b["names"].get(lang,b["names"]["en"])
    if COUNTS.get(lang,COUNTS["en"])[name]>1:name+=" ("+b["places"].get(lang,b["places"]["en"])+")"
    return name

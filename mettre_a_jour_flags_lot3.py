# SPDX-License-Identifier: GPL-3.0-only
"""Lot 3 cumulatif hors ligne. Aucun lecteur, moteur ou overlay remplace."""
import argparse,ast,copy,datetime,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,uuid
from pathlib import Path
REVISION='e6de1b79370755152f4f89c4a106a2d67c9ae674'
REPOSITORY='Grimrukh/soulstruct-vanilla'
UPDATE_ID='sourced_flags_lot3_offline_v1'
REGISTRY='tracker/combat_registry.py'
CONFIG='tracker/catalogue_data/combat_catalog.json'
CATALOGUE='tracker/catalogue_data/boss_catalog.json'
TARGETS=(REGISTRY,CONFIG)
FIELDS=('repository','revision','path','event','parameter')
MAX_ACTIVE=32
BASE_BANK={'1033420800': {'active_flag': 1033422806, 'path': 'eldenring/events/m60_33_42_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1036500800': {'active_flag': 1036502806, 'path': 'eldenring/events/m60_36_50_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1033450800': {'active_flag': 1033452806, 'path': 'eldenring/events/m60_33_45_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1039500800': {'active_flag': 1039502806, 'path': 'eldenring/events/m60_39_50_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1042370800': {'active_flag': 1042372806, 'path': 'eldenring/events/m60_42_37_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1038410800': {'active_flag': 1038412806, 'path': 'eldenring/events/m60_38_41_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1053560800': {'active_flag': 1053562806, 'path': 'eldenring/events/m60_53_56_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1044350800': {'active_flag': 1044352806, 'path': 'eldenring/events/m60_44_35_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1042330800': {'active_flag': 1042332806, 'path': 'eldenring/events/m60_42_33_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}, '1049390850': {'active_flag': 1049392856, 'path': 'eldenring/events/m60_49_39_00.evs.py', 'revision': 'e6de1b79370755152f4f89c4a106a2d67c9ae674', 'repository': 'Grimrukh/soulstruct-vanilla', 'event': 'CommonFunc_90005882', 'parameter': 'flag_3'}}
OLD_ROWS=[(30110800, 30112805, 'm30_11_00_00', 'Event_30112849', 'Event_30112810', 'Event_30112800'), (30040800, 30042805, 'm30_04_00_00', 'Event_30042849', 'Event_30042810', 'Event_30042800'), (31020800, 31022805, 'm31_02_00_00', 'Event_31022849', 'Event_31022810', 'Event_31022800'), (31040800, 31042805, 'm31_04_00_00', 'Event_31042849', 'Event_31042810', 'Event_31042800'), (30150800, 30152805, 'm30_15_00_00', 'Event_30152849', 'Event_30152810', 'Event_30152800'), (30130800, 30132805, 'm30_13_00_00', 'Event_30132849', 'Event_30132810', 'Event_30132800'), (30010800, 30012805, 'm30_01_00_00', 'Event_30012849', 'Event_30012810', 'Event_30012800'), (30020800, 30022805, 'm30_02_00_00', 'Event_30022849', 'Event_30022810', 'Event_30022800')]
NEW_ROWS=[(32020800, 32022805, 'm32_02_00_00', 'Event_32022849', 'Event_32022810', 'Event_32022800'), (32040800, 32042805, 'm32_04_00_00', 'Event_32042849', 'Event_32042810', 'Event_32042800'), (12040800, 12042805, 'm12_04_00_00', 'Event_12042849', 'Event_12042810', 'Event_12042800'), (12080800, 12082805, 'm12_08_00_00', 'Event_12082849', 'Event_12082810', 'Event_12082800'), (32080800, 32082805, 'm32_08_00_00', 'Event_32082849', 'Event_32082810', 'Event_32082800'), (43000800, 43002805, 'm43_00_00_00', 'Event_43002849', 'Event_43002810', 'Event_43002800'), (43010800, 43012805, 'm43_01_00_00', 'Event_43012849', 'Event_43012810', 'Event_43012800')]
REFERENCE_REGISTRY='# SPDX-License-Identifier: GPL-3.0-only\n"""Generic registry: explicit associations, no numeric suffix inference."""\nimport json\nfrom pathlib import Path\nfrom .boss_catalog import BOSSES, BY_ID, active_bosses, display_name\nfrom .i18n import get_language,settings,tr\nCONFIG_PATH=Path(__file__).resolve().parent/\'catalogue_data/combat_catalog.json\'\nSOURCE_BANK={\'1033420800\': {\'active_flag\': 1033422806, \'path\': \'eldenring/events/m60_33_42_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1036500800\': {\'active_flag\': 1036502806, \'path\': \'eldenring/events/m60_36_50_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1033450800\': {\'active_flag\': 1033452806, \'path\': \'eldenring/events/m60_33_45_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1039500800\': {\'active_flag\': 1039502806, \'path\': \'eldenring/events/m60_39_50_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1042370800\': {\'active_flag\': 1042372806, \'path\': \'eldenring/events/m60_42_37_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1038410800\': {\'active_flag\': 1038412806, \'path\': \'eldenring/events/m60_38_41_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1053560800\': {\'active_flag\': 1053562806, \'path\': \'eldenring/events/m60_53_56_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1044350800\': {\'active_flag\': 1044352806, \'path\': \'eldenring/events/m60_44_35_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1042330800\': {\'active_flag\': 1042332806, \'path\': \'eldenring/events/m60_42_33_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}, \'1049390850\': {\'active_flag\': 1049392856, \'path\': \'eldenring/events/m60_49_39_00.evs.py\', \'revision\': \'e6de1b79370755152f4f89c4a106a2d67c9ae674\', \'repository\': \'Grimrukh/soulstruct-vanilla\', \'event\': \'CommonFunc_90005882\', \'parameter\': \'flag_3\'}}\nUI_KEYS=(\'Suivi des combats\', \'Couverture du catalogue\', \'Historique du challenge\', \'Catalogue\', \'Historique\', \'Rencontres du catalogue\', \'Rencontres actives\', \'Suivis actifs disponibles\', \'Validé sur ton PC\', \'Non configuré\', \'À vérifier\', \'Prise en charge\', \'Disponible\', \'Non pris en charge par ce prototype\', \'Boss\', \'Contenu\', \'Flag de combat\', \'Validation\', \'Rechercher un boss\', \'Actualiser\', \'Jeu de base\', \'Aucun challenge sélectionné\', \'Aucune tentative enregistrée\', \'Tentative observée\', \'Résultat\', \'Début observé\', \'Fin observée\', \'Durée observée\', \'Sans fin enregistrée\', \'Temps inconnu\', \'Mort\', \'Victoire\', \'Victoire et mort observées\', \'Interrompu - résultat inconnu\', \'Résultat incertain\', \'Historique enregistré uniquement, sans import des diagnostics.\', \'Configurer une rencontre ne suffit pas à valider son suivi.\', \'Configuration de combat indisponible\', \'Connexion au tracker interrompue\', \'Le suivi actif reste limité à Godefroy.\', \'Documenté - non testé sur ton PC\', \'Disponible - expérimental\', \'Le suivi actif dépend des associations configurées.\', \'Suivi expérimental\', \'Plusieurs signaux de combat actifs - attribution suspendue\')\nENABLED_LEVELS=frozenset({\'documented\',\'user_tested\'})\n\n\ndef ui(language):return {key:tr(key,language) for key in UI_KEYS}\n\n\ndef read_configuration():\n    try:\n        doc=json.loads(CONFIG_PATH.read_text(encoding=\'utf-8\'))\n        if not isinstance(doc,dict) or doc.get(\'schema_version\')!=1 or not isinstance(doc.get(\'encounters\'),dict):raise ValueError(\'Configuration invalide\')\n        entries=doc[\'encounters\'];seen={};enabled=0\n        for key,item in entries.items():\n            if key not in BY_ID or not isinstance(item,dict):raise ValueError(\'Rencontre inconnue\')\n            level=item.get(\'validation\');active=item.get(\'active_flag\')\n            if level not in (\'not_configured\',\'candidate\',\'documented\',\'user_tested\'):raise ValueError(\'Validation invalide\')\n            if active is not None and (type(active) is not int or not 0<=active<=4294967295 or active==BY_ID[key][\'flag_id\']):raise ValueError(\'Flag invalide\')\n            if level==\'documented\':\n                reference=SOURCE_BANK.get(str(BY_ID[key][\'flag_id\']))\n                source=item.get(\'source\',{})\n                if not reference or active!=reference[\'active_flag\'] or not isinstance(source,dict) or any(source.get(field)!=reference[field] for field in (\'repository\',\'revision\',\'path\',\'event\',\'parameter\')):raise ValueError(\'Association documentee sans provenance correspondante\')\n            if level in ENABLED_LEVELS and item.get(\'enabled\',True) is not False:\n                if active is None:raise ValueError(\'Flag de combat manquant\')\n                if active in seen and seen[active]!=key:raise ValueError(\'Flag actif partage : attribution ambigue\')\n                seen[active]=key;enabled+=1\n        if enabled>32:raise ValueError(\'Plus de 32 suivis actifs : extension a valider avant activation\')\n        return entries,None\n    except (OSError,ValueError,TypeError):\n        import sys\n        return {},str(sys.exc_info()[1])\n\n\ndef supported_specs(active_only=True):\n    entries,error=read_configuration()\n    if error:return ()\n    allowed={b[\'id\'] for b in active_bosses()} if active_only else set(BY_ID)\n    return tuple(dict(boss_id=key,active_flag=item[\'active_flag\'],victory_flag=BY_ID[key][\'flag_id\'],validation=item[\'validation\'])\n                 for key,item in entries.items() if key in allowed and item.get(\'validation\') in ENABLED_LEVELS and item.get(\'enabled\',True) is not False)\n\n\ndef supported_spec(boss_id):return next((spec for spec in supported_specs(False) if spec[\'boss_id\']==boss_id),None)\n\n\ndef catalogue_view():\n    language=get_language();entries,error=read_configuration();active_ids={b[\'id\'] for b in active_bosses()};supported={s[\'boss_id\'] for s in supported_specs(False)};rows=[]\n    names={\'not_configured\':\'Non configuré\',\'candidate\':\'À vérifier\',\'documented\':\'Documenté - non testé sur ton PC\',\'user_tested\':\'Validé sur ton PC\'}\n    for boss in BOSSES:\n        key=boss[\'id\'];item=entries.get(key,{});level=item.get(\'validation\',\'not_configured\');available=key in supported\n        rows.append(dict(boss_id=key,name=display_name(key,language),content=boss.get(\'content\'),content_label=tr(\'Jeu de base\',language) if boss.get(\'content\')==\'base_game\' else \'DLC\',\n          active=key in active_ids,active_flag=item.get(\'active_flag\'),validation=level,validation_label=tr(names[level],language),live_supported=available,\n          support_label=tr((\'Disponible\' if level==\'user_tested\' else \'Disponible - expérimental\') if available else \'Non pris en charge par ce prototype\',language),source=item.get(\'source\')))\n    return dict(language=language,ui=ui(language),rows=rows,configuration_error=error,include_dlc=settings()[\'include_dlc\'],\n      summary=dict(catalogue_total=len(rows),active_total=len(active_ids),live_supported_active=sum(r[\'active\'] and r[\'live_supported\'] for r in rows),\n                   user_tested=sum(r[\'validation\']==\'user_tested\' for r in rows),documented=sum(r[\'validation\']==\'documented\' for r in rows)))\n# GENERIC_COMBAT_ENGINE_V1\n'
REFERENCE_TRACKING='# SPDX-License-Identifier: GPL-3.0-only\n"""Suivi experimental par boss ; historiques anciens conserves."""\nimport time\nfrom .i18n import tr\nimport math\nimport uuid\nfrom datetime import datetime, timezone\nBOSS_ID = \'flag_1039500800\'\nMODE = \'confirmed_active_flag_v1\'\nSUPPORTED_MODES = frozenset({\'confirmed_active_flag_v1\', \'godefroy_active_flag_v1\'})\n\ndef new_event(kind, attempt, seconds=None, boss_id=BOSS_ID, **fields):\n    return dict(id=uuid.uuid4().hex, type=kind, attempt_id=attempt, boss_id=boss_id, tracking_mode=MODE, run_seconds=seconds, observed_at=datetime.now(timezone.utc).isoformat(), **fields)\n\ndef count_observed_boss_deaths(history, boss_id=BOSS_ID):\n    starts = {item.get(\'attempt_id\') for item in history if isinstance(item, dict) and item.get(\'type\') == \'boss_attempt_start\' and (item.get(\'boss_id\') == boss_id) and (item.get(\'tracking_mode\') in SUPPORTED_MODES) and isinstance(item.get(\'attempt_id\'), str) and item[\'attempt_id\']}\n    deaths = {item.get(\'attempt_id\') for item in history if isinstance(item, dict) and item.get(\'type\') == \'boss_attempt_end\' and (item.get(\'boss_id\') == boss_id) and (item.get(\'tracking_mode\') in SUPPORTED_MODES) and (item.get(\'outcome\') in (\'death\', \'victory_and_death\')) and (item.get(\'attempt_id\') in starts)}\n    return len(deaths)\n\nclass CombatSession:\n\n    def __init__(self, history=None, tracked_deaths=0, boss_id=BOSS_ID):\n        if not isinstance(boss_id, str) or not boss_id:\n            raise ValueError(\'Identifiant de boss invalide\')\n        self.boss_id = boss_id\n        history = [] if history is None else history\n        if not isinstance(history, list) or type(tracked_deaths) is not int or tracked_deaths < 0:\n            raise ValueError(\'Historique de combat ou compteur invalide\')\n        self.existing = list(history)\n        self.events = []\n        starts = {}\n        ends = set()\n        for item in history:\n            if not isinstance(item, dict) or item.get(\'boss_id\') != self.boss_id or item.get(\'tracking_mode\') not in SUPPORTED_MODES:\n                continue\n            attempt = item.get(\'attempt_id\')\n            if not isinstance(attempt, str) or not attempt:\n                continue\n            if item.get(\'type\') == \'boss_attempt_start\':\n                starts.setdefault(attempt, item)\n            elif item.get(\'type\') == \'boss_attempt_end\':\n                ends.add(attempt)\n        self.attempts = len(starts)\n        self.observed_boss_deaths = count_observed_boss_deaths(history, boss_id=self.boss_id)\n        for attempt in starts.keys() - ends:\n            self.events.append(new_event(\'boss_attempt_end\', attempt, outcome=\'interrupted\', reason=\'tracking_restart\', run_end_unknown=True, boss_id=self.boss_id))\n        self.open = None\n        self.armed = False\n        self.phase = \'unknown\'\n        self.active = False\n        self.last_result = None\n        self.last_deaths = tracked_deaths\n        self.seconds = 0.0\n\n    def finish(self, outcome, reason=None):\n        if self.open is not None:\n            self.events.append(new_event(\'boss_attempt_end\', self.open[\'attempt_id\'], round(self.seconds, 6), outcome=outcome, reason=reason, boss_id=self.boss_id))\n            if outcome in (\'death\', \'victory_and_death\'):\n                self.observed_boss_deaths += 1\n            self.open = None\n        self.last_result = outcome\n        self.armed = False\n        self.active = False\n        self.phase = \'wait_reset\'\n\n    def observe(self, snap, seconds, tracked_deaths):\n        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or (not math.isfinite(seconds)) or (seconds < 0):\n            raise ValueError(\'Temps de combat invalide\')\n        if type(tracked_deaths) is not int or tracked_deaths < 0:\n            raise ValueError(\'Compteur de combat invalide\')\n        self.seconds = float(seconds)\n        delta = tracked_deaths - self.last_deaths\n        self.last_deaths = tracked_deaths\n        signal = snap.get(\'combat_signal\') if snap.get(\'can_count\') is True else None\n        valid = isinstance(signal, dict) and signal.get(\'boss_id\') == self.boss_id and (type(signal.get(\'active\')) is bool) and (type(signal.get(\'victory\')) is bool)\n        now = time.monotonic()\n        if not valid:\n            last_false = getattr(self, \'_last_confirmed_false_at\', None)\n            loading = snap.get(\'screen_state\') == 1 or bool(snap.get(\'blackscreen\'))\n            matching = snap.get(\'screen_state\') == 0 and snap.get(\'name_match\') is True\n            normal_pause = snap.get(\'screen_state\') in (0, 1) and snap.get(\'guard_status\') in (tr(\'pause automatique\'), tr(\'pause - confirmation du nom\'))\n            can_preserve = self.armed and last_false is not None and (0 <= now - last_false <= 12) and (snap.get(\'name_match\') is not False) and (not snap.get(\'combat_error\')) and (loading or matching or normal_pause)\n            if not can_preserve:\n                self.armed = False\n            self.active = False\n            if self.open is not None and delta:\n                self.finish(\'uncertain\', \'death_delta_without_valid_combat_signal\')\n            self.phase = \'suspended\' if self.open is not None else \'unknown\'\n            return\n        active, victory = (signal[\'active\'], signal[\'victory\'])\n        if self.open is not None:\n            if delta < 0 or delta > 1:\n                self.finish(\'uncertain\', \'death_counter_discontinuity\')\n                return\n            if victory:\n                self.finish(\'victory_and_death\' if delta == 1 else \'victory\')\n                return\n            if delta == 1:\n                self.finish(\'death\' if active else \'uncertain\', None if active else \'death_delta_after_combat_reset\')\n                return\n            if not active:\n                self.finish(\'interrupted\', \'active_flag_reset_without_confirmed_result\')\n                return\n            self.active = True\n            self.phase = \'active\'\n            return\n        if victory:\n            self.phase = \'defeated\'\n            self.active = False\n            self.armed = False\n            return\n        if not active:\n            self.phase = \'ready\'\n            self.armed = True\n            self.active = False\n            self._last_confirmed_false_at = now\n            return\n        if self.phase == \'wait_reset\':\n            self.active = False\n            return\n        last_false = getattr(self, \'_last_confirmed_false_at\', None)\n        if self.armed and (last_false is None or now - last_false > 12):\n            self.armed = False\n        if not self.armed:\n            self.phase = \'active_untracked\'\n            self.active = True\n            return\n        if delta:\n            self.phase = \'unknown\'\n            self.armed = False\n            self.active = False\n            return\n        attempt = uuid.uuid4().hex\n        event = new_event(\'boss_attempt_start\', attempt, round(self.seconds, 6), boss_id=self.boss_id)\n        self.events.append(event)\n        self.open = event\n        self.attempts += 1\n        self.armed = False\n        self.phase = \'active\'\n        self.active = True\n\n    def stop(self, seconds):\n        self.seconds = float(seconds)\n        if self.open is not None:\n            self.finish(\'interrupted\', \'tracking_stopped\')\n        self.active = False\n        self.armed = False\n        self.phase = \'stopped\'\n\n    def merge(self, current):\n        history = current.get(\'combat_history\', [])\n        if not isinstance(history, list):\n            raise ValueError(\'Historique de combat enregistre invalide\')\n        ids = {item.get(\'id\') for item in history if isinstance(item, dict) and isinstance(item.get(\'id\'), str)}\n        current[\'combat_history\'] = history + [dict(event) for event in self.events if event[\'id\'] not in ids]\n\n    def payload(self):\n        return dict(boss_id=self.boss_id, mode=MODE, phase=self.phase, active=self.active, observed_attempts=self.attempts, last_result=self.last_result, attempt_start_seconds=self.open[\'run_seconds\'] if self.open else None, observed_boss_deaths=self.observed_boss_deaths)\n# GODEFROY_ARMING_FIX_V1\n# COMBAT_CONTEXTUAL_UI_V1\n# GENERIC_COMBAT_ENGINE_V1\n'
REFERENCE_COORDINATOR='# SPDX-License-Identifier: GPL-3.0-only\n"""Routes confirmed observations to one independent tracker per boss."""\nfrom .combat_tracking import CombatSession\nfrom .combat_registry import supported_specs\n\nclass CombatCoordinator:\n    def __init__(self,history=None,tracked_deaths=0):\n        self.history=[] if history is None else list(history)\n        self.instances={spec[\'boss_id\']:CombatSession(self.history,tracked_deaths,boss_id=spec[\'boss_id\']) for spec in supported_specs(False)}\n        self.selected=None;self.error=None\n\n    def observe(self,snap,seconds,tracked_deaths):\n        signals=snap.get(\'combat_signals\')\n        signals=signals if isinstance(signals,dict) else {}\n        enabled={spec[\'boss_id\'] for spec in supported_specs(False)}\n        for key in enabled:\n            if key not in self.instances:self.instances[key]=CombatSession(self.history,tracked_deaths,boss_id=key)\n        active=[key for key,signal in signals.items() if key in enabled and isinstance(signal,dict) and signal.get(\'boss_id\')==key and signal.get(\'active\') is True and signal.get(\'victory\') is False]\n        ambiguous=len(active)>1\n        self.error=\'Plusieurs signaux de combat actifs - attribution suspendue\' if ambiguous else None\n        errors=snap.get(\'combat_errors\')\n        errors=errors if isinstance(errors,dict) else {}\n        for key,tracker in self.instances.items():\n            if key not in enabled:\n                if tracker.open is not None:tracker.stop(seconds)\n                continue\n            local=dict(snap)\n            local[\'combat_signal\']=None if ambiguous else signals.get(key)\n            local[\'combat_error\']=self.error or errors.get(key)\n            if not signals and snap.get(\'boss_error\'):local[\'combat_error\']=snap[\'boss_error\']\n            tracker.observe(local,seconds,tracked_deaths)\n        if len(active)==1 and not ambiguous:\n            key=active[0]\n            for other,tracker in self.instances.items():\n                if other!=key and tracker.open is not None:tracker.finish(\'interrupted\',\'different_boss_detected\')\n            self.selected=key\n\n    def payload(self):\n        if self.error or self.selected not in self.instances:return None\n        return self.instances[self.selected].payload()\n\n    def merge(self,current):\n        for tracker in self.instances.values():tracker.merge(current)\n\n    def stop(self,seconds):\n        for tracker in self.instances.values():tracker.stop(seconds)\n        self.error=None\n'


def digest(data): return hashlib.sha256(data).hexdigest()
def git_blob(text):
    data=text.encode('utf-8');return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()

def source_payload(rows):
    result={}
    for victory,active,map_name,caller,gate,end in rows:
        ref=dict(active_flag=active,repository=REPOSITORY,revision=REVISION,path='eldenring/events/'+map_name+'.evs.py',event='CommonFunc_9005800',parameter='flag_1')
        evidence=dict(caller_event=caller,activation_event=gate,victory_event=end,
                      activation_condition='FlagEnabled(active_flag) AND CharacterInsideRegion(PLAYER, arena)',
                      verification='caller_and_local_ai_gate_reviewed',reset='not_verified_in_common_function',pc_tested=False)
        if victory==32080800:
            evidence.update(first_and_repeat_gate_same_flag=True,phase_event='Event_32082811',phase_flag=32082802,
                            phase_note='Local phase event sets a separate phase flag; actual in-game continuity remains untested.')
        if victory==43010800:
            evidence.update(phase_event='Event_43012811',phase_flag=43012802,
                            phase_note='Local phase event sets a separate phase flag; actual in-game continuity remains untested.')
        result[victory]=dict(reference=ref,evidence=evidence)
    return result

PAYLOAD=source_payload(OLD_ROWS+NEW_ROWS)
NEW_IDS=tuple('flag_'+str(row[0]) for row in NEW_ROWS)
PROMOTIONS={'flag_30040800':30042805,'flag_1042370800':1042372806}

def bank_node(text):
    tree=ast.parse(text)
    nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_BANK' for t in n.targets)]
    if len(nodes)!=1: raise ValueError('SOURCE_BANK absente ou ambigue')
    node=nodes[0];bank=ast.literal_eval(node.value)
    if not isinstance(bank,dict): raise ValueError('SOURCE_BANK non litterale')
    return tree,node,bank

def shape(text):
    tree,node,_=bank_node(text);node.value=ast.Dict(keys=[],values=[])
    return ast.dump(tree,include_attributes=False)

def replace_bank(text,bank):
    _,node,_=bank_node(text);lines=text.splitlines(keepends=True)
    data=text.encode('utf-8')
    start=sum(len(s.encode('utf-8')) for s in lines[:node.value.lineno-1])+node.value.col_offset
    end=sum(len(s.encode('utf-8')) for s in lines[:node.value.end_lineno-1])+node.value.end_col_offset
    new=(data[:start]+repr(bank).encode('utf-8')+data[end:]).decode('utf-8')
    if shape(new)!=shape(REFERENCE_REGISTRY): raise ValueError('Le code du registre a change - mise a jour refusee')
    compile(new,REGISTRY,'exec');return new

def safe_path(root,relative):
    path=root/relative
    if not path.resolve().is_relative_to(root): raise ValueError('Chemin hors projet: '+relative)
    current=path
    while current!=root:
        if current.is_symlink(): raise ValueError('Chemin symbolique refuse: '+relative)
        current=current.parent
    return path

def read_base(root):
    if not (root/'main.py').is_file(): raise ValueError('Placer le PY et le BAT a cote de main.py')
    raw={p:safe_path(root,p).read_bytes() for p in TARGETS+(CATALOGUE,)}
    catalogue=json.loads(raw[CATALOGUE].decode('utf-8-sig'))
    if not isinstance(catalogue,list) or len(catalogue)!=207 or any(not isinstance(b,dict) for b in catalogue): raise ValueError('Catalogue incompatible - 207 rencontres requises')
    by_id={b['id']:b for b in catalogue}
    if len(by_id)!=207 or any(type(b['flag_id']) is not int for b in catalogue) or len({b['flag_id'] for b in catalogue})!=207: raise ValueError('Identifiants du catalogue invalides')
    config=json.loads(raw[CONFIG].decode('utf-8-sig'));text=raw[REGISTRY].decode('utf-8')
    if not isinstance(config,dict) or config.get('schema_version')!=1 or set(config.get('encounters',{}))!=set(by_id): raise ValueError('Configuration incompatible avec le catalogue')
    if shape(text)!=shape(REFERENCE_REGISTRY): raise ValueError('Version du registre non reconnue - aucune ecriture')
    _,_,bank=bank_node(text);validate(by_id,config,bank)
    safe_path(root,'sauvegardes_updates')
    return by_id,config,text,bank,raw

def validate(by_id,config,bank):
    seen={};enabled=0
    for key,item in config['encounters'].items():
        if key not in by_id or not isinstance(item,dict): raise ValueError('Rencontre inconnue')
        level=item.get('validation');active=item.get('active_flag')
        if level not in ('not_configured','candidate','documented','user_tested'): raise ValueError('Niveau de validation invalide')
        if 'enabled' in item and type(item['enabled']) is not bool: raise ValueError('Activation non booleenne: '+key)
        if active is not None and (type(active) is not int or not 0<=active<=4294967295 or active==by_id[key]['flag_id']): raise ValueError('Flag actif invalide: '+key)
        if level=='documented':
            ref=bank.get(str(by_id[key]['flag_id']));src=item.get('source')
            if not ref or active!=ref.get('active_flag') or not isinstance(src,dict) or any(src.get(f)!=ref.get(f) for f in FIELDS): raise ValueError('Provenance incoherente: '+key)
        if level in ('documented','user_tested') and item.get('enabled',True) is not False:
            if active is None or active in seen: raise ValueError('Signal de combat manquant ou partage')
            seen[active]=key;enabled+=1
    if enabled>MAX_ACTIVE: raise ValueError('Plus de 32 suivis actifs - plafond conserve')
    return enabled

def plan(by_id,config,text,bank):
    config=copy.deepcopy(config);bank=copy.deepcopy(bank);changes=[]
    active_count=validate(by_id,config,bank)
    for victory,new in PAYLOAD.items():
        key='flag_'+str(victory)
        if key not in by_id or by_id[key]['flag_id']!=victory: raise ValueError('Rencontre source absente ou remappee: '+key)
        old=config['encounters'][key];ref=new['reference'];existing=bank.get(str(victory))
        if existing is not None and any(existing.get(f)!=ref.get(f) for f in ('active_flag',)+FIELDS): raise ValueError('Conflit SOURCE_BANK: '+key)
        if old.get('active_flag') not in (None,ref['active_flag']): raise ValueError('Conflit de combat: '+key)
        if old.get('source') is not None and (not isinstance(old['source'],dict) or any(old['source'].get(f)!=ref.get(f) for f in FIELDS)): raise ValueError('Conflit de provenance: '+key)
        if any(other!=key and item.get('validation') in ('documented','user_tested') and item.get('active_flag')==ref['active_flag'] for other,item in config['encounters'].items()): raise ValueError('Flag associe a plusieurs rencontres: '+key)
        bank[str(victory)]=ref
        if old['validation'] in ('documented','user_tested'): continue
        disabled=old.get('enabled',True) is False;enabled=not disabled and active_count<MAX_ACTIVE
        old.update(active_flag=ref['active_flag'],validation='documented',enabled=enabled,source={f:ref[f] for f in FIELDS})
        evidence=copy.deepcopy(old.get('evidence',{}));evidence.update(new['evidence'])
        if not enabled and not disabled: evidence['activation_blocked']='provisional_capacity_32'
        old['evidence']=evidence
        if enabled: active_count+=1
        changes.append(key)
    for key,expected_active in PROMOTIONS.items():
        item=config['encounters'].get(key)
        if not item or item.get('active_flag')!=expected_active or item.get('validation') not in ('documented','user_tested'): raise ValueError('Promotion incompatible: '+key)
        if item['validation']=='user_tested': continue
        item['validation']='user_tested';evidence=copy.deepcopy(item.get('evidence',{}))
        evidence.update(pc_tested=True,user_reported_on='2026-10-02',user_report='User reported that tracking works. No new measured trace or detailed test sequence is claimed.')
        if key=='flag_1042370800': evidence['verification']='user_reported_full_tracking'
        item['evidence']=evidence
    count=validate(by_id,config,bank)
    prepared={REGISTRY:replace_bank(text,bank).encode('utf-8'),CONFIG:(json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode('utf-8')}
    summary=dict(catalogue_total=207,active_supported=count,configured=sum(i['validation'] in ('documented','user_tested') for i in config['encounters'].values()),
                 user_tested=sum(i['validation']=='user_tested' for i in config['encounters'].values()),documented=sum(i['validation']=='documented' for i in config['encounters'].values()),
                 not_configured=sum(i['validation']=='not_configured' for i in config['encounters'].values()),added=changes,
                 new_rows=[dict(boss_id=key,name=by_id[key].get('names',{}).get('fr',key),place=by_id[key].get('places',{}).get('en',''),
                                active_flag=config['encounters'][key]['active_flag'],victory_flag=by_id[key]['flag_id'],enabled=config['encounters'][key].get('enabled',True),validation=config['encounters'][key]['validation']) for key in NEW_IDS])
    return prepared,summary

PROBE=r"""
import importlib.util,json,sys,types
from pathlib import Path
root=Path(sys.argv[1]);catalog=json.loads((root/'tracker/catalogue_data/boss_catalog.json').read_text(encoding='utf-8-sig'))
prefix='_elt_lot3_validation';p=types.ModuleType(prefix);p.__path__=[str(root/'tracker')];sys.modules[prefix]=p
c=types.ModuleType(prefix+'.boss_catalog');c.BOSSES=tuple(catalog);c.BY_ID={b['id']:b for b in catalog};c.active_bosses=lambda:tuple(catalog);c.display_name=lambda key,language=None:key;sys.modules[c.__name__]=c
i=types.ModuleType(prefix+'.i18n');i.tr=lambda text,language=None:text;i.get_language=lambda:'fr';i.settings=lambda:{'include_dlc':True};sys.modules[i.__name__]=i
s=importlib.util.spec_from_file_location(prefix+'.combat_registry',root/'tracker/combat_registry.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
entries,error=m.read_configuration()
assert error is None,error
assert len(entries)==207
assert len(m.supported_specs(False))<=32
print(json.dumps(m.catalogue_view()['summary']))
"""

def probe(catalogue_bytes,prepared):
    with tempfile.TemporaryDirectory(prefix='elt_lot3_probe_') as temporary:
        root=Path(temporary)
        for p,data in dict(prepared,**{CATALOGUE:catalogue_bytes}).items():
            dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        process=subprocess.run([sys.executable,'-B','-c',PROBE,str(root)],capture_output=True,text=True,timeout=30)
        if process.returncode: raise ValueError('Validation par le registre reel echouee:\n'+process.stdout+process.stderr)
        return json.loads(process.stdout.strip())

def atomic_write(path,data):
    temporary=path.with_name(path.name+'.lot3-'+uuid.uuid4().hex+'.tmp')
    try:
        with open(temporary,'xb') as file:file.write(data);file.flush();os.fsync(file.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists(): temporary.unlink()

def commit(root,prepared,summary):
    changed={p:data for p,data in prepared.items() if safe_path(root,p).read_bytes()!=data}
    if not changed:return None
    base=safe_path(root,'sauvegardes_updates');base.mkdir(exist_ok=True)
    backup=base/(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]+'_flags_lot3');backup.mkdir()
    original={p:(root/p).read_bytes() for p in changed}
    manifest=dict(update=UPDATE_ID,state='prepared',files={p:dict(before=digest(original[p]),after=digest(data)) for p,data in changed.items()},summary=summary)
    for p,data in original.items():dest=backup/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    manifest_path=backup/'manifest.json';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    try:
        for p,data in original.items():
            if (root/p).read_bytes()!=data:raise ValueError('Fichier change pendant la preparation: '+p)
        for p,data in changed.items():atomic_write(root/p,data)
        if any((root/p).read_bytes()!=data for p,data in changed.items()):raise ValueError('Verification apres ecriture echouee')
        manifest['state']='applied';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    except BaseException:
        try:
            for p,data in original.items():atomic_write(root/p,data)
            manifest['state']='rolled_back';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
        except BaseException:pass
        raise
    return backup

def restore(root):
    base=safe_path(root,'sauvegardes_updates');candidates=[]
    if base.exists():
        for path in base.glob('*/manifest.json'):
            try:
                manifest=json.loads(path.read_text(encoding='utf-8'))
                if manifest.get('update')==UPDATE_ID and manifest.get('state') in ('applied','prepared'):candidates.append((path.parent,manifest))
            except (OSError,ValueError):pass
    if not candidates:raise ValueError('Aucune sauvegarde de ce lot a restaurer')
    backup,manifest=sorted(candidates,key=lambda item:item[0].name)[-1]
    if not manifest.get('files') or not set(manifest['files'])<=set(TARGETS):raise ValueError('Manifest invalide')
    originals={};current={}
    for p,item in manifest['files'].items():
        originals[p]=(backup/p).read_bytes();current[p]=safe_path(root,p).read_bytes()
        if digest(originals[p])!=item['before']:raise ValueError('Sauvegarde corrompue: '+p)
        if digest(current[p]) not in (item['before'],item['after']):raise ValueError('Modification ulterieure detectee - restauration refusee: '+p)
    print('Restauration du code uniquement: '+backup.name+'\nProfils, challenges et historiques non touches.')
    if input('Taper RESTAURER pour confirmer: ').strip()!='RESTAURER':return
    if any((root/p).read_bytes()!=data for p,data in current.items()):raise ValueError('Fichier modifie pendant la confirmation')
    try:
        for p,data in originals.items():atomic_write(root/p,data)
    except BaseException:
        for p,data in current.items():atomic_write(root/p,data)
        raise
    manifest['state']='restored';atomic_write(backup/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    print('Restauration terminee.')

def apply(root,dry=False):
    by_id,config,text,bank,initial=read_base(root)
    prepared,summary=plan(by_id,config,text,bank)
    checked=probe(initial[CATALOGUE],prepared)
    if checked['catalogue_total']!=207 or checked['live_supported_active']!=summary['active_supported']:raise ValueError('Desaccord des validations')
    print('Catalogue: 207 - configures: '+str(summary['configured'])+' - actifs: '+str(summary['active_supported']))
    print('user_tested: '+str(summary['user_tested'])+' - documented: '+str(summary['documented'])+' - not_configured: '+str(summary['not_configured']))
    for row in summary['new_rows']:
        print(row['name']+' - '+row['place']+' - combat '+str(row['active_flag'])+' - victoire '+str(row['victory_flag'])+' - '+('ACTIF EXPERIMENTAL' if row['enabled'] else 'DESACTIVE'))
    print('Reset reel non valide sur les nouvelles rencontres. Moteur, lecteur et overlay inchanges.')
    if dry:print('Apercu uniquement - aucune ecriture.');return
    if all((root/p).read_bytes()==data for p,data in prepared.items()):print('Deja applique - aucune ecriture.');return
    if input('Fermer le tracker, puis taper APPLIQUER: ').strip()!='APPLIQUER':print('Annule.');return
    if any((root/p).read_bytes()!=data for p,data in initial.items()):raise ValueError('La base a change pendant la preparation')
    backup=commit(root,prepared,summary)
    print('Lot applique. Sauvegarde: '+backup.name)


def self_test():
    import unittest
    from unittest.mock import patch

    class Fixture:
        def __init__(self,root,count=18):
            self.root=root
            victories=list(dict.fromkeys([int(k) for k in BASE_BANK]+list(PAYLOAD)))
            victories+=list(range(800000,800000+207-len(victories)))
            self.bosses=[dict(id='flag_'+str(v),flag_id=v,names={'fr':'Boss '+str(v),'en':'Boss '+str(v)},places={'fr':'Lieu','en':'Place'},content='dlc' if v in (43000800,43010800) else 'base_game') for v in victories]
            self.by={b['id']:b for b in self.bosses};self.config=dict(schema_version=1,encounters={k:dict(active_flag=None,validation='not_configured') for k in self.by});bank=copy.deepcopy(BASE_BANK)
            for victory,ref in BASE_BANK.items():
                self.config['encounters']['flag_'+victory]=dict(active_flag=ref['active_flag'],validation='user_tested' if victory=='1039500800' else 'documented',enabled=True,source={f:ref[f] for f in FIELDS})
            self.config['encounters']['flag_1039500800']['evidence']={'entry':'four_run_trace','victory':'user_reported'}
            old=OLD_ROWS[:2] if count==12 else OLD_ROWS if count>=18 else []
            for row in old:
                victory=row[0];item=PAYLOAD[victory];ref=item['reference'];bank[str(victory)]=ref
                self.config['encounters']['flag_'+str(victory)]=dict(active_flag=ref['active_flag'],validation='documented',enabled=True,source={f:ref[f] for f in FIELDS},evidence=copy.deepcopy(item['evidence']))
            if count>=12:
                i=self.config['encounters']['flag_1042370800'];i['validation']='user_tested';i['evidence']={'verification':'user_reported_full_tracking'}
            if count>=18:
                i=self.config['encounters']['flag_30040800'];i['validation']='user_tested';i['evidence']['pc_tested']=True;i['evidence']['user_report']='works'
            self.text=replace_bank(REFERENCE_REGISTRY,bank);self.bank=bank
            files={REGISTRY:self.text.encode(),CONFIG:json.dumps(self.config,ensure_ascii=False,indent=2).encode(),CATALOGUE:json.dumps(self.bosses).encode(),
                   'main.py':b'# existing launcher\n','tracker/combat_tracking.py':REFERENCE_TRACKING.encode(),'tracker/combat_coordinator.py':REFERENCE_COORDINATOR.encode(),
                   'profiles/user.json':b'{"history":[1,2,3],"challenge":"keep"}','overlay/style.css':b'keep overlay','settings.json':b'keep settings'}
            for p,data in files.items():dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        def save(self):
            (self.root/CONFIG).write_text(json.dumps(self.config),encoding='utf-8')
            (self.root/REGISTRY).write_text(self.text,encoding='utf-8')
        def planned(self):return plan(self.by,self.config,self.text,self.bank)
        def snapshot(self):return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    class InstallerTests(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.fixture=Fixture(self.root)
        def test_reference_registry_git_fingerprint(self):self.assertEqual(git_blob(REFERENCE_REGISTRY),'6eea4f18496ce857c9a780937fc763a2a612af5f')
        def test_reference_engine_git_fingerprint(self):self.assertEqual(git_blob(REFERENCE_TRACKING),'38c89f8b97fafb3bdb815af22c0cf55aa0b3869f')
        def test_lot2_to_25(self):
            _,s=self.fixture.planned();self.assertEqual((s['configured'],s['active_supported'],s['user_tested'],s['documented'],s['not_configured']),(25,25,3,22,182))
        def test_initial_10_to_25(self):
            f=Fixture(self.root,10);_,s=f.planned();self.assertEqual((s['configured'],s['active_supported'],s['user_tested']),(25,25,3))
        def test_lot1_12_to_25(self):
            f=Fixture(self.root,12);_,s=f.planned();self.assertEqual((s['configured'],s['active_supported'],s['user_tested']),(25,25,3))
        def test_all_seven_explicit_flags(self):
            files,s=self.fixture.planned();doc=json.loads(files[CONFIG]);expected={32020800:32022805,32040800:32042805,12040800:12042805,12080800:12082805,32080800:32082805,43000800:43002805,43010800:43012805}
            for victory,active in expected.items():self.assertEqual(doc['encounters']['flag_'+str(victory)]['active_flag'],active)
        def test_provenance_complete(self):
            files,_=self.fixture.planned();doc=json.loads(files[CONFIG]);_,_,bank=bank_node(files[REGISTRY].decode())
            for key in NEW_IDS:
                item=doc['encounters'][key];self.assertEqual(item['validation'],'documented');self.assertFalse(item['evidence']['pc_tested'])
                for field in FIELDS:self.assertEqual(item['source'][field],bank[str(self.fixture.by[key]['flag_id'])][field])
        def test_caller_events_recorded(self):
            files,_=self.fixture.planned();doc=json.loads(files[CONFIG]);self.assertEqual(doc['encounters']['flag_43010800']['evidence']['caller_event'],'Event_43012849')
        def test_fallingstar_first_repeat_gate_recorded(self):
            files,_=self.fixture.planned();doc=json.loads(files[CONFIG]);self.assertTrue(doc['encounters']['flag_32080800']['evidence']['first_and_repeat_gate_same_flag'])
        def test_phase_flag_is_not_used_as_active(self):
            files,_=self.fixture.planned();doc=json.loads(files[CONFIG]);item=doc['encounters']['flag_32080800'];self.assertEqual(item['evidence']['phase_flag'],32082802);self.assertEqual(item['active_flag'],32082805)
        def test_idempotent_plan(self):
            files,_=self.fixture.planned();text=files[REGISTRY].decode();_,_,bank=bank_node(text)
            again,_=plan(self.fixture.by,json.loads(files[CONFIG]),text,bank);self.assertEqual(again,files)
        def test_manual_disable_of_new_boss_preserved(self):
            self.fixture.config['encounters']['flag_12040800']['enabled']=False
            files,s=self.fixture.planned();self.assertFalse(json.loads(files[CONFIG])['encounters']['flag_12040800']['enabled']);self.assertEqual(s['active_supported'],24)
        def test_manual_disable_of_existing_boss_preserved(self):
            self.fixture.config['encounters']['flag_30040800']['enabled']=False
            files,_=self.fixture.planned();self.assertFalse(json.loads(files[CONFIG])['encounters']['flag_30040800']['enabled'])
        def test_godefroy_evidence_unchanged(self):
            old=copy.deepcopy(self.fixture.config['encounters']['flag_1039500800']);files,_=self.fixture.planned();self.assertEqual(json.loads(files[CONFIG])['encounters']['flag_1039500800'],old)
        def test_user_tested_new_boss_not_demoted(self):
            item=self.fixture.config['encounters']['flag_12040800'];item.update(active_flag=12042805,validation='user_tested',evidence={'report':'keep'})
            files,_=self.fixture.planned();self.assertEqual(json.loads(files[CONFIG])['encounters']['flag_12040800'],item)
        def test_conflicting_flag_refused(self):
            self.fixture.config['encounters']['flag_12040800']['active_flag']=12345
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_conflicting_source_refused(self):
            self.fixture.config['encounters']['flag_12040800']['source']={f:'wrong' for f in FIELDS}
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_conflicting_bank_refused(self):
            self.fixture.bank['12040800']=dict(PAYLOAD[12040800]['reference'],active_flag=12345)
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_duplicate_active_refused(self):
            self.fixture.config['encounters']['flag_800000'].update(active_flag=12042805,validation='user_tested')
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_catalogue_206_refused(self):
            (self.root/CATALOGUE).write_text(json.dumps(self.fixture.bosses[:-1]))
            with self.assertRaises(ValueError):read_base(self.root)
        def test_flag_boolean_refused(self):
            self.fixture.config['encounters']['flag_12040800']['active_flag']=True
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_missing_payload_encounter_refused(self):
            self.fixture.by.pop('flag_12040800');self.fixture.config['encounters'].pop('flag_12040800')
            with self.assertRaises(ValueError):self.fixture.planned()
        def test_altered_registry_code_refused(self):
            (self.root/REGISTRY).write_text(self.fixture.text.replace('enabled>32','enabled>999'))
            with self.assertRaises(ValueError):read_base(self.root)
        def test_bank_only_patch(self):
            files,_=self.fixture.planned();self.assertEqual(shape(files[REGISTRY].decode()),shape(self.fixture.text))
        def test_real_registry_probe(self):
            files,_=self.fixture.planned();s=probe((self.root/CATALOGUE).read_bytes(),files);self.assertEqual((s['catalogue_total'],s['live_supported_active']),(207,25))
        def test_capacity_preserved(self):
            for index in range(14):self.fixture.config['encounters']['flag_'+str(800000+index)].update(active_flag=900000+index,validation='user_tested')
            files,s=self.fixture.planned();self.assertEqual(s['active_supported'],32)
            for key in NEW_IDS:self.assertFalse(json.loads(files[CONFIG])['encounters'][key]['enabled'])
        def test_backup_exact_bytes(self):
            before={p:(self.root/p).read_bytes() for p in TARGETS};files,s=self.fixture.planned();backup=commit(self.root,files,s)
            for p in TARGETS:self.assertEqual((backup/p).read_bytes(),before[p])
        def test_no_unrelated_files_touched(self):
            before=self.fixture.snapshot();files,s=self.fixture.planned();commit(self.root,files,s)
            for p,data in before.items():
                if p not in TARGETS:self.assertEqual((self.root/p).read_bytes(),data)
        def test_no_extra_backup_on_repeat(self):
            files,s=self.fixture.planned();commit(self.root,files,s);self.assertIsNone(commit(self.root,files,s));self.assertEqual(len(list((self.root/'sauvegardes_updates').iterdir())),1)
        def test_restore_exact(self):
            before={p:(self.root/p).read_bytes() for p in TARGETS};files,s=self.fixture.planned();commit(self.root,files,s)
            with patch('builtins.input',return_value='RESTAURER'),patch('builtins.print'):restore(self.root)
            for p,data in before.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_restore_refuses_subsequent_edit(self):
            files,s=self.fixture.planned();commit(self.root,files,s);(self.root/REGISTRY).write_bytes(b'modified later')
            with self.assertRaises(ValueError):restore(self.root)
            self.assertEqual((self.root/REGISTRY).read_bytes(),b'modified later')
        def test_restore_refuses_corrupt_backup(self):
            files,s=self.fixture.planned();backup=commit(self.root,files,s);(backup/REGISTRY).write_bytes(b'corrupted')
            with self.assertRaises(ValueError):restore(self.root)
        def test_restore_prepared_partial_transaction(self):
            before={p:(self.root/p).read_bytes() for p in TARGETS};files,s=self.fixture.planned();backup=commit(self.root,files,s)
            manifest=json.loads((backup/'manifest.json').read_text());manifest['state']='prepared';(backup/'manifest.json').write_text(json.dumps(manifest));(self.root/REGISTRY).write_bytes(before[REGISTRY])
            with patch('builtins.input',return_value='RESTAURER'),patch('builtins.print'):restore(self.root)
            for p,data in before.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_write_failure_rolls_back(self):
            files,s=self.fixture.planned();before={p:(self.root/p).read_bytes() for p in TARGETS};real=atomic_write;count=[0]
            def failing(path,data):
                count[0]+=1
                if count[0]==3:raise OSError('synthetic failure')
                real(path,data)
            with patch(__name__+'.atomic_write',side_effect=failing):
                with self.assertRaises(OSError):commit(self.root,files,s)
            for p,data in before.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_preview_no_write(self):
            before=self.fixture.snapshot()
            with patch('builtins.print'):apply(self.root,dry=True)
            self.assertEqual(before,self.fixture.snapshot())
        def test_cancel_no_write(self):
            before=self.fixture.snapshot()
            with patch('builtins.print'),patch('builtins.input',return_value='NON'):apply(self.root)
            self.assertEqual(before,self.fixture.snapshot())
        def test_confirmation_race_refused(self):
            before=(self.root/CONFIG).read_bytes()
            def change(_):
                (self.root/CATALOGUE).write_bytes(b'changed during confirmation');return 'APPLIQUER'
            with patch('builtins.print'),patch('builtins.input',side_effect=change):
                with self.assertRaises(ValueError):apply(self.root)
            self.assertEqual((self.root/CONFIG).read_bytes(),before)
        def test_menu_apply(self):
            with patch('sys.argv',['update','--root',str(self.root)]),patch('builtins.input',side_effect=['1','APPLIQUER']),patch('builtins.print'):main()
            _,s=self.fixture.planned();self.assertFalse((self.root/'.elt_flags_lot3.lock').exists());self.assertEqual(len(json.loads((self.root/CONFIG).read_bytes())['encounters']),207)
        def test_menu_restore(self):
            before={p:(self.root/p).read_bytes() for p in TARGETS};files,s=self.fixture.planned();commit(self.root,files,s)
            with patch('sys.argv',['update','--root',str(self.root)]),patch('builtins.input',side_effect=['3','RESTAURER']),patch('builtins.print'):main()
            for p,data in before.items():self.assertEqual((self.root/p).read_bytes(),data)

    class EngineTests(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.fixture=Fixture(self.root)
            files,_=self.fixture.planned()
            for p,data in files.items():(self.root/p).write_bytes(data)
            prefix='_lot3_test_'+uuid.uuid4().hex;p=types.ModuleType(prefix);p.__path__=[str(self.root/'tracker')]
            c=types.ModuleType(prefix+'.boss_catalog');c.BOSSES=tuple(self.fixture.bosses);c.BY_ID=self.fixture.by;c.active_bosses=lambda:tuple(self.fixture.bosses);c.display_name=lambda key,language=None:key
            i=types.ModuleType(prefix+'.i18n');i.tr=lambda text,language=None:text;i.get_language=lambda:'fr';i.settings=lambda:{'include_dlc':True}
            context=patch.dict(sys.modules,{prefix:p,c.__name__:c,i.__name__:i});context.start();self.addCleanup(context.stop)
            def load(name,path):
                spec=importlib.util.spec_from_file_location(prefix+'.'+name,self.root/path);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module
            self.registry=load('combat_registry',REGISTRY);self.tracking=load('combat_tracking','tracker/combat_tracking.py');self.coordinator=load('combat_coordinator','tracker/combat_coordinator.py')
        def snap(self,key,active=False,victory=False):return dict(can_count=True,screen_state=0,name_match=True,combat_signal=dict(boss_id=key,active=active,victory=victory))
        def start(self,key):
            session=self.tracking.CombatSession(boss_id=key);session.observe(self.snap(key),0,0);session.observe(self.snap(key,True),1,0);return session
        def test_each_new_boss_supported(self):
            for key in NEW_IDS:self.assertIsNotNone(self.registry.supported_spec(key))
        def test_stable_active_one_attempt(self):
            for key in NEW_IDS:
                session=self.start(key)
                for seconds in range(2,8):session.observe(self.snap(key,True),seconds,0)
                self.assertEqual(session.attempts,1)
        def test_midfight_no_fictitious_attempt(self):
            for key in NEW_IDS:
                session=self.tracking.CombatSession(boss_id=key);session.observe(self.snap(key,True),0,0);self.assertEqual(session.attempts,0);self.assertEqual(session.phase,'active_untracked')
        def test_death_then_reset_then_retry(self):
            for key in NEW_IDS:
                session=self.start(key);session.observe(self.snap(key,True),2,1);session.observe(self.snap(key,True),3,1);self.assertEqual(session.attempts,1)
                session.observe(self.snap(key),4,1);session.observe(self.snap(key,True),5,1);self.assertEqual((session.attempts,session.observed_boss_deaths),(2,1))
        def test_victory_not_death(self):
            for key in NEW_IDS:
                session=self.start(key);session.observe(self.snap(key,True,True),2,0);self.assertEqual(session.last_result,'victory');self.assertEqual(session.observed_boss_deaths,0)
        def test_simultaneous_victory_death_once(self):
            for key in NEW_IDS:
                session=self.start(key);session.observe(self.snap(key,True,True),2,1);self.assertEqual(session.last_result,'victory_and_death');self.assertEqual(session.observed_boss_deaths,1)
        def test_missing_signal_with_death_uncertain(self):
            session=self.start(NEW_IDS[0]);session.observe(dict(can_count=False,screen_state=1),2,1);self.assertEqual(session.last_result,'uncertain');self.assertEqual(session.observed_boss_deaths,0)
        def test_counter_jump_uncertain(self):
            session=self.start(NEW_IDS[0]);session.observe(self.snap(NEW_IDS[0],True),2,2);self.assertEqual(session.last_result,'uncertain');self.assertEqual(session.observed_boss_deaths,0)
        def test_counter_rollback_uncertain(self):
            session=self.start(NEW_IDS[0]);session.last_deaths=2;session.observe(self.snap(NEW_IDS[0],True),2,1);self.assertEqual(session.last_result,'uncertain')
        def test_histories_independent(self):
            current={'combat_history':[dict(id='unrelated',type='note',boss_id='other')]}
            for key in NEW_IDS:
                session=self.start(key);session.observe(self.snap(key,True),2,1);session.merge(current);n=len(current['combat_history']);session.merge(current);self.assertEqual(len(current['combat_history']),n)
            for key in NEW_IDS:self.assertEqual(self.tracking.count_observed_boss_deaths(current['combat_history'],key),1)
            self.assertEqual(current['combat_history'][0]['id'],'unrelated')
        def test_restart_closes_unfinished_as_interrupted(self):
            session=self.start(NEW_IDS[0]);again=self.tracking.CombatSession(session.events,boss_id=NEW_IDS[0]);self.assertEqual(again.events[0]['outcome'],'interrupted');self.assertEqual(again.observed_boss_deaths,0)
        def test_legacy_godefroy_history_preserved(self):
            history=[dict(type='boss_attempt_start',attempt_id='old',boss_id='flag_1039500800',tracking_mode='godefroy_active_flag_v1'),dict(type='boss_attempt_end',attempt_id='old',boss_id='flag_1039500800',tracking_mode='godefroy_active_flag_v1',outcome='death')];old=copy.deepcopy(history)
            session=self.tracking.CombatSession(history,boss_id='flag_1039500800');self.assertEqual((session.attempts,session.observed_boss_deaths),(1,1));self.assertEqual(history,old)
        def test_phase_hint_does_not_create_attempt(self):
            for key in ('flag_32080800','flag_43010800'):
                session=self.start(key);snap=self.snap(key,True);snap['phase_hint']=True;session.observe(snap,2,0);self.assertEqual(session.attempts,1)
        def test_two_active_signals_suspend_attribution(self):
            c=self.coordinator.CombatCoordinator();a,b=NEW_IDS[:2]
            def many(active):return dict(can_count=True,screen_state=0,name_match=True,combat_signals={key:dict(boss_id=key,active=active,victory=False) for key in (a,b)})
            c.observe(many(False),0,0);c.observe(many(True),1,1);self.assertIsNone(c.payload());self.assertIsNotNone(c.error)
            for key in (a,b):self.assertEqual(c.instances[key].attempts,0);self.assertEqual(c.instances[key].observed_boss_deaths,0)
        def test_multiple_signals_during_open_attempt_no_arbitrary_death(self):
            c=self.coordinator.CombatCoordinator();a,b=NEW_IDS[:2]
            def many(a_active,b_active):return dict(can_count=True,screen_state=0,name_match=True,combat_signals={a:dict(boss_id=a,active=a_active,victory=False),b:dict(boss_id=b,active=b_active,victory=False)})
            c.observe(many(False,False),0,0);c.observe(many(True,False),1,0);c.observe(many(True,True),2,1)
            self.assertIsNone(c.payload());self.assertEqual(c.instances[a].observed_boss_deaths,0);self.assertEqual(c.instances[a].last_result,'uncertain')
        def test_disabled_new_spec_not_returned(self):
            doc=json.loads((self.root/CONFIG).read_bytes());doc['encounters'][NEW_IDS[0]]['enabled']=False;(self.root/CONFIG).write_text(json.dumps(doc))
            self.assertIsNone(self.registry.supported_spec(NEW_IDS[0]))
        def test_dlc_option_limits_active_scope(self):
            self.registry.active_bosses=lambda:tuple(b for b in self.fixture.bosses if b['content']=='base_game')
            self.assertEqual(len(self.registry.supported_specs()),23);self.assertEqual(len(self.registry.supported_specs(False)),25)
        def test_source_tampering_rejected_by_real_registry(self):
            doc=json.loads((self.root/CONFIG).read_bytes());doc['encounters'][NEW_IDS[0]]['source']['path']='wrong.py';(self.root/CONFIG).write_text(json.dumps(doc))
            self.assertIsNotNone(self.registry.read_configuration()[1])
        def test_phase_substitution_rejected_by_real_registry(self):
            doc=json.loads((self.root/CONFIG).read_bytes());doc['encounters']['flag_32080800']['active_flag']=32082802;(self.root/CONFIG).write_text(json.dumps(doc))
            self.assertIsNotNone(self.registry.read_configuration()[1])
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(InstallerTests),unittest.defaultTestLoader.loadTestsFromTestCase(EngineTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default=str(Path(__file__).resolve().parent));parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--restore',action='store_true');parser.add_argument('--self-test',action='store_true')
    opts=parser.parse_args()
    if opts.self_test:return self_test()
    root=Path(opts.root).resolve()
    if not (root/'main.py').is_file():raise ValueError('Placer le PY et le BAT a cote de main.py')
    if not opts.restore and not opts.dry_run:
        print('1 - Appliquer le lot cumulatif hors ligne\n2 - Apercu sans installation\n3 - Restaurer ce lot\n4 - Tests synthetiques')
        choice=input('Choix: ').strip()
        if choice=='2':opts.dry_run=True
        elif choice=='3':opts.restore=True
        elif choice=='4':return self_test()
        elif choice!='1':print('Annule.');return 0
    lock=safe_path(root,'.elt_flags_lot3.lock')
    try:
        with open(lock,'x',encoding='utf-8') as file:file.write(str(os.getpid()))
    except FileExistsError:raise ValueError('Update deja en cours ou verrou restant: .elt_flags_lot3.lock')
    try:
        if opts.restore:restore(root)
        else:apply(root,dry=opts.dry_run)
    finally:lock.unlink(missing_ok=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ERREUR - '+str(exc),file=sys.stderr);sys.exit(1)

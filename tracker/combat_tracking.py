# SPDX-License-Identifier: GPL-3.0-only
"""Suivi experimental par boss ; historiques anciens conserves."""
import time
from .i18n import tr
import math
import uuid
from datetime import datetime, timezone
BOSS_ID = 'flag_1039500800'
MODE = 'confirmed_active_flag_v1'
SUPPORTED_MODES = frozenset({'confirmed_active_flag_v1', 'godefroy_active_flag_v1'})

def new_event(kind, attempt, seconds=None, boss_id=BOSS_ID, **fields):
    return dict(id=uuid.uuid4().hex, type=kind, attempt_id=attempt, boss_id=boss_id, tracking_mode=MODE, run_seconds=seconds, observed_at=datetime.now(timezone.utc).isoformat(), **fields)

def count_observed_boss_deaths(history, boss_id=BOSS_ID):
    starts = {item.get('attempt_id') for item in history if isinstance(item, dict) and item.get('type') == 'boss_attempt_start' and (item.get('boss_id') == boss_id) and (item.get('tracking_mode') in SUPPORTED_MODES) and isinstance(item.get('attempt_id'), str) and item['attempt_id']}
    deaths = {item.get('attempt_id') for item in history if isinstance(item, dict) and item.get('type') == 'boss_attempt_end' and (item.get('boss_id') == boss_id) and (item.get('tracking_mode') in SUPPORTED_MODES) and (item.get('outcome') in ('death', 'victory_and_death')) and (item.get('attempt_id') in starts)}
    return len(deaths)

class CombatSession:

    def __init__(self, history=None, tracked_deaths=0, boss_id=BOSS_ID):
        if not isinstance(boss_id, str) or not boss_id:
            raise ValueError('Identifiant de boss invalide')
        self.boss_id = boss_id
        history = [] if history is None else history
        if not isinstance(history, list) or type(tracked_deaths) is not int or tracked_deaths < 0:
            raise ValueError('Historique de combat ou compteur invalide')
        self.existing = list(history)
        self.events = []
        starts = {}
        ends = set()
        for item in history:
            if not isinstance(item, dict) or item.get('boss_id') != self.boss_id or item.get('tracking_mode') not in SUPPORTED_MODES:
                continue
            attempt = item.get('attempt_id')
            if not isinstance(attempt, str) or not attempt:
                continue
            if item.get('type') == 'boss_attempt_start':
                starts.setdefault(attempt, item)
            elif item.get('type') == 'boss_attempt_end':
                ends.add(attempt)
        self.attempts = len(starts)
        self.observed_boss_deaths = count_observed_boss_deaths(history, boss_id=self.boss_id)
        for attempt in starts.keys() - ends:
            self.events.append(new_event('boss_attempt_end', attempt, outcome='interrupted', reason='tracking_restart', run_end_unknown=True, boss_id=self.boss_id))
        self.open = None
        self.armed = False
        self.phase = 'unknown'
        self.active = False
        self.last_result = None
        self.last_deaths = tracked_deaths
        self.seconds = 0.0

    def finish(self, outcome, reason=None):
        if self.open is not None:
            self.events.append(new_event('boss_attempt_end', self.open['attempt_id'], round(self.seconds, 6), outcome=outcome, reason=reason, boss_id=self.boss_id))
            if outcome in ('death', 'victory_and_death'):
                self.observed_boss_deaths += 1
            self.open = None
        self.last_result = outcome
        self.armed = False
        self.active = False
        self.phase = 'wait_reset'

    def observe(self, snap, seconds, tracked_deaths):
        if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or (not math.isfinite(seconds)) or (seconds < 0):
            raise ValueError('Temps de combat invalide')
        if type(tracked_deaths) is not int or tracked_deaths < 0:
            raise ValueError('Compteur de combat invalide')
        self.seconds = float(seconds)
        delta = tracked_deaths - self.last_deaths
        self.last_deaths = tracked_deaths
        signal = snap.get('combat_signal') if snap.get('can_count') is True else None
        valid = isinstance(signal, dict) and signal.get('boss_id') == self.boss_id and (type(signal.get('active')) is bool) and (type(signal.get('victory')) is bool)
        now = time.monotonic()
        if not valid:
            last_false = getattr(self, '_last_confirmed_false_at', None)
            loading = snap.get('screen_state') == 1 or bool(snap.get('blackscreen'))
            matching = snap.get('screen_state') == 0 and snap.get('name_match') is True
            normal_pause = snap.get('screen_state') in (0, 1) and snap.get('guard_status') in (tr('pause automatique'), tr('pause - confirmation du nom'))
            can_preserve = self.armed and last_false is not None and (0 <= now - last_false <= 12) and (snap.get('name_match') is not False) and (not snap.get('combat_error')) and (loading or matching or normal_pause)
            if not can_preserve:
                self.armed = False
            self.active = False
            if self.open is not None and delta:
                self.finish('uncertain', 'death_delta_without_valid_combat_signal')
            self.phase = 'suspended' if self.open is not None else 'unknown'
            return
        active, victory = (signal['active'], signal['victory'])
        if self.open is not None:
            if delta < 0 or delta > 1:
                self.finish('uncertain', 'death_counter_discontinuity')
                return
            if victory:
                self.finish('victory_and_death' if delta == 1 else 'victory')
                return
            if delta == 1:
                self.finish('death' if active else 'uncertain', None if active else 'death_delta_after_combat_reset')
                return
            if not active:
                self.finish('interrupted', 'active_flag_reset_without_confirmed_result')
                return
            self.active = True
            self.phase = 'active'
            return
        if victory:
            self.phase = 'defeated'
            self.active = False
            self.armed = False
            return
        if not active:
            self.phase = 'ready'
            self.armed = True
            self.active = False
            self._last_confirmed_false_at = now
            return
        if self.phase == 'wait_reset':
            self.active = False
            return
        last_false = getattr(self, '_last_confirmed_false_at', None)
        if self.armed and (last_false is None or now - last_false > 12):
            self.armed = False
        if not self.armed:
            self.phase = 'active_untracked'
            self.active = True
            return
        if delta:
            self.phase = 'unknown'
            self.armed = False
            self.active = False
            return
        attempt = uuid.uuid4().hex
        event = new_event('boss_attempt_start', attempt, round(self.seconds, 6), boss_id=self.boss_id)
        self.events.append(event)
        self.open = event
        self.attempts += 1
        self.armed = False
        self.phase = 'active'
        self.active = True

    def stop(self, seconds):
        self.seconds = float(seconds)
        if self.open is not None:
            self.finish('interrupted', 'tracking_stopped')
        self.active = False
        self.armed = False
        self.phase = 'stopped'

    def merge(self, current):
        history = current.get('combat_history', [])
        if not isinstance(history, list):
            raise ValueError('Historique de combat enregistre invalide')
        ids = {item.get('id') for item in history if isinstance(item, dict) and isinstance(item.get('id'), str)}
        current['combat_history'] = history + [dict(event) for event in self.events if event['id'] not in ids]

    def payload(self):
        return dict(boss_id=self.boss_id, mode=MODE, phase=self.phase, active=self.active, observed_attempts=self.attempts, last_result=self.last_result, attempt_start_seconds=self.open['run_seconds'] if self.open else None, observed_boss_deaths=self.observed_boss_deaths)
# GODEFROY_ARMING_FIX_V1
# COMBAT_CONTEXTUAL_UI_V1
# GENERIC_COMBAT_ENGINE_V1

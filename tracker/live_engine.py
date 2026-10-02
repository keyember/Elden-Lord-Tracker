# SPDX-License-Identifier: GPL-3.0-only
"""v0.5.0 : controle experimental du nom ; profil fige durant la session."""
from .combat_coordinator import CombatCoordinator as CombatSession
from .i18n import tr, translate_status
import time, json, logging
from datetime import datetime, timezone
from .character_guard import NameReader, expected_name
from .paths import DATA, OBS
from .storage import write_json, atomic_text
from .profiles import DIRECTORY, selected_profile
from .save_reader import copy_save, read_names
from .run_clock import RunClock
from .death_counter import DeathSession
from .boss_reader import BossReader
from .boss_timeline import BossTimeline
from .boss_catalog import BOSS_IDS, active_bosses

def run_live(app, source, slot, stop):
    reader = None
    clock = None
    profile = None
    snap = {}
    name = None
    deaths = None
    timeline = None
    combat = None

    def persist():
        try:
            path = DIRECTORY / (profile['id'] + '.json')
            current = json.loads(path.read_text(encoding='utf-8'))
            current.update(run_seconds=round(clock.seconds, 6), timer_mode='realtime_excluding_loading', updated_at=datetime.now(timezone.utc).isoformat())
            if deaths is not None:
                current['tracked_deaths'] = deaths.count
                current['death_tracking_mode'] = 'observed_session_increments'
            if snap.get('boss_states') is not None:
                current['boss_states'] = dict(snap['boss_states'])
                current['boss_scope'] = 'configured_catalog'
            if timeline is not None:
                timeline.merge(current)
            if combat is not None:
                combat.merge(current)
            write_json(path, current)
        except (OSError, ValueError, TypeError) as exc:
            logging.exception(tr('Persistance impossible'))
            app.queue.put(('status', f"{tr('Attention : temps en memoire non sauvegarde (')}{exc})"))

    def publish(status, running, counting=False):
        active_ids = tuple(b['id'] for b in active_bosses())
        payload = dict(challenge=profile['name'], profile_id=profile['id'], character=name, slot=slot, source=str(source.resolve()), seconds=clock.seconds, timer=clock.formatted(), running=running, counting=counting, status=status, updated_at=time.time(), identity_verified=False, identity_mode='name_only', name_match=snap.get('name_match'), observed_character=snap.get('observed_character'))
        payload.update(deaths=deaths.count if deaths is not None else None, deaths_total=snap.get('deaths_total'), death_tracking_status=snap.get('death_tracking_status'), death_tracking_mode='observed_session_increments')
        states = snap.get('boss_states')
        payload.update(boss_states=states, boss_scope='configured_catalog', defeated=sum(states[key] for key in active_ids) if isinstance(states, dict) and active_ids and all(type(states.get(key)) is bool for key in active_ids) else None, boss_progression=timeline.render(states) if timeline is not None else None, boss_times={key: value for key, value in timeline.times.items() if key not in timeline.blocked} if timeline is not None else {}, boss_timing_mode='confirmed_flag_observation', boss_catalog_count=len(active_ids))
        payload.update(combat=combat.payload() if combat is not None else None, combat_error=combat.error if combat is not None else None)
        try:
            write_json(DATA / 'live_clock.json', payload)
            atomic_text(OBS / 'timer.txt', clock.formatted())
            atomic_text(OBS / 'statut.txt', status)
            atomic_text(OBS / 'personnage.txt', name or tr('N/A'))
            atomic_text(OBS / 'morts.txt', str(deaths.count) if deaths is not None else tr('N/A'))
            atomic_text(OBS / 'morts_total_personnage.txt', str(snap['deaths_total']) if snap.get('deaths_total') is not None else tr('N/A'))
            atomic_text(OBS / 'progression_boss.txt', payload['boss_progression'] or tr('Progression : N/A'))
        except OSError:
            logging.exception('Publication impossible ; nouvel essai au prochain cycle')
    try:
        profile = selected_profile(source, slot)
        if not profile:
            raise ValueError(tr('Selectionne un challenge avant de demarrer'))
        clock = RunClock(profile.get('run_seconds', 0))
        deaths = DeathSession(profile.get('tracked_deaths', 0))
        timeline = BossTimeline(profile.get('boss_history', []))
        combat = CombatSession(profile.get('combat_history', []), deaths.count)
        names = read_names(copy_save(source, DATA / 'temp_identity_save.sl2'))
        name = expected_name(names, slot)
        app.queue.put(('names', names))
        publish(tr('Connexion - controle du nom uniquement'), False)
        if stop.is_set():
            return
        reader = BossReader(name)
        saved = time.monotonic()
        published = 0
        while not stop.is_set():
            selected = selected_profile(source, slot)
            if not selected or selected['id'] != profile['id']:
                app.queue.put(('status', tr('Challenge change : ancien temps conserve. Clique sur Demarrer pour le nouveau.')))
                break
            snap = reader.snapshot()
            snap.update(deaths.observe(snap))
            now = time.monotonic()
            clock.sample(now, snap['can_count'])
            timeline.observe(snap, clock.seconds)
            combat.observe(snap, clock.seconds, deaths.count)
            if now - published >= 0.2:
                status = snap['screen_name'] + ' - ' + snap['guard_status']
                if snap.get('death_tracking_status'):
                    status += ' - ' + snap['death_tracking_status']
                if snap.get('boss_error'):
                    status += ' - progression N/A : ' + snap['boss_error']
                publish(status, True, snap['can_count'])
                app.queue.put(('status', f"{profile['name']} - {clock.formatted()} - {status}"))
                published = now
            if now - saved >= 2:
                persist()
                saved = now
            stop.wait(0.1)
        clock.freeze()
        if combat is not None:
            combat.stop(clock.seconds)
        persist()
        snap = {}
        publish(tr('Chrono arrete - temps conserve'), False)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        logging.exception('Chrono suspendu')
        app.queue.put(('status', f"{tr('Chrono en pause : ')}{exc}. Corrige puis clique sur Demarrer."))
        if clock and profile:
            clock.freeze()
            if combat is not None:
                combat.stop(clock.seconds)
            persist()
            snap = {}
            publish(f"{tr('Lecture interrompue : ')}{exc}", False)
    finally:
        if reader:
            reader.close()
        app.runtime(False, None)

# ACTIVE_BOSS_SCOPE_V1

# GODEFROY_COMBAT_PROTOTYPE_V1

# GENERIC_COMBAT_ENGINE_V1

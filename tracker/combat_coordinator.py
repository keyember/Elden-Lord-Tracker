# SPDX-License-Identifier: GPL-3.0-only
"""Routes confirmed observations to one independent tracker per boss."""
from .combat_tracking import CombatSession
from .combat_registry import supported_specs

class CombatCoordinator:
    def __init__(self,history=None,tracked_deaths=0):
        self.history=[] if history is None else list(history)
        self.instances={spec['boss_id']:CombatSession(self.history,tracked_deaths,boss_id=spec['boss_id']) for spec in supported_specs(False)}
        self.selected=None;self.error=None

    def observe(self,snap,seconds,tracked_deaths):
        signals=snap.get('combat_signals')
        signals=signals if isinstance(signals,dict) else {}
        enabled={spec['boss_id'] for spec in supported_specs(False)}
        for key in enabled:
            if key not in self.instances:self.instances[key]=CombatSession(self.history,tracked_deaths,boss_id=key)
        active=[key for key,signal in signals.items() if key in enabled and isinstance(signal,dict) and signal.get('boss_id')==key and signal.get('active') is True and signal.get('victory') is False]
        ambiguous=len(active)>1
        self.error='Plusieurs signaux de combat actifs - attribution suspendue' if ambiguous else None
        errors=snap.get('combat_errors')
        errors=errors if isinstance(errors,dict) else {}
        for key,tracker in self.instances.items():
            if key not in enabled:
                if tracker.open is not None:tracker.stop(seconds)
                continue
            local=dict(snap)
            local['combat_signal']=None if ambiguous else signals.get(key)
            local['combat_error']=self.error or errors.get(key)
            if not signals and snap.get('boss_error'):local['combat_error']=snap['boss_error']
            tracker.observe(local,seconds,tracked_deaths)
        if len(active)==1 and not ambiguous:
            key=active[0]
            for other,tracker in self.instances.items():
                if other!=key and tracker.open is not None:tracker.finish('interrupted','different_boss_detected')
            self.selected=key

    def payload(self):
        if self.error or self.selected not in self.instances:return None
        return self.instances[self.selected].payload()

    def merge(self,current):
        for tracker in self.instances.values():tracker.merge(current)

    def stop(self,seconds):
        for tracker in self.instances.values():tracker.stop(seconds)
        self.error=None

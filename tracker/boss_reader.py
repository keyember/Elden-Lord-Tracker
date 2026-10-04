# SPDX-License-Identifier: GPL-3.0-only
"""Generic confirmed boss observations on the existing independent worker."""
import time,threading
from .death_counter import DeathReader
from .character_guard import NameReader
from .boss_flags import locate_flags,flag,FlagBatch
from .boss_catalog import BOSS_IDS,active_bosses
from .combat_registry import supported_specs
from .i18n import tr


class BossReader(DeathReader):
    def __init__(self,expected):
        super().__init__(expected)
        self._boss_stop=threading.Event();self._boss_lock=threading.Lock();self._boss_result=None;self._boss_after=0
        self._boss_thread=threading.Thread(target=self._boss_worker,daemon=True);self._boss_thread.start()
    def _store(self,value):
        with self._boss_lock:self._boss_result=value
    def _boss_worker(self):
        worker=None;pending={};repeats={}
        try:
            worker=NameReader(self.expected);worker.globals['event_flags']=locate_flags(worker)
            while not self._boss_stop.is_set():
                began=time.monotonic()
                try:
                    before=worker.snapshot()
                    if not before['can_count']:
                        self._store(None);pending={};repeats={};self._boss_stop.wait(.25);continue
                    root=worker.ptr(worker.globals['identity_root']);player=worker.ptr(root+8);manager=worker.ptr(worker.globals['event_flags'])
                    batch=FlagBatch(worker,manager,deadline=began+2.0)
                    if batch.get(6000) is not False or batch.get(6001) is not True:raise ValueError(tr('Flags de controle incorrects'))
                    states={key:None for key in BOSS_IDS};errors=[]
                    for boss in active_bosses():
                        if self._boss_stop.is_set():break
                        key=boss['id']
                        try:
                            value=batch.get(boss['flag_id']);repeats[key]=repeats.get(key,0)+1 if pending.get(key) is value else 1;pending[key]=value
                            if repeats[key]>=2:states[key]=value
                        except (OSError,ValueError,KeyError) as exc:
                            pending.pop(key,None);repeats.pop(key,None);errors.append(key+': '+str(exc))
                    signals={};signal_errors={}
                    for spec in supported_specs():
                        key=spec['boss_id'];token='_combat_'+key;signals[key]=None
                        try:
                            value=batch.get(spec['active_flag']);repeats[token]=repeats.get(token,0)+1 if pending.get(token) is value else 1;pending[token]=value
                            victory=states.get(key)
                            if type(value) is bool and type(victory) is bool and repeats[token]>=2:signals[key]=dict(boss_id=key,active=value,victory=victory)
                        except (OSError,ValueError,KeyError) as exc:
                            pending.pop(token,None);repeats.pop(token,None);signal_errors[key]=str(exc)
                    batch.verify()
                    after=worker.snapshot()
                    if worker.ptr(worker.globals['identity_root'])!=root or worker.ptr(root+8)!=player or worker.ptr(worker.globals['event_flags'])!=manager or not after['can_count'] or after.get('observed_character')!=self.expected:
                        self._store(None);pending={};repeats={}
                    else:
                        batch._check()
                        error=(tr('Boss illisibles : ')+'; '.join(errors[:3])+(' ...' if len(errors)>3 else '')) if errors else None
                        self._store(dict(time=began,root=root,player=player,states=states,error=error,combat_signals=signals,combat_errors=signal_errors))
                except (OSError,ValueError,KeyError) as exc:
                    self._store(dict(time=time.monotonic(),error=str(exc),states=None));pending={};repeats={}
                self._boss_stop.wait(max(.05,1-(time.monotonic()-began)))
        except (OSError,ValueError,KeyError) as exc:self._store(dict(time=time.monotonic(),error=str(exc),states=None))
        finally:
            if worker:worker.close()
    def snapshot(self):
        snap=super().snapshot();snap.update(boss_states=None,boss_error=None,combat_signals=None,combat_signal=None,combat_errors={},combat_error=None)
        if not snap['can_count']:
            self._boss_after=time.monotonic();return snap
        with self._boss_lock:value=self._boss_result
        if not value:return snap
        snap['boss_error']=value.get('error')
        if value.get('states') is None or value['time']<self._boss_after or time.monotonic()-value['time']>4:return snap
        try:
            root=self.ptr(self.globals['identity_root'])
            if root!=value['root'] or self.ptr(root+8)!=value['player']:return snap
            snap['boss_states']=dict(value['states']);snap['combat_signals']={key:dict(signal) if isinstance(signal,dict) else None for key,signal in value.get('combat_signals',{}).items()};snap['combat_errors']=dict(value.get('combat_errors',{}))
        except (OSError,ValueError):pass
        return snap
    def close(self):
        if hasattr(self,'_boss_stop'):
            self._boss_stop.set()
            if self._boss_thread is not threading.current_thread():self._boss_thread.join(timeout=2)
        super().close()
# GENERIC_COMBAT_ENGINE_V1


# SCALABLE_CONFIRMED_FLAGS_V1
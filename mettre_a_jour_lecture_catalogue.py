# SPDX-License-Identifier: GPL-3.0-only
"""Lecture evolutive du catalogue existant. Ne fournit pas les associations de combat manquantes."""
import argparse,ast,copy,datetime,hashlib,json,os,struct,sys,tempfile,types,uuid
from pathlib import Path
FLAG_PATH='tracker/boss_flags.py'
READER_PATH='tracker/boss_reader.py'
REGISTRY_PATH='tracker/combat_registry.py'
CONFIG_PATH='tracker/catalogue_data/combat_catalog.json'
CATALOGUE_PATH='tracker/catalogue_data/boss_catalog.json'
TEST_PATH='tests/test_classic_arena_update.py'
UPDATE_ID='scalable_catalogue_reader_v1'
ALLOWED=(FLAG_PATH,READER_PATH,REGISTRY_PATH,TEST_PATH)
FLAGS_OLD="# SPDX-License-Identifier: GPL-3.0-only\n# Lecture adaptee de SoulMemory, Frank van der Stam ; adaptation Python 2026-10-02.\nfrom .i18n import tr, translate_status\nimport struct\n\ndef locate_flags(reader):\n    import re\n\n    def pattern_regex(pattern):\n        return re.compile(b''.join((b'.' if token == '?' else re.escape(bytes([int(token, 16)])) for token in pattern.split())), re.DOTALL)\n    header = reader.read(reader.base, 4096)\n    pe = struct.unpack_from('<I', header, 60)[0]\n    if header[pe:pe + 4] != b'PE\\x00\\x00':\n        raise ValueError('Executable PE invalide')\n    count = struct.unpack_from('<H', header, pe + 6)[0]\n    optional = struct.unpack_from('<H', header, pe + 20)[0]\n    if not 1 <= count <= 128:\n        raise ValueError('Nombre de sections PE incoherent')\n    table = reader.read(reader.base + pe + 24 + optional, count * 40)\n    pattern = pattern_regex('44 89 7c 24 28 4c 8b 25 ? ? ? ? 4d 85 e4')\n    matches = set()\n    for i in range(count):\n        section = table[i * 40:(i + 1) * 40]\n        size, rva = struct.unpack_from('<II', section, 8)\n        flags = struct.unpack_from('<I', section, 36)[0]\n        if not flags & 536870912:\n            continue\n        if rva + size > reader.size:\n            raise ValueError('Section executable incoherente')\n        previous = b''\n        for offset in range(0, size, 1024 * 1024):\n            block = reader.read(reader.base + rva + offset, min(1024 * 1024, size - offset))\n            chunk = previous + block\n            origin = reader.base + rva + offset - len(previous)\n            matches.update((origin + match.start() for match in pattern.finditer(chunk)))\n            previous = chunk[-64:]\n    if len(matches) != 1:\n        raise ValueError(f'Signature complete event_flags : {len(matches)} correspondances, lecture refusee')\n    address = next(iter(matches))\n    instruction = reader.read(address, 12)\n    return address + 12 + struct.unpack_from('<i', instruction, 8)[0]\n\ndef flag(reader, manager, identifier):\n    divisor = reader.integer(manager + 28)\n    if not 1 <= divisor <= 1000000:\n        raise ValueError('Diviseur de flags invalide ou non initialise')\n    category, remainder = divmod(identifier, divisor)\n    header = reader.ptr(manager + 56)\n    node = reader.ptr(header + 8)\n    candidate = header\n    seen = set()\n    for _ in range(128):\n        sentinel = reader.read(node + 25, 1)[0]\n        if sentinel == 1:\n            break\n        if sentinel != 0 or node in seen:\n            raise ValueError('Arbre de flags incoherent')\n        seen.add(node)\n        key = reader.integer(node + 32)\n        if key < category:\n            node = reader.ptr(node + 16)\n        else:\n            candidate = node\n            node = reader.ptr(node)\n    else:\n        raise ValueError('Parcours de flags trop long')\n    if candidate == header or reader.integer(candidate + 32) != category:\n        raise ValueError('Categorie absente : etat inconnu, pas faux')\n    mode = reader.integer(candidate + 40)\n    if mode == 1:\n        stride = reader.integer(manager + 32)\n        index = reader.integer(candidate + 48)\n        if stride <= 0 or index < 0:\n            raise ValueError('Stockage indexe invalide')\n        storage = reader.ptr(manager + 40) + stride * index\n    elif mode == 2:\n        raise ValueError('Categorie sans stockage lisible')\n    else:\n        storage = reader.ptr(candidate + 48)\n    byte = reader.read(storage + (remainder >> 3), 1)[0]\n    return bool(byte & 1 << 7 - (remainder & 7))\n"
FLAGS_NEW="# SPDX-License-Identifier: GPL-3.0-only\n# Lecture adaptee de SoulMemory, Frank van der Stam ; adaptation Python 2026-10-02.\nfrom .i18n import tr, translate_status\nimport struct\n\ndef locate_flags(reader):\n    import re\n\n    def pattern_regex(pattern):\n        return re.compile(b''.join((b'.' if token == '?' else re.escape(bytes([int(token, 16)])) for token in pattern.split())), re.DOTALL)\n    header = reader.read(reader.base, 4096)\n    pe = struct.unpack_from('<I', header, 60)[0]\n    if header[pe:pe + 4] != b'PE\\x00\\x00':\n        raise ValueError('Executable PE invalide')\n    count = struct.unpack_from('<H', header, pe + 6)[0]\n    optional = struct.unpack_from('<H', header, pe + 20)[0]\n    if not 1 <= count <= 128:\n        raise ValueError('Nombre de sections PE incoherent')\n    table = reader.read(reader.base + pe + 24 + optional, count * 40)\n    pattern = pattern_regex('44 89 7c 24 28 4c 8b 25 ? ? ? ? 4d 85 e4')\n    matches = set()\n    for i in range(count):\n        section = table[i * 40:(i + 1) * 40]\n        size, rva = struct.unpack_from('<II', section, 8)\n        flags = struct.unpack_from('<I', section, 36)[0]\n        if not flags & 536870912:\n            continue\n        if rva + size > reader.size:\n            raise ValueError('Section executable incoherente')\n        previous = b''\n        for offset in range(0, size, 1024 * 1024):\n            block = reader.read(reader.base + rva + offset, min(1024 * 1024, size - offset))\n            chunk = previous + block\n            origin = reader.base + rva + offset - len(previous)\n            matches.update((origin + match.start() for match in pattern.finditer(chunk)))\n            previous = chunk[-64:]\n    if len(matches) != 1:\n        raise ValueError(f'Signature complete event_flags : {len(matches)} correspondances, lecture refusee')\n    address = next(iter(matches))\n    instruction = reader.read(address, 12)\n    return address + 12 + struct.unpack_from('<i', instruction, 8)[0]\n\ndef flag(reader, manager, identifier):\n    divisor = reader.integer(manager + 28)\n    if not 1 <= divisor <= 1000000:\n        raise ValueError('Diviseur de flags invalide ou non initialise')\n    category, remainder = divmod(identifier, divisor)\n    header = reader.ptr(manager + 56)\n    node = reader.ptr(header + 8)\n    candidate = header\n    seen = set()\n    for _ in range(128):\n        sentinel = reader.read(node + 25, 1)[0]\n        if sentinel == 1:\n            break\n        if sentinel != 0 or node in seen:\n            raise ValueError('Arbre de flags incoherent')\n        seen.add(node)\n        key = reader.integer(node + 32)\n        if key < category:\n            node = reader.ptr(node + 16)\n        else:\n            candidate = node\n            node = reader.ptr(node)\n    else:\n        raise ValueError('Parcours de flags trop long')\n    if candidate == header or reader.integer(candidate + 32) != category:\n        raise ValueError('Categorie absente : etat inconnu, pas faux')\n    mode = reader.integer(candidate + 40)\n    if mode == 1:\n        stride = reader.integer(manager + 32)\n        index = reader.integer(candidate + 48)\n        if stride <= 0 or index < 0:\n            raise ValueError('Stockage indexe invalide')\n        storage = reader.ptr(manager + 40) + stride * index\n    elif mode == 2:\n        raise ValueError('Categorie sans stockage lisible')\n    else:\n        storage = reader.ptr(candidate + 48)\n    byte = reader.read(storage + (remainder >> 3), 1)[0]\n    return bool(byte & 1 << 7 - (remainder & 7))\n\n# FLAG_BATCH_CYCLE_V1 - caches invalides entre deux cycles.\nimport time as _batch_time\n\nclass FlagBatch:\n    def __init__(self, reader, manager, deadline=None, clock=None):\n        self.reader=reader;self.manager=manager;self.clock=clock or _batch_time.monotonic;self.deadline=deadline\n        self.nodes={};self.groups={};self.bytes={};self.indexed=None\n        self._check()\n        self.divisor=reader.integer(manager+28)\n        if not 1<=self.divisor<=1000000: raise ValueError('Diviseur de flags invalide ou non initialise')\n        self.header=reader.ptr(manager+56);self.root=reader.ptr(self.header+8)\n    def _check(self):\n        if self.deadline is not None and self.clock()>self.deadline: raise ValueError('Cycle de flags trop lent - attribution suspendue')\n    def _node(self, address):\n        self._check()\n        if address not in self.nodes:\n            sentinel=self.reader.read(address+25,1)\n            if len(sentinel)!=1: raise ValueError('Lecture de noeud incomplete')\n            sentinel=sentinel[0]\n            if sentinel not in (0,1): raise ValueError('Arbre de flags incoherent')\n            if sentinel==1: self.nodes[address]=(1,None,None,None)\n            else: self.nodes[address]=(0,self.reader.integer(address+32),self.reader.ptr(address),self.reader.ptr(address+16))\n        return self.nodes[address]\n    def _group(self, category):\n        if category in self.groups: return self.groups[category][0]\n        node=self.root;candidate=self.header;seen=set()\n        for _ in range(128):\n            sentinel,key,left,right=self._node(node)\n            if sentinel==1: break\n            if node in seen: raise ValueError('Arbre de flags incoherent')\n            seen.add(node)\n            if key<category: node=right\n            else: candidate=node;node=left\n        else: raise ValueError('Parcours de flags trop long')\n        if candidate==self.header or self._node(candidate)[1]!=category: raise ValueError('Categorie absente : etat inconnu, pas faux')\n        mode=self.reader.integer(candidate+40)\n        if mode==1:\n            if self.indexed is None:\n                stride=self.reader.integer(self.manager+32);base=self.reader.ptr(self.manager+40)\n                if stride<=0: raise ValueError('Stockage indexe invalide')\n                self.indexed=(stride,base)\n            index=self.reader.integer(candidate+48)\n            if index<0: raise ValueError('Stockage indexe invalide')\n            storage=self.indexed[1]+self.indexed[0]*index;detail=index\n        elif mode==2: raise ValueError('Categorie sans stockage lisible')\n        else: storage=self.reader.ptr(candidate+48);detail=storage\n        self.groups[category]=(storage,candidate,mode,detail)\n        return storage\n    def get(self, identifier):\n        self._check()\n        if type(identifier) is not int or not 0<=identifier<=4294967295: raise ValueError('Identifiant de flag invalide')\n        category,remainder=divmod(identifier,self.divisor);address=self._group(category)+(remainder>>3)\n        if address not in self.bytes:\n            data=self.reader.read(address,1)\n            if len(data)!=1: raise ValueError('Lecture de flag incomplete')\n            self.bytes[address]=data[0]\n        return bool(self.bytes[address] & (1 << (7-(remainder&7))))\n    def verify(self):\n        self._check()\n        r=self.reader\n        if r.integer(self.manager+28)!=self.divisor or r.ptr(self.manager+56)!=self.header or r.ptr(self.header+8)!=self.root:\n            raise ValueError('Structure de flags en transition - attribution suspendue')\n        if self.indexed is not None and (r.integer(self.manager+32),r.ptr(self.manager+40))!=self.indexed:\n            raise ValueError('Stockage de flags en transition - attribution suspendue')\n        for category,(_,node,mode,detail) in self.groups.items():\n            self._check()\n            if r.integer(node+32)!=category or r.integer(node+40)!=mode:\n                raise ValueError('Categorie de flags en transition - attribution suspendue')\n            current=r.integer(node+48) if mode==1 else r.ptr(node+48)\n            if current!=detail: raise ValueError('Stockage de categorie en transition - attribution suspendue')\n        if flag(r,self.manager,6000) is not False or flag(r,self.manager,6001) is not True:\n            raise ValueError('Flags de controle incorrects')\n        self._check()\n"
READER_OLD='# SPDX-License-Identifier: GPL-3.0-only\n"""Generic confirmed boss observations on the existing independent worker."""\nimport time,threading\nfrom .death_counter import DeathReader\nfrom .character_guard import NameReader\nfrom .boss_flags import locate_flags,flag\nfrom .boss_catalog import BOSS_IDS,active_bosses\nfrom .combat_registry import supported_specs\nfrom .i18n import tr\n\nclass BossReader(DeathReader):\n    def __init__(self,expected):\n        super().__init__(expected)\n        self._boss_stop=threading.Event();self._boss_lock=threading.Lock();self._boss_result=None;self._boss_after=0\n        self._boss_thread=threading.Thread(target=self._boss_worker,daemon=True);self._boss_thread.start()\n    def _store(self,value):\n        with self._boss_lock:self._boss_result=value\n    def _boss_worker(self):\n        worker=None;pending={};repeats={}\n        try:\n            worker=NameReader(self.expected);worker.globals[\'event_flags\']=locate_flags(worker)\n            while not self._boss_stop.is_set():\n                began=time.monotonic()\n                try:\n                    before=worker.snapshot()\n                    if not before[\'can_count\']:\n                        self._store(None);pending={};repeats={};self._boss_stop.wait(.25);continue\n                    root=worker.ptr(worker.globals[\'identity_root\']);player=worker.ptr(root+8);manager=worker.ptr(worker.globals[\'event_flags\'])\n                    if flag(worker,manager,6000) is not False or flag(worker,manager,6001) is not True:raise ValueError(tr(\'Flags de controle incorrects\'))\n                    states={key:None for key in BOSS_IDS};errors=[]\n                    for boss in active_bosses():\n                        if self._boss_stop.is_set():break\n                        key=boss[\'id\']\n                        try:\n                            value=flag(worker,manager,boss[\'flag_id\']);repeats[key]=repeats.get(key,0)+1 if pending.get(key) is value else 1;pending[key]=value\n                            if repeats[key]>=2:states[key]=value\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(key,None);repeats.pop(key,None);errors.append(key+\': \'+str(exc))\n                    signals={};signal_errors={}\n                    for spec in supported_specs():\n                        key=spec[\'boss_id\'];token=\'_combat_\'+key;signals[key]=None\n                        try:\n                            value=flag(worker,manager,spec[\'active_flag\']);repeats[token]=repeats.get(token,0)+1 if pending.get(token) is value else 1;pending[token]=value\n                            victory=states.get(key)\n                            if type(value) is bool and type(victory) is bool and repeats[token]>=2:signals[key]=dict(boss_id=key,active=value,victory=victory)\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(token,None);repeats.pop(token,None);signal_errors[key]=str(exc)\n                    after=worker.snapshot()\n                    if worker.ptr(worker.globals[\'identity_root\'])!=root or worker.ptr(root+8)!=player or worker.ptr(worker.globals[\'event_flags\'])!=manager or not after[\'can_count\'] or after.get(\'observed_character\')!=self.expected:\n                        self._store(None);pending={};repeats={}\n                    else:\n                        error=(tr(\'Boss illisibles : \')+\'; \'.join(errors[:3])+(\' ...\' if len(errors)>3 else \'\')) if errors else None\n                        self._store(dict(time=time.monotonic(),root=root,player=player,states=states,error=error,combat_signals=signals,combat_errors=signal_errors))\n                except (OSError,ValueError,KeyError) as exc:\n                    self._store(dict(time=time.monotonic(),error=str(exc),states=None));pending={};repeats={}\n                self._boss_stop.wait(max(.05,1-(time.monotonic()-began)))\n        except (OSError,ValueError,KeyError) as exc:self._store(dict(time=time.monotonic(),error=str(exc),states=None))\n        finally:\n            if worker:worker.close()\n    def snapshot(self):\n        snap=super().snapshot();snap.update(boss_states=None,boss_error=None,combat_signals=None,combat_signal=None,combat_errors={},combat_error=None)\n        if not snap[\'can_count\']:\n            self._boss_after=time.monotonic();return snap\n        with self._boss_lock:value=self._boss_result\n        if not value:return snap\n        snap[\'boss_error\']=value.get(\'error\')\n        if value.get(\'states\') is None or value[\'time\']<self._boss_after or time.monotonic()-value[\'time\']>4:return snap\n        try:\n            root=self.ptr(self.globals[\'identity_root\'])\n            if root!=value[\'root\'] or self.ptr(root+8)!=value[\'player\']:return snap\n            snap[\'boss_states\']=dict(value[\'states\']);snap[\'combat_signals\']={key:dict(signal) if isinstance(signal,dict) else None for key,signal in value.get(\'combat_signals\',{}).items()};snap[\'combat_errors\']=dict(value.get(\'combat_errors\',{}))\n        except (OSError,ValueError):pass\n        return snap\n    def close(self):\n        if hasattr(self,\'_boss_stop\'):\n            self._boss_stop.set()\n            if self._boss_thread is not threading.current_thread():self._boss_thread.join(timeout=2)\n        super().close()\n# GENERIC_COMBAT_ENGINE_V1\n'
READER_NEW='# SPDX-License-Identifier: GPL-3.0-only\n"""Generic confirmed boss observations on the existing independent worker."""\nimport time,threading\nfrom .death_counter import DeathReader\nfrom .character_guard import NameReader\nfrom .boss_flags import locate_flags,flag,FlagBatch\nfrom .boss_catalog import BOSS_IDS,active_bosses\nfrom .combat_registry import supported_specs\nfrom .i18n import tr\n\nclass BossReader(DeathReader):\n    def __init__(self,expected):\n        super().__init__(expected)\n        self._boss_stop=threading.Event();self._boss_lock=threading.Lock();self._boss_result=None;self._boss_after=0\n        self._boss_thread=threading.Thread(target=self._boss_worker,daemon=True);self._boss_thread.start()\n    def _store(self,value):\n        with self._boss_lock:self._boss_result=value\n    def _boss_worker(self):\n        worker=None;pending={};repeats={}\n        try:\n            worker=NameReader(self.expected);worker.globals[\'event_flags\']=locate_flags(worker)\n            while not self._boss_stop.is_set():\n                began=time.monotonic()\n                try:\n                    before=worker.snapshot()\n                    if not before[\'can_count\']:\n                        self._store(None);pending={};repeats={};self._boss_stop.wait(.25);continue\n                    root=worker.ptr(worker.globals[\'identity_root\']);player=worker.ptr(root+8);manager=worker.ptr(worker.globals[\'event_flags\'])\n                    batch=FlagBatch(worker,manager,deadline=began+2.0)\n                    if batch.get(6000) is not False or batch.get(6001) is not True:raise ValueError(tr(\'Flags de controle incorrects\'))\n                    states={key:None for key in BOSS_IDS};errors=[]\n                    for boss in active_bosses():\n                        if self._boss_stop.is_set():break\n                        key=boss[\'id\']\n                        try:\n                            value=batch.get(boss[\'flag_id\']);repeats[key]=repeats.get(key,0)+1 if pending.get(key) is value else 1;pending[key]=value\n                            if repeats[key]>=2:states[key]=value\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(key,None);repeats.pop(key,None);errors.append(key+\': \'+str(exc))\n                    signals={};signal_errors={}\n                    for spec in supported_specs():\n                        key=spec[\'boss_id\'];token=\'_combat_\'+key;signals[key]=None\n                        try:\n                            value=batch.get(spec[\'active_flag\']);repeats[token]=repeats.get(token,0)+1 if pending.get(token) is value else 1;pending[token]=value\n                            victory=states.get(key)\n                            if type(value) is bool and type(victory) is bool and repeats[token]>=2:signals[key]=dict(boss_id=key,active=value,victory=victory)\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(token,None);repeats.pop(token,None);signal_errors[key]=str(exc)\n                    batch.verify()\n                    after=worker.snapshot()\n                    if worker.ptr(worker.globals[\'identity_root\'])!=root or worker.ptr(root+8)!=player or worker.ptr(worker.globals[\'event_flags\'])!=manager or not after[\'can_count\'] or after.get(\'observed_character\')!=self.expected:\n                        self._store(None);pending={};repeats={}\n                    else:\n                        batch._check()\n                        error=(tr(\'Boss illisibles : \')+\'; \'.join(errors[:3])+(\' ...\' if len(errors)>3 else \'\')) if errors else None\n                        self._store(dict(time=began,root=root,player=player,states=states,error=error,combat_signals=signals,combat_errors=signal_errors))\n                except (OSError,ValueError,KeyError) as exc:\n                    self._store(dict(time=time.monotonic(),error=str(exc),states=None));pending={};repeats={}\n                self._boss_stop.wait(max(.05,1-(time.monotonic()-began)))\n        except (OSError,ValueError,KeyError) as exc:self._store(dict(time=time.monotonic(),error=str(exc),states=None))\n        finally:\n            if worker:worker.close()\n    def snapshot(self):\n        snap=super().snapshot();snap.update(boss_states=None,boss_error=None,combat_signals=None,combat_signal=None,combat_errors={},combat_error=None)\n        if not snap[\'can_count\']:\n            self._boss_after=time.monotonic();return snap\n        with self._boss_lock:value=self._boss_result\n        if not value:return snap\n        snap[\'boss_error\']=value.get(\'error\')\n        if value.get(\'states\') is None or value[\'time\']<self._boss_after or time.monotonic()-value[\'time\']>4:return snap\n        try:\n            root=self.ptr(self.globals[\'identity_root\'])\n            if root!=value[\'root\'] or self.ptr(root+8)!=value[\'player\']:return snap\n            snap[\'boss_states\']=dict(value[\'states\']);snap[\'combat_signals\']={key:dict(signal) if isinstance(signal,dict) else None for key,signal in value.get(\'combat_signals\',{}).items()};snap[\'combat_errors\']=dict(value.get(\'combat_errors\',{}))\n        except (OSError,ValueError):pass\n        return snap\n    def close(self):\n        if hasattr(self,\'_boss_stop\'):\n            self._boss_stop.set()\n            if self._boss_thread is not threading.current_thread():self._boss_thread.join(timeout=2)\n        super().close()\n# GENERIC_COMBAT_ENGINE_V1\n\n# SCALABLE_CONFIRMED_FLAGS_V1\n'
READ_CONFIGURATION_REFERENCE="def read_configuration():\n    try:\n        doc=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))\n        if not isinstance(doc,dict) or doc.get('schema_version')!=1 or not isinstance(doc.get('encounters'),dict):raise ValueError('Configuration invalide')\n        entries=doc['encounters'];seen={};enabled=0\n        for key,item in entries.items():\n            if key not in BY_ID or not isinstance(item,dict):raise ValueError('Rencontre inconnue')\n            level=item.get('validation');active=item.get('active_flag')\n            if level not in ('not_configured','candidate','documented','user_tested'):raise ValueError('Validation invalide')\n            if active is not None and (type(active) is not int or not 0<=active<=4294967295 or active==BY_ID[key]['flag_id']):raise ValueError('Flag invalide')\n            if level=='documented':\n                reference=SOURCE_BANK.get(str(BY_ID[key]['flag_id']))\n                source=item.get('source',{})\n                if not reference or active!=reference['active_flag'] or not isinstance(source,dict) or any(source.get(field)!=reference[field] for field in ('repository','revision','path','event','parameter')):raise ValueError('Association documentee sans provenance correspondante')\n            if level in ENABLED_LEVELS and item.get('enabled',True) is not False:\n                if active is None:raise ValueError('Flag de combat manquant')\n                if active in seen and seen[active]!=key:raise ValueError('Flag actif partage : attribution ambigue')\n                seen[active]=key;enabled+=1\n        if enabled>32:raise ValueError('Plus de 32 suivis actifs : extension a valider avant activation')\n        return entries,None\n    except (OSError,ValueError,TypeError):\n        import sys\n        return {},str(sys.exc_info()[1])\n"
LEGACY_TEST="def test_32_guard_remains(self):\n    for index in range(21):\n        key='synthetic_'+str(index)\n        self.registry.BY_ID[key]=dict(id=key,flag_id=800000+index)\n        self.config['encounters'][key]=dict(active_flag=900000+index,validation='user_tested')\n    self.save()\n    self.assertIn('32',self.registry.read_configuration()[1])\n"
NEW_CAP_TEST="def test_catalogue_capacity_guard(self):\n    for index in range(208):\n        key='synthetic_'+str(index)\n        self.registry.BY_ID[key]=dict(id=key,flag_id=800000+index)\n        self.config['encounters'][key]=dict(active_flag=900000+index,validation='user_tested')\n    self.save()\n    self.assertIn('catalogue',self.registry.read_configuration()[1])\n"
SYNTHETIC_BENCHMARK={'logical_flags': 416, 'baseline_memory_reads': 15823, 'batched_memory_reads_including_checks': 5079, 'reduction_percent': 67.9, 'synthetic_only': True}

def digest(data):return hashlib.sha256(data).hexdigest()
def git_blob(text):
    data=text.encode();return hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()
def safe_path(root,relative):
    path=root/relative
    if not path.resolve().is_relative_to(root):raise ValueError('Chemin hors projet: '+relative)
    current=path
    while current!=root:
        if current.is_symlink():raise ValueError('Chemin symbolique refuse: '+relative)
        current=current.parent
    return path

def segment_replace(text,node,replacement):
    lines=text.splitlines(keepends=True);data=text.encode('utf-8')
    start=sum(len(s.encode()) for s in lines[:node.lineno-1])+node.col_offset
    end=sum(len(s.encode()) for s in lines[:node.end_lineno-1])+node.end_col_offset
    return (data[:start]+replacement.encode()+data[end:]).decode('utf-8')

def patch_registry(text):
    tree=ast.parse(text)
    if not any(isinstance(n,ast.ImportFrom) and n.module=='boss_catalog' and any(a.name=='BOSSES' for a in n.names) for n in tree.body):raise ValueError('Import BOSSES du registre non reconnu')
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read_configuration']
    if len(functions)!=1:raise ValueError('Validateur du registre non reconnu')
    function=functions[0];checks=[n for n in ast.walk(function) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='enabled'
                                and len(n.test.ops)==1 and isinstance(n.test.ops[0],ast.Gt)]
    if len(checks)!=1:raise ValueError('Garde de capacite non reconnu')
    check=checks[0];original_check=next(n for n in ast.walk(ast.parse(READ_CONFIGURATION_REFERENCE)) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='enabled')
    current_rhs=ast.dump(check.test.comparators[0],include_attributes=False)
    if current_rhs not in (ast.dump(ast.Constant(32),include_attributes=False),ast.dump(ast.parse('len(BOSSES)',mode='eval').body,include_attributes=False)):
        raise ValueError('Capacite modifiee autrement - mise a jour refusee')
    clone=copy.deepcopy(function)
    clone_check=next(n for n in ast.walk(clone) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='enabled')
    clone_check.test=copy.deepcopy(original_check.test);clone_check.body=copy.deepcopy(original_check.body)
    reference=ast.parse(READ_CONFIGURATION_REFERENCE).body[0]
    if ast.dump(clone,include_attributes=False)!=ast.dump(reference,include_attributes=False):raise ValueError('Regles du registre non reconnues - aucune ecriture')
    new="if enabled>len(BOSSES):raise ValueError('Suivis actifs au dela du catalogue : configuration refusee')"
    result=segment_replace(text,check,new);compile(result,REGISTRY_PATH,'exec');return result

def patch_legacy_test(text):
    tree=ast.parse(text);methods=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_32_guard_remains']
    if not methods:return text
    if len(methods)!=1 or ast.dump(methods[0],include_attributes=False)!=ast.dump(ast.parse(LEGACY_TEST).body[0],include_attributes=False):
        raise ValueError('Ancien test de capacite non reconnu - modification automatique refusee')
    node=methods[0];indent=' '*node.col_offset
    replacement=NEW_CAP_TEST.strip().replace('\n','\n'+indent)
    result=segment_replace(text,node,replacement);compile(result,TEST_PATH,'exec');return result

def check_configuration(root,registry_text):
    catalog=json.loads(safe_path(root,CATALOGUE_PATH).read_text(encoding='utf-8-sig'))
    config=json.loads(safe_path(root,CONFIG_PATH).read_text(encoding='utf-8-sig'))
    if not isinstance(catalog,list) or len(catalog)!=207:raise ValueError('Catalogue de 207 rencontres requis')
    by_id={b['id']:b for b in catalog}
    if len(by_id)!=207 or len({b['flag_id'] for b in catalog})!=207:raise ValueError('Identifiants du catalogue incoherents')
    if any(type(b['flag_id']) is not int for b in catalog):raise ValueError('Flags de victoire invalides')
    if not isinstance(config,dict) or config.get('schema_version')!=1 or set(config.get('encounters',{}))!=set(by_id):raise ValueError('Configuration incompatible avec le catalogue')
    tree=ast.parse(registry_text)
    bank_nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE_BANK' for t in n.targets)]
    if len(bank_nodes)!=1:raise ValueError('SOURCE_BANK invalide')
    bank=ast.literal_eval(bank_nodes[0].value)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read_configuration')
    module=ast.Module(body=[copy.deepcopy(function)],type_ignores=[]);ast.fix_missing_locations(module)
    env=dict(json=json,CONFIG_PATH=safe_path(root,CONFIG_PATH),BY_ID=by_id,BOSSES=tuple(catalog),SOURCE_BANK=bank,ENABLED_LEVELS=frozenset({'documented','user_tested'}))
    exec(compile(module,REGISTRY_PATH,'exec'),env)
    entries,error=env['read_configuration']()
    if error:raise ValueError(error)
    configured=[k for k,v in entries.items() if v['validation'] in ('documented','user_tested')]
    active=[k for k in configured if entries[k].get('enabled',True) is not False]
    return dict(catalogue_total=207,configured=len(configured),active=len(active),unconfigured=207-len(configured),
                complete_combat_coverage=len(configured)==207,associations_added=0,synthetic_benchmark=SYNTHETIC_BENCHMARK)

def prepare(root):
    if not (root/'main.py').is_file():raise ValueError('Placer le PY et le BAT a cote de main.py')
    originals={p:safe_path(root,p).read_bytes() for p in (FLAG_PATH,READER_PATH,REGISTRY_PATH,CONFIG_PATH,CATALOGUE_PATH)}
    if originals[FLAG_PATH].decode('utf-8') not in (FLAGS_OLD,FLAGS_NEW):raise ValueError('Version de boss_flags.py non reconnue - mise a jour refusee')
    if originals[READER_PATH].decode('utf-8') not in (READER_OLD,READER_NEW):raise ValueError('Version de boss_reader.py non reconnue - mise a jour refusee')
    registry=patch_registry(originals[REGISTRY_PATH].decode('utf-8'))
    prepared={FLAG_PATH:FLAGS_NEW.encode(),READER_PATH:READER_NEW.encode(),REGISTRY_PATH:registry.encode()}
    test_path=safe_path(root,TEST_PATH)
    if test_path.exists():
        originals[TEST_PATH]=test_path.read_bytes();prepared[TEST_PATH]=patch_legacy_test(originals[TEST_PATH].decode('utf-8')).encode()
    summary=check_configuration(root,registry)
    for p,data in prepared.items():compile(data.decode('utf-8'),p,'exec')
    safe_path(root,'sauvegardes_updates')
    return originals,prepared,summary

def atomic_write(path,data):
    temporary=path.with_name(path.name+'.catalogue-'+uuid.uuid4().hex+'.tmp')
    try:
        with open(temporary,'xb') as file:file.write(data);file.flush();os.fsync(file.fileno())
        os.replace(temporary,path)
    finally:
        if temporary.exists():temporary.unlink()

def commit(root,prepared,summary):
    changed={p:data for p,data in prepared.items() if safe_path(root,p).read_bytes()!=data}
    if not changed:return None
    before={p:(root/p).read_bytes() for p in changed};base=safe_path(root,'sauvegardes_updates');base.mkdir(exist_ok=True)
    backup=base/(datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]+'_lecture_catalogue');backup.mkdir()
    manifest=dict(update=UPDATE_ID,state='prepared',files={p:dict(before=digest(before[p]),after=digest(data)) for p,data in changed.items()},summary=summary)
    for p,data in before.items():path=backup/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    manifest_path=backup/'manifest.json';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    try:
        if any((root/p).read_bytes()!=data for p,data in before.items()):raise ValueError('Base modifiee avant ecriture')
        for p,data in changed.items():atomic_write(root/p,data)
        if any((root/p).read_bytes()!=data for p,data in changed.items()):raise ValueError('Verification apres ecriture echouee')
        manifest['state']='applied';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    except BaseException:
        try:
            for p,data in before.items():atomic_write(root/p,data)
            manifest['state']='rolled_back';atomic_write(manifest_path,json.dumps(manifest,ensure_ascii=False,indent=2).encode())
        except BaseException:pass
        raise
    return backup

def restore(root):
    base=safe_path(root,'sauvegardes_updates');found=[]
    if base.exists():
        for p in base.glob('*/manifest.json'):
            try:
                doc=json.loads(p.read_text(encoding='utf-8'))
                if doc.get('update')==UPDATE_ID and doc.get('state') in ('prepared','applied'):found.append((p.parent,doc))
            except (ValueError,OSError):pass
    if not found:raise ValueError('Aucune sauvegarde de cette mise a jour a restaurer')
    backup,manifest=sorted(found,key=lambda item:item[0].name)[-1]
    if not manifest.get('files') or not set(manifest['files'])<=set(ALLOWED):raise ValueError('Manifest invalide')
    before={};current={}
    for p,h in manifest['files'].items():
        before[p]=(backup/p).read_bytes();current[p]=safe_path(root,p).read_bytes()
        if digest(before[p])!=h['before']:raise ValueError('Sauvegarde corrompue')
        if digest(current[p]) not in (h['before'],h['after']):raise ValueError('Fichier modifie depuis cette update - restauration refusee: '+p)
    if input('Fermer le tracker, puis taper RESTAURER pour revenir au lecteur precedent: ').strip()!='RESTAURER':return
    if any((root/p).read_bytes()!=data for p,data in current.items()):raise ValueError('Modification pendant la confirmation')
    try:
        for p,data in before.items():atomic_write(root/p,data)
    except BaseException:
        for p,data in current.items():atomic_write(root/p,data)
        raise
    manifest['state']='restored';atomic_write(backup/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode())
    print('Restauration terminee. Configurations, profils et historiques non touches.')

def apply(root,dry=False):
    originals,prepared,summary=prepare(root)
    print('Capacite du lecteur: toutes les '+str(summary['catalogue_total'])+' rencontres configurees, sans groupes de 32.')
    print('Associations presentes: '+str(summary['configured'])+' - actives: '+str(summary['active'])+' - encore non configurees: '+str(summary['unconfigured']))
    print('Aucune association ajoutee par cette update. Elle ne fournit pas les signaux manquants.')
    print('Caches limites a un cycle, confirmations conservees, refus des cycles depassant 2 secondes.')
    if dry:print('Apercu uniquement - aucun fichier modifie.');return
    if all((root/p).read_bytes()==data for p,data in prepared.items()):print('Deja applique - aucune ecriture.');return
    if input('Fermer le tracker, puis taper APPLIQUER: ').strip()!='APPLIQUER':print('Annule.');return
    if any((root/p).read_bytes()!=data for p,data in originals.items()):raise ValueError('La base a change pendant la preparation')
    backup=commit(root,prepared,summary);print('Lecteur mis a jour. Sauvegarde: '+backup.name)

FAKE_MEMORY_SOURCE="class FakeMemory:\n    def __init__(self,categories=None,mode=0):\n        self.data={};self.calls=0;self.manager=0x100000;self.header=0x200000;self.node_by_cat={};self.storage_by_cat={}\n        categories=sorted(set(categories or [6,10,11,12]))\n        self.put(self.manager+28,struct.pack('<i',1000));self.put(self.manager+32,struct.pack('<i',125));self.put(self.manager+40,struct.pack('<Q',0x1000000));self.put(self.manager+56,struct.pack('<Q',self.header));self.put(self.header+25,b'\\1')\n        for index,cat in enumerate(categories):\n            node=0x300000+index*64;storage=0x1000000+index*125;self.node_by_cat[cat]=node;self.storage_by_cat[cat]=storage\n            self.put(node+25,b'\\0');self.put(node+32,struct.pack('<i',cat));self.put(node+40,struct.pack('<i',mode));self.put(node+48,struct.pack('<i',index) if mode==1 else struct.pack('<Q',storage));self.put(storage,bytes(125))\n        def build(values):\n            if not values:return self.header\n            mid=len(values)//2;node=self.node_by_cat[values[mid]];self.put(node,struct.pack('<Q',build(values[:mid])));self.put(node+16,struct.pack('<Q',build(values[mid+1:])));return node\n        self.put(self.header+8,struct.pack('<Q',build(categories)));self.set_flag(6001,True)\n    def put(self,address,data):\n        for index,value in enumerate(data):self.data[address+index]=value\n    def read(self,address,size):\n        self.calls+=1\n        try:return bytes(self.data[address+i] for i in range(size))\n        except KeyError:raise OSError('unmapped synthetic memory')\n    def ptr(self,address):return struct.unpack('<Q',self.read(address,8))[0]\n    def integer(self,address):return struct.unpack('<i',self.read(address,4))[0]\n    def set_flag(self,identifier,value):\n        cat,remainder=divmod(identifier,1000);address=self.storage_by_cat[cat]+(remainder>>3);mask=1<<(7-(remainder&7));byte=self.data[address]\n        self.put(address,bytes([(byte|mask) if value else (byte&~mask)]))\n"


def self_test():
    import unittest,random,threading
    from unittest.mock import patch
    scope={'struct':struct};exec(FAKE_MEMORY_SOURCE,scope);FakeMemory=scope['FakeMemory']
    def load_flags():
        prefix='_scalable_flags_test';p=types.ModuleType(prefix);p.__path__=[];i=types.ModuleType(prefix+'.i18n');i.tr=lambda text,*_:text;i.translate_status=lambda text,*_:text
        m=types.ModuleType(prefix+'.boss_flags');m.__package__=prefix
        with patch.dict(sys.modules,{prefix:p,i.__name__:i}):exec(compile(FLAGS_NEW,FLAG_PATH,'exec'),m.__dict__)
        return m
    flags=load_flags()
    def fixture(root,count=25):
        catalog=[dict(id='boss_'+str(n),flag_id=100000+n,names={'fr':'Boss '+str(n),'en':'Boss'},places={'fr':'Place','en':'Place'},content='base_game') for n in range(207)]
        config=dict(schema_version=1,encounters={b['id']:dict(active_flag=200000+n if n<count else None,validation='user_tested' if n<count else 'not_configured',enabled=True) for n,b in enumerate(catalog)})
        registry='import json\nfrom pathlib import Path\nfrom .boss_catalog import BOSSES,BY_ID\nCONFIG_PATH=Path(__file__).resolve().parent/"catalogue_data/combat_catalog.json"\nSOURCE_BANK={}\nENABLED_LEVELS=frozenset({"documented","user_tested"})\n'+READ_CONFIGURATION_REFERENCE
        files={FLAG_PATH:FLAGS_OLD.encode(),READER_PATH:READER_OLD.encode(),REGISTRY_PATH:registry.encode(),CONFIG_PATH:json.dumps(config).encode(),CATALOGUE_PATH:json.dumps(catalog).encode(),'main.py':b'keep launcher','overlay/style.css':b'keep overlay','profiles/history.json':b'keep history','settings.json':b'keep settings',TEST_PATH:('class Tests:\n    '+LEGACY_TEST.strip().replace('\n','\n    ')+'\n').encode()}
        for p,data in files.items():dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        return catalog,config
    class FlagTests(unittest.TestCase):
        def test_original_flags_fingerprint(self):self.assertEqual(git_blob(FLAGS_OLD),'6299f27ee2a62a79d01aabf91a07a2c79fea00f1')
        def test_original_reader_fingerprint(self):self.assertEqual(git_blob(READER_OLD),'a04a93a9da37cd63de8af228aadf148fc07f1a18')
        def test_direct_storage_parity(self):
            memory=FakeMemory();memory.set_flag(10800,True);batch=flags.FlagBatch(memory,memory.manager)
            for identifier in (6000,6001,10800,11805):self.assertEqual(batch.get(identifier),flags.flag(memory,memory.manager,identifier))
            batch.verify()
        def test_indexed_storage_parity(self):
            memory=FakeMemory(mode=1);memory.set_flag(10800,True);batch=flags.FlagBatch(memory,memory.manager)
            for identifier in (6000,6001,10800,11805):self.assertEqual(batch.get(identifier),flags.flag(memory,memory.manager,identifier))
            batch.verify()
        def test_bit_order_all_bits(self):
            memory=FakeMemory();memory.put(memory.storage_by_cat[10],b'\xa5');batch=flags.FlagBatch(memory,memory.manager)
            self.assertEqual([batch.get(10000+i) for i in range(8)],[True,False,True,False,False,True,False,True])
        def test_shared_byte_one_read_per_cycle(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager);batch.get(6000);before=memory.calls;batch.get(6001);self.assertEqual(memory.calls,before)
        def test_no_cache_between_cycles(self):
            memory=FakeMemory();one=flags.FlagBatch(memory,memory.manager);self.assertFalse(one.get(10800));memory.set_flag(10800,True)
            self.assertTrue(flags.FlagBatch(memory,memory.manager).get(10800))
        def test_unknown_category_is_not_false(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager)
            with self.assertRaises(ValueError):batch.get(99900800)
        def test_unreadable_storage_refused(self):
            memory=FakeMemory();memory.put(memory.node_by_cat[10]+40,struct.pack('<i',2))
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager).get(10800)
        def test_invalid_divisor_refused(self):
            memory=FakeMemory();memory.put(memory.manager+28,struct.pack('<i',0))
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager)
        def test_invalid_identifier_refused(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager)
            for value in (True,-1,4294967296,'10800'):
                with self.assertRaises(ValueError):batch.get(value)
        def test_bad_sentinel_refused(self):
            memory=FakeMemory();root=memory.ptr(memory.header+8);memory.put(root+25,b'\3')
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager).get(10800)
        def test_tree_cycle_refused(self):
            memory=FakeMemory();root=memory.ptr(memory.header+8);memory.put(root,struct.pack('<Q',root))
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager).get(6000)
        def test_negative_index_refused(self):
            memory=FakeMemory(mode=1);memory.put(memory.node_by_cat[10]+48,struct.pack('<i',-1))
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager).get(10800)
        def test_zero_stride_refused(self):
            memory=FakeMemory(mode=1);memory.put(memory.manager+32,struct.pack('<i',0))
            with self.assertRaises(ValueError):flags.FlagBatch(memory,memory.manager).get(10800)
        def test_changed_root_refused(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager);batch.get(10800);memory.put(memory.header+8,struct.pack('<Q',memory.header))
            with self.assertRaises(ValueError):batch.verify()
        def test_changed_storage_refused(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager);batch.get(10800);memory.put(memory.node_by_cat[10]+48,struct.pack('<Q',12345678))
            with self.assertRaises(ValueError):batch.verify()
        def test_changed_category_refused(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager);batch.get(10800);memory.put(memory.node_by_cat[10]+32,struct.pack('<i',14))
            with self.assertRaises(ValueError):batch.verify()
        def test_changed_indexed_base_refused(self):
            memory=FakeMemory(mode=1);batch=flags.FlagBatch(memory,memory.manager);batch.get(10800);memory.put(memory.manager+40,struct.pack('<Q',0x1100000))
            with self.assertRaises(ValueError):batch.verify()
        def test_control_flags_rechecked_without_cache(self):
            memory=FakeMemory();batch=flags.FlagBatch(memory,memory.manager);batch.get(6001);memory.set_flag(6001,False)
            with self.assertRaises(ValueError):batch.verify()
        def test_deadline_refused(self):
            memory=FakeMemory();now=[0];batch=flags.FlagBatch(memory,memory.manager,deadline=2,clock=lambda:now[0]);now[0]=3
            with self.assertRaises(ValueError):batch.get(10800)
        def test_verification_deadline_refused(self):
            memory=FakeMemory();now=[0];batch=flags.FlagBatch(memory,memory.manager,deadline=2,clock=lambda:now[0]);batch.get(10800);now[0]=3
            with self.assertRaises(ValueError):batch.verify()
        def test_load_207_victories_207_combats(self):
            memory=FakeMemory([6]+list(range(10000,11024)));ids=[6000,6001]+[(10000+i*3)*1000+800 for i in range(207)]+[(10002+i*3)*1000+805 for i in range(207)]
            rng=random.Random(207)
            for identifier in ids[2:]:memory.set_flag(identifier,rng.choice([True,False]))
            memory.calls=0;old=[flags.flag(memory,memory.manager,v) for v in ids];baseline=memory.calls
            memory.calls=0;batch=flags.FlagBatch(memory,memory.manager);new=[batch.get(v) for v in ids];batch.verify()
            self.assertEqual(old,new);self.assertLess(memory.calls,baseline);self.assertEqual((baseline,memory.calls),(15823,5079))
    class InstallerTests(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.catalog,self.config=fixture(self.root)
        def test_207_configured_accepted(self):
            fixture(self.root,207);_,_,s=prepare(self.root);self.assertEqual(s['active'],207)
        def test_25_associations_remain_25(self):
            _,_,s=prepare(self.root);self.assertEqual((s['configured'],s['unconfigured'],s['associations_added']),(25,182,0));self.assertFalse(s['complete_combat_coverage'])
        def test_no_configuration_edit(self):
            before=(self.root/CONFIG_PATH).read_bytes();_,files,s=prepare(self.root);commit(self.root,files,s);self.assertEqual((self.root/CONFIG_PATH).read_bytes(),before)
        def test_manual_disables_preserved(self):
            self.config['encounters']['boss_0']['enabled']=False;(self.root/CONFIG_PATH).write_text(json.dumps(self.config));_,_,s=prepare(self.root);self.assertEqual(s['active'],24)
        def test_unknown_reader_refused(self):
            (self.root/READER_PATH).write_bytes(b'changed by user')
            with self.assertRaises(ValueError):prepare(self.root)
        def test_unknown_flags_refused(self):
            (self.root/FLAG_PATH).write_bytes(b'changed by user')
            with self.assertRaises(ValueError):prepare(self.root)
        def test_changed_registry_rules_refused(self):
            text=(self.root/REGISTRY_PATH).read_text().replace('0<=active<=4294967295','0<=active<=999')
            with self.assertRaises(ValueError):patch_registry(text)
        def test_missing_provenance_still_refused(self):
            self.config['encounters']['boss_0']['validation']='documented';(self.root/CONFIG_PATH).write_text(json.dumps(self.config))
            with self.assertRaises(ValueError):prepare(self.root)
        def test_duplicate_active_still_refused(self):
            self.config['encounters']['boss_1']['active_flag']=self.config['encounters']['boss_0']['active_flag'];(self.root/CONFIG_PATH).write_text(json.dumps(self.config))
            with self.assertRaises(ValueError):prepare(self.root)
        def test_incompatible_catalogue_refused(self):
            (self.root/CATALOGUE_PATH).write_text(json.dumps(self.catalog[:-1]))
            with self.assertRaises(ValueError):prepare(self.root)
        def test_capacity_test_migrated(self):
            _,files,_=prepare(self.root);text=files[TEST_PATH].decode();self.assertIn('test_catalogue_capacity_guard',text);self.assertIn('208',text);self.assertNotIn('test_32_guard_remains',text)
        def test_unknown_legacy_test_refused(self):
            text=LEGACY_TEST.replace('range(21)','range(23)')
            with self.assertRaises(ValueError):patch_legacy_test(text)
        def test_idempotent_preparation(self):
            _,files,s=prepare(self.root);commit(self.root,files,s);_,again,_=prepare(self.root);self.assertEqual(again,files)
        def test_backup_exact_bytes(self):
            _,files,s=prepare(self.root);old={p:(self.root/p).read_bytes() for p in files};backup=commit(self.root,files,s)
            for p,data in old.items():self.assertEqual((backup/p).read_bytes(),data)
        def test_no_extra_backup_on_repeat(self):
            _,files,s=prepare(self.root);commit(self.root,files,s);self.assertIsNone(commit(self.root,files,s));self.assertEqual(len(list((self.root/'sauvegardes_updates').iterdir())),1)
        def test_histories_overlay_settings_unchanged(self):
            old={p:(self.root/p).read_bytes() for p in ('profiles/history.json','overlay/style.css','settings.json',CATALOGUE_PATH,CONFIG_PATH)}
            _,files,s=prepare(self.root);commit(self.root,files,s)
            for p,data in old.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_restore_exact(self):
            _,files,s=prepare(self.root);old={p:(self.root/p).read_bytes() for p in files};commit(self.root,files,s)
            with patch('builtins.input',return_value='RESTAURER'),patch('builtins.print'):restore(self.root)
            for p,data in old.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_restore_subsequent_edit_refused(self):
            _,files,s=prepare(self.root);commit(self.root,files,s);(self.root/READER_PATH).write_bytes(b'changed later')
            with self.assertRaises(ValueError):restore(self.root)
        def test_restore_corrupt_backup_refused(self):
            _,files,s=prepare(self.root);backup=commit(self.root,files,s);(backup/FLAG_PATH).write_bytes(b'corrupt')
            with self.assertRaises(ValueError):restore(self.root)
        def test_write_failure_rolls_back(self):
            _,files,s=prepare(self.root);old={p:(self.root/p).read_bytes() for p in files};real=atomic_write;counter=[0]
            def failing(path,data):
                counter[0]+=1
                if counter[0]==3:raise OSError('synthetic disk failure')
                return real(path,data)
            with patch(__name__+'.atomic_write',side_effect=failing):
                with self.assertRaises(OSError):commit(self.root,files,s)
            for p,data in old.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_preview_no_write(self):
            before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
            with patch('builtins.print'):apply(self.root,dry=True)
            self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        def test_cancel_no_write(self):
            before=(self.root/READER_PATH).read_bytes()
            with patch('builtins.input',return_value='NON'),patch('builtins.print'):apply(self.root)
            self.assertEqual((self.root/READER_PATH).read_bytes(),before)
        def test_menu_apply(self):
            with patch('sys.argv',['update','--root',str(self.root)]),patch('builtins.input',side_effect=['1','APPLIQUER']),patch('builtins.print'):main()
            self.assertEqual((self.root/READER_PATH).read_text(),READER_NEW);self.assertFalse((self.root/'.elt_lecture_catalogue.lock').exists())
    class WorkerTests(unittest.TestCase):
        def run_worker(self,cycles=2,after_hook=None,wait_hook=None,n=207):
            catalog=[dict(id='boss_'+str(i),flag_id=(10000+i*3)*1000+800) for i in range(n)]
            specs=[dict(boss_id=b['id'],active_flag=(10002+i*3)*1000+805) for i,b in enumerate(catalog)]
            memory=FakeMemory([6]+list(range(10000,11024)));clock=[0.0];memory.globals={'identity_root':0x510000}
            memory.put(0x510000,struct.pack('<Q',0x800000));memory.put(0x800008,struct.pack('<Q',0x810000));memory.put(0x500000,struct.pack('<Q',memory.manager));memory.snap_count=0;memory.closed=False
            def snapshot():
                memory.snap_count+=1
                if after_hook:after_hook(memory,memory.snap_count,clock)
                return dict(can_count=True,observed_character='Test')
            memory.snapshot=snapshot;memory.close=lambda:setattr(memory,'closed',True)
            class Stop:
                done=0
                def is_set(self):return self.done>=cycles
                def wait(self,seconds):
                    self.done+=1;clock[0]+=seconds
                    if wait_hook:wait_hook(memory,self.done,clock)
            prefix='_worker_'+uuid.uuid4().hex;p=types.ModuleType(prefix);p.__path__=[]
            f=types.ModuleType(prefix+'.boss_flags');f.__package__=prefix;f.__dict__.update(flags.__dict__);f.locate_flags=lambda reader:0x500000
            c=types.ModuleType(prefix+'.boss_catalog');c.BOSS_IDS=tuple(b['id'] for b in catalog);c.active_bosses=lambda:tuple(catalog)
            r=types.ModuleType(prefix+'.combat_registry');r.supported_specs=lambda:tuple(specs)
            d=types.ModuleType(prefix+'.death_counter')
            class FakeDeathReader:
                def snapshot(self):return dict(can_count=getattr(self,'_parent_can_count',True))
                def close(self):pass
            d.DeathReader=FakeDeathReader
            g=types.ModuleType(prefix+'.character_guard');g.NameReader=lambda expected:memory
            i=types.ModuleType(prefix+'.i18n');i.tr=lambda text,*_:text
            m=types.ModuleType(prefix+'.boss_reader');m.__package__=prefix
            outputs=[]
            with patch.dict(sys.modules,{prefix:p,prefix+'.boss_flags':f,c.__name__:c,r.__name__:r,d.__name__:d,g.__name__:g,i.__name__:i}),patch('time.monotonic',side_effect=lambda:clock[0]):
                exec(compile(READER_NEW,READER_PATH,'exec'),m.__dict__)
                obj=m.BossReader.__new__(m.BossReader);obj.expected='Test';obj._boss_stop=Stop();obj._store=outputs.append;obj._boss_worker()
                obj._boss_lock=threading.Lock();obj._boss_after=0;obj._boss_result=outputs[-1];obj.globals=memory.globals;obj.ptr=memory.ptr;self._last_obj=obj
            return outputs,memory
        def test_207_victories_and_signals_confirmed_after_two_cycles(self):
            outputs,memory=self.run_worker();self.assertEqual(len(outputs[-1]['states']),207);self.assertEqual(len(outputs[-1]['combat_signals']),207)
            self.assertTrue(all(value is False for value in outputs[-1]['states'].values()));self.assertTrue(all(isinstance(value,dict) for value in outputs[-1]['combat_signals'].values()));self.assertTrue(memory.closed)
        def test_first_cycle_does_not_publish_unconfirmed_values(self):
            outputs,_=self.run_worker(cycles=1);self.assertTrue(all(value is None for value in outputs[-1]['states'].values()));self.assertTrue(all(value is None for value in outputs[-1]['combat_signals'].values()))
        def test_flag_changes_require_two_new_cycles(self):
            def change(memory,done,clock):
                if done==1:memory.set_flag(10002805,True)
            outputs,_=self.run_worker(cycles=3,wait_hook=change);self.assertIsNone(outputs[1]['combat_signals']['boss_0']);self.assertTrue(outputs[2]['combat_signals']['boss_0']['active'])
        def test_late_guard_snapshot_rejected(self):
            def slow(memory,count,clock):
                if count==2:clock[0]+=3
            outputs,_=self.run_worker(cycles=1,after_hook=slow);self.assertIsNone(outputs[-1]['states']);self.assertIn('lent',outputs[-1]['error'])
        def test_character_pointer_transition_rejected(self):
            def transition(memory,count,clock):
                if count==2:memory.put(0x800008,struct.pack('<Q',0x820000))
            outputs,_=self.run_worker(cycles=1,after_hook=transition);self.assertIsNone(outputs[-1])
        def test_invalid_control_flags_rejected(self):
            def change(memory,count,clock):
                if count==1:memory.set_flag(6001,False)
            outputs,_=self.run_worker(cycles=1,after_hook=change);self.assertIsNone(outputs[-1]['states']);self.assertIn('controle',outputs[-1]['error'])
        def test_timestamp_is_cycle_start_not_cycle_end(self):
            def slow(memory,count,clock):
                if count==2:clock[0]+=.5
            outputs,_=self.run_worker(cycles=1,after_hook=slow);self.assertEqual(outputs[-1]['time'],0.0)
        def test_ambiguity_routing_code_not_modified(self):
            self.assertNotIn('combat_coordinator.py',ALLOWED)

        def test_fresh_snapshot_remains_available(self):
            outputs,_=self.run_worker()
            with patch('time.monotonic',return_value=outputs[-1]['time']+.1):snap=self._last_obj.snapshot()
            self.assertIsNotNone(snap['boss_states']);self.assertEqual(len(snap['combat_signals']),207)
        def test_stale_snapshot_rejected(self):
            outputs,_=self.run_worker()
            with patch('time.monotonic',return_value=outputs[-1]['time']+4.1):snap=self._last_obj.snapshot()
            self.assertIsNone(snap['boss_states']);self.assertIsNone(snap['combat_signals'])
        def test_observation_before_guard_reset_rejected(self):
            outputs,_=self.run_worker();self._last_obj._boss_after=outputs[-1]['time']+1
            with patch('time.monotonic',return_value=outputs[-1]['time']+1.1):snap=self._last_obj.snapshot()
            self.assertIsNone(snap['boss_states'])
        def test_paused_parent_rejects_snapshot(self):
            outputs,_=self.run_worker();self._last_obj._parent_can_count=False
            with patch('time.monotonic',return_value=outputs[-1]['time']+.1):snap=self._last_obj.snapshot()
            self.assertIsNone(snap['boss_states'])
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (FlagTests,InstallerTests,WorkerTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',default=str(Path(__file__).resolve().parent));parser.add_argument('--self-test',action='store_true');parser.add_argument('--restore',action='store_true');parser.add_argument('--dry-run',action='store_true');opts=parser.parse_args()
    if opts.self_test:return self_test()
    root=Path(opts.root).resolve()
    if not (root/'main.py').is_file():raise ValueError('Placer le PY et le BAT a cote de main.py')
    if not opts.restore and not opts.dry_run:
        print('1 - Mettre a jour le lecteur du catalogue\n2 - Apercu\n3 - Restaurer le lecteur precedent\n4 - Tests synthetiques')
        choice=input('Choix: ').strip()
        if choice=='2':opts.dry_run=True
        elif choice=='3':opts.restore=True
        elif choice=='4':return self_test()
        elif choice!='1':return 0
    lock=safe_path(root,'.elt_lecture_catalogue.lock')
    try:
        with open(lock,'x') as f:f.write(str(os.getpid()))
    except FileExistsError:raise ValueError('Update deja en cours ou verrou restant: .elt_lecture_catalogue.lock')
    try:
        if opts.restore:restore(root)
        else:apply(root,dry=opts.dry_run)
    finally:lock.unlink(missing_ok=True)
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ERREUR - '+str(exc),file=sys.stderr);sys.exit(1)

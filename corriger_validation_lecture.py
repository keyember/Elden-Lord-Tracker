# SPDX-License-Identifier: GPL-3.0-only
"""Corrige la validation de l'update deja livree, sans forcer un lecteur different."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import types

UPDATER='mettre_a_jour_lecture_catalogue.py'
EXPECTED_UPDATE='scalable_catalogue_reader_v1'
EXPECTED_PATHS=('tracker/boss_flags.py','tracker/boss_reader.py','tracker/combat_registry.py','tests/test_classic_arena_update.py')
OLD_BLOBS={'FLAGS_OLD':'6299f27ee2a62a79d01aabf91a07a2c79fea00f1','READER_OLD':'a04a93a9da37cd63de8af228aadf148fc07f1a18'}
PREPARE_REFERENCE="""def prepare(root):
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
"""

def normalized(text):return text.lstrip('\ufeff').replace('\r\n','\n').replace('\r','\n')
def decode_source(data):
    try:return normalized(data.decode('utf-8-sig'))
    except UnicodeError as exc:raise ValueError('Le fichier Python doit etre en UTF-8; aucun remplacement effectue') from exc

def structure(text):
    try:return ast.dump(ast.parse(normalized(text)),include_attributes=False)
    except (SyntaxError,ValueError) as exc:raise ValueError('Code Python illisible; aucun remplacement effectue: '+str(exc)) from exc

def git_blob(text):
    data=normalized(text).encode('utf-8');return hashlib.sha1(b'blob '+str(len(data)).encode()+bytes([0])+data).hexdigest()

def compatibility(data,old,new):
    text=decode_source(data);tree=structure(text)
    version='old' if tree==structure(old) else 'new' if tree==structure(new) else None
    return version,dict(sha256=hashlib.sha256(data).hexdigest(),normalized_git_blob=git_blob(text),
                       utf8_bom=data.startswith(b'\xef\xbb\xbf'),crlf_lines=data.count(b'\r\n'),lf_characters=data.count(b'\n'),matched_version=version)

def changed_parts(text,reference):
    def parts(source):
        tree=ast.parse(normalized(source));return {n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    try:
        actual=parts(text);expected=parts(reference)
        changed=[name for name in sorted(set(actual)|set(expected)) if actual.get(name)!=expected.get(name)]
        return changed or ['imports_or_module_statements']
    except (SyntaxError,ValueError):return ['unparseable_source']

def prepare_compatible(module,root,emit=True):
    if not (root/'main.py').is_file():raise ValueError('Placer le correctif a cote de main.py')
    targets=(module.FLAG_PATH,module.READER_PATH,module.REGISTRY_PATH,module.CONFIG_PATH,module.CATALOGUE_PATH)
    originals={p:module.safe_path(root,p).read_bytes() for p in targets}
    diagnostics={}
    for path,old,new in ((module.FLAG_PATH,module.FLAGS_OLD,module.FLAGS_NEW),(module.READER_PATH,module.READER_OLD,module.READER_NEW)):
        version,info=compatibility(originals[path],old,new);diagnostics[path]=info
        if version is None:
            info['different_parts_from_old']=changed_parts(decode_source(originals[path]),old)
            lines=['LECTEUR REELLEMENT DIFFERENT - aucun fichier du tracker remplace.',path+' - '+json.dumps(info,ensure_ascii=False,sort_keys=True)]
            if emit:
                for line in lines:print(line)
            raise ValueError('Logique du lecteur non reconnue: '+path)
        if emit:print('COMPATIBILITE - '+Path(path).name+' - '+('lecteur initial' if version=='old' else 'lecteur optimise')+' - code reconnu, formatage accepte')
    registry=module.patch_registry(decode_source(originals[module.REGISTRY_PATH]))
    prepared={module.FLAG_PATH:module.FLAGS_NEW.encode('utf-8'),module.READER_PATH:module.READER_NEW.encode('utf-8'),module.REGISTRY_PATH:registry.encode('utf-8')}
    test_path=module.safe_path(root,module.TEST_PATH)
    if test_path.exists():
        originals[module.TEST_PATH]=test_path.read_bytes();prepared[module.TEST_PATH]=module.patch_legacy_test(decode_source(originals[module.TEST_PATH])).encode('utf-8')
    summary=module.check_configuration(root,registry)
    summary['compatibility_validation']='python_ast_equal_not_byte_equal'
    summary['source_formats']=diagnostics
    for path,data in prepared.items():compile(data.decode('utf-8'),path,'exec')
    module.safe_path(root,'sauvegardes_updates')
    return originals,prepared,summary

def read_constants(tree):
    selected={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('FLAGS_OLD','FLAGS_NEW','READER_OLD','READER_NEW','UPDATE_ID','FLAG_PATH','READER_PATH','REGISTRY_PATH','TEST_PATH','CONFIG_PATH','CATALOGUE_PATH'):
                try:selected[name]=ast.literal_eval(node.value)
                except (ValueError,TypeError) as exc:raise ValueError('Constante non litterale dans l update: '+name) from exc
    return selected

def validate_updater(source):
    tree=ast.parse(source);constants=read_constants(tree)
    if constants.get('UPDATE_ID')!=EXPECTED_UPDATE:raise ValueError('Ce correctif concerne uniquement l update de lecture du catalogue livree precedemment')
    paths=tuple(constants.get(k) for k in ('FLAG_PATH','READER_PATH','REGISTRY_PATH','TEST_PATH'))
    if paths!=EXPECTED_PATHS or constants.get('CONFIG_PATH')!='tracker/catalogue_data/combat_catalog.json' or constants.get('CATALOGUE_PATH')!='tracker/catalogue_data/boss_catalog.json':
        raise ValueError('Cibles de l update non reconnues')
    for name,expected in OLD_BLOBS.items():
        value=constants.get(name)
        if not isinstance(value,str) or git_blob(value)!=expected:raise ValueError('Reference de lecteur alteree dans l update: '+name)
    if not isinstance(constants.get('FLAGS_NEW'),str) or not constants['FLAGS_NEW'].startswith(constants['FLAGS_OLD']) or '# FLAG_BATCH_CYCLE_V1' not in constants['FLAGS_NEW']:
        raise ValueError('Contenu de la nouvelle lecture non reconnu')
    if not isinstance(constants.get('READER_NEW'),str) or '# SCALABLE_CONFIRMED_FLAGS_V1' not in constants['READER_NEW']:
        raise ValueError('Contenu du nouveau lecteur non reconnu')
    prepares=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare']
    expected=ast.parse(PREPARE_REFERENCE).body[0]
    if len(prepares)!=1 or ast.dump(prepares[0],include_attributes=False)!=ast.dump(expected,include_attributes=False):
        raise ValueError('Procedure de preparation de l update non reconnue')
    allowed_imports={'argparse','ast','copy','datetime','hashlib','json','os','struct','sys','tempfile','types','uuid','pathlib'}
    for node in tree.body:
        if isinstance(node,ast.Import):
            if any(alias.name not in allowed_imports for alias in node.names):raise ValueError('Import inattendu dans l update')
        elif isinstance(node,ast.ImportFrom):
            if node.module not in allowed_imports or node.level:raise ValueError('Import inattendu dans l update')
        elif isinstance(node,ast.FunctionDef):
            if node.decorator_list or any(not isinstance(v,ast.Constant) for v in node.args.defaults):raise ValueError('Definition dynamique inattendue')
        elif isinstance(node,ast.Assign):
            if any(isinstance(n,ast.Call) for n in ast.walk(node.value)):raise ValueError('Initialisation dynamique inattendue')
        elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):pass
        elif isinstance(node,ast.If):
            guard=ast.parse("if __name__=='__main__':\n    pass\n").body[0].test
            if ast.dump(node.test,include_attributes=False)!=ast.dump(guard,include_attributes=False) or node.orelse:raise ValueError('Bloc de lancement inattendu')
        else:raise ValueError('Instruction de niveau module inattendue dans l update')
    return constants

def load_updater(root):
    path=root/UPDATER
    if not path.is_file():raise ValueError('Conserver '+UPDATER+' a cote du correctif; il contient la mise a jour deja livree')
    if path.is_symlink() or not path.resolve().is_relative_to(root):raise ValueError('Chemin de l update symbolique refuse')
    source=decode_source(path.read_bytes());validate_updater(source)
    name='_elt_catalogue_update_compatible';module=types.ModuleType(name);module.__file__=str(path);sys.modules[name]=module
    exec(compile(source,str(path),'exec'),module.__dict__)
    if tuple(module.ALLOWED)!=EXPECTED_PATHS:raise ValueError('Liste des fichiers remplaces non reconnue')
    module.prepare=lambda folder:prepare_compatible(module,folder)
    return module

TEST_FLAGS_REFERENCE="# SPDX-License-Identifier: GPL-3.0-only\n# Lecture adaptee de SoulMemory, Frank van der Stam ; adaptation Python 2026-10-02.\nfrom .i18n import tr, translate_status\nimport struct\n\ndef locate_flags(reader):\n    import re\n\n    def pattern_regex(pattern):\n        return re.compile(b''.join((b'.' if token == '?' else re.escape(bytes([int(token, 16)])) for token in pattern.split())), re.DOTALL)\n    header = reader.read(reader.base, 4096)\n    pe = struct.unpack_from('<I', header, 60)[0]\n    if header[pe:pe + 4] != b'PE\\x00\\x00':\n        raise ValueError('Executable PE invalide')\n    count = struct.unpack_from('<H', header, pe + 6)[0]\n    optional = struct.unpack_from('<H', header, pe + 20)[0]\n    if not 1 <= count <= 128:\n        raise ValueError('Nombre de sections PE incoherent')\n    table = reader.read(reader.base + pe + 24 + optional, count * 40)\n    pattern = pattern_regex('44 89 7c 24 28 4c 8b 25 ? ? ? ? 4d 85 e4')\n    matches = set()\n    for i in range(count):\n        section = table[i * 40:(i + 1) * 40]\n        size, rva = struct.unpack_from('<II', section, 8)\n        flags = struct.unpack_from('<I', section, 36)[0]\n        if not flags & 536870912:\n            continue\n        if rva + size > reader.size:\n            raise ValueError('Section executable incoherente')\n        previous = b''\n        for offset in range(0, size, 1024 * 1024):\n            block = reader.read(reader.base + rva + offset, min(1024 * 1024, size - offset))\n            chunk = previous + block\n            origin = reader.base + rva + offset - len(previous)\n            matches.update((origin + match.start() for match in pattern.finditer(chunk)))\n            previous = chunk[-64:]\n    if len(matches) != 1:\n        raise ValueError(f'Signature complete event_flags : {len(matches)} correspondances, lecture refusee')\n    address = next(iter(matches))\n    instruction = reader.read(address, 12)\n    return address + 12 + struct.unpack_from('<i', instruction, 8)[0]\n\ndef flag(reader, manager, identifier):\n    divisor = reader.integer(manager + 28)\n    if not 1 <= divisor <= 1000000:\n        raise ValueError('Diviseur de flags invalide ou non initialise')\n    category, remainder = divmod(identifier, divisor)\n    header = reader.ptr(manager + 56)\n    node = reader.ptr(header + 8)\n    candidate = header\n    seen = set()\n    for _ in range(128):\n        sentinel = reader.read(node + 25, 1)[0]\n        if sentinel == 1:\n            break\n        if sentinel != 0 or node in seen:\n            raise ValueError('Arbre de flags incoherent')\n        seen.add(node)\n        key = reader.integer(node + 32)\n        if key < category:\n            node = reader.ptr(node + 16)\n        else:\n            candidate = node\n            node = reader.ptr(node)\n    else:\n        raise ValueError('Parcours de flags trop long')\n    if candidate == header or reader.integer(candidate + 32) != category:\n        raise ValueError('Categorie absente : etat inconnu, pas faux')\n    mode = reader.integer(candidate + 40)\n    if mode == 1:\n        stride = reader.integer(manager + 32)\n        index = reader.integer(candidate + 48)\n        if stride <= 0 or index < 0:\n            raise ValueError('Stockage indexe invalide')\n        storage = reader.ptr(manager + 40) + stride * index\n    elif mode == 2:\n        raise ValueError('Categorie sans stockage lisible')\n    else:\n        storage = reader.ptr(candidate + 48)\n    byte = reader.read(storage + (remainder >> 3), 1)[0]\n    return bool(byte & 1 << 7 - (remainder & 7))\n"
TEST_READER_REFERENCE='# SPDX-License-Identifier: GPL-3.0-only\n"""Generic confirmed boss observations on the existing independent worker."""\nimport time,threading\nfrom .death_counter import DeathReader\nfrom .character_guard import NameReader\nfrom .boss_flags import locate_flags,flag\nfrom .boss_catalog import BOSS_IDS,active_bosses\nfrom .combat_registry import supported_specs\nfrom .i18n import tr\n\nclass BossReader(DeathReader):\n    def __init__(self,expected):\n        super().__init__(expected)\n        self._boss_stop=threading.Event();self._boss_lock=threading.Lock();self._boss_result=None;self._boss_after=0\n        self._boss_thread=threading.Thread(target=self._boss_worker,daemon=True);self._boss_thread.start()\n    def _store(self,value):\n        with self._boss_lock:self._boss_result=value\n    def _boss_worker(self):\n        worker=None;pending={};repeats={}\n        try:\n            worker=NameReader(self.expected);worker.globals[\'event_flags\']=locate_flags(worker)\n            while not self._boss_stop.is_set():\n                began=time.monotonic()\n                try:\n                    before=worker.snapshot()\n                    if not before[\'can_count\']:\n                        self._store(None);pending={};repeats={};self._boss_stop.wait(.25);continue\n                    root=worker.ptr(worker.globals[\'identity_root\']);player=worker.ptr(root+8);manager=worker.ptr(worker.globals[\'event_flags\'])\n                    if flag(worker,manager,6000) is not False or flag(worker,manager,6001) is not True:raise ValueError(tr(\'Flags de controle incorrects\'))\n                    states={key:None for key in BOSS_IDS};errors=[]\n                    for boss in active_bosses():\n                        if self._boss_stop.is_set():break\n                        key=boss[\'id\']\n                        try:\n                            value=flag(worker,manager,boss[\'flag_id\']);repeats[key]=repeats.get(key,0)+1 if pending.get(key) is value else 1;pending[key]=value\n                            if repeats[key]>=2:states[key]=value\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(key,None);repeats.pop(key,None);errors.append(key+\': \'+str(exc))\n                    signals={};signal_errors={}\n                    for spec in supported_specs():\n                        key=spec[\'boss_id\'];token=\'_combat_\'+key;signals[key]=None\n                        try:\n                            value=flag(worker,manager,spec[\'active_flag\']);repeats[token]=repeats.get(token,0)+1 if pending.get(token) is value else 1;pending[token]=value\n                            victory=states.get(key)\n                            if type(value) is bool and type(victory) is bool and repeats[token]>=2:signals[key]=dict(boss_id=key,active=value,victory=victory)\n                        except (OSError,ValueError,KeyError) as exc:\n                            pending.pop(token,None);repeats.pop(token,None);signal_errors[key]=str(exc)\n                    after=worker.snapshot()\n                    if worker.ptr(worker.globals[\'identity_root\'])!=root or worker.ptr(root+8)!=player or worker.ptr(worker.globals[\'event_flags\'])!=manager or not after[\'can_count\'] or after.get(\'observed_character\')!=self.expected:\n                        self._store(None);pending={};repeats={}\n                    else:\n                        error=(tr(\'Boss illisibles : \')+\'; \'.join(errors[:3])+(\' ...\' if len(errors)>3 else \'\')) if errors else None\n                        self._store(dict(time=time.monotonic(),root=root,player=player,states=states,error=error,combat_signals=signals,combat_errors=signal_errors))\n                except (OSError,ValueError,KeyError) as exc:\n                    self._store(dict(time=time.monotonic(),error=str(exc),states=None));pending={};repeats={}\n                self._boss_stop.wait(max(.05,1-(time.monotonic()-began)))\n        except (OSError,ValueError,KeyError) as exc:self._store(dict(time=time.monotonic(),error=str(exc),states=None))\n        finally:\n            if worker:worker.close()\n    def snapshot(self):\n        snap=super().snapshot();snap.update(boss_states=None,boss_error=None,combat_signals=None,combat_signal=None,combat_errors={},combat_error=None)\n        if not snap[\'can_count\']:\n            self._boss_after=time.monotonic();return snap\n        with self._boss_lock:value=self._boss_result\n        if not value:return snap\n        snap[\'boss_error\']=value.get(\'error\')\n        if value.get(\'states\') is None or value[\'time\']<self._boss_after or time.monotonic()-value[\'time\']>4:return snap\n        try:\n            root=self.ptr(self.globals[\'identity_root\'])\n            if root!=value[\'root\'] or self.ptr(root+8)!=value[\'player\']:return snap\n            snap[\'boss_states\']=dict(value[\'states\']);snap[\'combat_signals\']={key:dict(signal) if isinstance(signal,dict) else None for key,signal in value.get(\'combat_signals\',{}).items()};snap[\'combat_errors\']=dict(value.get(\'combat_errors\',{}))\n        except (OSError,ValueError):pass\n        return snap\n    def close(self):\n        if hasattr(self,\'_boss_stop\'):\n            self._boss_stop.set()\n            if self._boss_thread is not threading.current_thread():self._boss_thread.join(timeout=2)\n        super().close()\n# GENERIC_COMBAT_ENGINE_V1\n'

def fixture_updater_source():
    old_flags=TEST_FLAGS_REFERENCE;old_reader=TEST_READER_REFERENCE
    new_flags=old_flags+'\n# FLAG_BATCH_CYCLE_V1\nclass FlagBatch: pass\n'
    new_reader=old_reader+'\n# SCALABLE_CONFIRMED_FLAGS_V1\nSCALABLE=True\n'
    constants=dict(UPDATE_ID=EXPECTED_UPDATE,FLAG_PATH=EXPECTED_PATHS[0],READER_PATH=EXPECTED_PATHS[1],REGISTRY_PATH=EXPECTED_PATHS[2],TEST_PATH=EXPECTED_PATHS[3],
                   CONFIG_PATH='tracker/catalogue_data/combat_catalog.json',CATALOGUE_PATH='tracker/catalogue_data/boss_catalog.json',ALLOWED=EXPECTED_PATHS,
                   FLAGS_OLD=old_flags,FLAGS_NEW=new_flags,READER_OLD=old_reader,READER_NEW=new_reader)
    helpers=r"""
def safe_path(root,relative):
    p=root/relative
    if p.is_symlink() or not p.resolve().is_relative_to(root):raise ValueError('unsafe path')
    return p
def patch_registry(text):
    ast.parse(text)
    return text.replace('enabled>32','enabled>len(BOSSES)')
def patch_legacy_test(text):
    ast.parse(text)
    return text.replace('range(21)','range(208)')
def check_configuration(root,text):
    catalog=json.loads((root/CATALOGUE_PATH).read_text(encoding='utf-8-sig'));config=json.loads((root/CONFIG_PATH).read_text(encoding='utf-8-sig'))
    if len(catalog)!=207:raise ValueError('catalogue must have 207')
    return dict(configured=len(config),active=len(config))
def commit(root,prepared):
    before={p:(root/p).read_bytes() for p in prepared}
    backup=root/'sauvegardes_updates'/'test_backup';backup.mkdir(parents=True)
    for p,data in before.items():d=backup/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
    for p,data in prepared.items():(root/p).write_bytes(data)
    return backup
"""
    return 'import argparse,ast,json\nfrom pathlib import Path\n'+'\n'.join(k+'='+repr(v) for k,v in constants.items())+'\n'+helpers+'\n'+PREPARE_REFERENCE+"\ndef main():\n    parser=argparse.ArgumentParser();parser.add_argument('--root');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--restore',action='store_true');opts=parser.parse_args()\n    root=Path(opts.root)\n    if opts.restore:return 0\n    _,prepared,_=prepare(root)\n    if opts.dry_run:return 0\n    if input('APPLIQUER: ')!='APPLIQUER':return 0\n    commit(root,prepared)\n    return 0\n"


def self_test():
    import tempfile,unittest
    from unittest.mock import patch
    class CompatibilityTests(unittest.TestCase):
        def setUp(self):
            self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
            (self.root/'main.py').write_bytes(b'keep launcher')
            source=fixture_updater_source();(self.root/UPDATER).write_text(source,encoding='utf-8');self.source=source
            self.module=load_updater(self.root)
            files={self.module.FLAG_PATH:self.module.FLAGS_OLD.encode(),self.module.READER_PATH:self.module.READER_OLD.encode(),
                   self.module.REGISTRY_PATH:b'BOSSES=[]\nenabled=0\nif enabled>32: raise ValueError()\n',
                   self.module.CONFIG_PATH:b'{"existing":true}',self.module.CATALOGUE_PATH:json.dumps(list(range(207))).encode(),
                   self.module.TEST_PATH:b'def test_guard():\n    for i in range(21):pass\n',
                   'profiles/history.json':b'preserve history','settings.json':b'preserve settings','overlay/style.css':b'preserve overlay'}
            for p,data in files.items():d=self.root/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data)
        def prepared(self):return prepare_compatible(self.module,self.root,emit=False)
        def test_exact_old_flags(self):self.assertEqual(compatibility(self.module.FLAGS_OLD.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'old')
        def test_exact_new_flags(self):self.assertEqual(compatibility(self.module.FLAGS_NEW.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'new')
        def test_crlf_accepted(self):
            data=self.module.FLAGS_OLD.replace('\n','\r\n').encode();v,info=compatibility(data,self.module.FLAGS_OLD,self.module.FLAGS_NEW);self.assertEqual(v,'old');self.assertGreater(info['crlf_lines'],0)
        def test_bom_accepted(self):
            data=b'\xef\xbb\xbf'+self.module.FLAGS_OLD.encode();v,info=compatibility(data,self.module.FLAGS_OLD,self.module.FLAGS_NEW);self.assertEqual(v,'old');self.assertTrue(info['utf8_bom'])
        def test_bom_crlf_accepted(self):
            data=b'\xef\xbb\xbf'+self.module.FLAGS_OLD.replace('\n','\r\n').encode();self.assertEqual(compatibility(data,self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'old')
        def test_comments_and_blank_lines_accepted(self):
            data=('# harmless comment\n\n'+self.module.FLAGS_OLD+'\n# another comment\n').encode();self.assertEqual(compatibility(data,self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'old')
        def test_quote_style_accepted(self):
            source=self.module.FLAGS_OLD.replace("'Stockage indexe invalide'",'"Stockage indexe invalide"');self.assertEqual(compatibility(source.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'old')
        def test_whitespace_accepted(self):
            source=self.module.FLAGS_OLD.replace('def flag(reader, manager, identifier):','def flag( reader , manager , identifier ):');self.assertEqual(compatibility(source.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0],'old')
        def test_pointer_offset_change_refused(self):
            source=self.module.FLAGS_OLD.replace('manager + 28','manager + 24');self.assertIsNone(compatibility(source.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0])
        def test_bit_order_change_refused(self):
            source=self.module.FLAGS_OLD.replace('7 - (remainder & 7)','6 - (remainder & 7)');self.assertIsNone(compatibility(source.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0])
        def test_added_executable_statement_refused(self):
            source=self.module.FLAGS_OLD+'\nprint("unexpected")\n';self.assertIsNone(compatibility(source.encode(),self.module.FLAGS_OLD,self.module.FLAGS_NEW)[0])
        def test_syntax_error_refused(self):
            with self.assertRaises(ValueError):compatibility(b'def broken(',self.module.FLAGS_OLD,self.module.FLAGS_NEW)
        def test_changed_function_reported(self):
            changed=self.module.FLAGS_OLD.replace('manager + 28','manager + 24');self.assertIn('flag',changed_parts(changed,self.module.FLAGS_OLD))
        def test_crlf_flags_preparation(self):
            path=self.root/self.module.FLAG_PATH;raw=self.module.FLAGS_OLD.replace('\n','\r\n').encode();path.write_bytes(raw);old,prepared,s=self.prepared();self.assertEqual(old[self.module.FLAG_PATH],raw);self.assertEqual(prepared[self.module.FLAG_PATH],self.module.FLAGS_NEW.encode())
        def test_crlf_reader_preparation(self):
            path=self.root/self.module.READER_PATH;path.write_bytes(self.module.READER_OLD.replace('\n','\r\n').encode());old,prepared,s=self.prepared();self.assertEqual(prepared[self.module.READER_PATH],self.module.READER_NEW.encode())
        def test_bom_registry_and_test_preparation(self):
            for p in (self.module.REGISTRY_PATH,self.module.TEST_PATH):(self.root/p).write_bytes(b'\xef\xbb\xbf'+(self.root/p).read_bytes().replace(b'\n',b'\r\n'))
            _,prepared,_=self.prepared();self.assertIn(b'len(BOSSES)',prepared[self.module.REGISTRY_PATH]);self.assertIn(b'208',prepared[self.module.TEST_PATH])
        def test_real_difference_no_project_write(self):
            path=self.root/self.module.FLAG_PATH;path.write_text(self.module.FLAGS_OLD.replace('manager + 28','manager + 24'));before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
            with self.assertRaises(ValueError):self.prepared()
            self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        def test_reader_logic_change_refused(self):
            (self.root/self.module.READER_PATH).write_text(self.module.READER_OLD.replace('repeats[key]>=2','repeats[key]>=1'))
            with self.assertRaises(ValueError):self.prepared()
        def test_original_updater_not_modified(self):
            before=(self.root/UPDATER).read_bytes();self.prepared();self.assertEqual((self.root/UPDATER).read_bytes(),before)
        def test_user_files_not_modified(self):
            paths=['profiles/history.json','settings.json','overlay/style.css',self.module.CONFIG_PATH,self.module.CATALOGUE_PATH];before={p:(self.root/p).read_bytes() for p in paths};_,prepared,_=self.prepared();self.module.commit(self.root,prepared)
            for p,data in before.items():self.assertEqual((self.root/p).read_bytes(),data)
        def test_backup_preserves_original_crlf_bytes(self):
            raw=b'\xef\xbb\xbf'+self.module.FLAGS_OLD.replace('\n','\r\n').encode();(self.root/self.module.FLAG_PATH).write_bytes(raw)
            _,prepared,_=self.prepared();backup=self.module.commit(self.root,prepared);self.assertEqual((backup/self.module.FLAG_PATH).read_bytes(),raw)
        def test_restoration_of_original_format(self):
            raw=b'\xef\xbb\xbf'+self.module.FLAGS_OLD.replace('\n','\r\n').encode();(self.root/self.module.FLAG_PATH).write_bytes(raw)
            _,prepared,_=self.prepared();backup=self.module.commit(self.root,prepared);(self.root/self.module.FLAG_PATH).write_bytes((backup/self.module.FLAG_PATH).read_bytes());self.assertEqual((self.root/self.module.FLAG_PATH).read_bytes(),raw)
        def test_idempotent_recognition_after_update(self):
            _,prepared,_=self.prepared();self.module.commit(self.root,prepared);_,again,_=self.prepared();self.assertEqual(again,prepared)
        def test_unknown_update_id_refused(self):
            with self.assertRaises(ValueError):validate_updater(self.source.replace(EXPECTED_UPDATE,'unknown_update'))
        def test_changed_update_targets_refused(self):
            with self.assertRaises(ValueError):validate_updater(self.source.replace('tracker/boss_flags.py','profiles/user.json'))
        def test_changed_update_reference_refused(self):
            source=self.source.replace('manager + 28','manager + 24')
            with self.assertRaises(ValueError):validate_updater(source)
        def test_unknown_prepare_procedure_refused(self):
            with self.assertRaises(ValueError):validate_updater(self.source.replace("decode('utf-8') not in","decode('utf-8-sig') not in"))
        def test_missing_original_update_explicit(self):
            (self.root/UPDATER).unlink()
            with self.assertRaises(ValueError):load_updater(self.root)
        def test_loading_does_not_start_update(self):
            before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};load_updater(self.root);self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        def test_original_rejection_reproduced_and_fixed(self):
            (self.root/self.module.FLAG_PATH).write_bytes(self.module.FLAGS_OLD.replace('\n','\r\n').encode());context=dict(self.module.__dict__);exec(PREPARE_REFERENCE,context)
            with self.assertRaises(ValueError):context['prepare'](self.root)
            self.assertIsInstance(self.prepared()[1],dict)

        def test_wrapper_preview_delegates_without_write(self):
            before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
            with patch.dict(globals(),{'__file__':str(self.root/'corriger_validation_lecture.py')}),patch('sys.argv',['fix','--dry-run']),patch('builtins.print'):
                self.assertEqual(main(),0)
            self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
        def test_wrapper_apply_delegates_and_backs_up_crlf(self):
            raw=self.module.FLAGS_OLD.replace('\n','\r\n').encode();(self.root/self.module.FLAG_PATH).write_bytes(raw)
            with patch.dict(globals(),{'__file__':str(self.root/'corriger_validation_lecture.py')}),patch('sys.argv',['fix']),patch('builtins.input',return_value='APPLIQUER'),patch('builtins.print'):
                self.assertEqual(main(),0)
            self.assertEqual((self.root/self.module.FLAG_PATH).read_bytes(),self.module.FLAGS_NEW.encode())
            self.assertEqual((self.root/'sauvegardes_updates/test_backup'/self.module.FLAG_PATH).read_bytes(),raw)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompatibilityTests))
    return 0 if result.wasSuccessful() else 1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true');parser.add_argument('--dry-run',action='store_true');parser.add_argument('--restore',action='store_true')
    opts=parser.parse_args()
    if opts.self_test:return self_test()
    root=Path(__file__).resolve().parent
    if not (root/'main.py').is_file():raise ValueError('Placer le PY et le BAT a cote de main.py')
    module=load_updater(root)
    print('Validation corrigee - differences LF/CRLF, BOM, espaces et commentaires acceptees si le code correspond.')
    print('Aucun controle de logique memoire desactive. Ancienne update conservee sans modification.')
    forwarded=[str(root/UPDATER),'--root',str(root)]
    if opts.dry_run:forwarded.append('--dry-run')
    if opts.restore:forwarded.append('--restore')
    sys.argv=forwarded
    return module.main()

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ERREUR - '+str(exc),file=sys.stderr);sys.exit(1)

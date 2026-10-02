import argparse
import traceback

def parse_args():
    parser = argparse.ArgumentParser(description="Mettre a jour le catalogue")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les logs de debug")
    return parser.parse_args()

ARGS = parse_args()

def log(*msg):
    if ARGS.dry_run:
        print("[DEBUG]", *msg)

# ... (début inchangé jusqu'à check_configuration) ...

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
    bank_node=bank_nodes[0].value
    if isinstance(bank_node,(ast.Dict,ast.Call,ast.DictComp)):
        module=ast.Module(body=[ast.copy_location(ast.Assign(targets=[ast.Name(id='_BANK',ctx=ast.Store())],value=bank_node),ast.Expr(value=ast.Constant(value=None)))],type_ignores=[])
        ast.fix_missing_locations(module)
        env=dict(BOSSES=tuple(catalog))
        exec(compile(module,'<bank>','exec'),env)
        bank=env['_BANK']
    else:
        bank=ast.literal_eval(bank_node)
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='read_configuration')
    module=ast.Module(body=[copy.deepcopy(function)],type_ignores=[]);ast.fix_missing_locations(module)
    env=dict(json=json,CONFIG_PATH=safe_path(root,CONFIG_PATH),BY_ID=by_id,BOSSES=tuple(catalog),SOURCE_BANK=bank,ENABLED_LEVELS=frozenset({'documented','user_tested'}))
    exec(compile(module,REGISTRY_PATH,'exec'),env)
    entries,error=env['read_configuration']()
    if error:raise ValueError(error)
    configured=[k for k,v in entries.items() if v['validation'] in ('documented','user_tested')]
    active=[k for k in configured if entries[k].get('enabled',True) is not False]
    return dict(catalogue_total=207,configured=len(configured),active=len(active),unconfigured=207-len(configured),
                complete_combat_coverage=len(configured)==207,associations_added=0)

# ... (fin inchangée) ...

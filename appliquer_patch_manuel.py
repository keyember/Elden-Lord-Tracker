import ast,re,sys
from pathlib import Path

root=Path(__file__).resolve().parent
f=root/'mettre_a_jour_lecture_catalogue.py'
if not f.exists():print('ERREUR: fichier introuvable');sys.exit(1)

text=f.read_text(encoding='utf-8-sig')
old='bank=ast.literal_eval(bank_nodes[0].value)'
if old not in text:print('ERREUR: ligne non trouvee');sys.exit(1)

new='bank_node=bank_nodes[0].value\n    if isinstance(bank_node,(ast.Dict,ast.Call,ast.DictComp)):\n        module=ast.Module(body=[ast.copy_location(ast.Assign(targets=[ast.Name(id="_BANK",ctx=ast.Store())],value=bank_node),ast.Expr(value=ast.Constant(value=None)))],type_ignores=[])\n        ast.fix_missing_locations(module)\n        env=dict(BOSSES=tuple(catalog))\n        exec(compile(module,"<bank>","exec"),env)\n        bank=env["_BANK"]\n    else:\n        bank=ast.literal_eval(bank_node)'

new_text=text.replace(old,new)
ast.parse(new_text)

f.with_name(f.name+'.orig').write_bytes(f.read_bytes())
f.write_text(new_text,encoding='utf-8')
print('PATCH APPLIQUE')
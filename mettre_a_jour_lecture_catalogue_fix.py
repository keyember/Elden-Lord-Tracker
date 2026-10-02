# SPDX-License-Identifier: GPL-3.0-only
"Correctif pour mettre_a_jour_lecture_catalogue.py."
import ast,sys
from pathlib import Path

UPDATE_FILE='mettre_a_jour_lecture_catalogue.py'

def fix_check_configuration():
    root=Path(__file__).resolve().parent
    update_path=root/UPDATE_FILE
    if not update_path.is_file():print('ERREUR: '+UPDATE_FILE+' introuvable');return 1
    text=update_path.read_text(encoding="utf-8-sig")
    old_line='bank=ast.literal_eval(bank_nodes[0].value)'
    new_line1='bank_node=bank_nodes[0].value'
    new_line2='    if isinstance(bank_node,(ast.Dict,ast.Call,ast.DictComp)):'
    new_line3='        module=ast.Module(body=[ast.copy_location(ast.Assign(targets=[ast.Name(id="_BANK",ctx=ast.Store())],value=bank_node),ast.Expr(value=ast.Constant(value=None)))],type_ignores=[])'
    new_line4='        ast.fix_missing_locations(module)'
    new_line5='        env=dict(BOSSES=tuple(catalog))'
    new_line6='        exec(compile(module,"<bank>","exec"),env)'
    new_line7='        bank=env["_BANK"]'
    new_line8='    else:'
    new_line9='        bank=ast.literal_eval(bank_node)'
    if old_line not in text:print('ERREUR: Ligne non trouvee');return 1
    new_text=text.replace(old_line,chr(10).join([new_line1,new_line2,new_line3,new_line4,new_line5,new_line6,new_line7,new_line8,new_line9]))
    ast.parse(new_text)
    backup=update_path.with_name(update_path.name+".bak");backup.write_bytes(update_path.read_bytes())
    update_path.write_text(new_text,encoding="utf-8")
    print('CORRECTIF APPLIQUE');print('Prochaine etape: lancer_update_lecture_catalogue.bat -> Choix 1 -> APPLIQUER')
    return 0

if __name__=="__main__":
    try:sys.exit(fix_check_configuration())
    except Exception as exc:print("ERREUR - "+str(exc),file=sys.stderr);sys.exit(1)
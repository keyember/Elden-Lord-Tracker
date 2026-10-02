#!/usr/bin/env python3
"""
Applique le correctif de debug a mettre_a_jour_lecture_catalogue.py
- Ajoute --dry-run et les logs
- Ajoute try/except autour de main()
- Cree une backup du fichier original
"""

import os
import sys
import shutil
from datetime import datetime

SCRIPT_A_CORRIGER = "mettre_a_jour_lecture_catalogue.py"
BACKUP_DIR = "backups"

def main():
    if not os.path.exists(SCRIPT_A_CORRIGER):
        print(f"ERREUR: {SCRIPT_A_CORRIGER} introuvable dans le dossier actuel.")
        print("Execute ce script depuis la racine du repo Elden-Lord-Tracker.")
        sys.exit(1)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"{SCRIPT_A_CORRIGER}.{timestamp}.bak")
    shutil.copy2(SCRIPT_A_CORRIGER, backup_path)
    print(f"[OK] Backup cree: {backup_path}")

    with open(SCRIPT_A_CORRIGER, "r", encoding="utf-8") as f:
        contenu = f.read()

    lignes = contenu.splitlines(keepends=True)
    idx_insert = 0
    for i, ligne in enumerate(lignes):
        if ligne.startswith("import ") or ligne.startswith("from "):
            idx_insert = i + 1
        elif ligne.strip() == "" and idx_insert > 0:
            break

    code_a_inserer = """import argparse
import traceback

def parse_args():
    parser = argparse.ArgumentParser(description="Mettre a jour le catalogue")
    parser.add_argument("--dry-run", action="store_true", help="Afficher les logs de debug")
    return parser.parse_args()

ARGS = parse_args()

def log(*msg):
    if ARGS.dry_run:
        print("[DEBUG]", *msg)

"""

    lignes.insert(idx_insert, code_a_inserer)
    contenu_modifie = "".join(lignes)

    # Envelopper main() avec try/except
    ancien_bloc = 'if __name__ == "__main__":\n    main()'
    
    nouveau_bloc = ('if __name__ == "__main__":\n'
                    '    try:\n'
                    '        log("=== Demarrage du script ===")\n'
                    '        main()\n'
                    '        log("=== Script termine avec succes ===")\n'
                    '    except Exception as e:\n'
                    '        print()\n'
                    '        print("=" * 60)\n'
                    '        print("ERREUR CRITIQUE:", e)\n'
                    '        print("=" * 60)\n'
                    '        traceback.print_exc()\n'
                    '        print()\n'
                    '        print("=" * 60)\n'
                    '        input("Appuyez sur une touche pour quitter...")\n'
                    '        sys.exit(1)\n')

    if ancien_bloc in contenu_modifie:
        contenu_modifie = contenu_modifie.replace(ancien_bloc, nouveau_bloc)
        print("[OK] Bloc main() enveloppe avec try/except")
    else:
        print("[WARN] Bloc main() non trouve exactement, methode alternative...")
        lignes2 = contenu_modifie.splitlines(keepends=True)
        resultat = []
        i = 0
        while i < len(lignes2):
            ligne = lignes2[i]
            if 'if __name__' in ligne and '__main__' in ligne:
                resultat.append(ligne)
                i += 1
                if i < len(lignes2) and 'main()' in lignes2[i]:
                    resultat.append("    try:\n")
                    resultat.append('        log("=== Demarrage du script ===")\n')
                    resultat.append("        " + lignes2[i].lstrip())
                    i += 1
                    resultat.append("    except Exception as e:\n")
                    resultat.append('        print()\n')
                    resultat.append('        print("=" * 60)\n')
                    resultat.append('        print("ERREUR CRITIQUE:", e)\n')
                    resultat.append('        print("=" * 60)\n')
                    resultat.append('        traceback.print_exc()\n')
                    resultat.append('        print()\n')
                    resultat.append('        print("=" * 60)\n')
                    resultat.append('        input("Appuyez sur une touche pour quitter...")\n')
                    resultat.append('        sys.exit(1)\n')
                continue
            resultat.append(ligne)
            i += 1
        contenu_modifie = "".join(resultat)
        print("[OK] Bloc main() enveloppe (methode alternative)")

    with open(SCRIPT_A_CORRIGER, "w", encoding="utf-8") as f:
        f.write(contenu_modifie)

    print(f"[OK] Correctif applique a {SCRIPT_A_CORRIGER}")
    print()
    print("Utilisation:")
    print(f"  python -B {SCRIPT_A_CORRIGER}          # Mode normal")
    print(f"  python -B {SCRIPT_A_CORRIGER} --dry-run  # Mode debug avec logs")

if __name__ == "__main__":
    main()

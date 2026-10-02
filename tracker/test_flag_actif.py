# SPDX-License-Identifier: GPL-3.0-only
"""Test rapide du flag actif 1049522800 pour Black Blade Kindred."""

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in (HERE, HERE.parent) if (p / "tracker" / "boss_flags.py").is_file()), None)

if ROOT is None:
    print("Place ce fichier a la racine ou dans tracker/")
    sys.exit(1)

sys.path.insert(0, str(ROOT))

from tracker.character_guard import NameReader
from tracker.boss_flags import locate_flags, flag

def main():
    character = input("Nom du personnage : ").strip()
    if not character:
        print("Nom requis")
        sys.exit(1)
    
    victory_flag = 1052410800
    active_flag_hypothese = 1052412800  # +2000, pas +2005
    
    print(f"Victoire : {victory_flag}")
    print(f"Actif (hypothese) : {active_flag_hypothese}")
    print()
    print("Lecture en continu...")
    print("Appuie sur Ctrl+C pour arreter")
    
    reader = NameReader(character)
    reader.globals['event_flags'] = locate_flags(reader)
    manager = reader.ptr(reader.globals['event_flags'])
    
    try:
        last_victory = None
        last_active = None
        
        while True:
            try:
                victory = flag(reader, manager, victory_flag)
                active = flag(reader, manager, active_flag_hypothese)
                
                if victory != last_victory or active != last_active:
                    print(f"Victoire: {victory} | Actif: {active}")
                    last_victory = victory
                    last_active = active
                
                time.sleep(0.2)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"ERREUR: {e}")
                time.sleep(1)
    
    finally:
        reader.close()

if __name__ == '__main__':
    main()
# SPDX-License-Identifier: GPL-3.0-only
"""Diagnostic local avec scan large de flags pour trouver le flag actif."""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = next((p for p in (HERE, HERE.parent) if (p / "tracker" / "boss_reader.py").is_file()), None)


def diagnostic(snap, boss_id):
    states = snap.get("boss_states")
    signals = snap.get("combat_signals")
    errors = snap.get("combat_errors") or {}
    return {
        "can_count": snap.get("can_count"),
        "observed_character": snap.get("observed_character"),
        "status": snap.get("status"),
        "boss_states_available": isinstance(states, dict),
        "victory": states.get(boss_id) if isinstance(states, dict) else None,
        "combat_signals_available": isinstance(signals, dict),
        "target_registered_in_signals": boss_id in signals if isinstance(signals, dict) else None,
        "signal": signals.get(boss_id) if isinstance(signals, dict) else None,
        "signal_error": errors.get(boss_id),
        "boss_error": snap.get("boss_error"),
    }


def scan_flags_range(reader, manager, start, end):
    """Scanne tous les flags dans [start, end] et retourne ceux qui sont True."""
    from tracker.boss_flags import flag
    active = {}
    for flag_id in range(start, end + 1):
        try:
            value = flag(reader, manager, flag_id)
            if value is True:
                active[flag_id] = True
        except (OSError, ValueError, KeyError):  # <-- ValueError est déjà là normalement
            pass
    return active


def main():
    parser = argparse.ArgumentParser(description="Diagnostic avec scan large de flags")
    parser.add_argument("--character", help="Nom exact du personnage")
    parser.add_argument("--boss-id", default="flag_1052410800")
    parser.add_argument("--scan-start", type=int, default=1052410000, help="Debut du scan large")
    parser.add_argument("--scan-end", type=int, default=1052413000, help="Fin du scan large")
    parser.add_argument("--scan-interval", type=float, default=0.05, help="Secondes entre scans larges (defaut 50ms)")
    args = parser.parse_args()
    
    if ROOT is None:
        parser.error("Place ces fichiers a la racine du projet ou dans tracker.")
    
    sys.path.insert(0, str(ROOT))
    from tracker.boss_reader import BossReader
    from tracker.combat_registry import supported_specs
    from tracker.boss_flags import locate_flags
    
    character = args.character or input("Nom exact du personnage : ").strip()
    if not character:
        parser.error("Nom du personnage requis.")
    
    specs = [s for s in supported_specs() if s.get("boss_id") == args.boss_id]
    folder = ROOT / "diagnostics_combat_local"
    folder.mkdir(exist_ok=True)
    path = folder / ("combat_scan_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".jsonl")
    
    print("Specs configurees :", json.dumps(specs, ensure_ascii=True))
    print(f"Scan large de {args.scan_start} a {args.scan_end}")
    print(f"Intervalle de scan : {args.scan_interval*1000:.0f}ms")
    print()
    print("1. Reste hors combat quelques secondes")
    print("2. Lance le combat")
    print("3. Termine le combat")
    print("4. Ctrl+C pour arreter")
    print("Journal :", path)
    
    reader = BossReader(character)
    reader.globals['event_flags'] = locate_flags(reader)
    manager = reader.ptr(reader.globals['event_flags'])
    
    last_full_scan = {}
    changes = []
    next_scan = time.monotonic()
    
    try:
        with path.open("w", encoding="utf-8") as log:
            log.write(json.dumps({
                "type": "configuration",
                "character": character,
                "boss_id": args.boss_id,
                "specs": specs,
                "scan_start": args.scan_start,
                "scan_end": args.scan_end
            }, ensure_ascii=True) + "\n")
            log.flush()
            
            while True:
                snap = reader.snapshot()
                state = diagnostic(snap, args.boss_id)
                record = {"at": datetime.now().astimezone().isoformat(), **state}
                log.write(json.dumps(record, ensure_ascii=True) + "\n")
                log.flush()
                
                now = time.monotonic()
                if now >= next_scan:
                    active_flags = scan_flags_range(reader, manager, args.scan_start, args.scan_end)
                    
                    new_flags = set(active_flags.keys()) - set(last_full_scan.keys())
                    lost_flags = set(last_full_scan.keys()) - set(active_flags.keys())
                    
                    if new_flags or lost_flags:
                        event = {
                            "at": datetime.now().astimezone().isoformat(),
                            "new_flags": list(new_flags),
                            "lost_flags": list(lost_flags),
                            "total_active": len(active_flags)
                        }
                        changes.append(event)
                        log.write(json.dumps({"type": "flag_change", **event}, ensure_ascii=True) + "\n")
                        log.flush()
                        print(f"[{event['at']}] +{len(new_flags)} -{len(lost_flags)} flags (total: {len(active_flags)})")
                        if new_flags:
                            print(f"  NOUVEAUX: {sorted(new_flags)[:10]}{'...' if len(new_flags)>10 else ''}")
                        if lost_flags:
                            print(f"  PERDUS: {sorted(lost_flags)[:10]}{'...' if len(lost_flags)>10 else ''}")
                    
                    last_full_scan = active_flags
                    next_scan = now + args.scan_interval
                
                time.sleep(0.01)  # 10ms pour eviter de bouffer 100% CPU
    
    except KeyboardInterrupt:
        print("\nDiagnostic arrete. Journal conserve.")
        if changes:
            print(f"\n{len(changes)} changements de flags detectes.")
            print(f"Rapport detaille dans: {path}")
    except Exception as exc:
        print(f"ERREUR {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        reader.close()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
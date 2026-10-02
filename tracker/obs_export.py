from .paths import DATA, OBS
from .storage import atomic_text, write_json

def export(report):
    write_json(DATA / "diagnostic.json", report)
    atomic_text(OBS / "timer.txt", report["timer"])
    atomic_text(OBS / "personnage.txt", report["character_name"])
    atomic_text(OBS / "morts.txt", "Morts : N/A")
    atomic_text(OBS / "boss_actuel.txt", "Boss : N/A - Tentatives : N/A")
    atomic_text(OBS / "historique_boss.txt", "Historique indisponible")

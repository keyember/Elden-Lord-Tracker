import os
from pathlib import Path
DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "EldenRingTracker"
OBS = DATA / "obs"
def prepare():
    DATA.mkdir(parents=True, exist_ok=True)
    OBS.mkdir(parents=True, exist_ok=True)

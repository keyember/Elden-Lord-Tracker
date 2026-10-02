"""Ecritures atomiques avec essais courts sous Windows."""
import json
import os
import tempfile
import threading
import time
from pathlib import Path
_LOCK=threading.Lock()

def atomic_text(path,text):
    path=Path(path)
    with _LOCK:
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=str(path.parent))
        pending=Path(name)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as handle:
                handle.write(text)
            # Delai borne court pour ne pas bloquer la boucle du chrono.
            for attempt in range(3):
                try:
                    os.replace(pending,path)
                    return
                except OSError as exc:
                    transient=isinstance(exc,PermissionError) or getattr(exc,"winerror",None) in (5,32,33)
                    if not transient or attempt==2:raise
                    time.sleep((0.005,0.015)[attempt])
        finally:
            try:pending.unlink(missing_ok=True)
            except OSError:pass

def write_json(path,value):
    atomic_text(path,json.dumps(value,ensure_ascii=False,indent=2))

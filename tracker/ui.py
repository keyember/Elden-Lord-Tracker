from .i18n import get_language, set_setting, settings
'Interface Tk ; copie et lecture executees dans un thread de travail.'
from .i18n import tr, translate_status
import logging
import os
import queue
import threading
import time
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from .paths import DATA, OBS, prepare
from .storage import write_json, atomic_text
from .save_reader import copy_save, read_names, read_profile
from .obs_export import export
from .overlay_server import start_server
from .challenge_ui import open_manager
from .profiles import selected_profile
from .live_engine import run_live

class App:

    def __init__(self, root):
        prepare()
        logging.basicConfig(filename=str(DATA / 'tracker.log'), level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', encoding='utf-8')
        self.root = root
        self.queue = queue.Queue()
        self.worker = None
        self.stop = threading.Event()
        self.pending = None
        self.source = tk.StringVar()
        self.status = tk.StringVar(value=tr('Selectionne une sauvegarde.'))
        self.names = [tr('Nom indisponible')] * 10
        self.slot = tk.StringVar(value='Nom indisponible - Slot 0')
        self.active = None
        self.server = None
        self.closed = False
        root.title('Elden Ring Tracker - v0.11.0 / overlay compact')
        root.geometry('900x640')
        f = ttk.Frame(root, padding=18)
        f.pack(fill='both', expand=True)
        ttk.Label(f, text=tr('Sauvegarde officielle - lecture seule')).pack(anchor='w')
        ttk.Entry(f, textvariable=self.source, state='readonly').pack(fill='x', pady=6)
        ttk.Button(f, text=tr('Choisir ER0000.sl2'), command=self.browse).pack(anchor='w')
        ttk.Label(f, text=tr('Personnage a suivre')).pack(anchor='w', pady=(14, 5))
        self.box = ttk.Combobox(f, textvariable=self.slot, state='readonly', width=55)
        self.box.pack(anchor='w')
        self.set_names(self.names)
        ttk.Button(f, text=tr('Demarrer / appliquer le slot'), command=self.start).pack(anchor='w', pady=12)
        ttk.Button(f, text=tr('Arreter le suivi'), command=self.pause).pack(anchor='w')
        ttk.Button(f, text=tr('Choisir / creer un challenge pour ce slot'), command=self.manage_challenge).pack(anchor='w', pady=8)
        ttk.Button(f, text=tr("Ouvrir l'overlay"), command=lambda: webbrowser.open('http://127.0.0.1:8765')).pack(anchor='w', pady=8)
        ttk.Button(f, text=tr('Ouvrir les donnees'), command=lambda: os.startfile(str(DATA))).pack(anchor='w')
        ttk.Label(f, textvariable=self.status, wraplength=730).pack(anchor='w', pady=10)
        ttk.Label(f, text=tr('Chrono, morts observees et progression automatique des boss suivis. Combat actuel et tentatives : N/A.')).pack(anchor='w')
        langrow = ttk.Frame(f)
        langrow.pack(anchor='w', pady=5)
        ttk.Label(langrow, text=tr('Langue')).pack(side='left', padx=(0, 8))
        self.language = tk.StringVar(value=get_language())
        langbox = ttk.Combobox(langrow, textvariable=self.language, values=('fr', 'en'), state='readonly', width=6)
        langbox.pack(side='left')

        def change_language(event=None):
            try:
                set_setting('language', self.language.get())
                messagebox.showinfo(tr('Langue'), tr('Langue enregistree. Relance le tracker pour traduire tous les boutons.'), parent=self.root)
            except OSError as exc:
                messagebox.showerror(tr('Erreur'), str(exc), parent=self.root)
        langbox.bind('<<ComboboxSelected>>', change_language)
        self.include_dlc = tk.BooleanVar(value=settings()['include_dlc'])

        def change_dlc():
            try:
                set_setting('include_dlc', bool(self.include_dlc.get()))
            except OSError as exc:
                messagebox.showerror(tr('Erreur'), str(exc), parent=self.root)
        ttk.Checkbutton(langrow, text=tr('Inclure Shadow of the Erdtree'), variable=self.include_dlc, command=change_dlc).pack(side='left', padx=12)
        ttk.Button(f, text=tr('Ouvrir le catalogue complet'), command=lambda: webbrowser.open('http://127.0.0.1:8765/catalogue.html')).pack(anchor='w', pady=5)
        try:
            self.server = start_server()
        except OSError as exc:
            logging.exception('Serveur overlay indisponible')
            self.status.set(f"Port 8765 indisponible : ferme l'ancien lancer_overlay. {exc}")
        appdata = os.environ.get('APPDATA')
        saves = sorted((Path(appdata) / 'EldenRing').glob('*/ER0000.sl2')) if appdata else []
        if len(saves) == 1:
            self.source.set(str(saves[0]))
            self.request('names')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(150, self.poll)

    def set_names(self, names):
        index = max(0, self.box.current())
        self.names = names
        values = [f"{name or tr('Nom indisponible')} - Slot {i}" for i, name in enumerate(names)]
        self.box.configure(values=values)
        self.box.current(index)

    def manage_challenge(self):
        source = Path(self.source.get())
        if not source.is_file():
            self.status.set(tr('Selectionne une sauvegarde avant de choisir le challenge.'))
            return
        slot = max(0, self.box.current())
        open_manager(self.root, source, slot)

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[(tr('Sauvegarde Elden Ring'), '*.sl2')])
        if path:
            self.pause()
            self.source.set(path)
            self.request('names')

    def request(self, mode):
        source = Path(self.source.get())
        if not source.is_file():
            self.status.set(tr('Selectionne un fichier existant.'))
            return
        slot = max(0, self.box.current())
        self.pending = (mode, source, slot)
        self.stop.set()
        self.launch_pending()

    def launch_pending(self):
        if not self.pending or (self.worker and self.worker.is_alive()):
            return
        mode, source, slot = self.pending
        self.pending = None
        self.stop = threading.Event()
        self.active = (str(source.resolve()), slot)
        if mode == 'track':
            self.runtime(True, None)
        self.worker = threading.Thread(target=self.run, args=(mode, source, slot, self.stop), daemon=True)
        self.worker.start()

    def runtime(self, running, error):
        source, slot = self.active or (None, None)
        try:
            write_json(DATA / 'runtime.json', dict(running=running, error=error, source=source, slot=slot))
        except OSError:
            logging.exception('Ecriture etat runtime')

    def start(self):
        source = Path(self.source.get())
        slot = max(0, self.box.current())
        if not source.is_file():
            self.status.set(tr('Selectionne une sauvegarde.'))
            return
        profile = selected_profile(source, slot)
        if not profile:
            self.status.set(tr('Cree ou selectionne un challenge pour ce slot.'))
            return
        name = self.names[slot] or tr('Nom indisponible')
        if not messagebox.askyesno(tr('Confirmer le personnage'), f"{tr('Chrono pour ')}{profile['name']} / {name} / slot {slot}.\nControle experimental du nom actif. Slot et identite durable non verifies. Noms identiques dans la save : suivi refuse. Solo avec EAC desactive.", parent=self.root):
            return
        self.request('track')

    def pause(self):
        self.pending = None
        self.stop.set()
        self.runtime(False, None)
        self.status.set(tr('Suivi arrete.'))

    def run(self, mode, source, slot, stop):
        if mode == 'track':
            run_live(self, source, slot, stop)
        else:
            self.run_saved(mode, source, slot, stop)

    def run_saved(self, mode, source, slot, stop):
        while not stop.is_set():
            began = time.monotonic()
            try:
                data = copy_save(source, DATA / 'temp_save.sl2')
                names = read_names(data)
                self.queue.put(('names', names))
                if mode == 'names':
                    self.queue.put(('status', tr('Personnages charges. Choisis un slot puis demarre.')))
                    break
                report = read_profile(data, slot)
                report.update(source=str(source.resolve()), observed_at=time.time())
                if stop.is_set():
                    break
                export(report)
                self.runtime(True, None)
                text = '{} - Slot {} - Temps : {} (a verifier)'.format(report['character_name'], slot, report['timer'])
                atomic_text(OBS / 'statut.txt', text)
                self.queue.put(('status', text))
            except (OSError, ValueError) as exc:
                logging.exception(tr('Lecture impossible'))
                self.runtime(False, str(exc))
                self.queue.put(('status', f"{tr('Lecture suspendue : ')}{exc}"))
            stop.wait(max(0, 2 - (time.monotonic() - began)))
        if mode == 'track':
            self.runtime(False, None)

    def poll(self):
        while not self.queue.empty():
            kind, value = self.queue.get_nowait()
            if kind == 'names':
                self.set_names(value)
            elif not self.pending:
                self.status.set(translate_status(value))
        self.launch_pending()
        if not self.closed:
            self.root.after(150, self.poll)

    def close(self):
        self.closed = True
        self.stop.set()
        self.pending = None
        self.runtime(False, None)
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.root.destroy()

def launch():
    root = tk.Tk()
    App(root)
    root.mainloop()

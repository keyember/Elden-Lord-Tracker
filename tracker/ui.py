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
        logging.basicConfig(
            filename=str(DATA / 'tracker.log'),
            level=logging.INFO,
            format='%(asctime)s %(levelname)s %(message)s',
            encoding='utf-8'
        )

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

        # ------------------------------------------------------------------
        # Interface
        # ------------------------------------------------------------------
        root.title('Elden Lord Tracker - v0.11.0 / overlay compact')
        root.geometry('820x700')
        root.minsize(720, 620)
        root.configure(bg='#0b0b0c')

        style = ttk.Style(root)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        bg = '#0b0b0c'
        panel = '#141416'
        panel_alt = '#101012'
        border = '#2a2a2e'
        text = '#f5f5f5'
        muted = '#a1a1aa'
        gold = '#b89b5e'
        gold_hover = '#c7ad74'

        style.configure(
            'App.TFrame',
            background=bg
        )
        style.configure(
            'Card.TFrame',
            background=panel
        )
        style.configure(
            'CardAlt.TFrame',
            background=panel_alt
        )
        style.configure(
            'Title.TLabel',
            background=bg,
            foreground=text,
            font=('Segoe UI Semibold', 20)
        )
        style.configure(
            'Subtitle.TLabel',
            background=bg,
            foreground=muted,
            font=('Segoe UI', 9)
        )
        style.configure(
            'Section.TLabel',
            background=panel,
            foreground=gold,
            font=('Segoe UI Semibold', 9)
        )
        style.configure(
            'Body.TLabel',
            background=panel,
            foreground=text,
            font=('Segoe UI', 10)
        )
        style.configure(
            'Muted.TLabel',
            background=panel,
            foreground=muted,
            font=('Segoe UI', 9)
        )
        style.configure(
            'Status.TLabel',
            background=panel_alt,
            foreground=muted,
            font=('Segoe UI', 9)
        )
        style.configure(
            'Action.TButton',
            background='#1d1d20',
            foreground=text,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            padding=(14, 9),
            font=('Segoe UI Semibold', 9)
        )
        style.map(
            'Action.TButton',
            background=[('active', '#29292d')],
            foreground=[('active', '#ffffff')]
        )
        style.configure(
            'Primary.TButton',
            background=gold,
            foreground='#111111',
            bordercolor=gold,
            lightcolor=gold,
            darkcolor=gold,
            padding=(16, 10),
            font=('Segoe UI Semibold', 9)
        )
        style.map(
            'Primary.TButton',
            background=[('active', gold_hover)]
        )
        style.configure(
            'Danger.TButton',
            background='#1d1d20',
            foreground=text,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            padding=(16, 10),
            font=('Segoe UI Semibold', 9)
        )
        style.map(
            'Danger.TButton',
            background=[('active', '#29292d')]
        )
        style.configure(
            'App.TCombobox',
            fieldbackground='#1d1d20',
            background='#1d1d20',
            foreground=text,
            bordercolor=border,
            lightcolor=border,
            darkcolor=border,
            arrowcolor=gold,
            padding=7
        )
        style.map(
            'App.TCombobox',
            fieldbackground=[('readonly', '#1d1d20')],
            foreground=[('readonly', text)]
        )
        style.configure(
            'App.TCheckbutton',
            background=panel_alt,
            foreground=text,
            font=('Segoe UI', 9),
            padding=(0, 2)
        )
        style.map(
            'App.TCheckbutton',
            background=[('active', panel_alt)],
            foreground=[('active', text)]
        )

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        f = ttk.Frame(root, style='App.TFrame', padding=(28, 24))
        f.grid(row=0, column=0, sticky='nsew')
        f.columnconfigure(0, weight=1)

        header = ttk.Frame(f, style='App.TFrame')
        header.grid(row=0, column=0, sticky='ew', pady=(0, 22))

        ttk.Label(
            header,
            text='✦  ELDEN LORD TRACKER',
            style='Title.TLabel'
        ).pack(anchor='w')
        ttk.Label(
            header,
            text='Challenge & Progress Tracker',
            style='Subtitle.TLabel'
        ).pack(anchor='w', pady=(3, 0))

        # Save / character card
        save_card = ttk.Frame(f, style='Card.TFrame', padding=(18, 16))
        save_card.grid(row=1, column=0, sticky='ew', pady=(0, 12))
        save_card.columnconfigure(0, weight=1)

        ttk.Label(
            save_card,
            text=tr('Sauvegarde officielle - lecture seule'),
            style='Section.TLabel'
        ).grid(row=0, column=0, columnspan=2, sticky='w')

        ttk.Entry(
            save_card,
            textvariable=self.source,
            state='readonly',
            font=('Segoe UI', 9)
        ).grid(row=1, column=0, sticky='ew', pady=(10, 8))

        ttk.Button(
            save_card,
            text=tr('Choisir ER0000.sl2'),
            command=self.browse,
            style='Action.TButton'
        ).grid(row=1, column=1, sticky='e', padx=(10, 0))

        ttk.Label(
            save_card,
            text=tr('Personnage a suivre'),
            style='Section.TLabel'
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=(12, 0))

        self.box = ttk.Combobox(
            save_card,
            textvariable=self.slot,
            state='readonly',
            style='App.TCombobox',
            width=55
        )
        self.box.grid(row=3, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        self.set_names(self.names)

        # Challenge card
        challenge_card = ttk.Frame(f, style='Card.TFrame', padding=(18, 16))
        challenge_card.grid(row=2, column=0, sticky='ew', pady=(0, 12))
        challenge_card.columnconfigure(0, weight=1)

        ttk.Label(
            challenge_card,
            text='CHALLENGE',
            style='Section.TLabel'
        ).grid(row=0, column=0, sticky='w')

        ttk.Label(
            challenge_card,
            text=tr('Choisir / creer un challenge pour ce slot'),
            style='Body.TLabel'
        ).grid(row=1, column=0, sticky='w', pady=(7, 10))

        ttk.Button(
            challenge_card,
            text=tr('Choisir / creer un challenge pour ce slot'),
            command=self.manage_challenge,
            style='Action.TButton'
        ).grid(row=2, column=0, sticky='w')

        # Control row
        controls = ttk.Frame(f, style='App.TFrame')
        controls.grid(row=3, column=0, sticky='ew', pady=(2, 12))
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)

        ttk.Button(
            controls,
            text=tr('Demarrer / appliquer le slot'),
            command=self.start,
            style='Primary.TButton'
        ).grid(row=0, column=0, sticky='ew', padx=(0, 6))

        ttk.Button(
            controls,
            text=tr('Arreter le suivi'),
            command=self.pause,
            style='Danger.TButton'
        ).grid(row=0, column=1, sticky='ew', padx=(6, 0))

        # Status card
        status_card = ttk.Frame(f, style='CardAlt.TFrame', padding=(18, 14))
        status_card.grid(row=4, column=0, sticky='ew', pady=(0, 12))
        status_card.columnconfigure(0, weight=1)

        ttk.Label(
            status_card,
            text='ÉTAT',
            style='Section.TLabel'
        ).grid(row=0, column=0, sticky='w')

        ttk.Label(
            status_card,
            textvariable=self.status,
            wraplength=730,
            style='Status.TLabel'
        ).grid(row=1, column=0, sticky='w', pady=(7, 0))

        ttk.Label(
            status_card,
            text=tr('Chrono, morts observees et progression automatique des boss suivis. Combat actuel et tentatives : N/A.'),
            wraplength=730,
            style='Status.TLabel'
        ).grid(row=2, column=0, sticky='w', pady=(6, 0))

        # Footer / settings
        footer = ttk.Frame(f, style='CardAlt.TFrame', padding=(14, 10))
        footer.grid(row=5, column=0, sticky='ew')
        footer.columnconfigure(3, weight=1)

        ttk.Label(
            footer,
            text=tr('Langue'),
            style='Status.TLabel'
        ).grid(row=0, column=0, sticky='w')

        self.language = tk.StringVar(value=get_language())
        langbox = ttk.Combobox(
            footer,
            textvariable=self.language,
            values=('fr', 'en'),
            state='readonly',
            width=6,
            style='App.TCombobox'
        )
        langbox.grid(row=0, column=1, sticky='w', padx=(8, 14))

        def change_language(event=None):
            try:
                set_setting('language', self.language.get())
                messagebox.showinfo(
                    tr('Langue'),
                    tr('Langue enregistree. Relance le tracker pour traduire tous les boutons.'),
                    parent=self.root
                )
            except OSError as exc:
                messagebox.showerror(tr('Erreur'), str(exc), parent=self.root)

        langbox.bind('<<ComboboxSelected>>', change_language)

        self.include_dlc = tk.BooleanVar(value=settings()['include_dlc'])

        def change_dlc():
            try:
                set_setting('include_dlc', bool(self.include_dlc.get()))
            except OSError as exc:
                messagebox.showerror(tr('Erreur'), str(exc), parent=self.root)

        ttk.Checkbutton(
            footer,
            text=tr('Inclure Shadow of the Erdtree'),
            variable=self.include_dlc,
            command=change_dlc,
            style='App.TCheckbutton'
        ).grid(row=0, column=2, sticky='w')

        ttk.Button(
            footer,
            text=tr("Ouvrir l'overlay"),
            command=lambda: webbrowser.open('http://127.0.0.1:8765'),
            style='Action.TButton'
        ).grid(row=0, column=4, sticky='e', padx=(8, 6))

        ttk.Button(
            footer,
            text=tr('Ouvrir les donnees'),
            command=lambda: os.startfile(str(DATA)),
            style='Action.TButton'
        ).grid(row=0, column=5, sticky='e')

        ttk.Button(
            f,
            text=tr('Ouvrir le catalogue complet'),
            command=lambda: webbrowser.open('http://127.0.0.1:8765/catalogue.html'),
            style='Action.TButton'
        ).grid(row=6, column=0, sticky='e', pady=(10, 0))

        # ------------------------------------------------------------------
        # Existing application logic (unchanged)
        # ------------------------------------------------------------------
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
        if not messagebox.askyesno(
            tr('Confirmer le personnage'),
            f"{tr('Chrono pour ')}{profile['name']} / {name} / slot {slot}.\n"
            f"Controle experimental du nom actif. Slot et identite durable non verifies. "
            f"Noms identiques dans la save : suivi refuse. Solo avec EAC desactive.",
            parent=self.root
        ):
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
                text = '{} - Slot {} - Temps : {} (a verifier)'.format(
                    report['character_name'], slot, report['timer']
                )
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

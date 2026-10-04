"""Gestion visuelle du challenge associe au fichier et au slot affiches."""
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from .i18n import tr
from .profiles import (
    list_profiles,
    create_profile,
    rename_profile,
    select_profile,
    selected_profile,
)
from .ui_theme import PANEL, BORDER, TEXT, configure_styles
from .ui_components import (
    setup_root,
    create_app_frame,
    create_header,
    create_card,
    create_section_title,
    create_body_label,
    create_button,
)


def open_manager(parent, source, slot):
    window = tk.Toplevel(parent)
    window.title(f"{tr('Challenges - Slot ')}{slot}")
    window.geometry('700x540')
    window.minsize(620, 470)
    window.transient(parent)

    configure_styles(window)
    setup_root(window)
    frame = create_app_frame(window)

    create_header(
        frame,
        f'✦  {tr("Challenges - Slot ")} {slot}'.replace('  ', ' '),
        tr(' - historiques independants'),
    )

    info_card = create_card(frame, 1, padding=(18, 15))
    create_section_title(info_card, tr('Challenge actuel'), 0)
    create_body_label(
        info_card,
        tr('Save remplacee / nouveau personnage / nouvelle run : cree un nouveau challenge.'),
        1,
        wraplength=620,
        pady=(7, 0),
    )

    challenge_card = create_card(frame, 2, padding=(18, 15))
    challenge_card.rowconfigure(1, weight=1)
    create_section_title(challenge_card, tr('Challenges disponibles'), 0)

    list_frame = tk.Frame(
        challenge_card,
        bg=PANEL,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    list_frame.grid(row=1, column=0, sticky='nsew', pady=(10, 10))
    list_frame.rowconfigure(0, weight=1)
    list_frame.columnconfigure(0, weight=1)

    box = tk.Listbox(
        list_frame,
        height=8,
        bg='#1a1a1d',
        fg=TEXT,
        selectbackground='#806b3f',
        selectforeground='#ffffff',
        highlightthickness=0,
        borderwidth=0,
        relief='flat',
        activestyle='none',
        font=('Segoe UI', 10),
    )
    box.grid(row=0, column=0, sticky='nsew')

    scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=box.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')
    box.configure(yscrollcommand=scrollbar.set)

    selection_card = create_card(frame, 3, alternate=True, padding=(18, 12), pady=(0, 10))
    selection_card.columnconfigure(0, weight=1)
    label = tk.StringVar()
    ttk.Label(
        selection_card,
        textvariable=label,
        style='Status.TLabel',
        wraplength=620,
    ).grid(row=0, column=0, sticky='w')

    actions = ttk.Frame(frame, style='App.TFrame')
    actions.grid(row=4, column=0, sticky='ew')
    actions.columnconfigure(0, weight=1)
    actions.columnconfigure(1, weight=1)
    actions.columnconfigure(2, weight=1)

    profiles = []

    def refresh():
        nonlocal profiles
        profiles = list_profiles(source, slot)
        box.delete(0, 'end')
        active = selected_profile(source, slot)
        for index, profile in enumerate(profiles):
            created = profile.get('created_at', '')[:10]
            box.insert('end', f"{profile.get('name', tr('N/A'))}  ·  {created}")
            if active and active.get('id') == profile.get('id'):
                box.selection_clear(0, 'end')
                box.selection_set(index)
                box.see(index)
        if active:
            label.set(f"{tr('Selection : ')}{active.get('name', tr('N/A'))}")
        else:
            label.set(tr('Aucun challenge selectionne'))

    def selected_from_list():
        indexes = box.curselection()
        if not indexes or indexes[0] >= len(profiles):
            return None
        return profiles[indexes[0]]

    def on_list_selection(event=None):
        profile = selected_from_list()
        if profile:
            label.set(f"{tr('Selection : ')}{profile.get('name', tr('N/A'))}")

    def create():
        name = simpledialog.askstring(tr('Nouveau challenge'), tr('Nom du challenge :'), parent=window)
        if name is None:
            return
        try:
            profile = create_profile(source, slot, name)
            select_profile(profile)
            refresh()
        except (OSError, ValueError) as exc:
            messagebox.showerror(tr('Erreur'), str(exc), parent=window)

    def rename():
        profile = selected_from_list()
        if not profile:
            return
        name = simpledialog.askstring(
            tr('Renommer le challenge'),
            tr('Nouveau nom du challenge :'),
            initialvalue=profile.get('name', ''),
            parent=window,
        )
        if name is None:
            return
        try:
            updated = rename_profile(profile, name)
            active = selected_profile(source, slot)
            if active and active.get('id') == updated.get('id'):
                select_profile(updated)
            refresh()
            label.set(f"{tr('Selection : ')}{updated.get('name', tr('N/A'))}")
        except (OSError, ValueError) as exc:
            messagebox.showerror(tr('Erreur'), str(exc), parent=window)

    def choose():
        profile = selected_from_list()
        if not profile:
            return
        try:
            select_profile(profile)
            refresh()
            label.set(tr("Challenge selectionne. L'overlay sera actualise au prochain cycle."))
        except OSError as exc:
            messagebox.showerror(tr('Erreur'), str(exc), parent=window)

    box.bind('<<ListboxSelect>>', on_list_selection)

    create_button(actions, tr('Creer un nouveau challenge'), create, 0, style='Action.TButton', sticky='w')
    create_button(actions, tr('Renommer le challenge'), rename, 0, column=1, style='Action.TButton', sticky='ew', padx=(6, 6))
    create_button(actions, tr('Reprendre le challenge selectionne'), choose, 0, column=2, style='Primary.TButton', sticky='e', padx=(6, 0))

    refresh()

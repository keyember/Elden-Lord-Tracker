
"""Choix manuel du challenge associe au fichier et au slot affiches."""
from .i18n import tr, translate_status
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from .profiles import list_profiles, create_profile, select_profile, selected_profile

def open_manager(parent, source, slot):
    window = tk.Toplevel(parent)
    window.title(f"{tr('Challenges - Slot ')}{slot}")
    window.geometry('620x380')
    window.transient(parent)
    frame = ttk.Frame(window, padding=16)
    frame.pack(fill='both', expand=True)
    ttk.Label(frame, text=f"Slot {slot}{tr(' - historiques independants')}", font=('Segoe UI', 12)).pack(anchor='w')
    ttk.Label(frame, text=tr('Save remplacee / nouveau personnage / nouvelle run : cree un nouveau challenge.'), wraplength=570).pack(anchor='w', pady=8)
    box = tk.Listbox(frame, height=8)
    box.pack(fill='both', expand=True)
    label = tk.StringVar()
    ttk.Label(frame, textvariable=label, wraplength=570).pack(anchor='w', pady=8)
    profiles = []

    def refresh():
        nonlocal profiles
        profiles = list_profiles(source, slot)
        box.delete(0, 'end')
        active = selected_profile(source, slot)
        for index, p in enumerate(profiles):
            box.insert('end', p['name'] + ' - ' + p['created_at'][:10])
            if active and active['id'] == p['id']:
                box.selection_set(index)
        label.set(tr('Selection : ') + (active['name'] if active else tr('N/A')))

    def create():
        name = simpledialog.askstring(tr('Nouveau challenge'), tr('Nom du challenge :'), parent=window)
        if name is None:
            return
        try:
            p = create_profile(source, slot, name)
            select_profile(p)
            refresh()
        except (OSError, ValueError) as exc:
            messagebox.showerror(tr('Erreur'), str(exc), parent=window)

    def choose():
        indexes = box.curselection()
        if not indexes:
            return
        try:
            select_profile(profiles[indexes[0]])
            refresh()
            label.set(tr("Challenge selectionne. L'overlay sera actualise au prochain cycle."))
        except OSError as exc:
            messagebox.showerror(tr('Erreur'), str(exc), parent=window)
    ttk.Button(frame, text=tr('Creer un nouveau challenge'), command=create).pack(side='left', pady=6)
    ttk.Button(frame, text=tr('Reprendre le challenge selectionne'), command=choose).pack(side='right', pady=6)
    refresh()

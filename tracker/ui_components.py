import tkinter as tk
from tkinter import ttk

from .ui_theme import (
    BG,
    PANEL,
    PANEL_ALT,
    configure_styles,
)


def setup_root(root):
    root.configure(bg=BG)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)


def create_app_frame(root):
    frame = ttk.Frame(root, style='App.TFrame', padding=(28, 24))
    frame.grid(row=0, column=0, sticky='nsew')
    frame.columnconfigure(0, weight=1)
    return frame


def create_header(parent, title, subtitle):
    frame = ttk.Frame(parent, style='App.TFrame')
    frame.grid(row=0, column=0, sticky='ew', pady=(0, 22))

    ttk.Label(
        frame,
        text=title,
        style='Title.TLabel',
    ).pack(anchor='w')

    ttk.Label(
        frame,
        text=subtitle,
        style='Subtitle.TLabel',
    ).pack(anchor='w', pady=(3, 0))

    return frame


def create_card(parent, row, *, alternate=False, padding=(18, 16), pady=(0, 12)):
    style = 'CardAlt.TFrame' if alternate else 'Card.TFrame'
    frame = ttk.Frame(parent, style=style, padding=padding)
    frame.grid(row=row, column=0, sticky='ew', pady=pady)
    frame.columnconfigure(0, weight=1)
    return frame


def create_section_title(parent, text, row, column=0, columnspan=1):
    label = ttk.Label(
        parent,
        text=text,
        style='Section.TLabel',
    )
    label.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky='w',
    )
    return label


def create_body_label(parent, text, row, *, wraplength=None, pady=(0, 0), column=0):
    options = {
        'row': row,
        'column': column,
        'sticky': 'w',
        'pady': pady,
    }
    if wraplength is not None:
        options['wraplength'] = wraplength

    label = ttk.Label(parent, text=text, style='Body.TLabel')
    label.grid(**options)
    return label


def create_muted_label(parent, text, row, *, wraplength=None, pady=(0, 0), column=0):
    options = {
        'row': row,
        'column': column,
        'sticky': 'w',
        'pady': pady,
    }
    if wraplength is not None:
        options['wraplength'] = wraplength

    label = ttk.Label(parent, text=text, style='Muted.TLabel')
    label.grid(**options)
    return label


def create_status_label(parent, textvariable, row, *, wraplength=None, pady=(0, 0)):
    options = {
        'row': row,
        'column': 0,
        'sticky': 'w',
        'pady': pady,
    }
    if wraplength is not None:
        options['wraplength'] = wraplength

    label = ttk.Label(
        parent,
        textvariable=textvariable,
        style='Status.TLabel',
    )
    label.grid(**options)
    return label


def create_entry(parent, variable, row, *, column=0, columnspan=1):
    entry = ttk.Entry(
        parent,
        textvariable=variable,
        state='readonly',
        font=('Segoe UI', 9),
    )
    entry.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky='ew',
    )
    return entry


def create_combobox(parent, variable, row, *, width=55, column=0, columnspan=1):
    box = ttk.Combobox(
        parent,
        textvariable=variable,
        state='readonly',
        width=width,
        style='App.TCombobox',
    )
    box.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky='ew',
    )
    return box


def create_button(parent, text, command, row, *, style='Action.TButton', column=0, columnspan=1, sticky='w', padx=(0, 0), pady=(0, 0)):
    button = ttk.Button(
        parent,
        text=text,
        command=command,
        style=style,
    )
    button.grid(
        row=row,
        column=column,
        columnspan=columnspan,
        sticky=sticky,
        padx=padx,
        pady=pady,
    )
    return button


def create_controls(parent, start_text, stop_text, start_command, stop_command):
    parent.columnconfigure(0, weight=1)
    parent.columnconfigure(1, weight=1)

    create_button(
        parent,
        start_text,
        start_command,
        0,
        style='Primary.TButton',
        sticky='ew',
        padx=(0, 6),
    )
    create_button(
        parent,
        stop_text,
        stop_command,
        0,
        style='Danger.TButton',
        column=1,
        sticky='ew',
        padx=(6, 0),
    )


def create_footer(parent, language_variable, include_dlc_variable, language_command, dlc_command,
                  overlay_command, data_command, language_text, dlc_text, overlay_text, data_text):
    footer = ttk.Frame(parent, style='CardAlt.TFrame', padding=(14, 10))
    footer.grid(row=0, column=0, sticky='ew')
    footer.columnconfigure(3, weight=1)

    ttk.Label(
        footer,
        text=language_text,
        style='Status.TLabel',
    ).grid(row=0, column=0, sticky='w')

    langbox = ttk.Combobox(
        footer,
        textvariable=language_variable,
        values=('fr', 'en'),
        state='readonly',
        width=6,
        style='App.TCombobox',
    )
    langbox.grid(row=0, column=1, sticky='w', padx=(8, 14))
    langbox.bind('<<ComboboxSelected>>', language_command)

    ttk.Checkbutton(
        footer,
        text=dlc_text,
        variable=include_dlc_variable,
        command=dlc_command,
        style='App.TCheckbutton',
    ).grid(row=0, column=2, sticky='w')

    create_button(
        footer,
        overlay_text,
        overlay_command,
        0,
        style='Action.TButton',
        column=4,
        sticky='e',
        padx=(8, 6),
    )

    create_button(
        footer,
        data_text,
        data_command,
        0,
        style='Action.TButton',
        column=5,
        sticky='e',
    )

    return footer

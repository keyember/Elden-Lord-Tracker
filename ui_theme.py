from tkinter import ttk


# Shared visual language for Elden Lord Tracker.
BG = '#0b0b0c'
PANEL = '#141416'
PANEL_ALT = '#101012'
BORDER = '#2a2a2e'
TEXT = '#f5f5f5'
MUTED = '#a1a1aa'
GOLD = '#b89b5e'
GOLD_HOVER = '#c7ad74'


def configure_styles(root):
    style = ttk.Style(root)

    try:
        style.theme_use('clam')
    except Exception:
        pass

    style.configure('App.TFrame', background=BG)
    style.configure('Card.TFrame', background=PANEL)
    style.configure('CardAlt.TFrame', background=PANEL_ALT)

    style.configure(
        'Title.TLabel',
        background=BG,
        foreground=TEXT,
        font=('Segoe UI Semibold', 20),
    )
    style.configure(
        'Subtitle.TLabel',
        background=BG,
        foreground=MUTED,
        font=('Segoe UI', 9),
    )
    style.configure(
        'Section.TLabel',
        background=PANEL,
        foreground=GOLD,
        font=('Segoe UI Semibold', 9),
    )
    style.configure(
        'Body.TLabel',
        background=PANEL,
        foreground=TEXT,
        font=('Segoe UI', 10),
    )
    style.configure(
        'Muted.TLabel',
        background=PANEL,
        foreground=MUTED,
        font=('Segoe UI', 9),
    )
    style.configure(
        'Status.TLabel',
        background=PANEL_ALT,
        foreground=MUTED,
        font=('Segoe UI', 9),
    )

    style.configure(
        'Action.TButton',
        background='#1d1d20',
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=(14, 9),
        font=('Segoe UI Semibold', 9),
    )
    style.map(
        'Action.TButton',
        background=[('active', '#29292d')],
        foreground=[('active', '#ffffff')],
    )

    style.configure(
        'Primary.TButton',
        background=GOLD,
        foreground='#111111',
        bordercolor=GOLD,
        lightcolor=GOLD,
        darkcolor=GOLD,
        padding=(16, 10),
        font=('Segoe UI Semibold', 9),
    )
    style.map('Primary.TButton', background=[('active', GOLD_HOVER)])

    style.configure(
        'Danger.TButton',
        background='#1d1d20',
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=(16, 10),
        font=('Segoe UI Semibold', 9),
    )
    style.map('Danger.TButton', background=[('active', '#29292d')])

    style.configure(
        'App.TCombobox',
        fieldbackground='#1d1d20',
        background='#1d1d20',
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        arrowcolor=GOLD,
        padding=7,
    )
    style.map(
        'App.TCombobox',
        fieldbackground=[('readonly', '#1d1d20')],
        foreground=[('readonly', TEXT)],
    )

    style.configure(
        'App.TCheckbutton',
        background=PANEL_ALT,
        foreground=TEXT,
        font=('Segoe UI', 9),
        padding=(0, 2),
    )
    style.map(
        'App.TCheckbutton',
        background=[('active', PANEL_ALT)],
        foreground=[('active', TEXT)],
    )

    return style

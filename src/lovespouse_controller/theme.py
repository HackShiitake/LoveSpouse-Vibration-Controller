"""Design system for the desktop UI.

Everything about how the app *looks* lives here so that restyling never means
hunting through widget code. To change the look, edit a :class:`Palette` (or add
a new :class:`Theme`) and the whole window follows — no other file needs to
change.

Concepts
--------
``Palette``  Semantic colors (``accent``, ``surface``, ``text`` …). Widgets ask
             for *roles*, never raw hex, so a new skin is one palette away.
``Theme``    A palette plus a font family and an 8px spacing scale.
``configure_styles``  Maps the active theme onto ttk's ``clam`` styles.

Adding a theme
--------------
>>> MIDNIGHT = Theme(name="midnight", palette=Palette(...))
>>> # then run the app with --theme midnight (see config.py: THEMES)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Palette:
    """Semantic colors for one theme. Every widget references these roles."""

    window_bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    accent_pressed: str
    on_accent: str
    danger: str
    danger_hover: str
    danger_pressed: str
    on_danger: str
    success: str
    track: str
    selection: str
    selection_text: str
    row_alt: str


@dataclass(frozen=True)
class Theme:
    """A palette plus typography and an 8px-based spacing scale."""

    name: str
    palette: Palette
    font_family: str = "Segoe UI"
    mono_family: str = "Cascadia Mono"

    # Spacing scale (px). Stick to these instead of ad-hoc pixel values so the
    # layout keeps a consistent rhythm.
    space_xs: int = 4
    space_sm: int = 8
    space_md: int = 12
    space_lg: int = 16
    space_xl: int = 24

    def font(self, size: int, weight: str = "normal") -> Tuple[str, int, str]:
        """A font tuple in the theme's family, e.g. ``theme.font(11, "bold")``."""

        return (self.font_family, size, weight)


# --- Concrete themes ---------------------------------------------------------
# Two ready-made skins. Duplicate one, tweak the hex values, give it a name, and
# register it in config.py's THEMES map to make it selectable from the CLI.

LIGHT_THEME = Theme(
    name="light",
    palette=Palette(
        window_bg="#eef1f6",
        surface="#ffffff",
        surface_alt="#f4f6fa",
        border="#d8dee9",
        text="#1b2431",
        text_muted="#64748b",
        accent="#2563eb",
        accent_hover="#1d4ed8",
        accent_pressed="#1e40af",
        on_accent="#ffffff",
        danger="#dc2626",
        danger_hover="#b91c1c",
        danger_pressed="#991b1b",
        on_danger="#ffffff",
        success="#16a34a",
        track="#e2e8f0",
        selection="#2563eb",
        selection_text="#ffffff",
        row_alt="#f6f8fb",
    ),
)

DARK_THEME = Theme(
    name="dark",
    palette=Palette(
        window_bg="#0f141b",
        surface="#1a2029",
        surface_alt="#222a35",
        border="#313b48",
        text="#e6edf3",
        text_muted="#94a3b8",
        accent="#3b82f6",
        accent_hover="#60a5fa",
        accent_pressed="#2563eb",
        on_accent="#ffffff",
        danger="#ef4444",
        danger_hover="#f87171",
        danger_pressed="#dc2626",
        on_danger="#ffffff",
        success="#22c55e",
        track="#2a3340",
        selection="#3b82f6",
        selection_text="#ffffff",
        row_alt="#1f2731",
    ),
)

THEMES = {theme.name: theme for theme in (LIGHT_THEME, DARK_THEME)}


def configure_styles(theme: Theme, root) -> None:
    """Apply ``theme`` to every named ttk style used by the window.

    Called once at startup and again whenever the theme is toggled; because the
    style *names* are stable, existing widgets restyle themselves automatically.
    """

    from tkinter import ttk  # local import keeps headless/sidecar builds tkinter-free

    p = theme.palette
    style = ttk.Style(root)
    style.theme_use("clam")

    # Frames / surfaces
    style.configure("App.TFrame", background=p.window_bg)
    style.configure("Surface.TFrame", background=p.surface)
    style.configure("Header.TFrame", background=p.surface_alt)

    # Cards
    style.configure(
        "Card.TLabelframe",
        background=p.surface,
        bordercolor=p.border,
        relief="solid",
        borderwidth=1,
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=p.surface,
        foreground=p.text_muted,
        font=theme.font(10, "bold"),
    )

    # Typography
    style.configure("Display.TLabel", background=p.surface, foreground=p.text, font=theme.font(30, "bold"))
    style.configure("Title.TLabel", background=p.surface_alt, foreground=p.text, font=theme.font(15, "bold"))
    style.configure("Subtitle.TLabel", background=p.surface_alt, foreground=p.text_muted, font=theme.font(9))
    style.configure("Body.TLabel", background=p.surface, foreground=p.text, font=theme.font(9))
    style.configure("Muted.TLabel", background=p.surface, foreground=p.text_muted, font=theme.font(9))
    style.configure("Status.TLabel", background=p.surface_alt, foreground=p.text, font=theme.font(9))
    style.configure("StatusStrong.TLabel", background=p.surface_alt, foreground=p.text, font=theme.font(9, "bold"))

    # Buttons
    style.configure(
        "Accent.TButton",
        background=p.accent,
        foreground=p.on_accent,
        borderwidth=0,
        focuscolor="none",
        font=theme.font(9, "bold"),
        padding=(14, 8),
    )
    style.map(
        "Accent.TButton",
        background=[("pressed", p.accent_pressed), ("active", p.accent_hover)],
    )
    style.configure(
        "Danger.TButton",
        background=p.danger,
        foreground=p.on_danger,
        borderwidth=0,
        focuscolor="none",
        font=theme.font(9, "bold"),
        padding=(14, 8),
    )
    style.map(
        "Danger.TButton",
        background=[("pressed", p.danger_pressed), ("active", p.danger_hover)],
    )
    style.configure(
        "Ghost.TButton",
        background=p.surface_alt,
        foreground=p.text,
        borderwidth=1,
        bordercolor=p.border,
        focuscolor="none",
        font=theme.font(9),
        padding=(10, 6),
    )
    style.map(
        "Ghost.TButton",
        background=[("active", p.border)],
        bordercolor=[("active", p.text_muted)],
    )

    # Scale (intensity slider)
    style.configure(
        "App.Horizontal.TScale",
        background=p.surface,
        troughcolor=p.track,
        bordercolor=p.surface,
        lightcolor=p.accent,
        darkcolor=p.accent,
    )

    # Separators / scrollbars
    style.configure("TSeparator", background=p.border)
    style.configure(
        "Vertical.TScrollbar",
        background=p.surface_alt,
        troughcolor=p.surface,
        bordercolor=p.surface,
        arrowcolor=p.text_muted,
    )

    # Treeview (pattern library)
    style.configure(
        "App.Treeview",
        background=p.surface,
        foreground=p.text,
        fieldbackground=p.surface,
        bordercolor=p.border,
        borderwidth=0,
        rowheight=28,
        font=theme.font(9),
    )
    style.configure(
        "App.Treeview.Heading",
        background=p.surface_alt,
        foreground=p.text_muted,
        font=theme.font(9, "bold"),
        relief="flat",
        padding=(8, 6),
    )
    style.map(
        "App.Treeview",
        background=[("selected", p.selection)],
        foreground=[("selected", p.selection_text)],
    )
    style.map("App.Treeview.Heading", background=[("active", p.border)])

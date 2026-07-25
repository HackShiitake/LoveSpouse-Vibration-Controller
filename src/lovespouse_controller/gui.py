"""Desktop control window (tkinter/ttk).

The window is intentionally split into small ``_build_*`` methods, one per
region, so a contributor can add or rearrange a panel without touching the rest.
All colors, fonts, and spacing come from :mod:`.theme`; this file never hard-codes
a hex value. Custom drawing (the intensity meter) lives in :class:`IntensityMeter`.

Extending the UI
----------------
* Restyle everything → edit :mod:`.theme`.
* Add a control → write a ``_build_<name>`` method and call it from ``_build``.
* React to output state → call :meth:`ControllerWindow.set_status`; the status
  dot and label update automatically.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, Optional

from .models import Pattern
from .playback import PlaybackService
from .theme import DARK_THEME, LIGHT_THEME, Theme, configure_styles

# Type of the optional callback used by the "Reload" button to re-scan patterns
# from disk. Returning a fresh mapping keeps the GUI decoupled from where
# patterns come from.
ReloadCallback = Callable[[], Dict[str, Pattern]]


class IntensityMeter:
    """A segmented 0–9 bar drawn on a Canvas, filled up to the current level.

    Pure view: it holds no playback state, just draws whatever value it is told.
    It redraws on resize, so it stays crisp at any window width.
    """

    def __init__(self, parent: tk.Widget, theme: Theme, levels: int = 9, height: int = 26) -> None:
        self._theme = theme
        self._levels = levels
        self._value = 0
        self.canvas = tk.Canvas(
            parent,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=theme.palette.surface,
        )
        self.canvas.bind("<Configure>", lambda _event: self._redraw())

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.canvas.configure(bg=theme.palette.surface)
        self._redraw()

    def set_value(self, value: int) -> None:
        self._value = max(0, min(self._levels, value))
        self._redraw()

    def _redraw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:  # not laid out yet
            return

        gap = 6
        seg_width = (width - gap * (self._levels - 1)) / self._levels
        palette = self._theme.palette
        for index in range(self._levels):
            x1 = index * (seg_width + gap)
            filled = index < self._value
            color = palette.accent if filled else palette.track
            self._rounded_rect(canvas, x1, 2, x1 + seg_width, height - 2, radius=5, fill=color)

    @staticmethod
    def _rounded_rect(canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, radius: float, **kwargs) -> None:
        radius = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
        points = [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]
        canvas.create_polygon(points, smooth=True, **kwargs)


class ControllerWindow:
    """Main application window: manual output, pattern library, and status."""

    def __init__(
        self,
        playback: PlaybackService,
        patterns: Dict[str, Pattern],
        theme: Theme = LIGHT_THEME,
        reload_patterns: Optional[ReloadCallback] = None,
    ) -> None:
        self._playback = playback
        self._patterns = patterns
        self._theme = theme
        self._reload_patterns = reload_patterns

        self.root = tk.Tk()
        self.root.title("LoveSpouse Operations Console")
        self.root.geometry("820x560")
        self.root.minsize(720, 500)
        self.root.configure(bg=theme.palette.window_bg)

        configure_styles(self._theme, self.root)
        self._build()
        self._bind_shortcuts()

    # --- public API ---------------------------------------------------------
    def set_status(self, status: str) -> None:
        """Thread-safe: update the status line and its colored indicator."""

        self.root.after(0, lambda: self._render_status(status))

    def run(self) -> None:
        self._center_on_screen()
        self.root.mainloop()

    # --- layout -------------------------------------------------------------
    def _build(self) -> None:
        self._build_menu()

        root_frame = ttk.Frame(self.root, style="App.TFrame", padding=self._theme.space_lg)
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=0, minsize=288)
        root_frame.columnconfigure(1, weight=1)
        root_frame.rowconfigure(1, weight=1)

        self._build_header(root_frame)
        self._build_control_panel(root_frame)
        self._build_pattern_table(root_frame)
        self._build_status_bar(root_frame)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Stop Output", accelerator="Esc", command=self._stop)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Toggle Light/Dark", accelerator="Ctrl+D", command=self._toggle_theme)
        menubar.add_cascade(label="View", menu=view_menu)

        self.root.config(menu=menubar)
        self._menubar = menubar
        self._menus = (file_menu, view_menu)
        self._apply_menu_colors()

    def _build_header(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent, style="Header.TFrame", padding=(self._theme.space_lg, self._theme.space_md))
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, self._theme.space_md))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Operations Console", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Local BLE controller and automation API",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        actions = ttk.Frame(header, style="Header.TFrame")
        actions.grid(row=0, column=1, rowspan=2, sticky="e")
        self._theme_button = ttk.Button(actions, text=self._theme_button_label(), style="Ghost.TButton", command=self._toggle_theme)
        self._theme_button.grid(row=0, column=0, padx=(0, self._theme.space_sm))
        ttk.Button(actions, text="Emergency Stop", style="Danger.TButton", command=self._stop).grid(row=0, column=1)

    def _build_control_panel(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="MANUAL OUTPUT", style="Card.TLabelframe", padding=self._theme.space_lg)
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, self._theme.space_md))
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Current intensity", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.strength_label = ttk.Label(panel, text="0", style="Display.TLabel")
        self.strength_label.grid(row=1, column=0, sticky="w")

        self._meter = IntensityMeter(panel, self._theme)
        self._meter.canvas.grid(row=2, column=0, sticky="ew", pady=(self._theme.space_sm, self._theme.space_md))

        self.strength_var = tk.IntVar(value=0)
        ttk.Scale(
            panel,
            from_=0,
            to=9,
            orient="horizontal",
            variable=self.strength_var,
            command=self._on_strength_change,
            style="App.Horizontal.TScale",
        ).grid(row=3, column=0, sticky="ew")

        ruler = ttk.Frame(panel, style="Surface.TFrame")
        ruler.grid(row=4, column=0, sticky="ew", pady=(self._theme.space_xs, self._theme.space_lg))
        for index in range(10):
            ruler.columnconfigure(index, weight=1)
            ttk.Label(ruler, text=str(index), style="Muted.TLabel").grid(row=0, column=index)

        ttk.Separator(panel).grid(row=5, column=0, sticky="ew", pady=(0, self._theme.space_md))
        ttk.Label(panel, text="Command mode", style="Muted.TLabel").grid(row=6, column=0, sticky="w")
        self.mode_value = ttk.Label(panel, text="Standby", style="Body.TLabel")
        self.mode_value.grid(row=7, column=0, sticky="w", pady=(2, self._theme.space_lg))

        ttk.Button(panel, text="Set Output To Zero", style="Danger.TButton", command=self._stop).grid(
            row=8, column=0, sticky="ew"
        )

    def _build_pattern_table(self, parent: ttk.Frame) -> None:
        panel = ttk.LabelFrame(parent, text="PATTERN LIBRARY", style="Card.TLabelframe", padding=self._theme.space_lg)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        columns = ("name", "author", "steps")
        self.pattern_table = ttk.Treeview(
            panel, columns=columns, show="headings", selectmode="browse", style="App.Treeview"
        )
        self.pattern_table.heading("name", text="Pattern")
        self.pattern_table.heading("author", text="Author")
        self.pattern_table.heading("steps", text="Steps")
        self.pattern_table.column("name", width=280, minwidth=180, anchor="w")
        self.pattern_table.column("author", width=150, minwidth=90, anchor="w")
        self.pattern_table.column("steps", width=70, minwidth=60, anchor="center")
        self.pattern_table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.pattern_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pattern_table.configure(yscrollcommand=scrollbar.set)

        self._populate_pattern_table()

        actions = ttk.Frame(panel, style="Surface.TFrame")
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(self._theme.space_md, 0))
        actions.columnconfigure(0, weight=1)

        self._pattern_count = ttk.Label(actions, style="Muted.TLabel")
        self._pattern_count.grid(row=0, column=0, sticky="w")
        if self._reload_patterns is not None:
            ttk.Button(actions, text="Reload", style="Ghost.TButton", command=self._reload).grid(
                row=0, column=1, padx=(0, self._theme.space_sm)
            )
        ttk.Button(actions, text="Play Selected", style="Accent.TButton", command=self._play_selected_pattern).grid(
            row=0, column=2, sticky="e"
        )
        self._update_pattern_count()

        self.pattern_table.bind("<Double-1>", self._play_selected_pattern)
        self.pattern_table.bind("<Return>", self._play_selected_pattern)

    def _build_status_bar(self, parent: ttk.Frame) -> None:
        status = ttk.Frame(parent, style="Header.TFrame", padding=(self._theme.space_md, self._theme.space_sm))
        status.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(self._theme.space_md, 0))
        status.columnconfigure(2, weight=1)

        self.status_dot = ttk.Label(status, text="●", style="StatusStrong.TLabel")
        self.status_dot.grid(row=0, column=0, sticky="w")
        self.status_value = ttk.Label(status, text="Ready", style="StatusStrong.TLabel")
        self.status_value.grid(row=0, column=1, sticky="w", padx=(self._theme.space_sm, 0))
        ttk.Label(status, text="API: localhost:4545", style="Status.TLabel").grid(row=0, column=2, sticky="e")

        self._render_status("Ready")

    # --- events -------------------------------------------------------------
    def _on_strength_change(self, value: str) -> None:
        strength = int(float(value))
        self.strength_label.config(text=str(strength))
        self._meter.set_value(strength)
        if strength == 0:
            self.mode_value.config(text="Standby")
            self._playback.stop_all()
            self.set_status("Ready")
        else:
            self.mode_value.config(text="Manual continuous output")
            self._playback.start_continuous(strength)

    def _play_selected_pattern(self, _event=None) -> None:
        selection = self.pattern_table.selection()
        if not selection:
            return
        display_name = selection[0]
        self.strength_var.set(0)
        self.strength_label.config(text="0")
        self._meter.set_value(0)
        self.mode_value.config(text="Pattern playback")
        self._playback.play_pattern(self._patterns[display_name])

    def _stop(self, _event=None) -> None:
        self.strength_var.set(0)
        self.strength_label.config(text="0")
        self._meter.set_value(0)
        self.mode_value.config(text="Standby")
        self._playback.stop_all()
        self.root.after(1000, lambda: self.set_status("Ready"))

    def _reload(self) -> None:
        if self._reload_patterns is None:
            return
        self._patterns = self._reload_patterns()
        self._populate_pattern_table()
        self._update_pattern_count()
        self.set_status(f"Reloaded {len(self._patterns)} patterns")

    def _toggle_theme(self, _event=None) -> None:
        self._theme = DARK_THEME if self._theme.name == "light" else LIGHT_THEME
        self._apply_theme()

    # --- helpers ------------------------------------------------------------
    def _populate_pattern_table(self) -> None:
        self.pattern_table.delete(*self.pattern_table.get_children())
        for index, (display_name, pattern) in enumerate(self._patterns.items()):
            tag = "odd" if index % 2 else "even"
            self.pattern_table.insert(
                "",
                "end",
                iid=display_name,
                values=(pattern.name, pattern.author or "-", len(pattern.commands)),
                tags=(tag,),
            )
        self._apply_zebra()

    def _apply_zebra(self) -> None:
        self.pattern_table.tag_configure("odd", background=self._theme.palette.row_alt)
        self.pattern_table.tag_configure("even", background=self._theme.palette.surface)

    def _update_pattern_count(self) -> None:
        self._pattern_count.config(text=f"{len(self._patterns)} patterns available")

    def _render_status(self, status: str) -> None:
        self.status_value.config(text=status)
        self.status_dot.config(foreground=self._status_color(status))

    def _status_color(self, status: str) -> str:
        text = status.lower()
        palette = self._theme.palette
        if any(word in text for word in ("running", "playing", "reload")):
            return palette.accent
        if "error" in text or "abort" in text:
            return palette.danger
        if "stopped" in text or "standby" in text:
            return palette.text_muted
        return palette.success

    def _theme_button_label(self) -> str:
        return "Dark mode" if self._theme.name == "light" else "Light mode"

    def _apply_theme(self) -> None:
        configure_styles(self._theme, self.root)
        self.root.configure(bg=self._theme.palette.window_bg)
        self._meter.set_theme(self._theme)
        self._apply_zebra()
        self._apply_menu_colors()
        self._theme_button.config(text=self._theme_button_label())
        self._render_status(self.status_value.cget("text"))

    def _apply_menu_colors(self) -> None:
        palette = self._theme.palette
        for menu in (self._menubar, *self._menus):
            menu.configure(
                background=palette.surface,
                foreground=palette.text,
                activebackground=palette.accent,
                activeforeground=palette.on_accent,
                borderwidth=0,
            )

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Escape>", self._stop)
        self.root.bind("<Control-d>", self._toggle_theme)

    def _center_on_screen(self) -> None:
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")

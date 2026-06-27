from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict

from .models import Pattern
from .playback import PlaybackService


class EnterpriseStyle:
    WINDOW_BG = "#f3f5f8"
    SURFACE = "#ffffff"
    SURFACE_ALT = "#eef2f6"
    BORDER = "#cfd6df"
    TEXT = "#182230"
    TEXT_MUTED = "#5d6978"
    ACCENT = "#1f6feb"
    ACCENT_ACTIVE = "#185abc"
    DANGER = "#b42318"
    DANGER_ACTIVE = "#912018"
    STATUS_READY = "#027a48"

    @staticmethod
    def configure() -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("App.TFrame", background=EnterpriseStyle.WINDOW_BG)
        style.configure("Surface.TFrame", background=EnterpriseStyle.SURFACE)
        style.configure("Header.TFrame", background=EnterpriseStyle.SURFACE_ALT)
        style.configure(
            "App.TLabelframe",
            background=EnterpriseStyle.SURFACE,
            bordercolor=EnterpriseStyle.BORDER,
            relief="solid",
        )
        style.configure(
            "App.TLabelframe.Label",
            background=EnterpriseStyle.SURFACE,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "Title.TLabel",
            background=EnterpriseStyle.SURFACE_ALT,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 14, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=EnterpriseStyle.SURFACE_ALT,
            foreground=EnterpriseStyle.TEXT_MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "App.TLabel",
            background=EnterpriseStyle.SURFACE,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Muted.TLabel",
            background=EnterpriseStyle.SURFACE,
            foreground=EnterpriseStyle.TEXT_MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Metric.TLabel",
            background=EnterpriseStyle.SURFACE,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "Status.TLabel",
            background=EnterpriseStyle.SURFACE_ALT,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Ready.TLabel",
            background=EnterpriseStyle.SURFACE_ALT,
            foreground=EnterpriseStyle.STATUS_READY,
            font=("Segoe UI", 9, "bold"),
        )
        style.configure(
            "App.Horizontal.TScale",
            background=EnterpriseStyle.SURFACE,
            troughcolor=EnterpriseStyle.SURFACE_ALT,
            bordercolor=EnterpriseStyle.BORDER,
            lightcolor=EnterpriseStyle.BORDER,
            darkcolor=EnterpriseStyle.BORDER,
        )
        style.configure(
            "Primary.TButton",
            background=EnterpriseStyle.ACCENT,
            foreground="#ffffff",
            borderwidth=1,
            focuscolor="none",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6),
        )
        style.map(
            "Primary.TButton",
            background=[("active", EnterpriseStyle.ACCENT_ACTIVE), ("pressed", EnterpriseStyle.ACCENT_ACTIVE)],
        )
        style.configure(
            "Danger.TButton",
            background=EnterpriseStyle.DANGER,
            foreground="#ffffff",
            borderwidth=1,
            focuscolor="none",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6),
        )
        style.map(
            "Danger.TButton",
            background=[("active", EnterpriseStyle.DANGER_ACTIVE), ("pressed", EnterpriseStyle.DANGER_ACTIVE)],
        )
        style.configure(
            "Treeview",
            background=EnterpriseStyle.SURFACE,
            foreground=EnterpriseStyle.TEXT,
            fieldbackground=EnterpriseStyle.SURFACE,
            bordercolor=EnterpriseStyle.BORDER,
            rowheight=26,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=EnterpriseStyle.SURFACE_ALT,
            foreground=EnterpriseStyle.TEXT,
            font=("Segoe UI", 9, "bold"),
            relief="flat",
        )
        style.map("Treeview", background=[("selected", EnterpriseStyle.ACCENT)])


class ControllerWindow:
    def __init__(self, playback: PlaybackService, patterns: Dict[str, Pattern]) -> None:
        self._playback = playback
        self._patterns = patterns
        self.root = tk.Tk()
        self.root.title("LoveSpouse Operations Console")
        self.root.geometry("760x520")
        self.root.minsize(700, 480)
        self.root.configure(bg=EnterpriseStyle.WINDOW_BG)
        EnterpriseStyle.configure()
        self._build()

    def set_status(self, status: str) -> None:
        self.root.after(0, lambda: self.status_value.config(text=status))

    def run(self) -> None:
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.root.winfo_width() // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"+{x}+{y}")
        self.root.mainloop()

    def _build(self) -> None:
        self._build_menu()

        root_frame = ttk.Frame(self.root, style="App.TFrame", padding=14)
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=0, minsize=260)
        root_frame.columnconfigure(1, weight=1)
        root_frame.rowconfigure(1, weight=1)

        self._build_header(root_frame)
        self._build_control_panel(root_frame)
        self._build_pattern_table(root_frame)
        self._build_status_bar(root_frame)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Stop Output", command=self._stop)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    def _build_header(self, parent) -> None:
        header = ttk.Frame(parent, style="Header.TFrame", padding=(14, 10))
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Operations Console", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Local BLE controller and automation API",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        ttk.Button(header, text="Emergency Stop", command=self._stop, style="Danger.TButton").grid(
            row=0,
            column=1,
            rowspan=2,
            sticky="e",
        )

    def _build_control_panel(self, parent) -> None:
        panel = ttk.LabelFrame(parent, text="Manual Output", style="App.TLabelframe", padding=14)
        panel.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="Current intensity", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        self.strength_var = tk.IntVar(value=0)
        self.strength_label = ttk.Label(panel, text="0", style="Metric.TLabel")
        self.strength_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

        ttk.Scale(
            panel,
            from_=0,
            to=9,
            orient="horizontal",
            variable=self.strength_var,
            command=self._on_strength_change,
            style="App.Horizontal.TScale",
        ).grid(row=2, column=0, sticky="ew")

        ruler = ttk.Frame(panel, style="Surface.TFrame")
        ruler.grid(row=3, column=0, sticky="ew", pady=(4, 16))
        for index in range(10):
            ruler.columnconfigure(index, weight=1)
            ttk.Label(ruler, text=str(index), style="Muted.TLabel").grid(row=0, column=index)

        ttk.Separator(panel).grid(row=4, column=0, sticky="ew", pady=(0, 14))
        ttk.Label(panel, text="Command mode", style="Muted.TLabel").grid(row=5, column=0, sticky="w")
        self.mode_value = ttk.Label(panel, text="Standby", style="App.TLabel")
        self.mode_value.grid(row=6, column=0, sticky="w", pady=(2, 16))

        ttk.Button(panel, text="Set Output To Zero", command=self._stop, style="Danger.TButton").grid(
            row=7,
            column=0,
            sticky="ew",
        )

    def _build_pattern_table(self, parent) -> None:
        panel = ttk.LabelFrame(parent, text="Pattern Library", style="App.TLabelframe", padding=14)
        panel.grid(row=1, column=1, sticky="nsew")
        panel.rowconfigure(0, weight=1)
        panel.columnconfigure(0, weight=1)

        columns = ("name", "author", "steps")
        self.pattern_table = ttk.Treeview(panel, columns=columns, show="headings", selectmode="browse")
        self.pattern_table.heading("name", text="Pattern")
        self.pattern_table.heading("author", text="Author")
        self.pattern_table.heading("steps", text="Steps")
        self.pattern_table.column("name", width=260, minwidth=180, anchor="w")
        self.pattern_table.column("author", width=140, minwidth=90, anchor="w")
        self.pattern_table.column("steps", width=70, minwidth=60, anchor="center")
        self.pattern_table.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(panel, orient="vertical", command=self.pattern_table.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.pattern_table.configure(yscrollcommand=scrollbar.set)

        for display_name, pattern in self._patterns.items():
            self.pattern_table.insert(
                "",
                "end",
                iid=display_name,
                values=(pattern.name, pattern.author or "-", len(pattern.commands)),
            )

        actions = ttk.Frame(panel, style="Surface.TFrame")
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure(0, weight=1)

        ttk.Label(actions, text=f"{len(self._patterns)} patterns available", style="Muted.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Button(actions, text="Play Selected", command=self._play_selected_pattern, style="Primary.TButton").grid(
            row=0,
            column=1,
            sticky="e",
        )

        self.pattern_table.bind("<Double-1>", self._play_selected_pattern)
        self.pattern_table.bind("<Return>", self._play_selected_pattern)

    def _build_status_bar(self, parent) -> None:
        status = ttk.Frame(parent, style="Header.TFrame", padding=(10, 7))
        status.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        status.columnconfigure(1, weight=1)

        ttk.Label(status, text="System status:", style="Status.TLabel").grid(row=0, column=0, sticky="w")
        self.status_value = ttk.Label(status, text="Ready", style="Ready.TLabel")
        self.status_value.grid(row=0, column=1, sticky="w", padx=(6, 0))
        ttk.Label(status, text="API: localhost:4545", style="Status.TLabel").grid(row=0, column=2, sticky="e")

    def _on_strength_change(self, value: str) -> None:
        strength = int(float(value))
        self.strength_label.config(text=str(strength))
        if strength == 0:
            self.mode_value.config(text="Standby")
            self._playback.stop_all()
            self.set_status("Ready")
        else:
            self.mode_value.config(text="Manual continuous output")
            self._playback.start_continuous(strength)

    def _play_selected_pattern(self, event=None) -> None:
        selection = self.pattern_table.selection()
        if not selection:
            return
        display_name = selection[0]
        self.strength_var.set(0)
        self.strength_label.config(text="0")
        self.mode_value.config(text="Pattern playback")
        self._playback.play_pattern(self._patterns[display_name])

    def _stop(self) -> None:
        self.strength_var.set(0)
        self.strength_label.config(text="0")
        self.mode_value.config(text="Standby")
        self._playback.stop_all()
        self.root.after(1000, lambda: self.set_status("Ready"))

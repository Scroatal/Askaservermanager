import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
import winreg
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_NAME = "ASKA Server Manager"
APP_VERSION = "0.1.1"
SOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_DIR
SETTINGS_FILE = APP_DIR / "settings.json"
MOD_SOURCES_FILE = APP_DIR / "mods.json"
ASSET_FILE = APP_DIR / "assets" / "aska_manager_icon.png"
SERVER_EXE_NAME = "AskaServer.exe"
ASKA_DEDICATED_SERVER_APP_ID = "3246670"
NEXUS_GAME_DOMAIN = "aska"
BACKUP_PREFIX = "backup_"
BACKUP_TIME_FORMAT = "%Y-%m-%d_%H-%M"

DEFAULT_INSTALL = Path(r"E:\steam\steamapps\common\ASKA Dedicated Server")
DEFAULT_BACKUPS = Path(r"E:\aska_backups")
DEFAULT_SAVE = Path(os.path.expandvars(
    r"%USERPROFILE%\AppData\LocalLow\Sand Sailor Studio\Aska\data\server"
))

DEFAULT_SETTINGS = {
    "server_install_path": str(DEFAULT_INSTALL),
    "server_bat_path": str(DEFAULT_INSTALL / "AskaServer.bat"),
    "server_config_path": str(DEFAULT_INSTALL / "server properties.txt"),
    "steamcmd_path": r"C:\steamcmd\steamcmd.exe",
    "bepinex_plugins_path": str(DEFAULT_INSTALL / "BepInEx" / "plugins"),
    "bepinex_config_path": str(DEFAULT_INSTALL / "BepInEx" / "config"),
    "save_folder_path": str(DEFAULT_SAVE),
    "backup_folder_path": str(DEFAULT_BACKUPS),
    "auto_backup_enabled": False,
    "backup_on_startup": False,
    "backup_interval_minutes": 60,
    "retention_hours": 24,
    "nexus_api_key": "",
}

CONFIG_FIELDS = [
    "save id",
    "display name",
    "server name",
    "seed",
    "password",
    "steam game port",
    "steam query port",
    "authentication token",
    "region",
    "keep server world alive",
    "autosave style",
    "mode",
    "terrain aspect",
    "terrain height",
    "starting season",
    "year length",
    "precipitation",
    "day length",
    "structure decay",
    "clothing decay",
    "invasion dificulty",
    "monster density",
    "monster population",
    "wulfar population",
    "herbivore population",
    "bear population",
]

COLORS = {
    "bg": "#1a1a1a",
    "panel": "#242424",
    "panel2": "#303030",
    "border": "#404040",
    "text": "#f8f2f0",
    "muted": "#b8b0ac",
    "accent": "#fdac00",
    "accent_dark": "#c98200",
    "danger": "#b93228",
    "danger_dark": "#81241f",
    "ok": "#63b96f",
}


def now_stamp() -> str:
    return datetime.now().strftime(BACKUP_TIME_FORMAT)


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default.copy()
    merged = default.copy()
    merged.update(data)
    return merged


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def extract_nexus_mod_id(url: str) -> str:
    match = re.search(r"/mods/(\d+)", url.strip(), re.IGNORECASE)
    return match.group(1) if match else ""


def human_size(path: Path) -> str:
    total = 0
    if not path.exists():
        return "0 B"
    if path.is_file():
        try:
            total = path.stat().st_size
        except OSError:
            total = 0
    else:
        for item in path.rglob("*"):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except OSError:
                pass
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(total)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{total} B"


def parse_backup_time(name: str):
    if not name.startswith(BACKUP_PREFIX):
        return None
    try:
        return datetime.strptime(name.removeprefix(BACKUP_PREFIX), BACKUP_TIME_FORMAT)
    except ValueError:
        return None


def parse_retained_backup_time(name: str):
    prefixes = [BACKUP_PREFIX, "secure_before_wipe_", "emergency_before_wipe_", "emergency_before_restore_"]
    for prefix in prefixes:
        if name.startswith(prefix):
            timestamp = name.removeprefix(prefix)
            if len(timestamp) >= len("YYYY-MM-DD_HH-mm"):
                timestamp = timestamp[:16]
            try:
                return datetime.strptime(timestamp, BACKUP_TIME_FORMAT)
            except ValueError:
                return None
    return None


class AskaServerManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.main_thread_id = threading.get_ident()
        self.title(APP_NAME)
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.settings = read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.mod_sources = read_json(MOD_SOURCES_FILE, {})
        self.auto_backup_job = None
        self.status_job = None
        self.config_vars = {}
        self.path_vars = {}
        self.dashboard_vars = {}
        self.log_text = None
        self.backup_tree = None
        self.mod_plugin_tree = None
        self.mod_config_tree = None
        self.mod_config_text = None
        self.current_mod_config_path = None
        self.mod_source_label_var = None
        self.icon_image = None
        self.dashboard_icon_image = None

        self.configure(bg=COLORS["bg"])
        self.build_styles()
        self.build_ui()
        self.ensure_settings_file()
        self.log("App startup.")
        self.refresh_all()
        if self.settings.get("backup_on_startup"):
            self.run_threaded("Startup backup", self.create_backup)
        self.schedule_status_refresh()
        self.schedule_auto_backup()
        self.after(3500, lambda: self.check_server_update(show_dialog=False))

    def build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        default_font = ("Segoe UI", 10)
        heading_font = ("Georgia", 20, "bold")
        self.option_add("*Font", default_font)
        style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], fieldbackground=COLORS["panel"])
        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Panel.TFrame", background=COLORS["panel"], relief="flat")
        style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", foreground=COLORS["muted"], background=COLORS["bg"])
        style.configure("Panel.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("Heading.TLabel", font=heading_font, foreground=COLORS["accent"], background=COLORS["bg"])
        style.configure("Status.TLabel", font=("Segoe UI", 12, "bold"), background=COLORS["panel"])
        style.configure("TNotebook", background=COLORS["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["panel2"], foreground=COLORS["text"], padding=(16, 9))
        style.map("TNotebook.Tab", background=[("selected", COLORS["accent"])], foreground=[("selected", "#201e1d")])
        style.configure("TButton", background=COLORS["panel2"], foreground=COLORS["text"], borderwidth=1, padding=(12, 8))
        style.map("TButton", background=[("active", COLORS["border"])])
        style.configure("Accent.TButton", background=COLORS["accent"], foreground="#201e1d")
        style.map("Accent.TButton", background=[("active", COLORS["accent_dark"])])
        style.configure("Danger.TButton", background=COLORS["danger"], foreground=COLORS["text"])
        style.map("Danger.TButton", background=[("active", COLORS["danger_dark"])])
        style.configure("TCheckbutton", background=COLORS["bg"], foreground=COLORS["text"])
        style.configure("Treeview", background="#181818", foreground=COLORS["text"], fieldbackground="#181818", rowheight=28)
        style.configure("Treeview.Heading", background=COLORS["panel2"], foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#111111", foreground=COLORS["text"], insertcolor=COLORS["text"])

    def build_ui(self):
        header = ttk.Frame(self, padding=(18, 14, 18, 10))
        header.pack(fill="x")
        asset_file = self.resource_path("assets/aska_manager_icon.png")
        if asset_file.exists():
            try:
                self.icon_image = tk.PhotoImage(file=str(asset_file)).subsample(16, 16)
                ttk.Label(header, image=self.icon_image, background=COLORS["bg"]).pack(side="left", padx=(0, 12))
                self.iconphoto(True, self.icon_image)
            except tk.TclError:
                self.icon_image = None
        title_box = ttk.Frame(header)
        title_box.pack(side="left", fill="x", expand=True)
        ttk.Label(title_box, text=APP_NAME.upper(), style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            title_box,
            text=f"Local Windows manager for ASKA dedicated server operations - v{APP_VERSION}",
            style="Muted.TLabel",
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.dashboard_tab = ttk.Frame(self.notebook, padding=14)
        self.backups_tab = ttk.Frame(self.notebook, padding=14)
        self.config_tab = ttk.Frame(self.notebook, padding=14)
        self.mods_tab = ttk.Frame(self.notebook, padding=14)
        self.settings_tab = ttk.Frame(self.notebook, padding=14)
        self.logs_tab = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.backups_tab, text="Backups")
        self.notebook.add(self.config_tab, text="Config")
        self.notebook.add(self.mods_tab, text="Mods")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.logs_tab, text="Logs")

        self.build_dashboard_tab()
        self.build_backups_tab()
        self.build_config_tab()
        self.build_mods_tab()
        self.build_settings_tab()
        self.build_logs_tab()

    def resource_path(self, relative_path: str) -> Path:
        bundle_dir = getattr(sys, "_MEIPASS", None)
        if bundle_dir:
            return Path(bundle_dir) / relative_path
        return SOURCE_DIR / relative_path

    def panel(self, parent, title=None):
        frame = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        if title:
            ttk.Label(frame, text=title.upper(), style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))
        return frame

    def build_dashboard_tab(self):
        top = ttk.Frame(self.dashboard_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Folders and backups")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        asset_file = self.resource_path("assets/aska_manager_icon.png")
        if asset_file.exists():
            try:
                self.dashboard_icon_image = tk.PhotoImage(file=str(asset_file)).subsample(6, 6)
                ttk.Label(left, image=self.dashboard_icon_image, background=COLORS["panel"]).pack(pady=(0, 14))
            except tk.TclError:
                self.dashboard_icon_image = None

        self.dashboard_vars["status"] = tk.StringVar(value="Checking...")
        status_row = ttk.Frame(left, style="Panel.TFrame")
        status_row.pack(fill="x", pady=(0, 14))
        ttk.Label(status_row, text="Server status", style="Panel.TLabel").pack(side="left")
        self.status_label = ttk.Label(status_row, textvariable=self.dashboard_vars["status"], style="Status.TLabel")
        self.status_label.pack(side="right")

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(0, 16))
        ttk.Button(buttons, text="Start Server", style="Accent.TButton", command=self.start_server).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Stop Server", command=self.stop_server).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Server", command=self.restart_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Now", style="Accent.TButton", command=lambda: self.run_threaded("Backup", self.create_backup)).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install Folder", command=lambda: self.open_path(self.path("server_install_path"))).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Save Folder", command=lambda: self.open_path(self.path("save_folder_path"))).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Server Update", command=lambda: self.check_server_update(show_dialog=True)).grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Update Server", style="Accent.TButton", command=self.update_server_with_steamcmd).grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        danger = self.panel(left, "Dangerous actions")
        danger.pack(fill="x", pady=(12, 0))
        ttk.Label(
            danger,
            text="Wiping refuses to run while the server is active and makes an emergency backup first.",
            style="Panel.TLabel",
            wraplength=480,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Button(danger, text="Wipe Current Server Save", style="Danger.TButton", command=self.wipe_save).pack(anchor="w")

        for key, label in [
            ("detected_process", "Detected process"),
            ("server_update_status", "Server update"),
            ("server_install_path", "Install path"),
            ("save_folder_path", "Save folder"),
            ("backup_folder_path", "Backup folder"),
            ("last_backup", "Last backup"),
            ("backup_count", "Backups stored"),
        ]:
            self.dashboard_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(right, style="Panel.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            ttk.Label(row, textvariable=self.dashboard_vars[key], style="Panel.TLabel", wraplength=430).pack(side="left", fill="x", expand=True)

        auto = ttk.Frame(right, style="Panel.TFrame")
        auto.pack(fill="x", pady=(16, 0))
        self.auto_backup_var = tk.BooleanVar(value=bool(self.settings.get("auto_backup_enabled")))
        self.startup_backup_var = tk.BooleanVar(value=bool(self.settings.get("backup_on_startup")))
        ttk.Checkbutton(auto, text="Enable hourly backups", variable=self.auto_backup_var, command=self.toggle_auto_backup).pack(anchor="w")
        ttk.Checkbutton(auto, text="Run backup on app startup", variable=self.startup_backup_var, command=self.toggle_startup_backup).pack(anchor="w", pady=(4, 0))
        ttk.Button(auto, text="Delete backups older than retention now", command=self.cleanup_now).pack(anchor="w", pady=(12, 0))

    def build_backups_tab(self):
        top = ttk.Frame(self.backups_tab)
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Refresh", command=self.refresh_backups).pack(side="left")
        ttk.Button(top, text="Backup Now", style="Accent.TButton", command=lambda: self.run_threaded("Backup", self.create_backup)).pack(side="left", padx=8)
        ttk.Button(top, text="Restore Selected Backup", style="Danger.TButton", command=self.restore_selected_backup).pack(side="left")
        ttk.Button(top, text="Open Backup Folder", command=lambda: self.open_path(self.path("backup_folder_path"))).pack(side="left", padx=8)

        columns = ("name", "date", "size")
        self.backup_tree = ttk.Treeview(self.backups_tab, columns=columns, show="headings", selectmode="browse")
        self.backup_tree.heading("name", text="Backup")
        self.backup_tree.heading("date", text="Date/time")
        self.backup_tree.heading("size", text="Approx size")
        self.backup_tree.column("name", width=360)
        self.backup_tree.column("date", width=190)
        self.backup_tree.column("size", width=120)
        self.backup_tree.pack(fill="both", expand=True)

    def build_config_tab(self):
        actions = ttk.Frame(self.config_tab)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Load Config", command=self.load_config).pack(side="left")
        ttk.Button(actions, text="Save Config", style="Accent.TButton", command=self.save_config).pack(side="left", padx=8)
        ttk.Button(actions, text="Open in Notepad", command=self.open_config_notepad).pack(side="left")

        canvas = tk.Canvas(self.config_tab, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.config_tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        form = ttk.Frame(canvas, style="Panel.TFrame", padding=14)
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def resize_form(event):
            canvas.itemconfigure(form_window, width=event.width)

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_form)
        form.bind("<Configure>", update_scroll_region)

        ttk.Label(form, text="RECOGNISED SETTINGS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row_index, key in enumerate(CONFIG_FIELDS):
            ttk.Label(form, text=key, width=26, style="Panel.TLabel").grid(row=row_index + 1, column=0, sticky="w", pady=4)
            var = tk.StringVar()
            self.config_vars[key] = var
            entry = ttk.Entry(form, textvariable=var)
            entry.grid(row=row_index + 1, column=1, sticky="ew", pady=4, padx=(8, 0))
        form.columnconfigure(1, weight=1)

    def build_mods_tab(self):
        actions = ttk.Frame(self.mods_tab)
        actions.pack(fill="x", pady=(0, 10))
        ttk.Button(actions, text="Refresh", command=self.refresh_mods).pack(side="left")
        ttk.Button(actions, text="Open Plugins Folder", command=lambda: self.open_path(self.path("bepinex_plugins_path"))).pack(side="left", padx=8)
        ttk.Button(actions, text="Open Config Folder", command=lambda: self.open_path(self.path("bepinex_config_path"))).pack(side="left")
        ttk.Button(actions, text="Backup BepInEx Mods", style="Accent.TButton", command=lambda: self.run_threaded("BepInEx backup", self.backup_bepinex)).pack(side="left", padx=8)
        ttk.Button(actions, text="Install Mod ZIP", command=self.install_mod_zip).pack(side="left")
        ttk.Button(actions, text="Set Nexus URL", command=self.set_selected_mod_source).pack(side="left", padx=8)
        ttk.Button(actions, text="Open Nexus Page", command=self.open_selected_mod_source).pack(side="left")
        ttk.Button(actions, text="Check Nexus Updates", command=self.check_nexus_updates).pack(side="left", padx=8)

        panes = ttk.PanedWindow(self.mods_tab, orient="horizontal")
        panes.pack(fill="both", expand=True)

        left = ttk.Frame(panes, style="Panel.TFrame", padding=10)
        right = ttk.Frame(panes, style="Panel.TFrame", padding=10)
        panes.add(left, weight=1)
        panes.add(right, weight=2)

        ttk.Label(left, text="PLUGIN DLLS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        plugin_columns = ("name", "size", "modified")
        self.mod_plugin_tree = ttk.Treeview(left, columns=plugin_columns, show="headings", height=7)
        for col, heading, width in [("name", "Plugin", 230), ("size", "Size", 85), ("modified", "Modified", 150)]:
            self.mod_plugin_tree.heading(col, text=heading)
            self.mod_plugin_tree.column(col, width=width)
        self.mod_plugin_tree.pack(fill="x", pady=(8, 14))
        self.mod_plugin_tree.bind("<<TreeviewSelect>>", self.update_selected_mod_source_label)

        self.mod_source_label_var = tk.StringVar(value="Nexus source: select a plugin")
        ttk.Label(left, textvariable=self.mod_source_label_var, style="Panel.TLabel", wraplength=460).pack(anchor="w", pady=(0, 14))

        ttk.Label(left, text="CONFIG FILES", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        config_columns = ("name", "size", "modified")
        self.mod_config_tree = ttk.Treeview(left, columns=config_columns, show="headings", height=11, selectmode="browse")
        for col, heading, width in [("name", "Config", 230), ("size", "Size", 85), ("modified", "Modified", 150)]:
            self.mod_config_tree.heading(col, text=heading)
            self.mod_config_tree.column(col, width=width)
        self.mod_config_tree.pack(fill="both", expand=True, pady=(8, 0))
        self.mod_config_tree.bind("<<TreeviewSelect>>", self.load_selected_mod_config)

        editor_actions = ttk.Frame(right, style="Panel.TFrame")
        editor_actions.pack(fill="x", pady=(0, 8))
        self.mod_config_label_var = tk.StringVar(value="Select a .cfg file to edit")
        ttk.Label(editor_actions, textvariable=self.mod_config_label_var, style="Panel.TLabel").pack(side="left", fill="x", expand=True)
        ttk.Button(editor_actions, text="Reload", command=self.reload_current_mod_config).pack(side="right")
        ttk.Button(editor_actions, text="Save Config", style="Accent.TButton", command=self.save_current_mod_config).pack(side="right", padx=8)

        self.mod_config_text = tk.Text(
            right,
            bg="#111111",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="none",
            undo=True,
        )
        text_scroll_y = ttk.Scrollbar(right, orient="vertical", command=self.mod_config_text.yview)
        text_scroll_x = ttk.Scrollbar(right, orient="horizontal", command=self.mod_config_text.xview)
        self.mod_config_text.configure(yscrollcommand=text_scroll_y.set, xscrollcommand=text_scroll_x.set)
        self.mod_config_text.pack(side="left", fill="both", expand=True)
        text_scroll_y.pack(side="right", fill="y")
        text_scroll_x.pack(side="bottom", fill="x")

    def build_settings_tab(self):
        form = ttk.Frame(self.settings_tab, style="Panel.TFrame", padding=14)
        form.pack(fill="x")
        ttk.Label(form, text="PATHS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))
        ttk.Button(form, text="Auto-detect Paths", style="Accent.TButton", command=self.autodetect_paths).grid(row=0, column=2, sticky="e", pady=(0, 10))
        for row_index, (key, label, is_file) in enumerate([
            ("server_install_path", "Server install folder", False),
            ("server_bat_path", "Launcher batch file", True),
            ("server_config_path", "Server properties file", True),
            ("steamcmd_path", "SteamCMD executable", True),
            ("bepinex_plugins_path", "BepInEx plugins folder", False),
            ("bepinex_config_path", "BepInEx config folder", False),
            ("save_folder_path", "Save folder", False),
            ("backup_folder_path", "Backup folder", False),
        ]):
            grid_row = row_index + 1
            ttk.Label(form, text=label, width=24, style="Panel.TLabel").grid(row=grid_row, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=str(self.settings.get(key, "")))
            self.path_vars[key] = var
            ttk.Entry(form, textvariable=var).grid(row=grid_row, column=1, sticky="ew", padx=8, pady=5)
            ttk.Button(form, text="Browse", command=lambda k=key, f=is_file: self.browse_path(k, f)).grid(row=grid_row, column=2, pady=5)
        form.columnconfigure(1, weight=1)

        opts = ttk.Frame(self.settings_tab, style="Panel.TFrame", padding=14)
        opts.pack(fill="x", pady=(14, 0))
        ttk.Label(opts, text="BACKUP POLICY", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.interval_var = tk.StringVar(value=str(self.settings.get("backup_interval_minutes", 60)))
        self.retention_var = tk.StringVar(value=str(self.settings.get("retention_hours", 24)))
        ttk.Label(opts, text="Backup interval minutes", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(opts, textvariable=self.interval_var, width=12).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(opts, text="Retention hours", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(opts, textvariable=self.retention_var, width=12).grid(row=2, column=1, sticky="w", pady=5)
        ttk.Button(opts, text="Save Settings", style="Accent.TButton", command=self.save_settings_from_ui).grid(row=3, column=0, sticky="w", pady=(12, 0))

        nexus = ttk.Frame(self.settings_tab, style="Panel.TFrame", padding=14)
        nexus.pack(fill="x", pady=(14, 0))
        ttk.Label(nexus, text="NEXUS MODS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.nexus_api_key_var = tk.StringVar(value=str(self.settings.get("nexus_api_key", "")))
        ttk.Label(nexus, text="Nexus API key", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(nexus, textvariable=self.nexus_api_key_var, show="*", width=52).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(
            nexus,
            text="Optional. Used only for checking tracked Nexus mod metadata. Manual ZIP install works without it.",
            style="Panel.TLabel",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
        nexus.columnconfigure(1, weight=1)

    def build_logs_tab(self):
        self.log_text = tk.Text(
            self.logs_tab,
            bg="#111111",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="word",
            height=18,
        )
        self.log_text.pack(fill="both", expand=True)

    def path(self, key: str) -> Path:
        return Path(os.path.expandvars(str(self.settings.get(key, "")))).expanduser()

    def ensure_settings_file(self):
        if not SETTINGS_FILE.exists():
            write_json(SETTINGS_FILE, self.settings)
        if not MOD_SOURCES_FILE.exists():
            write_json(MOD_SOURCES_FILE, self.mod_sources)

    def log(self, message: str):
        line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}"
        print(line)
        if threading.get_ident() != self.main_thread_id:
            self.after(0, self.append_log_line, line)
        else:
            self.append_log_line(line)
        try:
            backup_dir = self.path("backup_folder_path")
            backup_dir.mkdir(parents=True, exist_ok=True)
            with (backup_dir / "aska_manager.log").open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        except OSError:
            pass

    def append_log_line(self, line: str):
        if self.log_text:
            self.log_text.configure(state="normal")
            self.log_text.insert("end", line + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

    def refresh_all(self):
        self.refresh_status()
        self.refresh_dashboard()
        self.refresh_backups()
        self.refresh_mods()
        self.load_config(silent=True)

    def refresh_dashboard(self):
        backup_dir = self.path("backup_folder_path")
        backups = self.list_backups()
        self.dashboard_vars["server_install_path"].set(str(self.path("server_install_path")))
        self.dashboard_vars["save_folder_path"].set(str(self.path("save_folder_path")))
        self.dashboard_vars["backup_folder_path"].set(str(backup_dir))
        self.dashboard_vars["backup_count"].set(str(len(backups)))
        if backups:
            latest = backups[0][1]
            self.dashboard_vars["last_backup"].set(latest.strftime("%Y-%m-%d %H:%M"))
        else:
            self.dashboard_vars["last_backup"].set("No backups found")

    def is_server_running(self) -> bool:
        return self.get_server_process_text() is not None

    def get_server_process_text(self):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {SERVER_EXE_NAME}"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if SERVER_EXE_NAME.lower() in result.stdout.lower():
                return SERVER_EXE_NAME
        except (OSError, subprocess.SubprocessError):
            pass

        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Process -Name AskaServer -ErrorAction SilentlyContinue | "
                    "Select-Object -First 1 -ExpandProperty Path",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            path = result.stdout.strip()
            if path:
                return path
        except (OSError, subprocess.SubprocessError):
            pass

        return None

    def refresh_status(self):
        process_text = self.get_server_process_text()
        running = process_text is not None
        self.dashboard_vars["status"].set("Running" if running else "Stopped")
        if "detected_process" in self.dashboard_vars:
            self.dashboard_vars["detected_process"].set(process_text or "None")
        self.status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])

    def schedule_status_refresh(self):
        self.refresh_status()
        self.status_job = self.after(5000, self.schedule_status_refresh)

    def start_server(self):
        if self.is_server_running():
            messagebox.showinfo(APP_NAME, "The ASKA server is already running.")
            self.log("Start skipped: server already running.")
            return
        bat = self.path("server_bat_path")
        if not bat.exists():
            messagebox.showerror(APP_NAME, f"Launcher batch file not found:\n{bat}")
            self.log(f"Start failed: launcher not found: {bat}")
            return
        try:
            subprocess.Popen(
                [str(bat)],
                cwd=str(bat.parent),
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self.log("Server start requested.")
            self.after(2000, self.refresh_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start server:\n{exc}")
            self.log(f"Start failed: {exc}")

    def stop_server(self, ask_force=True) -> bool:
        if not self.is_server_running():
            self.log("Stop skipped: server is not running.")
            self.refresh_status()
            return True
        self.log("Server stop requested.")
        try:
            subprocess.run(
                ["taskkill", "/IM", SERVER_EXE_NAME, "/T"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.log(f"Graceful stop command failed: {exc}")

        deadline = time.time() + 15
        while time.time() < deadline:
            if not self.is_server_running():
                self.log("Server stopped.")
                self.refresh_status()
                return True
            time.sleep(1)

        if ask_force and messagebox.askyesno(APP_NAME, "The server did not stop within 15 seconds. Force kill it?"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", SERVER_EXE_NAME, "/T"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                self.log("Server force kill requested.")
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Force kill failed: {exc}")
                messagebox.showerror(APP_NAME, f"Force kill failed:\n{exc}")
                return False
            self.after(1500, self.refresh_status)
            return True
        self.log("Stop incomplete: server is still running.")
        return False

    def restart_server(self):
        def work():
            if self.stop_server():
                time.sleep(3)
                self.after(0, self.start_server)
        threading.Thread(target=work, daemon=True).start()

    def steam_appmanifest_path(self) -> Path:
        install_dir = self.path("server_install_path")
        try:
            steamapps_dir = install_dir.parent.parent
        except IndexError:
            return Path()
        return steamapps_dir / f"appmanifest_{ASKA_DEDICATED_SERVER_APP_ID}.acf"

    def local_server_build_id(self) -> str:
        manifest = self.steam_appmanifest_path()
        if not manifest.exists():
            return ""
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r'"buildid"\s+"(\d+)"', text, re.IGNORECASE)
        return match.group(1) if match else ""

    def check_server_update(self, show_dialog=True):
        if "server_update_status" in self.dashboard_vars:
            self.dashboard_vars["server_update_status"].set("Checking...")
        build_id = self.local_server_build_id()
        manifest = self.steam_appmanifest_path()
        if not build_id:
            if "server_update_status" in self.dashboard_vars:
                self.dashboard_vars["server_update_status"].set("Unknown - app manifest not found")
            if show_dialog:
                messagebox.showerror(
                    APP_NAME,
                    "Could not find the local ASKA Dedicated Server build ID.\n\n"
                    f"Expected Steam app manifest:\n{manifest}",
                )
            self.log(f"Server update check failed: build ID not found in {manifest}")
            return
        self.run_threaded("Steam update check", lambda: self.do_check_server_update(build_id, show_dialog=show_dialog))

    def do_check_server_update(self, build_id: str, show_dialog=True):
        url = (
            "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/"
            f"?appid={ASKA_DEDICATED_SERVER_APP_ID}&version={build_id}"
        )
        request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            result = data.get("response", {})
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Server update check failed: {exc}")
            if "server_update_status" in self.dashboard_vars:
                self.after(0, self.dashboard_vars["server_update_status"].set, "Check failed")
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Server update check failed:\n{exc}")
            return

        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        steam_message = result.get("message", "")
        if up_to_date:
            status_text = f"Latest - build {build_id}"
            message = f"ASKA Dedicated Server appears up to date.\n\nLocal build: {build_id}"
        else:
            status_text = f"Update available - local {build_id}, latest {required}"
            message = (
                "ASKA Dedicated Server update appears available.\n\n"
                f"Local build: {build_id}\n"
                f"Required build: {required}\n\n"
                "Use Update Server after stopping the server."
            )
        if steam_message:
            message += f"\n\nSteam message: {steam_message}"
        self.log(f"Server update check: local={build_id}, required={required}, up_to_date={up_to_date}")
        if "server_update_status" in self.dashboard_vars:
            self.after(0, self.dashboard_vars["server_update_status"].set, status_text)
        if show_dialog:
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def update_server_with_steamcmd(self):
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before running a SteamCMD update.")
            self.log("SteamCMD update refused: server is running.")
            return
        steamcmd = self.path("steamcmd_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet the SteamCMD executable path in Settings.")
            self.log(f"SteamCMD update failed: steamcmd not found: {steamcmd}")
            return
        install_dir = self.path("server_install_path")
        if not install_dir.exists():
            messagebox.showerror(APP_NAME, f"Server install folder was not found:\n{install_dir}")
            self.log(f"SteamCMD update failed: install folder missing: {install_dir}")
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Update ASKA Dedicated Server with SteamCMD?\n\n"
            "The app will create backups of saves, server config, launcher batch, and BepInEx folders first.",
        ):
            return
        self.run_threaded("SteamCMD server update", self.do_update_server_with_steamcmd)

    def backup_server_files_for_update(self):
        backup_dir = self.path("backup_folder_path")
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"server_update_preflight_{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"server_update_preflight_{now_stamp()}_{counter}"
            counter += 1
        target.mkdir(parents=True)
        copied_any = False
        for key in ["server_config_path", "server_bat_path"]:
            source = self.path(key)
            if source.exists() and source.is_file():
                shutil.copy2(source, target / source.name)
                copied_any = True
        for key, folder_name in [("bepinex_plugins_path", "BepInEx_plugins"), ("bepinex_config_path", "BepInEx_config")]:
            source = self.path(key)
            if source.exists() and source.is_dir():
                shutil.copytree(source, target / folder_name)
                copied_any = True
        if not copied_any:
            self.log("Server update preflight backup created with no config/mod files found.")
        self.log(f"Server update preflight backup created: {target}")
        return target

    def do_update_server_with_steamcmd(self):
        save_backup = self.create_backup(prefix_override="before_server_update_")
        if not save_backup:
            self.log("SteamCMD update aborted: save backup failed.")
            self.after(0, messagebox.showerror, APP_NAME, "Update aborted because the save backup failed.")
            return
        try:
            preflight_backup = self.backup_server_files_for_update()
        except OSError as exc:
            self.log(f"SteamCMD update aborted: preflight backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Update aborted because preflight backup failed:\n{exc}")
            return

        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("server_install_path")
        command = [
            str(steamcmd),
            "+login",
            "anonymous",
            "+force_install_dir",
            str(install_dir),
            "+app_update",
            ASKA_DEDICATED_SERVER_APP_ID,
            "validate",
            "+quit",
        ]
        self.log("Running SteamCMD update for ASKA Dedicated Server app 3246670.")
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(steamcmd.parent),
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            assert process.stdout is not None
            for line in process.stdout:
                clean = line.rstrip()
                if clean:
                    self.log(f"SteamCMD: {clean}")
            exit_code = process.wait()
        except OSError as exc:
            self.log(f"SteamCMD update failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"SteamCMD update failed:\n{exc}")
            return

        if exit_code == 0:
            self.log("SteamCMD update completed successfully.")
            self.after(
                0,
                messagebox.showinfo,
                APP_NAME,
                f"Server update complete.\n\nSave backup:\n{save_backup}\n\nPreflight backup:\n{preflight_backup}",
            )
        else:
            self.log(f"SteamCMD update exited with code {exit_code}.")
            self.after(0, messagebox.showerror, APP_NAME, f"SteamCMD update exited with code {exit_code}. Check Logs.")

    def validate_safe_folder(self, path: Path, label: str) -> bool:
        resolved = path.resolve() if path.exists() else path.absolute()
        if len(resolved.parts) < 3:
            self.after(0, messagebox.showerror, APP_NAME, f"Refusing to use unsafe {label} path:\n{resolved}")
            self.log(f"Unsafe {label} path refused: {resolved}")
            return False
        return True

    def create_backup(self, emergency=False, prefix_override=None) -> Path | None:
        save_dir = self.path("save_folder_path")
        backup_dir = self.path("backup_folder_path")
        if not save_dir.exists():
            self.after(0, messagebox.showerror, APP_NAME, f"Save folder does not exist:\n{save_dir}")
            self.log(f"Backup failed: save folder missing: {save_dir}")
            return None
        if not self.validate_safe_folder(save_dir, "save folder"):
            return None
        backup_dir.mkdir(parents=True, exist_ok=True)
        prefix = prefix_override or ("emergency_before_restore_" if emergency else BACKUP_PREFIX)
        target = backup_dir / f"{prefix}{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"{prefix}{now_stamp()}_{counter}"
            counter += 1
        try:
            shutil.copytree(save_dir, target)
            self.log(f"Backup created: {target}")
            if not emergency and not prefix_override:
                self.delete_old_backups()
            self.after(0, self.refresh_all)
            return target
        except OSError as exc:
            self.log(f"Backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Backup failed:\n{exc}")
            return None

    def list_backups(self):
        backup_dir = self.path("backup_folder_path")
        if not backup_dir.exists():
            return []
        items = []
        for item in backup_dir.iterdir():
            if item.is_dir():
                parsed = parse_retained_backup_time(item.name)
                if parsed:
                    items.append((item, parsed))
        return sorted(items, key=lambda row: row[1], reverse=True)

    def refresh_backups(self):
        if not self.backup_tree:
            return
        self.backup_tree.delete(*self.backup_tree.get_children())
        for path, parsed in self.list_backups():
            self.backup_tree.insert("", "end", iid=str(path), values=(path.name, parsed.strftime("%Y-%m-%d %H:%M"), human_size(path)))
        self.refresh_dashboard()

    def refresh_mods(self):
        if self.mod_plugin_tree:
            self.mod_plugin_tree.delete(*self.mod_plugin_tree.get_children())
            plugins_path = self.path("bepinex_plugins_path")
            if plugins_path.exists():
                for item in sorted(plugins_path.iterdir(), key=lambda p: p.name.lower()):
                    if item.is_file() and item.suffix.lower() == ".dll":
                        stat = item.stat()
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        self.mod_plugin_tree.insert("", "end", iid=str(item), values=(item.name, human_size(item), modified))

        if self.mod_config_tree:
            selected = set(self.mod_config_tree.selection())
            self.mod_config_tree.delete(*self.mod_config_tree.get_children())
            config_path = self.path("bepinex_config_path")
            if config_path.exists():
                for item in sorted(config_path.iterdir(), key=lambda p: p.name.lower()):
                    if item.is_file() and item.suffix.lower() == ".cfg":
                        stat = item.stat()
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        self.mod_config_tree.insert("", "end", iid=str(item), values=(item.name, human_size(item), modified))
                        if str(item) in selected:
                            self.mod_config_tree.selection_set(str(item))
        self.update_selected_mod_source_label()

    def selected_plugin_path(self) -> Path | None:
        selected = self.mod_plugin_tree.selection() if self.mod_plugin_tree else []
        if not selected:
            return None
        return Path(selected[0])

    def mod_source_key(self, plugin_path: Path) -> str:
        return plugin_path.name.lower()

    def selected_mod_source(self):
        plugin_path = self.selected_plugin_path()
        if not plugin_path:
            return None, {}
        key = self.mod_source_key(plugin_path)
        return plugin_path, self.mod_sources.get(key, {})

    def update_selected_mod_source_label(self, _event=None):
        if not self.mod_source_label_var:
            return
        plugin_path, source = self.selected_mod_source()
        if not plugin_path:
            self.mod_source_label_var.set("Nexus source: select a plugin")
            return
        url = source.get("nexus_url", "")
        self.mod_source_label_var.set(f"Nexus source for {plugin_path.name}: {url or 'not set'}")

    def save_mod_sources(self):
        write_json(MOD_SOURCES_FILE, self.mod_sources)

    def set_selected_mod_source(self):
        plugin_path = self.selected_plugin_path()
        if not plugin_path:
            messagebox.showinfo(APP_NAME, "Select a plugin DLL first.")
            return
        key = self.mod_source_key(plugin_path)
        existing = self.mod_sources.get(key, {})

        popup = tk.Toplevel(self)
        popup.title("Set Nexus URL")
        popup.configure(bg=COLORS["bg"])
        popup.transient(self)
        popup.grab_set()
        popup.columnconfigure(0, weight=1)
        ttk.Label(popup, text=f"Nexus mod page for {plugin_path.name}", padding=14).grid(row=0, column=0, sticky="w")
        url_var = tk.StringVar(value=existing.get("nexus_url", ""))
        ttk.Entry(popup, textvariable=url_var, width=72).grid(row=1, column=0, sticky="ew", padx=14)

        def save():
            url = url_var.get().strip()
            if url and "nexusmods.com" not in url.lower():
                messagebox.showerror(APP_NAME, "Please enter a Nexus Mods URL.")
                return
            self.mod_sources[key] = {
                "name": plugin_path.name,
                "nexus_url": url,
                "nexus_mod_id": extract_nexus_mod_id(url),
            }
            self.save_mod_sources()
            self.update_selected_mod_source_label()
            self.log(f"Saved Nexus source for {plugin_path.name}: {url or 'not set'}")
            popup.destroy()

        buttons = ttk.Frame(popup)
        buttons.grid(row=2, column=0, sticky="e", padx=14, pady=14)
        ttk.Button(buttons, text="Cancel", command=popup.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Save", style="Accent.TButton", command=save).pack(side="left")
        popup.wait_window()

    def open_selected_mod_source(self):
        plugin_path, source = self.selected_mod_source()
        if not plugin_path:
            messagebox.showinfo(APP_NAME, "Select a plugin DLL first.")
            return
        url = source.get("nexus_url", "")
        if not url:
            messagebox.showinfo(APP_NAME, "No Nexus URL is set for this plugin.")
            return
        webbrowser.open(url)
        self.log(f"Opened Nexus page for {plugin_path.name}: {url}")

    def check_nexus_updates(self):
        tracked = [source for source in self.mod_sources.values() if source.get("nexus_mod_id")]
        if not tracked:
            messagebox.showinfo(APP_NAME, "No tracked Nexus mod URLs are configured yet.")
            return
        api_key = self.settings.get("nexus_api_key", "").strip()
        if not api_key:
            pages = "\n".join(source.get("nexus_url", "") for source in tracked if source.get("nexus_url"))
            messagebox.showinfo(
                APP_NAME,
                "Nexus API key is not configured, so automatic metadata checks are unavailable.\n\n"
                "Use Open Nexus Page for each tracked mod, or add your API key in Settings.\n\n"
                f"Tracked pages:\n{pages}",
            )
            return
        self.run_threaded("Nexus update check", lambda: self.do_check_nexus_updates(api_key, tracked))

    def do_check_nexus_updates(self, api_key: str, tracked: list):
        lines = []
        for source in tracked:
            mod_id = source.get("nexus_mod_id")
            name = source.get("name", f"Mod {mod_id}")
            url = f"https://api.nexusmods.com/v1/games/{NEXUS_GAME_DOMAIN}/mods/{mod_id}.json"
            request = urllib.request.Request(url, headers={"apikey": api_key, "User-Agent": APP_NAME})
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    data = json.loads(response.read().decode("utf-8", errors="replace"))
                version = data.get("version") or "unknown version"
                updated = data.get("updated_time") or data.get("created_time") or "unknown update time"
                lines.append(f"{name}: latest {version}, updated {updated}")
            except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
                lines.append(f"{name}: check failed ({exc})")
                self.log(f"Nexus check failed for {name}: {exc}")
        message = "\n".join(lines) or "No Nexus results."
        self.log("Nexus update check complete.")
        self.after(0, messagebox.showinfo, APP_NAME, message)

    def install_mod_zip(self):
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before installing or updating mods.")
            self.log("Mod ZIP install refused: server is running.")
            return
        zip_path = filedialog.askopenfilename(
            title="Select downloaded Nexus mod ZIP",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")],
        )
        if not zip_path:
            return
        if not messagebox.askyesno(APP_NAME, "Install this mod ZIP?\n\nThe app will back up BepInEx first and then copy DLL/CFG files into place."):
            return
        self.run_threaded("Mod ZIP install", lambda: self.do_install_mod_zip(Path(zip_path)))

    def do_install_mod_zip(self, zip_path: Path):
        backup = self.backup_bepinex(show_success=False)
        if not backup:
            self.log("Mod ZIP install aborted: BepInEx backup failed.")
            self.after(0, messagebox.showerror, APP_NAME, "Install aborted because BepInEx backup failed.")
            return

        plugins_path = self.path("bepinex_plugins_path")
        config_path = self.path("bepinex_config_path")
        plugins_path.mkdir(parents=True, exist_ok=True)
        config_path.mkdir(parents=True, exist_ok=True)
        installed = []
        skipped = []
        try:
            with zipfile.ZipFile(zip_path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    name = Path(info.filename).name
                    suffix = Path(name).suffix.lower()
                    if suffix == ".dll":
                        target = plugins_path / name
                    elif suffix == ".cfg":
                        target = config_path / name
                    else:
                        skipped.append(info.filename)
                        continue
                    with archive.open(info) as src, target.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
                    installed.append(str(target))
            self.log(f"Installed mod ZIP: {zip_path}")
            for target in installed:
                self.log(f"Installed mod file: {target}")
            self.after(0, self.refresh_mods)
            summary = "\n".join(installed[:12])
            if len(installed) > 12:
                summary += f"\n...and {len(installed) - 12} more"
            self.after(
                0,
                messagebox.showinfo,
                APP_NAME,
                f"Mod ZIP installed.\n\nBackup:\n{backup}\n\nInstalled files:\n{summary or 'No DLL/CFG files found.'}",
            )
        except (OSError, zipfile.BadZipFile) as exc:
            self.log(f"Mod ZIP install failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Mod ZIP install failed:\n{exc}")

    def load_selected_mod_config(self, _event=None):
        selected = self.mod_config_tree.selection() if self.mod_config_tree else []
        if not selected:
            return
        self.load_mod_config(Path(selected[0]))

    def reload_current_mod_config(self):
        if not self.current_mod_config_path:
            messagebox.showinfo(APP_NAME, "Select a mod config file first.")
            return
        self.load_mod_config(self.current_mod_config_path)

    def load_mod_config(self, path: Path):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not load mod config:\n{exc}")
            self.log(f"Mod config load failed: {exc}")
            return
        self.current_mod_config_path = path
        self.mod_config_label_var.set(path.name)
        self.mod_config_text.configure(state="normal")
        self.mod_config_text.delete("1.0", "end")
        self.mod_config_text.insert("1.0", text)
        self.mod_config_text.edit_reset()
        self.log(f"Loaded mod config: {path}")

    def save_current_mod_config(self):
        if not self.current_mod_config_path:
            messagebox.showinfo(APP_NAME, "Select a mod config file first.")
            return
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before editing BepInEx config files.")
            self.log("Mod config save refused: server is running.")
            return
        path = self.current_mod_config_path
        try:
            backup_path = path.with_name(f"{path.stem}.backup_{now_stamp()}{path.suffix}")
            shutil.copy2(path, backup_path)
            text = self.mod_config_text.get("1.0", "end-1c")
            path.write_text(text, encoding="utf-8")
            self.log(f"Saved mod config: {path}")
            self.refresh_mods()
            messagebox.showinfo(APP_NAME, f"Mod config saved.\nBackup created:\n{backup_path}")
        except OSError as exc:
            self.log(f"Mod config save failed: {exc}")
            messagebox.showerror(APP_NAME, f"Mod config save failed:\n{exc}")

    def backup_bepinex(self, show_success=True):
        backup_dir = self.path("backup_folder_path")
        plugins_path = self.path("bepinex_plugins_path")
        config_path = self.path("bepinex_config_path")
        if not plugins_path.exists() and not config_path.exists():
            self.after(0, messagebox.showerror, APP_NAME, "BepInEx plugins and config folders were not found.")
            self.log("BepInEx backup failed: folders missing.")
            return None
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"bepinex_backup_{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"bepinex_backup_{now_stamp()}_{counter}"
            counter += 1
        try:
            target.mkdir(parents=True)
            if plugins_path.exists():
                shutil.copytree(plugins_path, target / "plugins")
            if config_path.exists():
                shutil.copytree(config_path, target / "config")
            self.log(f"BepInEx backup created: {target}")
            if show_success:
                self.after(0, messagebox.showinfo, APP_NAME, f"BepInEx backup created:\n{target}")
            return target
        except OSError as exc:
            self.log(f"BepInEx backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"BepInEx backup failed:\n{exc}")
            return None

    def delete_old_backups(self):
        retention = int(self.settings.get("retention_hours", 24))
        cutoff = datetime.now() - timedelta(hours=retention)
        for path, parsed in self.list_backups():
            if not path.name.startswith(BACKUP_PREFIX):
                continue
            if parsed < cutoff:
                try:
                    shutil.rmtree(path)
                    self.log(f"Deleted old backup: {path}")
                except OSError as exc:
                    self.log(f"Could not delete old backup {path}: {exc}")

    def cleanup_now(self):
        self.delete_old_backups()
        self.refresh_backups()
        messagebox.showinfo(APP_NAME, "Backup cleanup complete.")

    def restore_selected_backup(self):
        selected = self.backup_tree.selection()
        if not selected:
            messagebox.showinfo(APP_NAME, "Select a backup first.")
            return
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before restoring a backup.")
            self.log("Restore refused: server is running.")
            return
        backup_path = Path(selected[0])
        if not backup_path.exists():
            messagebox.showerror(APP_NAME, "The selected backup folder no longer exists.")
            return
        if not messagebox.askyesno(APP_NAME, f"Restore this backup?\n\n{backup_path.name}\n\nAn emergency backup will be created first."):
            return
        self.run_threaded("Restore", lambda: self.restore_backup(backup_path))

    def restore_backup(self, backup_path: Path):
        save_dir = self.path("save_folder_path")
        if not self.validate_safe_folder(save_dir, "save folder"):
            return
        self.create_backup(emergency=True)
        try:
            if save_dir.exists():
                shutil.rmtree(save_dir)
            shutil.copytree(backup_path, save_dir)
            self.log(f"Restored backup: {backup_path}")
            self.after(0, messagebox.showinfo, APP_NAME, "Backup restored successfully.")
            self.after(0, self.refresh_all)
        except OSError as exc:
            self.log(f"Restore failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Restore failed:\n{exc}")

    def wipe_save(self):
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before wiping the current save.")
            self.log("Wipe refused: server is running.")
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Are you sure you want to wipe the current ASKA server save?\n\n"
            "This will delete the contents of the configured save folder.",
        ):
            self.log("Wipe cancelled at first confirmation.")
            return

        popup = tk.Toplevel(self)
        popup.title("Really confirm wipe")
        popup.configure(bg=COLORS["bg"])
        popup.transient(self)
        popup.grab_set()
        popup.columnconfigure(0, weight=1)

        ttk.Label(
            popup,
            text="Are you really sure?\n\n"
            "A before-wipe backup will be created first. Leave secure backup enabled if you want "
            "a clearly named backup to keep and refer to later.",
            padding=14,
            wraplength=460,
            justify="left",
        ).grid(row=0, column=0, sticky="ew")

        secure_backup = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            popup,
            text="Create secure before-wipe backup",
            variable=secure_backup,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))

        ttk.Label(popup, text="Type DELETE to wipe the current server save.", padding=(14, 0, 14, 8)).grid(row=2, column=0, sticky="w")
        typed = tk.StringVar()
        ttk.Entry(popup, textvariable=typed).grid(row=3, column=0, sticky="ew", padx=14)

        def confirm():
            if typed.get() != "DELETE":
                messagebox.showerror(APP_NAME, "Confirmation did not match DELETE.")
                return
            make_secure_backup = secure_backup.get()
            popup.destroy()
            self.run_threaded("Wipe", lambda: self.do_wipe_save(secure_backup=make_secure_backup))

        buttons = ttk.Frame(popup)
        buttons.grid(row=4, column=0, sticky="e", padx=14, pady=14)
        ttk.Button(buttons, text="Cancel", command=popup.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Wipe Save", style="Danger.TButton", command=confirm).pack(side="left")
        popup.wait_window()

    def do_wipe_save(self, secure_backup=True):
        save_dir = self.path("save_folder_path")
        if not save_dir.exists():
            self.log(f"Wipe skipped: save folder does not exist: {save_dir}")
            return
        if not self.validate_safe_folder(save_dir, "save folder"):
            return
        prefix = "secure_before_wipe_" if secure_backup else "emergency_before_wipe_"
        backup_path = self.create_backup(emergency=True, prefix_override=prefix)
        if not backup_path:
            self.log("Wipe aborted: before-wipe backup failed.")
            self.after(0, messagebox.showerror, APP_NAME, "Wipe aborted because the before-wipe backup failed.")
            return
        try:
            for child in save_dir.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            self.log(f"Wiped save folder contents: {save_dir}")
            self.after(0, messagebox.showinfo, APP_NAME, f"Current server save was wiped.\n\nBefore-wipe backup:\n{backup_path}")
        except OSError as exc:
            self.log(f"Wipe failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Wipe failed:\n{exc}")

    def load_config(self, silent=False):
        config_path = self.path("server_config_path")
        values = {field: "" for field in CONFIG_FIELDS}
        if config_path.exists():
            try:
                for line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
                    match = re.match(r"^\s*([^#;][^=]+?)\s*=\s*(.*)$", line)
                    if match:
                        key = match.group(1).strip().lower()
                        if key in values:
                            values[key] = match.group(2).strip()
            except OSError as exc:
                if not silent:
                    messagebox.showerror(APP_NAME, f"Could not load config:\n{exc}")
                self.log(f"Config load failed: {exc}")
                return
        elif not silent:
            messagebox.showerror(APP_NAME, f"Config file not found:\n{config_path}")
        for key, var in self.config_vars.items():
            var.set(values.get(key, ""))
        if not silent:
            self.log(f"Config loaded: {config_path}")

    def save_config(self):
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before editing config.")
            self.log("Config save refused: server is running.")
            return
        config_path = self.path("server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Config file not found:\n{config_path}")
            return
        try:
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            original_lines = config_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
            remaining = {key: var.get() for key, var in self.config_vars.items()}
            new_lines = []
            for line in original_lines:
                match = re.match(r"^(\s*)([^#;][^=]+?)(\s*=\s*)(.*?)(\r?\n)?$", line)
                if match and match.group(2).strip().lower() in remaining:
                    key = match.group(2).strip().lower()
                    newline = match.group(5) or "\n"
                    new_lines.append(f"{match.group(1)}{match.group(2).strip()}{match.group(3)}{remaining.pop(key)}{newline}")
                else:
                    new_lines.append(line)
            if remaining:
                if new_lines and not new_lines[-1].endswith(("\n", "\r\n")):
                    new_lines[-1] += "\n"
                new_lines.append("\n# Added by ASKA Server Manager\n")
                for key, value in remaining.items():
                    new_lines.append(f"{key} = {value}\n")
            config_path.write_text("".join(new_lines), encoding="utf-8")
            self.log(f"Config saved: {config_path}")
            messagebox.showinfo(APP_NAME, f"Config saved.\nBackup created:\n{backup_path}")
        except OSError as exc:
            self.log(f"Config save failed: {exc}")
            messagebox.showerror(APP_NAME, f"Config save failed:\n{exc}")

    def browse_path(self, key: str, is_file: bool):
        current = self.path_vars[key].get()
        if is_file:
            selected = filedialog.askopenfilename(initialdir=str(Path(current).parent if current else APP_DIR))
        else:
            selected = filedialog.askdirectory(initialdir=current or str(APP_DIR))
        if selected:
            self.path_vars[key].set(selected)

    def steam_install_paths_from_registry(self):
        paths = []
        registry_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Valve\Steam"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Valve\Steam"),
        ]
        for hive, subkey in registry_locations:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    value, _ = winreg.QueryValueEx(key, "SteamPath")
                    if value:
                        paths.append(Path(value))
            except OSError:
                pass
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    value, _ = winreg.QueryValueEx(key, "InstallPath")
                    if value:
                        paths.append(Path(value))
            except OSError:
                pass
        for fallback in [Path(r"C:\Program Files (x86)\Steam"), Path(r"C:\Program Files\Steam"), Path(r"E:\steam")]:
            paths.append(fallback)
        return list(dict.fromkeys(path for path in paths if path))

    def steam_library_paths(self):
        libraries = []
        for steam_path in self.steam_install_paths_from_registry():
            steamapps = steam_path / "steamapps"
            if steamapps.exists():
                libraries.append(steamapps)
            library_vdf = steamapps / "libraryfolders.vdf"
            if not library_vdf.exists():
                continue
            try:
                text = library_vdf.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for match in re.finditer(r'"path"\s+"([^"]+)"', text, re.IGNORECASE):
                path_text = match.group(1).replace("\\\\", "\\")
                library_steamapps = Path(path_text) / "steamapps"
                if library_steamapps.exists():
                    libraries.append(library_steamapps)
        return list(dict.fromkeys(libraries))

    def detect_aska_install_from_steam(self):
        for steamapps in self.steam_library_paths():
            manifest = steamapps / f"appmanifest_{ASKA_DEDICATED_SERVER_APP_ID}.acf"
            if not manifest.exists():
                continue
            installdir = "ASKA Dedicated Server"
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
                match = re.search(r'"installdir"\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    installdir = match.group(1)
            except OSError:
                pass
            install_path = steamapps / "common" / installdir
            if (install_path / SERVER_EXE_NAME).exists() or install_path.exists():
                return install_path
        return None

    def detect_aska_install_from_process(self):
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Process -Name AskaServer -ErrorAction SilentlyContinue | "
                    "Select-Object -First 1 -ExpandProperty Path",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            path_text = result.stdout.strip()
            if path_text:
                path = Path(path_text)
                if path.exists():
                    return path.parent
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def detect_steamcmd_path(self):
        candidates = [
            self.path("steamcmd_path"),
            Path(r"C:\steamcmd\steamcmd.exe"),
            Path(r"E:\steamcmd\steamcmd.exe"),
            Path(r"D:\steamcmd\steamcmd.exe"),
            Path(r"C:\Program Files\SteamCMD\steamcmd.exe"),
            Path(r"C:\Program Files (x86)\SteamCMD\steamcmd.exe"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def autodetect_paths(self):
        detected = {}
        install_path = self.detect_aska_install_from_process() or self.detect_aska_install_from_steam()
        if install_path:
            detected["server_install_path"] = str(install_path)
            detected["server_bat_path"] = str(install_path / "AskaServer.bat")
            detected["server_config_path"] = str(install_path / "server properties.txt")
            detected["bepinex_plugins_path"] = str(install_path / "BepInEx" / "plugins")
            detected["bepinex_config_path"] = str(install_path / "BepInEx" / "config")

        steamcmd_path = self.detect_steamcmd_path()
        if steamcmd_path:
            detected["steamcmd_path"] = str(steamcmd_path)

        detected["save_folder_path"] = str(DEFAULT_SAVE)
        detected["backup_folder_path"] = self.path_vars.get("backup_folder_path", tk.StringVar(value=str(DEFAULT_BACKUPS))).get() or str(DEFAULT_BACKUPS)

        for key, value in detected.items():
            if key in self.path_vars:
                self.path_vars[key].set(value)
                self.settings[key] = value
        write_json(SETTINGS_FILE, self.settings)
        self.refresh_all()

        if install_path:
            message = "Detected ASKA dedicated server paths and saved them."
        else:
            message = (
                "Could not auto-detect the ASKA Dedicated Server install folder.\n\n"
                "The app still filled the standard save path. Start the server once or browse to the install folder manually."
            )
        if not steamcmd_path:
            message += "\n\nSteamCMD was not found. Set SteamCMD executable manually if you want server updates."
        self.log(f"Auto-detect paths result: {detected}")
        messagebox.showinfo(APP_NAME, message)

    def save_settings_from_ui(self):
        for key, var in self.path_vars.items():
            self.settings[key] = var.get()
        try:
            interval = int(self.interval_var.get())
            retention = int(self.retention_var.get())
            if interval < 1 or retention < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror(APP_NAME, "Backup interval and retention must be positive whole numbers.")
            return
        self.settings["backup_interval_minutes"] = interval
        self.settings["retention_hours"] = retention
        self.settings["auto_backup_enabled"] = self.auto_backup_var.get()
        self.settings["backup_on_startup"] = self.startup_backup_var.get()
        self.settings["nexus_api_key"] = self.nexus_api_key_var.get().strip()
        write_json(SETTINGS_FILE, self.settings)
        self.log("Settings saved.")
        self.refresh_all()
        self.schedule_auto_backup()
        messagebox.showinfo(APP_NAME, "Settings saved.")

    def toggle_auto_backup(self):
        self.settings["auto_backup_enabled"] = self.auto_backup_var.get()
        write_json(SETTINGS_FILE, self.settings)
        self.log(f"Hourly backups {'enabled' if self.auto_backup_var.get() else 'disabled'}.")
        self.schedule_auto_backup()

    def toggle_startup_backup(self):
        self.settings["backup_on_startup"] = self.startup_backup_var.get()
        write_json(SETTINGS_FILE, self.settings)
        self.log(f"Backup on startup {'enabled' if self.startup_backup_var.get() else 'disabled'}.")

    def schedule_auto_backup(self):
        if self.auto_backup_job:
            self.after_cancel(self.auto_backup_job)
            self.auto_backup_job = None
        if self.settings.get("auto_backup_enabled"):
            interval_ms = int(self.settings.get("backup_interval_minutes", 60)) * 60 * 1000
            self.auto_backup_job = self.after(interval_ms, self.auto_backup_tick)

    def auto_backup_tick(self):
        self.run_threaded("Automatic backup", self.create_backup)
        self.schedule_auto_backup()

    def run_threaded(self, label: str, func):
        def runner():
            self.log(f"{label} started.")
            func()
            self.log(f"{label} finished.")
        threading.Thread(target=runner, daemon=True).start()

    def open_path(self, path: Path):
        try:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
            os.startfile(path)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open path:\n{exc}")
            self.log(f"Open path failed: {exc}")

    def open_config_notepad(self):
        config_path = self.path("server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Config file not found:\n{config_path}")
            return
        try:
            subprocess.Popen(["notepad.exe", str(config_path)])
            self.log(f"Opened config in Notepad: {config_path}")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open Notepad:\n{exc}")
            self.log(f"Notepad failed: {exc}")


if __name__ == "__main__":
    app = AskaServerManager()
    app.mainloop()

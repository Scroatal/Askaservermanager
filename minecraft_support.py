"""Minecraft Fabric support for Gaming Dads Server Manager.

The mixin keeps Minecraft-specific UI and lifecycle code out of the original
single-file application.  It intentionally refuses to terminate a Minecraft
process that it did not start, so an existing family game is never interrupted
just because the manager was opened.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


MINECRAFT_ROOT = Path(r"C:\Users\Scott\Documents\ChatGPT\minecraftserver")
MINECRAFT_SERVER = MINECRAFT_ROOT / "server"
DEFAULT_CURSEFORGE_PROFILE = Path(r"C:\Users\Scott\curseforge\minecraft\Instances\Cozy Family 26.2 - Full")

MINECRAFT_DEFAULT_SETTINGS = {
    "minecraft_server_install_path": str(MINECRAFT_SERVER),
    "minecraft_java_exe_path": str(MINECRAFT_ROOT / "runtime" / "bin" / "java.exe"),
    "minecraft_launcher_jar_path": str(MINECRAFT_SERVER / "fabric-server-launch.jar"),
    "minecraft_server_properties_path": str(MINECRAFT_SERVER / "server.properties"),
    "minecraft_world_folder_path": str(MINECRAFT_SERVER / "world"),
    "minecraft_mods_folder_path": str(MINECRAFT_SERVER / "mods"),
    "minecraft_curseforge_profile_path": str(DEFAULT_CURSEFORGE_PROFILE),
    "minecraft_backup_folder_path": r"C:\GameBackups\Minecraft",
    "minecraft_min_memory": "2G",
    "minecraft_max_memory": "8G",
    "minecraft_server_port": "25565",
    "minecraft_start_server_on_app_launch": False,
    "minecraft_auto_restart_server": False,
    "minecraft_auto_sync_mods": True,
}

MINECRAFT_PROPERTY_FIELDS = [
    ("motd", "Server description", "text"),
    ("gamemode", "Default game mode", "choice:creative|survival|adventure|spectator"),
    ("difficulty", "Difficulty", "choice:peaceful|easy|normal|hard"),
    ("pvp", "Player versus player", "choice:false|true"),
    ("allow-flight", "Allow flying", "choice:true|false"),
    ("force-gamemode", "Force default mode on join", "choice:false|true"),
    ("max-players", "Maximum players", "text"),
    ("view-distance", "View distance", "text"),
    ("simulation-distance", "Simulation distance", "text"),
    ("spawn-protection", "Spawn protection radius", "text"),
    ("white-list", "Use whitelist", "choice:false|true"),
    ("online-mode", "Verify Minecraft accounts", "choice:true|false"),
    ("server-port", "Server port", "text"),
]


class MinecraftManagerMixin:
    """UI and lifecycle methods mixed into AskaServerManager."""

    def initialize_minecraft_state(self):
        self.minecraft_vars = {}
        self.minecraft_path_vars = {}
        self.minecraft_property_vars = {}
        self.minecraft_process = None
        self.minecraft_process_lock = threading.Lock()
        self.minecraft_process_cache = (0.0, None)
        self.minecraft_should_be_running = False
        self.minecraft_start_button = None
        self.minecraft_stop_button = None
        self.minecraft_status_label = None
        self.minecraft_console_text = None
        self.minecraft_command_var = None
        self.minecraft_mod_tree = None
        self.minecraft_config_text = None
        self.minecraft_auto_restart_var = None
        self.minecraft_start_on_launch_var = None
        self.minecraft_auto_sync_mods_var = None
        self.minecraft_mod_sync_status_var = None

    # ---------- UI ----------

    def build_minecraft_tab(self):
        self.minecraft_notebook = ttk.Notebook(self.minecraft_tab)
        self.minecraft_notebook.pack(fill="both", expand=True)
        self.minecraft_server_tab = ttk.Frame(self.minecraft_notebook, padding=14)
        self.minecraft_config_tab = ttk.Frame(self.minecraft_notebook, padding=14)
        self.minecraft_mods_tab = ttk.Frame(self.minecraft_notebook, padding=14)
        self.minecraft_settings_tab = ttk.Frame(self.minecraft_notebook, padding=14)
        self.minecraft_notebook.add(self.minecraft_server_tab, text="Server")
        self.minecraft_notebook.add(self.minecraft_config_tab, text="Config")
        self.minecraft_notebook.add(self.minecraft_mods_tab, text="Mods")
        self.minecraft_notebook.add(self.minecraft_settings_tab, text="Settings")
        self.build_minecraft_server_tab()
        self.build_minecraft_config_tab()
        self.build_minecraft_mods_tab()
        self.build_minecraft_settings_tab()

    def build_minecraft_server_tab(self):
        top = ttk.Frame(self.minecraft_server_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Minecraft Fabric Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Minecraft Status And Backups")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        for key, label in [
            ("status", "Server status"),
            ("control", "Console control"),
            ("detected_process", "Detected process"),
            ("install_path", "Server folder"),
            ("world_path", "World folder"),
            ("backup_path", "Backup folder"),
            ("backup_count", "Backups stored"),
            ("last_backup", "Last backup"),
        ]:
            self.minecraft_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(left if key == "status" else right, style="Panel.TFrame")
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            widget = ttk.Label(row, textvariable=self.minecraft_vars[key], style="Panel.TLabel", wraplength=430)
            widget.pack(side="left", fill="x", expand=True)
            if key == "status":
                self.minecraft_status_label = widget

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 10))
        self.minecraft_start_button = ttk.Button(buttons, text="Start Minecraft", command=self.start_minecraft_server)
        self.minecraft_start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.minecraft_stop_button = ttk.Button(buttons, text="Stop Minecraft", command=self.stop_minecraft_server)
        self.minecraft_stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Minecraft", command=self.restart_minecraft_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup World", style="Accent.TButton", command=self.backup_minecraft_now).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Server", command=lambda: self.open_path(self.minecraft_path("minecraft_server_install_path"))).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Backups", command=lambda: self.open_path(self.minecraft_path("minecraft_backup_folder_path"))).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        for column in range(3):
            buttons.columnconfigure(column, weight=1)

        command_box = self.panel(left, "Server Command")
        command_box.pack(fill="x", pady=(6, 0))
        command_row = ttk.Frame(command_box, style="Panel.TFrame")
        command_row.pack(fill="x")
        self.minecraft_command_var = tk.StringVar()
        entry = ttk.Entry(command_row, textvariable=self.minecraft_command_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self.send_minecraft_command())
        ttk.Button(command_row, text="Send", style="Accent.TButton", command=self.send_minecraft_command).pack(side="left", padx=(8, 0))
        ttk.Label(
            command_box,
            text="Examples: op PlayerName, gamemode survival PlayerName, gamerule keepInventory true, say Dinner is ready",
            style="Panel.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(7, 0))

        console = self.panel(self.minecraft_server_tab, "Minecraft Console")
        console.pack(fill="both", expand=True, pady=(12, 0))
        self.minecraft_console_text = tk.Text(
            console,
            bg="#111111",
            fg="#f8f2f0",
            insertbackground="#f8f2f0",
            relief="flat",
            wrap="word",
            height=10,
            state="disabled",
        )
        scroll = ttk.Scrollbar(console, orient="vertical", command=self.minecraft_console_text.yview)
        self.minecraft_console_text.configure(yscrollcommand=scroll.set)
        self.minecraft_console_text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.append_minecraft_console("Minecraft console output will appear here when this manager starts the server.")

    def build_minecraft_config_tab(self):
        notebook = ttk.Notebook(self.minecraft_config_tab)
        notebook.pack(fill="both", expand=True)
        form_page = ttk.Frame(notebook, padding=10)
        raw_page = ttk.Frame(notebook, padding=10)
        notebook.add(form_page, text="Common Settings")
        notebook.add(raw_page, text="Raw server.properties")

        form = ttk.Frame(form_page, style="Panel.TFrame", padding=14)
        form.pack(fill="both", expand=True)
        ttk.Label(
            form,
            text="Stop Minecraft before saving. Unknown properties are preserved and a timestamped backup is created first.",
            style="Panel.TLabel",
            wraplength=900,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row_index, (key, label, kind) in enumerate(MINECRAFT_PROPERTY_FIELDS, start=1):
            ttk.Label(form, text=label, width=30, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            self.minecraft_property_vars[key] = var
            if kind.startswith("choice:"):
                values = tuple(kind.removeprefix("choice:").split("|"))
                widget = ttk.Combobox(form, textvariable=var, values=values, state="readonly")
            else:
                widget = ttk.Entry(form, textvariable=var)
            widget.grid(row=row_index, column=1, sticky="ew", padx=(8, 0), pady=3)
        form.columnconfigure(1, weight=1)
        actions = ttk.Frame(form, style="Panel.TFrame")
        actions.grid(row=len(MINECRAFT_PROPERTY_FIELDS) + 1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Load Settings", command=self.load_minecraft_properties).pack(side="left")
        ttk.Button(actions, text="Save Settings", style="Accent.TButton", command=self.save_minecraft_properties_form).pack(side="left", padx=8)
        ttk.Button(actions, text="Family Preset", command=self.apply_minecraft_family_preset).pack(side="left")

        raw_actions = ttk.Frame(raw_page)
        raw_actions.pack(fill="x", pady=(0, 8))
        ttk.Button(raw_actions, text="Load", command=self.load_minecraft_properties).pack(side="left")
        ttk.Button(raw_actions, text="Save Raw File", style="Accent.TButton", command=self.save_minecraft_properties_raw).pack(side="left", padx=8)
        ttk.Button(raw_actions, text="Open in Notepad", command=self.open_minecraft_properties_notepad).pack(side="left")
        self.minecraft_config_text = tk.Text(raw_page, bg="#111111", fg="#f8f2f0", insertbackground="#f8f2f0", relief="flat", wrap="none", undo=True)
        raw_scroll_y = ttk.Scrollbar(raw_page, orient="vertical", command=self.minecraft_config_text.yview)
        raw_scroll_x = ttk.Scrollbar(raw_page, orient="horizontal", command=self.minecraft_config_text.xview)
        self.minecraft_config_text.configure(yscrollcommand=raw_scroll_y.set, xscrollcommand=raw_scroll_x.set)
        self.minecraft_config_text.pack(side="left", fill="both", expand=True)
        raw_scroll_y.pack(side="right", fill="y")
        raw_scroll_x.pack(side="bottom", fill="x")
        self.after_idle(lambda: self.load_minecraft_properties(silent=True))

    def build_minecraft_mods_tab(self):
        container = self.panel(self.minecraft_mods_tab, "Minecraft Server Mods")
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text="These are the server-side Fabric mod JARs. Client-only shaders and resource packs stay in the CurseForge profile on each computer.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(0, 10))
        actions = ttk.Frame(container, style="Panel.TFrame")
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Refresh", command=self.refresh_minecraft_mods).pack(side="left")
        ttk.Button(actions, text="Sync From CurseForge", command=self.sync_minecraft_mods_from_curseforge).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="Open Mods Folder", command=lambda: self.open_path(self.minecraft_path("minecraft_mods_folder_path"))).pack(side="left", padx=8)
        self.minecraft_mod_sync_status_var = tk.StringVar(value="Server mods sync when Minecraft starts.")
        ttk.Label(container, textvariable=self.minecraft_mod_sync_status_var, style="Panel.TLabel", wraplength=900).pack(anchor="w", pady=(0, 8))
        columns = ("name", "size", "modified")
        self.minecraft_mod_tree = ttk.Treeview(container, columns=columns, show="headings")
        for column, heading, width in (("name", "Mod JAR", 560), ("size", "Size", 100), ("modified", "Modified", 170)):
            self.minecraft_mod_tree.heading(column, text=heading)
            self.minecraft_mod_tree.column(column, width=width, anchor="w")
        scroll = ttk.Scrollbar(container, orient="vertical", command=self.minecraft_mod_tree.yview)
        self.minecraft_mod_tree.configure(yscrollcommand=scroll.set)
        self.minecraft_mod_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def build_minecraft_settings_tab(self):
        container = ttk.Frame(self.minecraft_settings_tab)
        container.pack(fill="both", expand=True)
        paths = ttk.Frame(container, style="Panel.TFrame", padding=14)
        paths.pack(fill="x")
        fields = [
            ("minecraft_server_install_path", "Server folder", False),
            ("minecraft_java_exe_path", "Java executable", True),
            ("minecraft_launcher_jar_path", "Fabric launcher JAR", True),
            ("minecraft_server_properties_path", "server.properties", True),
            ("minecraft_world_folder_path", "World folder", False),
            ("minecraft_mods_folder_path", "Server mods folder", False),
            ("minecraft_curseforge_profile_path", "CurseForge profile folder", False),
            ("minecraft_backup_folder_path", "Backup folder", False),
        ]
        for row_index, (key, label, is_file) in enumerate(fields):
            ttk.Label(paths, text=label, width=24, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(self.settings.get(key, MINECRAFT_DEFAULT_SETTINGS[key])))
            self.minecraft_path_vars[key] = var
            self.path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=row_index, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(paths, text="Browse", command=lambda k=key, f=is_file: self.browse_minecraft_path(k, f)).grid(row=row_index, column=2, pady=4)
        memory_row = len(fields)
        for offset, (key, label) in enumerate((("minecraft_min_memory", "Minimum memory"), ("minecraft_max_memory", "Maximum memory"), ("minecraft_server_port", "Server port"))):
            row = memory_row + offset
            ttk.Label(paths, text=label, width=24, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(self.settings.get(key, MINECRAFT_DEFAULT_SETTINGS[key])))
            self.minecraft_path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Button(paths, text="Save Minecraft Settings", style="Accent.TButton", command=self.save_minecraft_settings).grid(row=memory_row + 3, column=0, sticky="w", pady=(10, 0))

        behavior = self.panel(container, "Minecraft Server Behavior")
        behavior.pack(fill="x", pady=(14, 0))
        self.minecraft_start_on_launch_var = tk.BooleanVar(value=bool(self.settings.get("minecraft_start_server_on_app_launch", False)))
        self.minecraft_auto_restart_var = tk.BooleanVar(value=bool(self.settings.get("minecraft_auto_restart_server", False)))
        self.minecraft_auto_sync_mods_var = tk.BooleanVar(value=bool(self.settings.get("minecraft_auto_sync_mods", True)))
        ttk.Checkbutton(behavior, text="Start Minecraft when this manager opens", variable=self.minecraft_start_on_launch_var).pack(anchor="w")
        ttk.Checkbutton(behavior, text="Auto-restart Minecraft if a managed server crashes", variable=self.minecraft_auto_restart_var).pack(anchor="w", pady=(4, 0))
        ttk.Checkbutton(behavior, text="Sync installed server mods from CurseForge before Minecraft starts", variable=self.minecraft_auto_sync_mods_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(
            behavior,
            text="The manager never force-stops a Minecraft server launched by another app. Console commands are available after Minecraft is started here.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(7, 0))

    # ---------- Settings and configuration ----------

    def minecraft_path(self, key: str) -> Path:
        if key in self.minecraft_path_vars:
            value = self.minecraft_path_vars[key].get().strip()
        else:
            value = str(self.settings.get(key, MINECRAFT_DEFAULT_SETTINGS.get(key, ""))).strip()
        return Path(os.path.expandvars(value))

    def browse_minecraft_path(self, key: str, is_file: bool):
        current = self.minecraft_path_vars[key].get().strip()
        if is_file:
            chosen = filedialog.askopenfilename(initialdir=str(Path(current).parent if current else Path.cwd()))
        else:
            chosen = filedialog.askdirectory(initialdir=current or str(Path.cwd()))
        if chosen:
            self.minecraft_path_vars[key].set(chosen)

    def save_minecraft_settings(self, show_dialog=True):
        for key, var in self.minecraft_path_vars.items():
            self.settings[key] = var.get().strip()
        if self.minecraft_start_on_launch_var is not None:
            self.settings["minecraft_start_server_on_app_launch"] = bool(self.minecraft_start_on_launch_var.get())
        if self.minecraft_auto_restart_var is not None:
            self.settings["minecraft_auto_restart_server"] = bool(self.minecraft_auto_restart_var.get())
        if self.minecraft_auto_sync_mods_var is not None:
            self.settings["minecraft_auto_sync_mods"] = bool(self.minecraft_auto_sync_mods_var.get())
        try:
            self._write_minecraft_settings()
            self.log("Minecraft settings saved.")
            self.refresh_minecraft_all()
            if show_dialog:
                messagebox.showinfo(self.title(), "Minecraft settings saved.")
            return True
        except OSError as exc:
            self.log(f"Minecraft settings save failed: {exc}")
            if show_dialog:
                messagebox.showerror(self.title(), f"Minecraft settings could not be saved:\n{exc}")
            return False

    def _write_minecraft_settings(self):
        settings_path = Path(getattr(self, "settings_file", Path(__file__).resolve().parent / "settings.json"))
        settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def _read_minecraft_properties(self):
        path = self.minecraft_path("minecraft_server_properties_path")
        text = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        values = {}
        for line in text.splitlines():
            if line.lstrip().startswith(("#", "!")) or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return path, text, values

    def load_minecraft_properties(self, silent=False):
        try:
            path, text, values = self._read_minecraft_properties()
        except OSError as exc:
            if not silent:
                messagebox.showerror(self.title(), f"Could not read Minecraft settings:\n{exc}")
            return
        if self.minecraft_config_text is not None:
            self.minecraft_config_text.delete("1.0", "end")
            self.minecraft_config_text.insert("1.0", text)
        for key, var in self.minecraft_property_vars.items():
            var.set(values.get(key, ""))
        if "server-port" in values:
            self.settings["minecraft_server_port"] = values["server-port"]
            if "minecraft_server_port" in self.minecraft_path_vars:
                self.minecraft_path_vars["minecraft_server_port"].set(values["server-port"])
        if not silent:
            self.log(f"Minecraft server.properties loaded: {path}")

    def _minecraft_backup_config(self, path: Path) -> Path | None:
        if not path.exists():
            return None
        target = path.with_name(f"{path.stem}.backup_{datetime.now():%Y-%m-%d_%H-%M-%S}{path.suffix}")
        shutil.copy2(path, target)
        return target

    def save_minecraft_properties_form(self):
        if self.is_minecraft_running():
            messagebox.showwarning(self.title(), "Stop Minecraft before changing server.properties.")
            return False
        path, text, _values = self._read_minecraft_properties()
        if not path.exists():
            messagebox.showerror(self.title(), f"server.properties was not found:\n{path}")
            return False
        replacements = {key: var.get().strip() for key, var in self.minecraft_property_vars.items()}
        lines = text.splitlines(keepends=True)
        found = set()
        output = []
        for line in lines:
            match = re.match(r"^(\s*)([^#!\s][^=]*?)(\s*=\s*)(.*?)(\r?\n)?$", line)
            key = match.group(2).strip() if match else ""
            if match and key in replacements:
                output.append(f"{match.group(1)}{key}{match.group(3)}{replacements[key]}{match.group(5) or os.linesep}")
                found.add(key)
            else:
                output.append(line)
        if output and not output[-1].endswith(("\n", "\r")):
            output[-1] += os.linesep
        for key, value in replacements.items():
            if key not in found:
                output.append(f"{key}={value}{os.linesep}")
        try:
            backup = self._minecraft_backup_config(path)
            path.write_text("".join(output), encoding="utf-8")
            self.settings["minecraft_server_port"] = replacements.get("server-port", "25565")
            self._write_minecraft_settings()
            self.load_minecraft_properties(silent=True)
            self.log(f"Minecraft server.properties saved: {path}")
            messagebox.showinfo(self.title(), f"Minecraft settings saved.\n\nBackup created:\n{backup}")
            return True
        except OSError as exc:
            self.log(f"Minecraft settings save failed: {exc}")
            messagebox.showerror(self.title(), f"Minecraft settings could not be saved:\n{exc}")
            return False

    def save_minecraft_properties_raw(self):
        if self.is_minecraft_running():
            messagebox.showwarning(self.title(), "Stop Minecraft before changing server.properties.")
            return False
        path = self.minecraft_path("minecraft_server_properties_path")
        if self.minecraft_config_text is None:
            return False
        try:
            backup = self._minecraft_backup_config(path)
            path.write_text(self.minecraft_config_text.get("1.0", "end-1c"), encoding="utf-8")
            self.load_minecraft_properties(silent=True)
            self.log(f"Raw Minecraft server.properties saved: {path}")
            messagebox.showinfo(self.title(), f"Minecraft settings saved.\n\nBackup created:\n{backup}")
            return True
        except OSError as exc:
            messagebox.showerror(self.title(), f"Minecraft settings could not be saved:\n{exc}")
            return False

    def apply_minecraft_family_preset(self):
        preset = {
            "gamemode": "creative",
            "difficulty": "easy",
            "pvp": "false",
            "allow-flight": "true",
            "force-gamemode": "false",
        }
        for key, value in preset.items():
            if key in self.minecraft_property_vars:
                self.minecraft_property_vars[key].set(value)
        messagebox.showinfo(
            self.title(),
            "Family settings are loaded into the form. Click Save Settings while the server is stopped.\n\nKeep Inventory is a world rule; while the server is running here, send:\n\ngamerule keepInventory true",
        )

    def open_minecraft_properties_notepad(self):
        path = self.minecraft_path("minecraft_server_properties_path")
        if not path.exists():
            messagebox.showerror(self.title(), f"server.properties was not found:\n{path}")
            return
        try:
            subprocess.Popen(["notepad.exe", str(path)])
        except OSError as exc:
            messagebox.showerror(self.title(), f"Could not open Notepad:\n{exc}")

    # ---------- Process lifecycle ----------

    def _managed_minecraft_process(self):
        with self.minecraft_process_lock:
            process = self.minecraft_process
        if process is not None and process.poll() is None:
            return process
        return None

    def get_minecraft_process_info(self, force=False):
        managed = self._managed_minecraft_process()
        if managed is not None:
            return {"pid": managed.pid, "command": "fabric-server-launch.jar", "managed": True}
        cached_at, cached_value = self.minecraft_process_cache
        if not force and time.monotonic() - cached_at < 2.0:
            return cached_value
        script = (
            "$p=Get-CimInstance Win32_Process -Filter \"Name='java.exe' OR Name='javaw.exe'\" | "
            "Where-Object {$_.CommandLine -like '*fabric-server-launch.jar*'} | "
            "Select-Object -First 1 ProcessId,CommandLine; if($p){$p|ConvertTo-Json -Compress}"
        )
        info = None
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if result.stdout.strip():
                data = json.loads(result.stdout.strip())
                info = {"pid": int(data.get("ProcessId", 0)), "command": data.get("CommandLine", ""), "managed": False}
        except (OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError):
            info = None
        self.minecraft_process_cache = (time.monotonic(), info)
        return info

    def is_minecraft_running(self) -> bool:
        return self.get_minecraft_process_info() is not None

    def start_minecraft_server(self, show_dialog=True):
        self.save_minecraft_settings(show_dialog=False)
        existing = self.get_minecraft_process_info(force=True)
        if existing:
            if show_dialog:
                control = "this manager" if existing.get("managed") else "another app"
                messagebox.showinfo(self.title(), f"Minecraft is already running under {control}.")
            self.refresh_minecraft_all()
            return False
        if self.settings.get("minecraft_auto_sync_mods", True):
            if not self.sync_minecraft_mods_from_curseforge(show_dialog=show_dialog):
                return False
        server_dir = self.minecraft_path("minecraft_server_install_path")
        java = self.minecraft_path("minecraft_java_exe_path")
        launcher = self.minecraft_path("minecraft_launcher_jar_path")
        eula = server_dir / "eula.txt"
        missing = [str(path) for path in (server_dir, java, launcher) if not path.exists()]
        if missing:
            messagebox.showerror(self.title(), "Minecraft cannot start because these paths are missing:\n\n" + "\n".join(missing))
            return False
        if not eula.exists() or not re.search(r"^eula\s*=\s*true\s*$", eula.read_text(encoding="utf-8", errors="replace"), re.I | re.M):
            messagebox.showerror(self.title(), f"Minecraft EULA acceptance was not found in:\n{eula}")
            return False
        xms = str(self.settings.get("minecraft_min_memory", "2G")).strip() or "2G"
        xmx = str(self.settings.get("minecraft_max_memory", "8G")).strip() or "8G"
        command = [str(java), f"-Xms{xms}", f"-Xmx{xmx}", "-XX:+UseG1GC", "-jar", str(launcher), "nogui"]
        try:
            process = subprocess.Popen(
                command,
                cwd=str(server_dir),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except OSError as exc:
            self.log(f"Minecraft start failed: {exc}")
            messagebox.showerror(self.title(), f"Minecraft could not be started:\n{exc}")
            return False
        with self.minecraft_process_lock:
            self.minecraft_process = process
        self.minecraft_process_cache = (0.0, None)
        self.minecraft_should_be_running = True
        self.append_minecraft_console(f"Starting Minecraft with {xms} minimum and {xmx} maximum memory...")
        self.log(f"Minecraft server started under manager control (PID {process.pid}).")
        threading.Thread(target=self._read_minecraft_output, args=(process,), daemon=True).start()
        self.after(500, self.refresh_minecraft_all)
        return True

    def _read_minecraft_output(self, process):
        try:
            if process.stdout is not None:
                for raw_line in process.stdout:
                    clean = raw_line.rstrip()
                    if clean:
                        self.log(f"Minecraft: {clean}")
                        self.after(0, self.append_minecraft_console, clean)
            exit_code = process.wait()
            self.log(f"Minecraft process exited with code {exit_code}.")
            self.after(0, self.append_minecraft_console, f"Minecraft stopped (exit code {exit_code}).")
        finally:
            with self.minecraft_process_lock:
                if self.minecraft_process is process:
                    self.minecraft_process = None
            self.minecraft_process_cache = (0.0, None)
            self.after(0, self.refresh_minecraft_all)

    def send_minecraft_command(self, command=None, quiet=False):
        if command is None:
            command = self.minecraft_command_var.get().strip() if self.minecraft_command_var is not None else ""
        command = str(command).strip().lstrip("/")
        if not command:
            return False
        process = self._managed_minecraft_process()
        if process is None or process.stdin is None:
            if not quiet:
                messagebox.showwarning(
                    self.title(),
                    "Console commands are available after Minecraft has been started from this manager.\n\nThe current server is running outside this app, so use its existing console for now.",
                )
            return False
        try:
            process.stdin.write(command + "\n")
            process.stdin.flush()
            self.append_minecraft_console(f"> {command}")
            if self.minecraft_command_var is not None:
                self.minecraft_command_var.set("")
            return True
        except (OSError, ValueError) as exc:
            self.log(f"Minecraft command failed: {exc}")
            if not quiet:
                messagebox.showerror(self.title(), f"Minecraft command could not be sent:\n{exc}")
            return False

    def stop_minecraft_server(self, show_dialog=True):
        self.minecraft_should_be_running = False
        info = self.get_minecraft_process_info(force=True)
        if not info:
            self.refresh_minecraft_all()
            return True
        if not info.get("managed"):
            if show_dialog:
                messagebox.showwarning(
                    self.title(),
                    "Minecraft is running under the old manager or another console. It has been left running so nobody's game is interrupted.\n\nFor the one-time handover, stop it from the old manager. Then start it from this Minecraft tab.",
                )
            self.log("Minecraft stop refused: process is not controlled by this manager.")
            return False
        self.run_threaded("Minecraft graceful stop", lambda: self._stop_managed_minecraft(show_dialog=show_dialog))
        return True

    def _stop_managed_minecraft(self, show_dialog=True):
        process = self._managed_minecraft_process()
        if process is None:
            return True
        self.send_minecraft_command("stop", quiet=True)
        try:
            process.wait(timeout=45)
            self.log("Minecraft stopped cleanly.")
            self.after(0, self.refresh_minecraft_all)
            return True
        except subprocess.TimeoutExpired:
            self.log("Minecraft did not stop within 45 seconds; it was not force-killed.")
            if show_dialog:
                self.after(0, messagebox.showwarning, self.title(), "Minecraft did not stop within 45 seconds. It was not force-killed. Check the console output.")
            return False

    def restart_minecraft_server(self):
        info = self.get_minecraft_process_info(force=True)
        if info and not info.get("managed"):
            messagebox.showwarning(self.title(), "The existing Minecraft server is controlled by another app and will not be restarted here.")
            return

        def work():
            self.minecraft_should_be_running = False
            if self._stop_managed_minecraft(show_dialog=True):
                time.sleep(2)
                self.after(0, self.start_minecraft_server)

        self.run_threaded("Minecraft restart", work)

    def minecraft_watchdog_tick(self):
        if (
            self.minecraft_should_be_running
            and bool(self.settings.get("minecraft_auto_restart_server", False))
            and not self.is_minecraft_running()
        ):
            self.log("Minecraft watchdog detected a managed server stopped unexpectedly. Restarting it.")
            self.start_minecraft_server(show_dialog=False)

    def handle_minecraft_discord_command(self, command: str, author_id=""):
        if command == "status":
            info = self.get_minecraft_process_info(force=True)
            status = "running" if info else "stopped"
            control = " under this manager" if info and info.get("managed") else ""
            self.send_discord_channel_message(f"Minecraft is currently **{status}**{control}.")
        elif command == "start":
            self.send_discord_channel_message("Minecraft start requested.")
            self.after(0, lambda: self.start_minecraft_server(show_dialog=False))
        elif command == "stop":
            self.send_discord_channel_message("Minecraft graceful stop requested. A server owned by another app will be left running.")
            self.after(0, lambda: self.stop_minecraft_server(show_dialog=False))
        elif command == "restart":
            self.send_discord_channel_message("Minecraft restart requested. A server owned by another app will be left running.")
            self.after(0, self.restart_minecraft_server)
        elif command == "backup":
            self.send_discord_channel_message("Minecraft world backup requested.")
            self.after(0, self.backup_minecraft_now)
        elif command == "help":
            self.send_discord_channel_message("Commands: !minecraft status, start, stop, restart, backup, help")
        else:
            return
        self.log(f"Discord Minecraft command handled: {command} (user {author_id or 'unknown'}).")

    # ---------- Backups and views ----------

    def list_minecraft_backups(self):
        root = self.minecraft_path("minecraft_backup_folder_path")
        if not root.exists():
            return []
        items = []
        for path in root.glob("minecraft-world-*.zip"):
            try:
                items.append((path, datetime.fromtimestamp(path.stat().st_mtime)))
            except OSError:
                pass
        return sorted(items, key=lambda item: item[1], reverse=True)

    def backup_minecraft_now(self):
        info = self.get_minecraft_process_info(force=True)
        if info and not info.get("managed"):
            messagebox.showwarning(
                self.title(),
                "The running Minecraft server belongs to the old manager, so a safe save command cannot be sent from here.\n\nUse the old manager's backup button for now, or stop it and start it from this app before backing up.",
            )
            return
        self.run_threaded("Minecraft world backup", self.create_minecraft_backup)

    def create_minecraft_backup(self):
        world = self.minecraft_path("minecraft_world_folder_path")
        backup_root = self.minecraft_path("minecraft_backup_folder_path")
        if not world.exists() or not world.is_dir():
            self.after(0, messagebox.showerror, self.title(), f"Minecraft world folder was not found:\n{world}")
            return None
        managed_running = self._managed_minecraft_process() is not None
        if managed_running:
            self.send_minecraft_command("save-off", quiet=True)
            self.send_minecraft_command("save-all flush", quiet=True)
            time.sleep(2)
        try:
            backup_root.mkdir(parents=True, exist_ok=True)
            target = backup_root / f"minecraft-world-{datetime.now():%Y-%m-%d_%H-%M-%S}.zip"
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                for source in world.rglob("*"):
                    if not source.is_file() or source.name.lower() == "session.lock":
                        continue
                    archive.write(source, Path(world.name) / source.relative_to(world))
            if not target.exists() or target.stat().st_size == 0:
                raise OSError("backup archive is empty")
            self.log(f"Minecraft world backup created: {target}")
            self.after(0, self.refresh_minecraft_all)
            self.after(0, messagebox.showinfo, self.title(), f"Minecraft world backup created:\n{target}")
            return target
        except (OSError, zipfile.BadZipFile) as exc:
            self.log(f"Minecraft world backup failed: {exc}")
            self.after(0, messagebox.showerror, self.title(), f"Minecraft world backup failed:\n{exc}")
            return None
        finally:
            if managed_running:
                self.send_minecraft_command("save-on", quiet=True)

    def refresh_minecraft_mods(self):
        if self.minecraft_mod_tree is None:
            return
        self.minecraft_mod_tree.delete(*self.minecraft_mod_tree.get_children())
        mods = self.minecraft_path("minecraft_mods_folder_path")
        if not mods.exists():
            return
        for path in sorted(mods.glob("*.jar"), key=lambda item: item.name.lower()):
            try:
                stat = path.stat()
                size = f"{stat.st_size / (1024 * 1024):.2f} MB"
                modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                size, modified = "-", "-"
            self.minecraft_mod_tree.insert("", "end", values=(path.name, size, modified))

    def _read_fabric_mod_metadata(self, path: Path):
        try:
            with zipfile.ZipFile(path, "r") as archive:
                with archive.open("fabric.mod.json") as stream:
                    data = json.loads(stream.read().decode("utf-8"), strict=False)
        except (OSError, KeyError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            raise ValueError(f"Could not read Fabric metadata from {path.name}: {exc}") from exc
        mod_id = str(data.get("id", "")).strip()
        if not mod_id:
            raise ValueError(f"Fabric mod ID is missing from {path.name}.")
        depends = data.get("depends", {})
        return {
            "id": mod_id,
            "version": str(data.get("version", "")).strip(),
            "environment": str(data.get("environment", "*")).strip().lower(),
            "depends": set(depends) if isinstance(depends, dict) else set(),
            "path": path,
        }

    def _index_fabric_mods(self, mods_folder: Path):
        indexed = {}
        for path in sorted(mods_folder.glob("*.jar"), key=lambda item: item.name.lower()):
            metadata = self._read_fabric_mod_metadata(path)
            mod_id = metadata["id"]
            if mod_id in indexed:
                raise ValueError(f"Duplicate Fabric mod ID '{mod_id}' in {indexed[mod_id]['path'].name} and {path.name}.")
            indexed[mod_id] = metadata
        return indexed

    def _create_minecraft_mod_backup(self, server_mods: Path):
        backup_root = self.minecraft_path("minecraft_backup_folder_path") / "mod-backups"
        backup_root.mkdir(parents=True, exist_ok=True)
        target = backup_root / f"minecraft-mods-before-sync-{datetime.now():%Y-%m-%d_%H-%M-%S}.zip"
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in sorted(server_mods.glob("*.jar"), key=lambda item: item.name.lower()):
                archive.write(path, Path("mods") / path.name)
        if not target.exists() or target.stat().st_size == 0:
            raise OSError("Minecraft mod backup archive is empty.")
        return target

    def sync_minecraft_mods_from_curseforge(self, show_dialog=True):
        if self.is_minecraft_running():
            message = "Stop Minecraft before syncing server mods from CurseForge."
            self.log(f"Minecraft mod sync skipped: {message}")
            if self.minecraft_mod_sync_status_var is not None:
                self.minecraft_mod_sync_status_var.set(message)
            if show_dialog:
                messagebox.showwarning(self.title(), message)
            return False

        server_mods = self.minecraft_path("minecraft_mods_folder_path")
        profile = self.minecraft_path("minecraft_curseforge_profile_path")
        profile_mods = profile / "mods"
        try:
            if not server_mods.is_dir():
                raise FileNotFoundError(f"Server mods folder was not found: {server_mods}")
            if not profile_mods.is_dir():
                raise FileNotFoundError(f"CurseForge profile mods folder was not found: {profile_mods}")

            server_index = self._index_fabric_mods(server_mods)
            profile_index = self._index_fabric_mods(profile_mods)
            replacements = []
            for mod_id, server_mod in server_index.items():
                profile_mod = profile_index.get(mod_id)
                if profile_mod is None:
                    continue
                server_path = server_mod["path"]
                profile_path = profile_mod["path"]
                same_file = server_path.stat().st_size == profile_path.stat().st_size and server_path.read_bytes() == profile_path.read_bytes()
                if not same_file:
                    replacements.append((server_mod, profile_mod))

            additions = []
            available_ids = set(server_index)
            dependency_queue = [profile_mod for _, profile_mod in replacements]
            while dependency_queue:
                parent = dependency_queue.pop(0)
                for dependency_id in sorted(parent["depends"]):
                    dependency = profile_index.get(dependency_id)
                    if dependency_id in available_ids or dependency is None or dependency["environment"] == "client":
                        continue
                    available_ids.add(dependency_id)
                    additions.append(dependency)
                    dependency_queue.append(dependency)

            if not replacements and not additions:
                message = "Server mods already match the CurseForge profile."
                self.log(message)
                if self.minecraft_mod_sync_status_var is not None:
                    self.minecraft_mod_sync_status_var.set(message)
                return True

            backup = self._create_minecraft_mod_backup(server_mods)
            staged = []
            try:
                for profile_mod in [item[1] for item in replacements] + additions:
                    destination = server_mods / profile_mod["path"].name
                    temporary = destination.with_name(destination.name + ".syncing")
                    shutil.copy2(profile_mod["path"], temporary)
                    staged.append((temporary, destination))
                for temporary, destination in staged:
                    temporary.replace(destination)
                for server_mod, profile_mod in replacements:
                    old_path = server_mod["path"]
                    if old_path.name != profile_mod["path"].name and old_path.exists():
                        old_path.unlink()
            except OSError:
                for temporary, _ in staged:
                    temporary.unlink(missing_ok=True)
                raise

            changed_names = [item[1]["path"].name for item in replacements] + [item["path"].name for item in additions]
            message = f"Synced {len(changed_names)} server mod{'s' if len(changed_names) != 1 else ''} from CurseForge."
            self.log(f"{message} Rollback: {backup}")
            if self.minecraft_mod_sync_status_var is not None:
                self.minecraft_mod_sync_status_var.set(message)
            self.refresh_minecraft_mods()
            if show_dialog:
                messagebox.showinfo(self.title(), f"{message}\n\nRollback backup:\n{backup}")
            return True
        except (OSError, ValueError) as exc:
            message = f"Minecraft mod sync failed: {exc}"
            self.log(message)
            if self.minecraft_mod_sync_status_var is not None:
                self.minecraft_mod_sync_status_var.set(message)
            if show_dialog:
                messagebox.showerror(self.title(), message)
            return False

    def append_minecraft_console(self, line: str):
        if self.minecraft_console_text is None:
            return
        self.minecraft_console_text.configure(state="normal")
        self.minecraft_console_text.insert("end", str(line) + "\n")
        self.minecraft_console_text.see("end")
        self.minecraft_console_text.configure(state="disabled")

    def refresh_minecraft_status(self):
        if not self.minecraft_vars:
            return
        info = self.get_minecraft_process_info()
        running = info is not None
        managed = bool(info and info.get("managed"))
        self.minecraft_vars["status"].set("Running" if running else "Stopped")
        self.minecraft_vars["control"].set("Managed here - console available" if managed else ("Running outside this app" if running else "Not running"))
        self.minecraft_vars["detected_process"].set(f"java.exe (PID {info.get('pid')})" if info else "None")
        if self.minecraft_status_label is not None:
            self.minecraft_status_label.configure(foreground="#63b96f" if running else "#b8b0ac")
        if self.minecraft_start_button is not None:
            self.minecraft_start_button.configure(style="TButton" if running else "Green.TButton")
        if self.minecraft_stop_button is not None:
            self.minecraft_stop_button.configure(style="Danger.TButton" if managed else "TButton")

    def refresh_minecraft_dashboard(self):
        if not self.minecraft_vars:
            return
        backups = self.list_minecraft_backups()
        self.minecraft_vars["install_path"].set(str(self.minecraft_path("minecraft_server_install_path")))
        self.minecraft_vars["world_path"].set(str(self.minecraft_path("minecraft_world_folder_path")))
        self.minecraft_vars["backup_path"].set(str(self.minecraft_path("minecraft_backup_folder_path")))
        self.minecraft_vars["backup_count"].set(str(len(backups)))
        self.minecraft_vars["last_backup"].set(backups[0][1].strftime("%Y-%m-%d %H:%M") if backups else "No backups found")

    def refresh_minecraft_all(self):
        self.refresh_minecraft_status()
        self.refresh_minecraft_dashboard()
        self.refresh_minecraft_mods()

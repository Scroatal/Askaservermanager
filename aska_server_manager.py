import base64
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

from minecraft_support import MINECRAFT_DEFAULT_SETTINGS, MinecraftManagerMixin


APP_NAME = "Gaming Dads Server Manager"
APP_VERSION = "0.3.0"
SOURCE_DIR = Path(__file__).resolve().parent
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else SOURCE_DIR
SETTINGS_FILE = APP_DIR / "settings.json"
MOD_SOURCES_FILE = APP_DIR / "mods.json"
ASSET_FILE = APP_DIR / "assets" / "aska_manager_icon.png"
SERVER_EXE_NAME = "AskaServer.exe"
ASKA_DEDICATED_SERVER_APP_ID = "3246670"
WINDROSE_EXE_NAME = "WindroseServer.exe"
WINDROSE_DEDICATED_SERVER_APP_ID = "4129620"
PALWORLD_EXE_NAME = "PalServer.exe"
PALWORLD_PROCESS_NAME = "PalServer"
PALWORLD_DEDICATED_SERVER_APP_ID = "2394010"
VALHEIM_EXE_NAME = "valheim_server.exe"
VALHEIM_PROCESS_NAME = "valheim_server"
VALHEIM_DEDICATED_SERVER_APP_ID = "896660"
ABIOTIC_EXE_NAME = "AbioticFactorServer-Win64-Shipping.exe"
ABIOTIC_PROCESS_NAME = "AbioticFactorServer-Win64-Shipping"
ABIOTIC_DEDICATED_SERVER_APP_ID = "2857200"
NEXUS_GAME_DOMAIN = "aska"
BACKUP_PREFIX = "backup_"
BACKUP_TIME_FORMAT = "%Y-%m-%d_%H-%M"

DEFAULT_INSTALL = Path(r"E:\steam\steamapps\common\ASKA Dedicated Server")
DEFAULT_WINDROSE_INSTALL = Path(r"E:\steam\steamapps\common\Windrose Dedicated Server")
DEFAULT_BACKUPS = Path(r"E:\aska_backups")
DEFAULT_WINDROSE_BACKUPS = Path(r"E:\windrose_backups")
DEFAULT_PALWORLD_INSTALL = Path(r"E:\steam\steamapps\common\PalServer")
DEFAULT_PALWORLD_BACKUPS = Path(r"E:\palworld_backups")
DEFAULT_VALHEIM_INSTALL = Path(r"E:\steam\steamapps\common\Valheim dedicated server")
DEFAULT_VALHEIM_BACKUPS = Path(r"E:\valheim_backups")
DEFAULT_ABIOTIC_INSTALL = Path(r"E:\steam\steamapps\common\Abiotic Factor Dedicated Server")
DEFAULT_ABIOTIC_BACKUPS = Path(r"E:\abiotic_backups")
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
    "launch_on_windows_startup": False,
    "start_server_on_app_launch": False,
    "auto_restart_server": False,
    "windrose_server_install_path": str(DEFAULT_WINDROSE_INSTALL),
    "windrose_server_bat_path": str(DEFAULT_WINDROSE_INSTALL / "StartServerForeground.bat"),
    "windrose_server_exe_path": str(DEFAULT_WINDROSE_INSTALL / "WindroseServer.exe"),
    "windrose_server_config_path": str(DEFAULT_WINDROSE_INSTALL / "R5" / "ServerDescription.json"),
    "windrose_save_folder_path": str(DEFAULT_WINDROSE_INSTALL / "R5" / "Saved" / "SaveProfiles" / "Default" / "RocksDB"),
    "windrose_backup_folder_path": str(DEFAULT_WINDROSE_BACKUPS),
    "windrose_auto_restart_server": False,
    "palworld_server_install_path": str(DEFAULT_PALWORLD_INSTALL),
    "palworld_server_exe_path": str(DEFAULT_PALWORLD_INSTALL / PALWORLD_EXE_NAME),
    "palworld_server_config_path": str(DEFAULT_PALWORLD_INSTALL / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini"),
    "palworld_save_folder_path": str(DEFAULT_PALWORLD_INSTALL / "Pal" / "Saved" / "SaveGames"),
    "palworld_backup_folder_path": str(DEFAULT_PALWORLD_BACKUPS),
    "palworld_auto_restart_server": False,
    "palworld_rest_base_url": "http://127.0.0.1:8212/v1/api",
    "palworld_rest_username": "admin",
    "palworld_admin_password": "",
    "palworld_discord_monitor_enabled": False,
    "palworld_discord_bot_token": "",
    "palworld_discord_channel_id": "",
    "palworld_discord_webhook_url": "",
    "palworld_discord_allowed_user_ids": "",
    "palworld_discord_last_message_id": "",
    "discord_monitor_enabled": False,
    "discord_bot_token": "",
    "discord_channel_id": "",
    "discord_webhook_url": "",
    "discord_allowed_user_ids": "",
    "discord_last_message_id": "",
    "valheim_server_install_path": str(DEFAULT_VALHEIM_INSTALL),
    "valheim_server_exe_path": str(DEFAULT_VALHEIM_INSTALL / VALHEIM_EXE_NAME),
    "valheim_server_bat_path": str(DEFAULT_VALHEIM_INSTALL / "start_headless_server.bat"),
    "valheim_save_folder_path": str(Path(os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\IronGate\Valheim"))),
    "valheim_backup_folder_path": str(DEFAULT_VALHEIM_BACKUPS),
    "valheim_auto_restart_server": False,
    "abiotic_server_install_path": str(DEFAULT_ABIOTIC_INSTALL),
    "abiotic_server_exe_path": str(DEFAULT_ABIOTIC_INSTALL / "AbioticFactor" / "Binaries" / "Win64" / ABIOTIC_EXE_NAME),
    "abiotic_server_config_path": str(DEFAULT_ABIOTIC_INSTALL / "AbioticFactor" / "Saved" / "Config" / "WindowsServer"),
    "abiotic_sandbox_settings_path": str(DEFAULT_ABIOTIC_INSTALL / "AbioticFactor" / "Saved" / "Config" / "WindowsServer" / "SandboxSettings.ini"),
    "abiotic_save_folder_path": str(DEFAULT_ABIOTIC_INSTALL / "AbioticFactor" / "Saved" / "SaveGames" / "Server" / "Worlds"),
    "abiotic_server_port": "9876",
    "abiotic_query_port": "25575",
    "abiotic_server_name": "fleshraiders",
    "abiotic_server_password": "flesh123",
    "abiotic_backup_folder_path": str(DEFAULT_ABIOTIC_BACKUPS),
    "abiotic_auto_restart_server": False,
    "abiotic_backup_before_restart": True,
    "abiotic_last_preset": "",
}
DEFAULT_SETTINGS.update(MINECRAFT_DEFAULT_SETTINGS)

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

PALWORLD_CONFIG_FIELDS = [
    ("ServerName", "Server name", "text"),
    ("ServerDescription", "Server description", "text"),
    ("ServerPassword", "Server password", "text"),
    ("AdminPassword", "Admin password", "text"),
    ("ServerPlayerMaxNum", "Maximum players", "number"),
    ("bIsUseBackupSaveData", "Automatic world backups", "bool"),
    ("RESTAPIEnabled", "Enable REST API", "bool"),
    ("RESTAPIPort", "REST API port", "number"),
    ("RCONEnabled", "Enable RCON", "bool"),
    ("RCONPort", "RCON port", "number"),
    ("MaxBuildingLimitNum", "Building limit per player (0 = unlimited)", "number"),
    ("DeathPenalty", "Death penalty", "choice:None|Item|ItemAndEquipment|All"),
    ("bHardcore", "Hardcore mode", "bool"),
    ("bPalLost", "Pals lost on death", "bool"),
    ("PalCaptureRate", "Pal capture rate", "number"),
    ("CollectionDropRate", "Collection drop rate", "number"),
    ("EnemyDropItemRate", "Enemy drop item rate", "number"),
    ("ExpRate", "Experience rate", "number"),
    ("DayTimeSpeedRate", "Day speed rate", "number"),
    ("NightTimeSpeedRate", "Night speed rate", "number"),
    ("PlayerAutoHPRegeneRate", "Player health regeneration", "number"),
    ("PlayerStaminaDecreaceRate", "Player stamina drain", "number"),
    ("PlayerStomachDecreaceRate", "Player hunger drain", "number"),
    ("PalAutoHPRegeneRate", "Pal health regeneration", "number"),
    ("PalStaminaDecreaceRate", "Pal stamina drain", "number"),
    ("PalStomachDecreaceRate", "Pal hunger drain", "number"),
    ("bIsPvP", "Enable PvP", "bool"),
]

VALHEIM_CONFIG_FIELDS = [
    ("name", "Server name", "text"),
    ("port", "Port", "number"),
    ("world", "World name", "text"),
    ("password", "Server password", "text"),
    ("public", "Public listing (0 or 1)", "number"),
    ("savedir", "Save directory override", "text"),
    ("saveinterval", "Save interval seconds", "number"),
    ("backups", "Automatic backup count", "number"),
    ("backupshort", "Short backup interval seconds", "number"),
    ("backuplong", "Long backup interval seconds", "number"),
    ("crossplay", "Enable crossplay backend", "bool"),
    ("preset", "World modifier preset", "choice:Normal|Casual|Easy|Hard|Hardcore|Immersive|Hammer"),
]

ABIOTIC_SANDBOX_FIELDS = [
    ("GameDifficulty", "Game difficulty", "number", "World"),
    ("HardcoreMode", "Hardcore mode", "bool", "World"),
    ("LootRespawnEnabled", "Loot respawns", "bool", "World"),
    ("PowerSocketsOffAtNight", "Power sockets turn off at night", "bool", "World"),
    ("DayNightCycleState", "Day/night cycle", "number", "World"),
    ("DayNightCycleSpeedMultiplier", "Day/night speed multiplier", "number", "World"),
    ("WeatherFrequency", "Weather frequency", "number", "World"),
    ("SinkRefillRate", "Sink refill rate", "number", "World"),
    ("FoodSpoilSpeedMultiplier", "Food spoil speed", "number", "World"),
    ("RefrigerationEffectivenessMultiplier", "Refrigeration effectiveness", "number", "World"),
    ("StorageByTag", "Restrict storage by item tag", "bool", "World"),
    ("StructuralSupportLimit", "Structural support limit", "number", "World"),
    ("BridgeSupports", "Bridge supports required", "number", "World"),
    ("HomeWorlds", "Allow home worlds", "bool", "World"),
    ("TaintedSinkWater", "Sinks give tainted water", "bool", "World"),
    ("RadiationDealsDamage", "Radiation deals damage", "bool", "World"),
    ("EnemySpawnRate", "Enemy spawn rate", "number", "Enemies"),
    ("EnemyHealthMultiplier", "Enemy health multiplier", "number", "Enemies"),
    ("EnemyPlayerDamageMultiplier", "Enemy damage to players", "number", "Enemies"),
    ("EnemyDeployableDamageMultiplier", "Enemy damage to deployables", "number", "Enemies"),
    ("DetectionSpeedMultiplier", "Detection speed multiplier", "number", "Enemies"),
    ("EnemyAccuracy", "Enemy accuracy", "number", "Enemies"),
    ("ApocalypticAbilities", "Apocalyptic abilities", "bool", "Enemies"),
    ("MaximizeEnemySpawns", "Maximize enemy spawns", "bool", "Enemies"),
    ("DamageToAlliesMultiplier", "Friendly-fire damage multiplier", "number", "Players"),
    ("HungerSpeedMultiplier", "Hunger speed", "number", "Players"),
    ("ThirstSpeedMultiplier", "Thirst speed", "number", "Players"),
    ("FatigueSpeedMultiplier", "Fatigue speed", "number", "Players"),
    ("ContinenceSpeedMultiplier", "Continence speed", "number", "Players"),
    ("BonusPerkPoints", "Bonus perk points", "number", "Players"),
    ("PlayerXPGainMultiplier", "Player XP gain", "number", "Players"),
    ("ItemStackSizeMultiplier", "Item stack size multiplier", "number", "Items"),
    ("ItemWeightMultiplier", "Item weight multiplier", "number", "Items"),
    ("ItemDurabilityMultiplier", "Item durability multiplier", "number", "Items"),
    ("DurabilityLossOnDeathMultiplier", "Durability loss on death", "number", "Items"),
    ("ShowDeathMessages", "Show death messages", "bool", "Players"),
    ("AllowRecipeSharing", "Allow recipe sharing", "bool", "Players"),
    ("AllowPagers", "Allow pagers", "bool", "Players"),
    ("AllowTransmog", "Allow transmog", "bool", "Players"),
    ("DisableResearchMinigame", "Disable research minigame", "bool", "Players"),
    ("DeathPenalties", "Death penalties", "number", "Players"),
    ("FirstTimeStartingWeapon", "First-time starting weapon", "number", "Players"),
    ("HostAccessPlayerCorpses", "Host can access player corpses", "bool", "Players"),
    ("AllowCharacterReset", "Allow character reset", "bool", "Players"),
    ("BaseInventorySize", "Base inventory slots", "number", "Players"),
    ("PlayerFurnitureDestruction", "Players can destroy furniture", "bool", "Players"),
    ("AllowIronMode", "Allow Ironman mode", "bool", "Players"),
    ("InvisibleRadiation", "Invisible radiation", "bool", "Players"),
]

ABIOTIC_SANDBOX_DEFAULTS = {
    "GameDifficulty": "1", "HardcoreMode": "False", "LootRespawnEnabled": "False", "PowerSocketsOffAtNight": "True",
    "DayNightCycleState": "0", "DayNightCycleSpeedMultiplier": "1.0", "WeatherFrequency": "3", "SinkRefillRate": "1.0",
    "FoodSpoilSpeedMultiplier": "1.0", "RefrigerationEffectivenessMultiplier": "1.0", "StorageByTag": "True",
    "StructuralSupportLimit": "5", "BridgeSupports": "2", "HomeWorlds": "True", "TaintedSinkWater": "False",
    "RadiationDealsDamage": "False", "EnemySpawnRate": "1.0", "EnemyHealthMultiplier": "1.0",
    "EnemyPlayerDamageMultiplier": "1.0", "EnemyDeployableDamageMultiplier": "1.0", "DetectionSpeedMultiplier": "1.0",
    "EnemyAccuracy": "2", "ApocalypticAbilities": "False", "MaximizeEnemySpawns": "False", "DamageToAlliesMultiplier": "0.5",
    "HungerSpeedMultiplier": "1.0", "ThirstSpeedMultiplier": "1.0", "FatigueSpeedMultiplier": "1.0", "ContinenceSpeedMultiplier": "1.0",
    "BonusPerkPoints": "0", "PlayerXPGainMultiplier": "1.0", "ItemStackSizeMultiplier": "1.0", "ItemWeightMultiplier": "1.0",
    "ItemDurabilityMultiplier": "1.0", "DurabilityLossOnDeathMultiplier": "0.1", "ShowDeathMessages": "True",
    "AllowRecipeSharing": "True", "AllowPagers": "True", "AllowTransmog": "True", "DisableResearchMinigame": "False",
    "DeathPenalties": "1", "FirstTimeStartingWeapon": "0", "HostAccessPlayerCorpses": "True", "AllowCharacterReset": "True",
    "BaseInventorySize": "12", "PlayerFurnitureDestruction": "False", "AllowIronMode": "True", "InvisibleRadiation": "False",
}

ABIOTIC_QOL_PRESET = {
    "LootRespawnEnabled": "True", "SinkRefillRate": "10.0", "FoodSpoilSpeedMultiplier": "0.5", "StorageByTag": "False",
    "StructuralSupportLimit": "0", "BridgeSupports": "0", "DamageToAlliesMultiplier": "0.0", "ItemStackSizeMultiplier": "30.0",
    "ItemWeightMultiplier": "0.0", "ItemDurabilityMultiplier": "10.0", "DurabilityLossOnDeathMultiplier": "0.0",
    "DeathPenalties": "0", "BaseInventorySize": "42",
}

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


class AskaServerManager(MinecraftManagerMixin, tk.Tk):
    def __init__(self):
        super().__init__()
        self.main_thread_id = threading.get_ident()
        self.title(APP_NAME)
        self.geometry("1180x780")
        self.minsize(980, 680)
        self.settings = read_json(SETTINGS_FILE, DEFAULT_SETTINGS)
        self.settings_file = SETTINGS_FILE
        self.mod_sources = read_json(MOD_SOURCES_FILE, {})
        self.auto_backup_job = None
        self.status_job = None
        self.watchdog_job = None
        self.server_should_be_running = False
        self.config_vars = {}
        self.path_vars = {}
        self.dashboard_vars = {}
        self.overview_status_vars = {}
        self.aska_notebook = None
        self.log_text = None
        self.backup_tree = None
        self.backup_size_generation = 0
        self.mod_plugin_tree = None
        self.mod_config_tree = None
        self.mod_config_text = None
        self.current_mod_config_path = None
        self.mod_source_label_var = None
        self.start_button = None
        self.stop_button = None
        self.update_server_button = None
        self.windrose_vars = {}
        self.windrose_path_vars = {}
        self.windrose_start_button = None
        self.windrose_stop_button = None
        self.windrose_update_button = None
        self.windrose_backup_tree = None
        self.windrose_config_text = None
        self.windrose_config_notebook = None
        self.windrose_config_form_vars = {}
        self.windrose_config_form_types = {}
        self.windrose_config_form = None
        self.palworld_vars = {}
        self.palworld_path_vars = {}
        self.palworld_start_button = None
        self.palworld_stop_button = None
        self.palworld_update_button = None
        self.palworld_config_text = None
        self.palworld_config_vars = {}
        self.palworld_view_notebook = None
        self.palworld_config_notebook = None
        self.palworld_should_be_running = False
        self.palworld_auto_restart_var = None
        self.palworld_discord_enabled_var = None
        self.palworld_discord_token_var = None
        self.palworld_discord_channel_var = None
        self.palworld_discord_webhook_var = None
        self.palworld_discord_allowed_users_var = None
        self.discord_enabled_var = None
        self.discord_token_var = None
        self.discord_channel_var = None
        self.discord_webhook_var = None
        self.discord_allowed_users_var = None
        self.palworld_rest_url_var = None
        self.palworld_rest_user_var = None
        self.palworld_rest_password_var = None
        self.discord_monitor_thread = None
        self.discord_monitor_stop = threading.Event()
        self.valheim_vars = {}
        self.valheim_path_vars = {}
        self.valheim_start_button = None
        self.valheim_stop_button = None
        self.valheim_update_button = None
        self.valheim_config_text = None
        self.valheim_config_vars = {}
        self.valheim_config_types = {}
        self.valheim_auto_restart_var = None
        self.valheim_should_be_running = False
        self.abiotic_vars = {}
        self.abiotic_path_vars = {}
        self.abiotic_start_button = None
        self.abiotic_stop_button = None
        self.abiotic_update_button = None
        self.abiotic_should_be_running = False
        self.abiotic_auto_restart_var = None
        self.abiotic_backup_before_restart_var = None
        self.abiotic_sandbox_vars = {}
        self.abiotic_sandbox_kinds = {}
        self.abiotic_sandbox_status_var = None
        self.port_check_tree = None
        self.port_check_status_var = None
        self.port_check_button = None
        self.nexus_key_status_var = None
        self.icon_image = None
        self.dashboard_icon_image = None
        self.initialize_minecraft_state()

        self.configure(bg=COLORS["bg"])
        self.build_styles()
        self.build_ui()
        self.ensure_settings_file()
        self.log("App startup.")
        self.after(100, self.refresh_all)
        if self.settings.get("backup_on_startup"):
            self.run_threaded("Startup backup", self.create_backup)
        self.after(200, self.schedule_status_refresh)
        self.schedule_auto_backup()
        self.after(3500, lambda: self.check_server_update(show_dialog=False))
        self.after(4500, lambda: self.check_windrose_update(show_dialog=False))
        self.after(5500, lambda: self.check_palworld_update(show_dialog=False))
        self.after(6500, lambda: self.check_valheim_update(show_dialog=False))
        self.after(7500, lambda: self.check_abiotic_update(show_dialog=False))
        self.after(350, self.initialize_server_expectations)
        self.schedule_server_watchdog()
        self.start_discord_monitor()

    def initialize_server_expectations(self):
        if self.settings.get("start_server_on_app_launch"):
            self.server_should_be_running = True
            self.after(2500, self.start_server)
        elif self.is_server_running():
            self.server_should_be_running = True
        if self.is_palworld_running():
            self.palworld_should_be_running = True
        if self.is_valheim_running():
            self.valheim_should_be_running = True
        if self.is_abiotic_running():
            self.abiotic_should_be_running = True
        if self.settings.get("minecraft_start_server_on_app_launch"):
            self.after(3000, lambda: self.start_minecraft_server(show_dialog=False))

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
        style.configure("Green.TButton", background="#278a42", foreground=COLORS["text"])
        style.map("Green.TButton", background=[("active", "#1f6f35")])
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
            text=f"Local Windows manager for ASKA, Windrose, Palworld, Valheim, Abiotic Factor, and Minecraft servers - v{APP_VERSION}",
            style="Muted.TLabel",
        ).pack(anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.overview_tab = ttk.Frame(self.notebook, padding=14)
        self.aska_tab = ttk.Frame(self.notebook, padding=0)
        self.aska_notebook = ttk.Notebook(self.aska_tab)
        self.aska_notebook.pack(fill="both", expand=True)
        self.windrose_tab = ttk.Frame(self.notebook, padding=0)
        self.palworld_tab = ttk.Frame(self.notebook, padding=0)
        self.valheim_tab = ttk.Frame(self.notebook, padding=0)
        self.abiotic_tab = ttk.Frame(self.notebook, padding=0)
        self.minecraft_tab = ttk.Frame(self.notebook, padding=0)
        self.ports_tab = ttk.Frame(self.notebook, padding=14)
        self.backups_tab = ttk.Frame(self.notebook, padding=14)
        self.dashboard_tab = ttk.Frame(self.aska_notebook, padding=0)
        self.config_tab = ttk.Frame(self.aska_notebook, padding=14)
        self.mods_tab = ttk.Frame(self.aska_notebook, padding=14)
        self.settings_tab = ttk.Frame(self.aska_notebook, padding=0)
        self.logs_tab = ttk.Frame(self.notebook, padding=14)

        self.notebook.add(self.overview_tab, text="Dashboard")
        self.notebook.add(self.aska_tab, text="ASKA")
        self.notebook.add(self.windrose_tab, text="Windrose")
        self.notebook.add(self.palworld_tab, text="Palworld")
        self.notebook.add(self.valheim_tab, text="Valheim")
        self.notebook.add(self.abiotic_tab, text="Abiotic Factor")
        self.notebook.add(self.minecraft_tab, text="Minecraft")
        self.notebook.add(self.ports_tab, text="Ports")
        self.notebook.add(self.backups_tab, text="Backups")
        self.notebook.add(self.logs_tab, text="Logs")

        self.aska_notebook.add(self.dashboard_tab, text="Server")
        self.aska_notebook.add(self.config_tab, text="Config")
        self.aska_notebook.add(self.mods_tab, text="Mods")
        self.aska_notebook.add(self.settings_tab, text="Settings")

        self.build_overview_tab()
        self.build_dashboard_tab()
        self.build_windrose_tab()
        self.build_palworld_tab()
        self.build_valheim_tab()
        self.build_abiotic_tab()
        self.build_minecraft_tab()
        self.build_ports_tab()
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

    def build_overview_tab(self):
        top = ttk.Frame(self.overview_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Gaming Dads Servers")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Quick Access")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        ttk.Label(left, text="SERVER STATUS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        self.overview_status_vars = {}
        for server in ("ASKA", "Windrose", "Palworld", "Valheim", "Abiotic Factor", "Minecraft"):
            row = ttk.Frame(left, style="Panel.TFrame")
            row.pack(fill="x", pady=6)
            ttk.Label(row, text=server, width=18, style="Panel.TLabel").pack(side="left")
            status_var = tk.StringVar(value="Stopped")
            self.overview_status_vars[server] = status_var
            ttk.Label(row, textvariable=status_var, style="Panel.TLabel").pack(side="left")

        ttk.Label(right, text="OPEN SERVER MANAGERS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        actions = ttk.Frame(right, style="Panel.TFrame")
        actions.pack(fill="x")
        for label, tab in (("Open ASKA", self.aska_tab), ("Open Windrose", self.windrose_tab), ("Open Palworld", self.palworld_tab), ("Open Valheim", self.valheim_tab), ("Open Abiotic Factor", self.abiotic_tab), ("Open Minecraft", self.minecraft_tab), ("Open Ports", self.ports_tab)):
            ttk.Button(actions, text=label, command=lambda target=tab: self.notebook.select(target)).pack(fill="x", pady=4)

        ttk.Label(
            right,
            text="ASKA-specific server controls, config, mods, and settings are grouped inside the ASKA tab.",
            style="Panel.TLabel",
            wraplength=460,
        ).pack(anchor="w", pady=(16, 0))

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
                self.dashboard_icon_image = tk.PhotoImage(file=str(asset_file)).subsample(8, 8)
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
        self.start_button = ttk.Button(buttons, text="Start Server", command=self.start_server)
        self.start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.stop_button = ttk.Button(buttons, text="Stop Server", command=self.stop_server)
        self.stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Server", command=self.restart_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Now", style="Accent.TButton", command=lambda: self.run_threaded("Backup", self.create_backup)).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install Folder", command=lambda: self.open_path(self.path("server_install_path"))).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Save Folder", command=lambda: self.open_path(self.path("save_folder_path"))).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Server Update", command=lambda: self.check_server_update(show_dialog=True)).grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        self.update_server_button = ttk.Button(buttons, text="Update Server", command=self.update_server_with_steamcmd)
        self.update_server_button.grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        danger = self.panel(left, "Dangerous actions")
        danger.pack(fill="x", pady=(12, 0))
        ttk.Button(danger, text="Wipe Current Server Save", style="Danger.TButton", command=self.wipe_save).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            danger,
            text="Wiping refuses to run while the server is active and makes an emergency backup first.",
            style="Panel.TLabel",
            wraplength=480,
        ).pack(anchor="w")

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

    def build_windrose_tab(self):
        self.windrose_notebook = ttk.Notebook(self.windrose_tab)
        self.windrose_notebook.pack(fill="both", expand=True)
        self.windrose_server_tab = ttk.Frame(self.windrose_notebook, padding=14)
        self.windrose_config_tab = ttk.Frame(self.windrose_notebook, padding=14)
        self.windrose_mods_tab = ttk.Frame(self.windrose_notebook, padding=14)
        self.windrose_settings_tab = ttk.Frame(self.windrose_notebook, padding=14)
        self.windrose_notebook.add(self.windrose_server_tab, text="Server")
        self.windrose_notebook.add(self.windrose_config_tab, text="Config")
        self.windrose_notebook.add(self.windrose_mods_tab, text="Mods")
        self.windrose_notebook.add(self.windrose_settings_tab, text="Settings")
        self.build_windrose_server_tab()
        self.build_windrose_config_tab()
        self.build_game_mods_tab(self.windrose_mods_tab, "Windrose", "windrose_server_install_path")
        self.build_windrose_settings_tab()

    def build_windrose_server_tab(self):
        top = ttk.Frame(self.windrose_server_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Windrose Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Windrose Status And Backups")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        for key, label in [
            ("status", "Server status"),
            ("detected_process", "Detected process"),
            ("update_status", "Server update"),
            ("install_path", "Install path"),
            ("save_folder_path", "Save folder"),
            ("backup_folder_path", "Backup folder"),
            ("config_path", "Config file"),
            ("backup_count", "Backups stored"),
        ]:
            self.windrose_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(left if key == "status" else right, style="Panel.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            label_widget = ttk.Label(row, textvariable=self.windrose_vars[key], style="Panel.TLabel", wraplength=430)
            label_widget.pack(side="left", fill="x", expand=True)
            if key == "status":
                self.windrose_status_label = label_widget

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 16))
        self.windrose_start_button = ttk.Button(buttons, text="Start Windrose", command=self.start_windrose_server)
        self.windrose_start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.windrose_stop_button = ttk.Button(buttons, text="Stop Windrose", command=self.stop_windrose_server)
        self.windrose_stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Windrose", command=self.restart_windrose_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Windrose", style="Accent.TButton", command=lambda: self.run_threaded("Windrose backup", self.create_windrose_backup)).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Update", command=lambda: self.check_windrose_update(show_dialog=True)).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.windrose_update_button = ttk.Button(buttons, text="Update Windrose", command=self.update_windrose_server_with_steamcmd)
        self.windrose_update_button.grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install", command=lambda: self.open_path(self.path("windrose_server_install_path"))).grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Save", command=lambda: self.open_path(self.path("windrose_save_folder_path"))).grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Backups", command=lambda: self.open_path(self.path("windrose_backup_folder_path"))).grid(row=2, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Install Windrose Server", style="Green.TButton", command=self.install_windrose_server_with_steamcmd).grid(row=3, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        ttk.Label(
            left,
            text="Windrose support uses the official dedicated server tool. Restore and wipe controls are left out until your group confirms the exact save path on the host machine.",
            style="Panel.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(
            left,
            text="Configure paths and ServerDescription.json from the Settings and Config tabs.",
            style="Panel.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(0, 12))

    def build_windrose_config_tab(self):
        self.windrose_config_notebook = ttk.Notebook(self.windrose_config_tab)
        self.windrose_config_notebook.pack(fill="both", expand=True)
        form_page = ttk.Frame(self.windrose_config_notebook, padding=8)
        raw_page = ttk.Frame(self.windrose_config_notebook, padding=8)
        self.windrose_config_notebook.add(form_page, text="Config Form")
        self.windrose_config_notebook.add(raw_page, text="Raw JSON")
        self.build_windrose_config_form(form_page)

        config_actions = ttk.Frame(raw_page, style="Panel.TFrame")
        config_actions.pack(fill="x", pady=(0, 8))
        ttk.Label(config_actions, text="SERVERDESCRIPTION.JSON", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(config_actions, text="Load", command=self.load_windrose_config).pack(side="right")
        ttk.Button(config_actions, text="Save", style="Accent.TButton", command=self.save_windrose_config).pack(side="right", padx=8)
        self.windrose_config_text = tk.Text(
            raw_page,
            bg="#111111",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            relief="flat",
            wrap="none",
            height=8,
            undo=True,
        )
        self.windrose_config_text.pack(fill="both", expand=True)

    def build_windrose_settings_tab(self):
        container = ttk.Frame(self.windrose_settings_tab)
        container.pack(fill="both", expand=True)
        paths = ttk.Frame(container, style="Panel.TFrame", padding=14)
        paths.pack(fill="x")
        ttk.Button(paths, text="Auto-detect Windrose", style="Accent.TButton", command=self.autodetect_windrose_paths).grid(row=0, column=2, sticky="e", pady=(0, 10))
        for row_index, (key, label, is_file) in enumerate([
            ("windrose_server_install_path", "Install folder", False),
            ("windrose_server_bat_path", "Launcher batch file", True),
            ("windrose_server_exe_path", "Server executable", True),
            ("windrose_server_config_path", "ServerDescription.json", True),
            ("windrose_save_folder_path", "Save folder", False),
            ("windrose_backup_folder_path", "Backup folder", False),
        ]):
            grid_row = row_index + 1
            ttk.Label(paths, text=label, width=22, style="Panel.TLabel").grid(row=grid_row, column=0, sticky="w", pady=5)
            var = tk.StringVar(value=str(self.settings.get(key, "")))
            self.windrose_path_vars[key] = var
            self.path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=grid_row, column=1, sticky="ew", padx=8, pady=5)
            ttk.Button(paths, text="Browse", command=lambda k=key, f=is_file: self.browse_path(k, f)).grid(row=grid_row, column=2, pady=5)
        paths.columnconfigure(1, weight=1)
        ttk.Button(paths, text="Save Windrose Settings", style="Accent.TButton", command=self.save_windrose_settings).grid(row=7, column=0, sticky="w", pady=(12, 0))

        note = self.panel(container, "Server Behavior")
        note.pack(fill="x", pady=(14, 0))
        ttk.Label(note, text="Windrose does not start automatically when the manager opens. Configure the launcher and paths here before using the Server tab.", style="Panel.TLabel", wraplength=900).pack(anchor="w")

        self.build_discord_panel(
            container,
            "Windrose Discord Controls",
            "Commands: !windrose status, restart, start, stop, backup, help. The same bot settings are shared with Palworld.",
        )

    def get_discord_setting(self, name, default=""):
        shared_key = f"discord_{name}"
        legacy_key = f"palworld_discord_{name}"
        shared_value = self.settings.get(shared_key)
        legacy_value = self.settings.get(legacy_key)
        if name == "monitor_enabled":
            # Do not silently activate the built-in bot from an old Palworld
            # flag. Some machines still run the dedicated Discord bot at
            # startup; requiring the shared switch prevents duplicate replies.
            return bool(shared_value) if shared_value is not None else bool(default)
        if shared_value not in (None, "") and shared_value is not False:
            return shared_value
        if legacy_value not in (None, "") and legacy_value is not False:
            return legacy_value
        return default

    def ensure_discord_vars(self):
        if self.discord_enabled_var is None:
            self.discord_enabled_var = tk.BooleanVar(value=bool(self.get_discord_setting("monitor_enabled", False)))
            self.discord_token_var = tk.StringVar(value=str(self.get_discord_setting("bot_token", "")))
            self.discord_channel_var = tk.StringVar(value=str(self.get_discord_setting("channel_id", "")))
            self.discord_webhook_var = tk.StringVar(value=str(self.get_discord_setting("webhook_url", "")))
            self.discord_allowed_users_var = tk.StringVar(value=str(self.get_discord_setting("allowed_user_ids", "")))
        self.palworld_discord_enabled_var = self.discord_enabled_var
        self.palworld_discord_token_var = self.discord_token_var
        self.palworld_discord_channel_var = self.discord_channel_var
        self.palworld_discord_webhook_var = self.discord_webhook_var
        self.palworld_discord_allowed_users_var = self.discord_allowed_users_var

    def build_discord_panel(self, parent, title, command_note):
        self.ensure_discord_vars()
        discord = ttk.Frame(parent, style="Panel.TFrame", padding=14)
        discord.pack(fill="x", pady=(14, 0))
        ttk.Label(discord, text=title.upper(), style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Checkbutton(discord, text="Enable Discord monitor", variable=self.discord_enabled_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=3)
        for row_index, (label, var, show) in enumerate([
            ("Bot token", self.discord_token_var, "*"),
            ("Channel ID", self.discord_channel_var, None),
            ("Webhook URL", self.discord_webhook_var, None),
            ("Allowed user IDs", self.discord_allowed_users_var, None),
        ], start=2):
            ttk.Label(discord, text=label, width=22, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            ttk.Entry(discord, textvariable=var, show=show).grid(row=row_index, column=1, columnspan=2, sticky="ew", padx=8, pady=3)
        ttk.Button(discord, text="Save And Start Monitor", style="Accent.TButton", command=self.save_discord_settings_and_start).grid(row=6, column=0, sticky="w", pady=(5, 0))
        ttk.Label(discord, text=command_note, style="Panel.TLabel", wraplength=520).grid(row=6, column=1, columnspan=2, sticky="w", padx=8, pady=(5, 0))
        discord.columnconfigure(1, weight=1)

    def build_windrose_config_form(self, parent):
        self.windrose_config_form = ttk.Frame(parent, style="Panel.TFrame", padding=10)
        self.windrose_config_form.pack(fill="both", expand=True)
        ttk.Label(self.windrose_config_form, text="WINDROSE SERVER CONFIGURATION", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(self.windrose_config_form, text="Load ServerDescription.json to generate editable fields for top-level values. Nested/unknown JSON remains available in Raw JSON.", style="Panel.TLabel", wraplength=500).pack(anchor="w", pady=(4, 10))
        self.windrose_config_form_body = ttk.Frame(self.windrose_config_form, style="Panel.TFrame")
        self.windrose_config_form_body.pack(fill="both", expand=True)
        actions = ttk.Frame(self.windrose_config_form, style="Panel.TFrame")
        actions.pack(anchor="w", pady=(10, 0))
        ttk.Button(actions, text="Load Config Into Form", command=self.load_windrose_config_form).pack(side="left")
        ttk.Button(actions, text="Save Form Config", style="Accent.TButton", command=self.save_windrose_config_form).pack(side="left", padx=8)

    def refresh_windrose_config_form(self, text=None, silent=False):
        if text is None:
            config_path = self.path("windrose_server_config_path")
            if not config_path.exists():
                if not silent:
                    messagebox.showerror(APP_NAME, f"Windrose config file not found:\n{config_path}")
                return
            try:
                text = config_path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                if not silent:
                    messagebox.showerror(APP_NAME, f"Could not load Windrose config:\n{exc}")
                return
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            if not silent:
                messagebox.showerror(APP_NAME, f"Windrose config is not valid JSON:\n{exc}")
            return
        for child in self.windrose_config_form_body.winfo_children():
            child.destroy()
        self.windrose_config_form_vars = {}
        self.windrose_config_form_types = {}
        row = 0
        if not isinstance(data, dict):
            ttk.Label(self.windrose_config_form_body, text="The JSON root is not an object. Use Raw JSON to edit it.", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
            return
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                continue
            ttk.Label(self.windrose_config_form_body, text=str(key), width=32, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=3)
            var = tk.StringVar(value="" if value is None else str(value))
            self.windrose_config_form_vars[str(key)] = var
            self.windrose_config_form_types[str(key)] = type(value)
            ttk.Entry(self.windrose_config_form_body, textvariable=var).grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3)
            row += 1
        self.windrose_config_form_body.columnconfigure(1, weight=1)
        if row == 0:
            ttk.Label(self.windrose_config_form_body, text="No top-level primitive settings were found. Use Raw JSON.", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        if not silent:
            self.log("Loaded Windrose config form.")

    def load_windrose_config_form(self):
        self.sync_windrose_path_vars()
        config_path = self.path("windrose_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Windrose config file not found:\n{config_path}")
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not load Windrose config:\n{exc}")
            return
        self.windrose_config_text.configure(state="normal")
        self.windrose_config_text.delete("1.0", "end")
        self.windrose_config_text.insert("1.0", text)
        self.windrose_config_text.edit_reset()
        self.refresh_windrose_config_form(text)

    def save_windrose_config_form(self):
        self.sync_windrose_path_vars()
        if self.is_windrose_running():
            messagebox.showwarning(APP_NAME, "Stop the Windrose server before editing ServerDescription.json.")
            return
        config_path = self.path("windrose_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Windrose config file not found:\n{config_path}")
            return
        try:
            data = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
            if not isinstance(data, dict):
                raise ValueError("JSON root is not an object")
            for key, var in self.windrose_config_form_vars.items():
                original_type = self.windrose_config_form_types.get(key, str)
                value = var.get()
                if original_type is bool:
                    value = value.strip().lower() in {"true", "1", "yes", "on"}
                elif original_type is int:
                    value = int(value)
                elif original_type is float:
                    value = float(value)
                elif original_type is type(None):
                    value = None if not value.strip() else value
                data[key] = value
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            text = json.dumps(data, indent=2)
            config_path.write_text(text, encoding="utf-8")
            self.windrose_config_text.configure(state="normal")
            self.windrose_config_text.delete("1.0", "end")
            self.windrose_config_text.insert("1.0", text)
            self.refresh_windrose_config_form(text, silent=True)
            self.log(f"Saved Windrose config form: {config_path}")
            messagebox.showinfo(APP_NAME, f"Windrose config saved.\nBackup created:\n{backup_path}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_NAME, f"Windrose config form save failed:\n{exc}")

    def build_palworld_tab(self):
        self.palworld_view_notebook = ttk.Notebook(self.palworld_tab)
        self.palworld_view_notebook.pack(fill="both", expand=True)
        self.palworld_server_tab = ttk.Frame(self.palworld_view_notebook, padding=14)
        self.palworld_config_tab = ttk.Frame(self.palworld_view_notebook, padding=14)
        self.palworld_mods_tab = ttk.Frame(self.palworld_view_notebook, padding=14)
        self.palworld_settings_tab = ttk.Frame(self.palworld_view_notebook, padding=14)
        self.palworld_view_notebook.add(self.palworld_server_tab, text="Server")
        self.palworld_view_notebook.add(self.palworld_config_tab, text="Config")
        self.palworld_view_notebook.add(self.palworld_mods_tab, text="Mods")
        self.palworld_view_notebook.add(self.palworld_settings_tab, text="Settings")
        self.build_palworld_server_tab()
        self.build_palworld_config_tab()
        self.build_game_mods_tab(self.palworld_mods_tab, "Palworld", "palworld_server_install_path")
        self.build_palworld_settings_tab()

    def build_palworld_server_tab(self):
        top = ttk.Frame(self.palworld_server_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Palworld Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Palworld Status And Backups")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        for key, label in [
            ("status", "Server status"),
            ("detected_process", "Detected process"),
            ("update_status", "Server update"),
            ("install_path", "Install path"),
            ("save_folder_path", "Save folder"),
            ("backup_folder_path", "Backup folder"),
            ("config_path", "Config file"),
            ("backup_count", "Backups stored"),
            ("last_backup", "Last backup"),
        ]:
            self.palworld_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(left if key == "status" else right, style="Panel.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            label_widget = ttk.Label(row, textvariable=self.palworld_vars[key], style="Panel.TLabel", wraplength=430)
            label_widget.pack(side="left", fill="x", expand=True)
            if key == "status":
                self.palworld_status_label = label_widget

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 12))
        self.palworld_start_button = ttk.Button(buttons, text="Start Palworld", command=self.start_palworld_server)
        self.palworld_start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.palworld_stop_button = ttk.Button(buttons, text="Stop Palworld", command=self.stop_palworld_server)
        self.palworld_stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Palworld", command=self.restart_palworld_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Palworld", style="Accent.TButton", command=self.backup_palworld_now).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Save World", command=self.save_palworld_world).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Update", command=lambda: self.check_palworld_update(show_dialog=True)).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        self.palworld_update_button = ttk.Button(buttons, text="Update Palworld", command=self.update_palworld_server_with_steamcmd)
        self.palworld_update_button.grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install", command=lambda: self.open_path(self.path("palworld_server_install_path"))).grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Save", command=lambda: self.open_path(self.path("palworld_save_folder_path"))).grid(row=2, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Backups", command=lambda: self.open_path(self.path("palworld_backup_folder_path"))).grid(row=3, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Install Palworld Server", style="Green.TButton", command=self.install_palworld_server_with_steamcmd).grid(row=3, column=1, columnspan=2, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        ttk.Label(
            left,
            text="Palworld does not start automatically when this manager opens. Crash restart is opt-in and only applies after you start Palworld from this tab or it was already running when the manager opened.",
            style="Panel.TLabel",
            wraplength=520,
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(left, text="Use Config for PalworldSettings.ini and Settings for paths, REST, Discord, and crash restart.", style="Panel.TLabel", wraplength=520).pack(anchor="w", pady=(4, 0))

    def build_palworld_config_tab(self):
        config_page = self.palworld_config_tab
        config_header = ttk.Frame(config_page, style="Panel.TFrame")
        config_header.pack(fill="x", pady=(0, 10))
        ttk.Label(config_header, text="Edit Palworld server settings while the server is stopped.", style="Panel.TLabel").pack(side="left")
        ttk.Button(config_header, text="Apply Creative Preset", style="Accent.TButton", command=self.apply_palworld_kid_friendly_preset).pack(side="right")

        self.palworld_config_notebook = ttk.Notebook(config_page)
        self.palworld_config_notebook.pack(fill="both", expand=True)
        form_page = ttk.Frame(self.palworld_config_notebook, padding=8)
        raw_page = ttk.Frame(self.palworld_config_notebook, padding=8)
        self.palworld_config_notebook.add(form_page, text="Config Form")
        self.palworld_config_notebook.add(raw_page, text="Raw INI")
        config_actions = ttk.Frame(raw_page, style="Panel.TFrame")
        config_actions.pack(fill="x", pady=(0, 8))
        ttk.Label(config_actions, text="PALWORLDSETTINGS.INI", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(config_actions, text="Load", command=self.load_palworld_config).pack(side="right")
        ttk.Button(config_actions, text="Save", style="Accent.TButton", command=self.save_palworld_config).pack(side="right", padx=8)
        ttk.Button(config_actions, text="Notepad", command=self.open_palworld_config_notepad).pack(side="right")
        self.palworld_config_text = tk.Text(raw_page, bg="#111111", fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="none", height=7, undo=True)
        self.palworld_config_text.pack(fill="both", expand=True)
        self.build_palworld_config_form(form_page)

    def build_palworld_settings_tab(self):
        container = ttk.Frame(self.palworld_settings_tab)
        container.pack(fill="both", expand=True)
        paths = ttk.Frame(container, style="Panel.TFrame", padding=14)
        paths.pack(fill="x")
        ttk.Label(paths, text="PATHS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Button(paths, text="Auto-detect Palworld", style="Accent.TButton", command=self.autodetect_palworld_paths).grid(row=0, column=2, sticky="e", pady=(0, 8))
        for row_index, (key, label, is_file) in enumerate([
            ("palworld_server_install_path", "Install folder", False),
            ("palworld_server_exe_path", "Server executable", True),
            ("palworld_server_config_path", "PalWorldSettings.ini", True),
            ("palworld_save_folder_path", "Save folder", False),
            ("palworld_backup_folder_path", "Backup folder", False),
        ]):
            grid_row = row_index + 1
            ttk.Label(paths, text=label, width=22, style="Panel.TLabel").grid(row=grid_row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(self.settings.get(key, "")))
            self.palworld_path_vars[key] = var
            self.path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=grid_row, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(paths, text="Browse", command=lambda k=key, f=is_file: self.browse_path(k, f)).grid(row=grid_row, column=2, pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Button(paths, text="Save Palworld Settings", style="Accent.TButton", command=self.save_palworld_settings_and_start_discord).grid(row=6, column=0, sticky="w", pady=(8, 0))

        rest = ttk.Frame(container, style="Panel.TFrame", padding=14)
        rest.pack(fill="x", pady=(14, 0))
        ttk.Label(rest, text="REST API", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        self.palworld_rest_url_var = tk.StringVar(value=str(self.settings.get("palworld_rest_base_url", "")))
        self.palworld_rest_user_var = tk.StringVar(value=str(self.settings.get("palworld_rest_username", "admin")))
        self.palworld_rest_password_var = tk.StringVar(value=str(self.settings.get("palworld_admin_password", "")))
        for row_index, (label, var, show) in enumerate([
            ("Base URL", self.palworld_rest_url_var, None),
            ("Username", self.palworld_rest_user_var, None),
            ("Admin password", self.palworld_rest_password_var, "*"),
        ], start=1):
            ttk.Label(rest, text=label, width=22, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            ttk.Entry(rest, textvariable=var, show=show).grid(row=row_index, column=1, columnspan=2, sticky="ew", padx=8, pady=3)
        ttk.Button(rest, text="Test REST", command=self.test_palworld_rest_api).grid(row=4, column=0, sticky="w", pady=(5, 0))
        ttk.Label(rest, text="Enable RESTAPIEnabled=True in PalWorldSettings.ini. Keep this API on localhost/LAN.", style="Panel.TLabel", wraplength=420).grid(row=4, column=1, columnspan=2, sticky="w", padx=8, pady=(5, 0))
        rest.columnconfigure(1, weight=1)

        self.build_discord_panel(
            container,
            "Discord Monitor",
            "Commands: !palworld status, restart, start, stop, backup, save, help; !windrose status, restart, start, stop, backup, help; !abiotic status, restart, start, stop, backup, settings, preset qol, restore latest, help; !minecraft status, start, stop, restart, backup, help.",
        )

        watchdog = self.panel(container, "Palworld Server Behavior")
        watchdog.pack(fill="x", pady=(14, 0))
        self.palworld_auto_restart_var = tk.BooleanVar(value=bool(self.settings.get("palworld_auto_restart_server")))
        ttk.Checkbutton(watchdog, text="Auto-restart Palworld if it crashes", variable=self.palworld_auto_restart_var).pack(anchor="w")
        ttk.Label(watchdog, text="This never starts Palworld on app launch. Save the setting below after choosing it.", style="Panel.TLabel", wraplength=900).pack(anchor="w", pady=(4, 0))

        note = self.panel(container, "Kid-Friendly Preset")
        note.pack(fill="x", pady=(14, 0))
        ttk.Label(note, text="The creative preset is available on the Config tab. It backs up PalWorldSettings.ini before changing the supported values.", style="Panel.TLabel", wraplength=900).pack(anchor="w")

    def open_palworld_config_view(self):
        self.palworld_view_notebook.select(1)
        self.palworld_config_notebook.select(0)
        self.load_palworld_config_form(silent=True)

    def build_palworld_config_form(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        form = ttk.Frame(canvas, style="Panel.TFrame", padding=10)
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def resize_form(event):
            canvas.itemconfigure(form_window, width=event.width)

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_form)
        form.bind("<Configure>", update_scroll_region)

        ttk.Label(form, text="PALWORLD SERVER CONFIGURATION", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(form, text="These fields update the OptionSettings block and preserve unknown settings. Stop the server before saving.", style="Panel.TLabel", wraplength=520).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row_index, (key, label, kind) in enumerate(PALWORLD_CONFIG_FIELDS, start=2):
            ttk.Label(form, text=label, width=34, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            self.palworld_config_vars[key] = var
            if kind == "bool":
                widget = ttk.Combobox(form, textvariable=var, values=("True", "False"), state="readonly", width=18)
            elif kind.startswith("choice:"):
                choices = tuple(kind.removeprefix("choice:").split("|"))
                widget = ttk.Combobox(form, textvariable=var, values=choices, state="readonly", width=24)
            else:
                show = "*" if key in {"ServerPassword", "AdminPassword"} else None
                widget = ttk.Entry(form, textvariable=var, show=show)
            widget.grid(row=row_index, column=1, sticky="ew", padx=(8, 0), pady=3)
        form.columnconfigure(1, weight=1)

        actions = ttk.Frame(form, style="Panel.TFrame")
        actions.grid(row=len(PALWORLD_CONFIG_FIELDS) + 2, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Load Config Into Form", command=self.load_palworld_config_form).pack(side="left")
        ttk.Button(actions, text="Save Form Config", style="Accent.TButton", command=self.save_palworld_config_form).pack(side="left", padx=8)
        ttk.Button(actions, text="Apply Creative Preset", command=self.apply_palworld_kid_friendly_preset).pack(side="left")
        self.after_idle(lambda: self.load_palworld_config_form(silent=True))

    def build_valheim_tab(self):
        self.valheim_notebook = ttk.Notebook(self.valheim_tab)
        self.valheim_notebook.pack(fill="both", expand=True)
        self.valheim_server_tab = ttk.Frame(self.valheim_notebook, padding=14)
        self.valheim_config_tab = ttk.Frame(self.valheim_notebook, padding=14)
        self.valheim_mods_tab = ttk.Frame(self.valheim_notebook, padding=14)
        self.valheim_settings_tab = ttk.Frame(self.valheim_notebook, padding=14)
        self.valheim_notebook.add(self.valheim_server_tab, text="Server")
        self.valheim_notebook.add(self.valheim_config_tab, text="Config")
        self.valheim_notebook.add(self.valheim_mods_tab, text="Mods")
        self.valheim_notebook.add(self.valheim_settings_tab, text="Settings")
        self.build_valheim_server_tab()
        self.build_valheim_config_tab()
        self.build_game_mods_tab(self.valheim_mods_tab, "Valheim", "valheim_server_install_path")
        self.build_valheim_settings_tab()

    def build_valheim_server_tab(self):
        top = ttk.Frame(self.valheim_server_tab)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Valheim Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Valheim Status And Backups")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        for key, label in [
            ("status", "Server status"),
            ("detected_process", "Detected process"),
            ("update_status", "Server update"),
            ("install_path", "Install path"),
            ("launcher_path", "Launcher batch"),
            ("save_folder_path", "Save folder"),
            ("backup_folder_path", "Backup folder"),
            ("backup_count", "Backups stored"),
            ("last_backup", "Last backup"),
        ]:
            self.valheim_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(left if key == "status" else right, style="Panel.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            label_widget = ttk.Label(row, textvariable=self.valheim_vars[key], style="Panel.TLabel", wraplength=430)
            label_widget.pack(side="left", fill="x", expand=True)
            if key == "status":
                self.valheim_status_label = label_widget

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 12))
        self.valheim_start_button = ttk.Button(buttons, text="Start Valheim", command=self.start_valheim_server)
        self.valheim_start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.valheim_stop_button = ttk.Button(buttons, text="Stop Valheim", command=self.stop_valheim_server)
        self.valheim_stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Valheim", command=self.restart_valheim_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Valheim", style="Accent.TButton", command=self.backup_valheim_now).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Update", command=lambda: self.check_valheim_update(show_dialog=True)).grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.valheim_update_button = ttk.Button(buttons, text="Update Valheim", command=self.update_valheim_server_with_steamcmd)
        self.valheim_update_button.grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install", command=lambda: self.open_path(self.path("valheim_server_install_path"))).grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Save", command=lambda: self.open_path(self.path("valheim_save_folder_path"))).grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Backups", command=lambda: self.open_path(self.path("valheim_backup_folder_path"))).grid(row=2, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Install Valheim Server", style="Green.TButton", command=self.install_valheim_server_with_steamcmd).grid(row=3, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        ttk.Label(left, text="Use Config for start_headless_server.bat and Settings for paths and crash restart.", style="Panel.TLabel", wraplength=520).pack(anchor="w", pady=(0, 8))

    def build_valheim_config_tab(self):
        config_page = self.valheim_config_tab
        config_header = ttk.Frame(config_page, style="Panel.TFrame")
        config_header.pack(fill="x", pady=(0, 10))
        ttk.Label(config_header, text="Valheim's official Windows setup stores server settings in start_headless_server.bat.", style="Panel.TLabel").pack(side="left")
        self.valheim_config_notebook = ttk.Notebook(config_page)
        self.valheim_config_notebook.pack(fill="both", expand=True)
        form_page = ttk.Frame(self.valheim_config_notebook, padding=8)
        raw_page = ttk.Frame(self.valheim_config_notebook, padding=8)
        self.valheim_config_notebook.add(form_page, text="Config Form")
        self.valheim_config_notebook.add(raw_page, text="Raw BAT")
        self.build_valheim_config_form(form_page)
        config_actions = ttk.Frame(raw_page, style="Panel.TFrame")
        config_actions.pack(fill="x", pady=(0, 8))
        ttk.Label(config_actions, text="START_HEADLESS_SERVER.BAT", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).pack(side="left")
        ttk.Button(config_actions, text="Load", command=self.load_valheim_config).pack(side="right")
        ttk.Button(config_actions, text="Save", style="Accent.TButton", command=self.save_valheim_config).pack(side="right", padx=8)
        ttk.Button(config_actions, text="Notepad", command=self.open_valheim_config_notepad).pack(side="right")
        self.valheim_config_text = tk.Text(raw_page, bg="#111111", fg=COLORS["text"], insertbackground=COLORS["text"], relief="flat", wrap="none", height=7, undo=True)
        self.valheim_config_text.pack(fill="both", expand=True)

    def build_valheim_settings_tab(self):
        container = ttk.Frame(self.valheim_settings_tab)
        container.pack(fill="both", expand=True)
        paths = ttk.Frame(container, style="Panel.TFrame", padding=14)
        paths.pack(fill="x")
        ttk.Label(paths, text="PATHS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        ttk.Button(paths, text="Auto-detect Valheim", style="Accent.TButton", command=self.autodetect_valheim_paths).grid(row=0, column=2, sticky="e", pady=(0, 8))
        for row_index, (key, label, is_file) in enumerate([
            ("valheim_server_install_path", "Install folder", False),
            ("valheim_server_exe_path", "Server executable", True),
            ("valheim_server_bat_path", "Launcher batch file", True),
            ("valheim_save_folder_path", "Save folder", False),
            ("valheim_backup_folder_path", "Backup folder", False),
        ]):
            grid_row = row_index + 1
            ttk.Label(paths, text=label, width=22, style="Panel.TLabel").grid(row=grid_row, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(self.settings.get(key, "")))
            self.valheim_path_vars[key] = var
            self.path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=grid_row, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(paths, text="Browse", command=lambda k=key, f=is_file: self.browse_path(k, f)).grid(row=grid_row, column=2, pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Button(paths, text="Save Valheim Settings", style="Accent.TButton", command=self.save_valheim_settings).grid(row=6, column=0, sticky="w", pady=(8, 0))

        behavior = self.panel(container, "Valheim Server Behavior")
        behavior.pack(fill="x", pady=(14, 0))
        self.valheim_auto_restart_var = tk.BooleanVar(value=bool(self.settings.get("valheim_auto_restart_server")))
        ttk.Checkbutton(behavior, text="Auto-restart Valheim if it crashes", variable=self.valheim_auto_restart_var).pack(anchor="w")
        ttk.Label(behavior, text="Valheim never starts automatically when the manager opens. Save the setting below after choosing it.", style="Panel.TLabel", wraplength=900).pack(anchor="w", pady=(4, 0))

    def build_abiotic_tab(self):
        self.abiotic_view_notebook = ttk.Notebook(self.abiotic_tab)
        self.abiotic_view_notebook.pack(fill="both", expand=True)
        server_page = ttk.Frame(self.abiotic_view_notebook, padding=14)
        settings_page = ttk.Frame(self.abiotic_view_notebook, padding=14)
        guide_page = ttk.Frame(self.abiotic_view_notebook, padding=14)
        self.abiotic_view_notebook.add(server_page, text="Server")
        self.abiotic_view_notebook.add(settings_page, text="Sandbox Settings")
        self.abiotic_view_notebook.add(guide_page, text="Guide")
        top = ttk.Frame(server_page)
        top.pack(fill="both", expand=True)
        left = self.panel(top, "Abiotic Factor Dedicated Server")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self.panel(top, "Abiotic Factor Status")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        for key, label in [
            ("status", "Server status"),
            ("detected_process", "Detected process"),
            ("update_status", "Server update"),
            ("install_path", "Install path"),
            ("executable_path", "Server executable"),
            ("config_path", "Config folder"),
            ("save_folder_path", "World saves"),
            ("backup_folder_path", "Backup folder"),
            ("backup_count", "Backups stored"),
            ("last_backup", "Last backup"),
        ]:
            self.abiotic_vars[key] = tk.StringVar(value="-")
            row = ttk.Frame(left if key == "status" else right, style="Panel.TFrame")
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=18, style="Panel.TLabel").pack(side="left")
            label_widget = ttk.Label(row, textvariable=self.abiotic_vars[key], style="Panel.TLabel", wraplength=430)
            label_widget.pack(side="left", fill="x", expand=True)
            if key == "status":
                self.abiotic_status_label = label_widget

        buttons = ttk.Frame(left, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 12))
        self.abiotic_start_button = ttk.Button(buttons, text="Start Abiotic Factor", command=self.start_abiotic_server)
        self.abiotic_start_button.grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        self.abiotic_stop_button = ttk.Button(buttons, text="Stop Abiotic Factor", command=self.stop_abiotic_server)
        self.abiotic_stop_button.grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Restart Abiotic Factor", command=self.restart_abiotic_server).grid(row=0, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Check Update", command=lambda: self.check_abiotic_update(show_dialog=True)).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        self.abiotic_update_button = ttk.Button(buttons, text="Update Abiotic Factor", command=self.update_abiotic_server_with_steamcmd)
        self.abiotic_update_button.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Install", command=lambda: self.open_path(self.path("abiotic_server_install_path"))).grid(row=1, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Backup Abiotic Factor", style="Accent.TButton", command=self.backup_abiotic_now).grid(row=2, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Saves", command=lambda: self.open_path(self.path("abiotic_save_folder_path"))).grid(row=2, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Backups", command=lambda: self.open_path(self.path("abiotic_backup_folder_path"))).grid(row=2, column=2, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Install Abiotic Factor Server", style="Green.TButton", command=self.install_abiotic_server_with_steamcmd).grid(row=3, column=0, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Logs", command=lambda: self.open_path(self.path("abiotic_server_install_path") / "AbioticFactor" / "Saved" / "Logs")).grid(row=3, column=1, padx=4, pady=4, sticky="ew")
        ttk.Button(buttons, text="Open Sandbox Settings", command=lambda: self.open_path(self.path("abiotic_sandbox_settings_path").parent)).grid(row=3, column=2, padx=4, pady=4, sticky="ew")
        for i in range(3):
            buttons.columnconfigure(i, weight=1)

        ttk.Label(left, text="SteamCMD app 2857200. Abiotic Factor reuses Palworld's current ports: game 9876 and query 25575. Only run one of the two servers at a time.", style="Panel.TLabel", wraplength=520).pack(anchor="w", pady=(0, 8))

        paths = ttk.Frame(server_page, style="Panel.TFrame", padding=14)
        paths.pack(fill="x", pady=(14, 0))
        ttk.Label(paths, text="PATHS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        for row_index, (key, label, is_file) in enumerate([
            ("abiotic_server_install_path", "Install folder", False),
            ("abiotic_server_exe_path", "Server executable", True),
            ("abiotic_server_config_path", "Config folder", False),
            ("abiotic_sandbox_settings_path", "Sandbox settings file", True),
            ("abiotic_save_folder_path", "World saves", False),
            ("abiotic_backup_folder_path", "Backup folder", False),
            ("abiotic_server_port", "Game port", False),
            ("abiotic_query_port", "Query port", False),
        ], start=1):
            ttk.Label(paths, text=label, width=22, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=str(self.settings.get(key, "")))
            self.abiotic_path_vars[key] = var
            self.path_vars[key] = var
            ttk.Entry(paths, textvariable=var).grid(row=row_index, column=1, sticky="ew", padx=8, pady=4)
            ttk.Button(paths, text="Browse", command=lambda k=key, f=is_file: self.browse_path(k, f)).grid(row=row_index, column=2, pady=4)
        paths.columnconfigure(1, weight=1)
        ttk.Button(paths, text="Save Abiotic Factor Settings", style="Accent.TButton", command=self.save_abiotic_settings).grid(row=9, column=0, sticky="w", pady=(8, 0))

        behavior = self.panel(server_page, "Abiotic Factor Server Behavior")
        behavior.pack(fill="x", pady=(14, 0))
        self.abiotic_auto_restart_var = tk.BooleanVar(value=bool(self.settings.get("abiotic_auto_restart_server")))
        ttk.Checkbutton(behavior, text="Auto-restart Abiotic Factor if it crashes", variable=self.abiotic_auto_restart_var).pack(anchor="w")
        self.abiotic_backup_before_restart_var = tk.BooleanVar(value=bool(self.settings.get("abiotic_backup_before_restart", True)))
        ttk.Checkbutton(behavior, text="Back up the world before a managed restart", variable=self.abiotic_backup_before_restart_var).pack(anchor="w", pady=(4, 0))
        ttk.Label(behavior, text="This only restarts a server that the manager believes should be running. Clicking Stop disables that expectation.", style="Panel.TLabel", wraplength=900).pack(anchor="w", pady=(4, 0))

        self.build_abiotic_sandbox_editor(settings_page)
        self.build_abiotic_guide(guide_page)

    def build_abiotic_sandbox_editor(self, parent):
        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(0, 8))
        ttk.Button(actions, text="Load From Disk", command=self.load_abiotic_sandbox_settings).pack(side="left")
        ttk.Button(actions, text="Save Settings", style="Accent.TButton", command=self.save_abiotic_sandbox_settings).pack(side="left", padx=8)
        ttk.Button(actions, text="Apply QoL Preset", style="Green.TButton", command=self.apply_abiotic_qol_preset).pack(side="left")
        ttk.Button(actions, text="Show Vanilla Defaults", command=self.load_abiotic_sandbox_defaults).pack(side="left", padx=8)
        ttk.Button(actions, text="Open Raw File", command=self.open_abiotic_sandbox_notepad).pack(side="left")
        self.abiotic_sandbox_status_var = tk.StringVar(value="Load the sandbox settings before editing.")
        ttk.Label(parent, textvariable=self.abiotic_sandbox_status_var, style="Panel.TLabel", wraplength=900).pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(parent, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        form = ttk.Frame(canvas, style="Panel.TFrame", padding=10)
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def resize_form(event):
            canvas.itemconfigure(form_window, width=event.width)

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_form)
        form.bind("<Configure>", update_scroll_region)

        grouped = {}
        for key, label, kind, group in ABIOTIC_SANDBOX_FIELDS:
            grouped.setdefault(group, []).append((key, label, kind))
        row = 0
        for group, fields in grouped.items():
            ttk.Label(form, text=group.upper(), style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(8 if row else 0, 5))
            row += 1
            for key, label, kind in fields:
                ttk.Label(form, text=label, width=36, style="Panel.TLabel").grid(row=row, column=0, sticky="w", pady=3)
                var = tk.StringVar(value=ABIOTIC_SANDBOX_DEFAULTS.get(key, ""))
                self.abiotic_sandbox_vars[key] = var
                self.abiotic_sandbox_kinds[key] = kind
                if kind == "bool":
                    ttk.Checkbutton(form, variable=var, onvalue="True", offvalue="False").grid(row=row, column=1, sticky="w", pady=3)
                else:
                    ttk.Entry(form, textvariable=var).grid(row=row, column=1, sticky="ew", pady=3, padx=(8, 0))
                row += 1
        form.columnconfigure(1, weight=1)
        self.after(250, self.load_abiotic_sandbox_settings)

    def build_abiotic_guide(self, parent):
        guide = self.panel(parent, "Early Abiotic Factor Help")
        guide.pack(fill="x", pady=(0, 12))
        ttk.Label(
            guide,
            text="Anvil: in the starting Office Sector cafeteria storage area, take the third vent, wait until the power shuts down around 9 PM, then crawl through to the storeroom shelf.\n\n"
                 "Crafting from storage: build the Crafting Bench Item Transporter upgrade, then keep storage crates within its range. This is an in-game progression upgrade, not a SandboxSettings option.\n\n"
                 "Manager safety: saving a setting, applying the QoL preset, restoring a backup, and updating the server all require the server to be stopped and create a backup first.",
            style="Panel.TLabel",
            wraplength=900,
            justify="left",
        ).pack(anchor="w")

    def read_abiotic_sandbox_settings(self):
        values = ABIOTIC_SANDBOX_DEFAULTS.copy()
        path = self.path("abiotic_sandbox_settings_path")
        if not path.exists():
            return values
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self.log(f"Abiotic Factor sandbox settings read failed: {exc}")
            return values
        known = set(values)
        for line in text.splitlines():
            match = re.match(r"^\s*([^#;=]+?)\s*=\s*(.*?)\s*$", line)
            if not match:
                continue
            key, value = match.group(1).strip(), match.group(2).strip()
            if key in known:
                values[key] = value.title() if value.lower() in {"true", "false"} else value
        return values

    def abiotic_discord_settings_summary(self):
        values = self.read_abiotic_sandbox_settings()
        return (
            "Abiotic Factor QoL settings: "
            f"inventory {values.get('BaseInventorySize')}, "
            f"stacks {values.get('ItemStackSizeMultiplier')}x, "
            f"weight {values.get('ItemWeightMultiplier')}x, "
            f"friendly fire {values.get('DamageToAlliesMultiplier')}x, "
            f"death penalties {values.get('DeathPenalties')}, "
            f"food spoil {values.get('FoodSpoilSpeedMultiplier')}x, "
            f"sink refill {values.get('SinkRefillRate')}x, "
            f"storage by tag {values.get('StorageByTag')}."
        )

    def load_abiotic_sandbox_settings(self, silent=False):
        values = self.read_abiotic_sandbox_settings()
        for key, var in self.abiotic_sandbox_vars.items():
            var.set(str(values.get(key, ABIOTIC_SANDBOX_DEFAULTS.get(key, ""))))
        path = self.path("abiotic_sandbox_settings_path")
        if self.abiotic_sandbox_status_var:
            self.abiotic_sandbox_status_var.set(f"Loaded {path}" if path.exists() else f"Using defaults; file not found: {path}")
        if not silent:
            self.log(f"Loaded Abiotic Factor sandbox settings: {path}")

    def load_abiotic_sandbox_defaults(self):
        for key, var in self.abiotic_sandbox_vars.items():
            var.set(ABIOTIC_SANDBOX_DEFAULTS.get(key, ""))
        if self.abiotic_sandbox_status_var:
            self.abiotic_sandbox_status_var.set("Vanilla defaults loaded into the form. Click Save Settings to write them.")

    def validate_abiotic_sandbox_values(self, values):
        integer_keys = {"GameDifficulty", "DayNightCycleState", "WeatherFrequency", "StructuralSupportLimit", "BridgeSupports", "EnemyAccuracy", "BonusPerkPoints", "DeathPenalties", "FirstTimeStartingWeapon", "BaseInventorySize"}
        for key, value in values.items():
            kind = self.abiotic_sandbox_kinds.get(key, "number")
            if kind == "bool":
                if value not in {"True", "False"}:
                    return f"{key} must be True or False."
                continue
            try:
                number = float(value)
            except ValueError:
                return f"{key} must be numeric."
            if key in integer_keys and not number.is_integer():
                return f"{key} must be a whole number."
            if key == "BaseInventorySize" and not 0 <= number <= 42:
                return "BaseInventorySize must be between 0 and 42."
            if key == "ItemStackSizeMultiplier" and not 0 <= number <= 30:
                return "ItemStackSizeMultiplier must be between 0 and 30."
            if key == "BridgeSupports" and not 0 <= number <= 2:
                return "BridgeSupports must be between 0 and 2."
            if key == "SinkRefillRate" and not 0 <= number <= 10:
                return "SinkRefillRate must be between 0 and 10."
        return ""

    def write_abiotic_sandbox_settings(self, values):
        path = self.path("abiotic_sandbox_settings_path")
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            original_lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        else:
            original_lines = ["[SandboxSettings]\n"]
        known = set(values)
        written = set()
        output = []
        for line in original_lines:
            match = re.match(r"^(\s*)([^#;=]+?)(\s*=\s*)(.*?)(\r?\n)?$", line)
            if match and match.group(2).strip() in known:
                key = match.group(2).strip()
                newline = match.group(5) or "\n"
                output.append(f"{match.group(1)}{key}={values[key]}{newline}")
                written.add(key)
            else:
                output.append(line)
        if output and not output[-1].endswith(("\n", "\r")):
            output[-1] += "\n"
        missing = [key for key, _label, _kind, _group in ABIOTIC_SANDBOX_FIELDS if key not in written]
        if missing:
            if output and output[-1].strip():
                output.append("\n")
            for key in missing:
                output.append(f"{key}={values[key]}\n")
        path.write_text("".join(output), encoding="utf-8")

    def save_abiotic_sandbox_settings(self, show_dialog=True):
        if self.is_abiotic_running():
            message = "Stop the Abiotic Factor server before saving sandbox settings."
            if show_dialog:
                messagebox.showwarning(APP_NAME, message)
            self.log("Abiotic Factor sandbox settings save refused: server is running.")
            return False
        values = {key: var.get().strip() for key, var in self.abiotic_sandbox_vars.items()}
        error = self.validate_abiotic_sandbox_values(values)
        if error:
            if show_dialog:
                messagebox.showerror(APP_NAME, error)
            self.log(f"Abiotic Factor sandbox settings validation failed: {error}")
            return False
        backup = self.create_abiotic_backup(prefix_override="before_abiotic_settings_", show_missing_error=show_dialog)
        if backup is None:
            self.log("Abiotic Factor sandbox settings save aborted: backup was not created.")
            return False
        try:
            self.write_abiotic_sandbox_settings(values)
            self.settings["abiotic_last_preset"] = "custom"
            write_json(SETTINGS_FILE, self.settings)
            self.load_abiotic_sandbox_settings(silent=True)
            self.log(f"Saved Abiotic Factor sandbox settings: {self.path('abiotic_sandbox_settings_path')}")
            if show_dialog:
                messagebox.showinfo(APP_NAME, f"Abiotic Factor sandbox settings saved.\n\nBackup created:\n{backup}\n\nThe server must be started again to load the changes.")
            return True
        except OSError as exc:
            self.log(f"Abiotic Factor sandbox settings save failed: {exc}")
            if show_dialog:
                messagebox.showerror(APP_NAME, f"Could not save Abiotic Factor sandbox settings:\n{exc}")
            return False

    def apply_abiotic_qol_preset(self, show_dialog=True):
        if show_dialog and not messagebox.askyesno(APP_NAME, "Apply the Abiotic Factor QoL preset?\n\nThis changes the selected sandbox settings and creates a backup first."):
            return False
        if self.is_abiotic_running():
            if show_dialog:
                messagebox.showwarning(APP_NAME, "Stop the Abiotic Factor server before applying the QoL preset.")
            self.log("Abiotic Factor QoL preset refused: server is running.")
            return False
        values = self.read_abiotic_sandbox_settings()
        values.update(ABIOTIC_QOL_PRESET)
        backup = self.create_abiotic_backup(prefix_override="before_abiotic_preset_", show_missing_error=show_dialog)
        if backup is None:
            return False
        try:
            self.write_abiotic_sandbox_settings(values)
            self.settings["abiotic_last_preset"] = "qol"
            write_json(SETTINGS_FILE, self.settings)
            self.after(0, self.load_abiotic_sandbox_settings, True)
            self.log(f"Applied Abiotic Factor QoL preset: {backup}")
            if show_dialog:
                messagebox.showinfo(APP_NAME, f"Abiotic Factor QoL preset applied.\n\nBackup created:\n{backup}\n\nRestart the server to load the changes.")
            return True
        except OSError as exc:
            self.log(f"Abiotic Factor QoL preset failed: {exc}")
            if show_dialog:
                messagebox.showerror(APP_NAME, f"Could not apply Abiotic Factor QoL preset:\n{exc}")
            return False

    def open_abiotic_sandbox_notepad(self):
        path = self.path("abiotic_sandbox_settings_path")
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("[SandboxSettings]\n", encoding="utf-8")
            subprocess.Popen(["notepad.exe", str(path)])
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open Abiotic Factor sandbox settings:\n{exc}")

    def build_valheim_config_form(self, parent):
        canvas = tk.Canvas(parent, bg=COLORS["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        form = ttk.Frame(canvas, style="Panel.TFrame", padding=10)
        form_window = canvas.create_window((0, 0), window=form, anchor="nw")

        def resize_form(event):
            canvas.itemconfigure(form_window, width=event.width)

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_form)
        form.bind("<Configure>", update_scroll_region)
        ttk.Label(form, text="VALHEIM SERVER CONFIGURATION", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(form, text="These fields edit the Valheim server command in start_headless_server.bat. Stop the server before saving.", style="Panel.TLabel", wraplength=520).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))
        for row_index, (key, label, kind) in enumerate(VALHEIM_CONFIG_FIELDS, start=2):
            ttk.Label(form, text=label, width=34, style="Panel.TLabel").grid(row=row_index, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            self.valheim_config_vars[key] = var
            if kind == "bool":
                widget = ttk.Combobox(form, textvariable=var, values=("True", "False"), state="readonly", width=18)
            elif kind.startswith("choice:"):
                widget = ttk.Combobox(form, textvariable=var, values=tuple(kind.removeprefix("choice:").split("|")), state="readonly", width=24)
            else:
                show = "*" if key == "password" else None
                widget = ttk.Entry(form, textvariable=var, show=show)
            widget.grid(row=row_index, column=1, sticky="ew", padx=(8, 0), pady=3)
        form.columnconfigure(1, weight=1)
        actions = ttk.Frame(form, style="Panel.TFrame")
        actions.grid(row=len(VALHEIM_CONFIG_FIELDS) + 2, column=0, columnspan=2, sticky="w", pady=(12, 0))
        ttk.Button(actions, text="Load Config Into Form", command=self.load_valheim_config_form).pack(side="left")
        ttk.Button(actions, text="Save Form Config", style="Accent.TButton", command=self.save_valheim_config_form).pack(side="left", padx=8)
        self.after_idle(lambda: self.load_valheim_config_form(silent=True))

    def build_ports_tab(self):
        container = self.panel(self.ports_tab, "Port Check")
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text="Configured ports, local listeners, and Windows inbound allow rules.",
            style="Panel.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        actions = ttk.Frame(container, style="Panel.TFrame")
        actions.pack(fill="x", pady=(0, 8))
        self.port_check_button = ttk.Button(actions, text="Check All Ports", style="Accent.TButton", command=self.check_all_ports)
        self.port_check_button.pack(side="left")
        ttk.Button(actions, text="Refresh Configured Ports", command=self.refresh_port_check_view).pack(side="left", padx=8)
        ttk.Button(actions, text="Apply ASKA Port Profile", command=self.apply_aska_port_profile).pack(side="left")
        self.port_check_status_var = tk.StringVar(value="Not checked")
        ttk.Label(actions, textvariable=self.port_check_status_var, style="Panel.TLabel").pack(side="left", padx=8)

        ttk.Label(
            container,
            text="Windrose uses a P2P proxy. Minecraft uses its standard TCP port 25565; the other servers retain their configured native ports.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(0, 10))

        table_frame = ttk.Frame(container, style="Panel.TFrame")
        table_frame.pack(fill="both", expand=True)
        columns = ("server", "purpose", "protocol", "port", "listener", "firewall")
        self.port_check_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        headings = {
            "server": "Server",
            "purpose": "Purpose",
            "protocol": "Protocol",
            "port": "Port",
            "listener": "Local listener",
            "firewall": "Inbound firewall",
        }
        widths = {"server": 110, "purpose": 180, "protocol": 90, "port": 100, "listener": 220, "firewall": 220}
        for column in columns:
            self.port_check_tree.heading(column, text=headings[column])
            self.port_check_tree.column(column, width=widths[column], anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.port_check_tree.yview)
        self.port_check_tree.configure(yscrollcommand=scrollbar.set)
        self.port_check_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.after(300, self.refresh_port_check_view)

    def apply_aska_port_profile(self):
        running = []
        if self.is_server_running():
            running.append("ASKA")
        if self.is_windrose_running():
            running.append("Windrose")
        if self.is_palworld_running():
            running.append("Palworld")
        if self.is_valheim_running():
            running.append("Valheim")
        if running:
            messagebox.showwarning(APP_NAME, "Stop these servers before applying shared ports:\n" + ", ".join(running))
            return

        palworld_path = self.path("palworld_server_config_path")
        valheim_path = self.path("valheim_server_bat_path")
        palworld_text = self.read_port_source(palworld_path)
        valheim_text = self.read_port_source(valheim_path)
        valheim_line = self.valheim_command_line(valheim_text)
        if "OptionSettings=(" not in palworld_text:
            messagebox.showerror(APP_NAME, f"Palworld OptionSettings block not found:\n{palworld_path}")
            return
        if not valheim_line:
            messagebox.showerror(APP_NAME, f"Valheim server command not found:\n{valheim_path}")
            return

        try:
            palworld_backup = palworld_path.with_name(f"{palworld_path.stem}.before_shared_ports_{now_stamp()}{palworld_path.suffix}")
            valheim_backup = valheim_path.with_name(f"{valheim_path.stem}.before_shared_ports_{now_stamp()}{valheim_path.suffix}")
            shutil.copy2(palworld_path, palworld_backup)
            shutil.copy2(valheim_path, valheim_backup)
            palworld_text = self.replace_palworld_setting(palworld_text, "PublicPort", "27015")
            palworld_text = self.replace_palworld_setting(palworld_text, "RESTAPIPort", "27016")
            palworld_path.write_text(palworld_text, encoding="utf-8")
            new_valheim_line = self.set_valheim_arg(valheim_line, "port", "27015", "number")
            valheim_text = valheim_text.replace(valheim_line, new_valheim_line, 1)
            valheim_path.write_text(valheim_text, encoding="utf-8")
            self.settings["palworld_rest_base_url"] = "http://127.0.0.1:27016/v1/api"
            write_json(SETTINGS_FILE, self.settings)
            if self.palworld_rest_url_var:
                self.palworld_rest_url_var.set(self.settings["palworld_rest_base_url"])
            self.refresh_palworld_dashboard()
            self.refresh_valheim_dashboard()
            self.refresh_port_check_view()
            self.log("Applied shared ASKA port profile: Palworld 27015/27016; Valheim 27015-27017.")
            messagebox.showinfo(APP_NAME, f"Shared ASKA port profile applied.\n\nPalworld game: 27015\nPalworld REST API: 27016\nValheim: 27015-27017\n\nBackups:\n{palworld_backup}\n{valheim_backup}\n\nOnly run one of these servers at a time.")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Shared port profile failed:\n{exc}")

    def read_port_source(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
        except OSError:
            return ""

    def parse_port_source_value(self, text: str, key: str) -> str:
        if not text:
            return ""
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
        match = pattern.search(text)
        return match.group(1).strip() if match else ""

    def configured_port_rows(self):
        rows = []

        aska_text = self.read_port_source(self.path("server_config_path"))
        aska_game_port = self.parse_port_source_value(aska_text, "steam game port") or "27015"
        aska_query_port = self.parse_port_source_value(aska_text, "steam query port") or "27016"
        rows.extend([
            {"server": "ASKA", "purpose": "Gameplay", "protocol": "TCP/UDP", "port": aska_game_port, "port_numbers": self.port_numbers(aska_game_port)},
            {"server": "ASKA", "purpose": "Steam query", "protocol": "UDP", "port": aska_query_port, "port_numbers": self.port_numbers(aska_query_port)},
        ])

        windrose_text = self.read_port_source(self.path("windrose_server_config_path"))
        windrose_port = ""
        if windrose_text:
            try:
                windrose_data = json.loads(windrose_text)
                persistent = windrose_data.get("ServerDescription_Persistent", {})
                direct_port = persistent.get("DirectConnectionServerPort", -1)
                if isinstance(direct_port, int) and direct_port > 0:
                    windrose_port = str(direct_port)
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        if windrose_port:
            rows.append({"server": "Windrose", "purpose": "Direct connection", "protocol": "TCP/UDP", "port": windrose_port, "port_numbers": self.port_numbers(windrose_port)})
        else:
            rows.append({"server": "Windrose", "purpose": "P2P proxy", "protocol": "P2P", "port": "-", "port_numbers": [], "static_listener": "P2P proxy", "static_firewall": "Not applicable"})

        palworld_text = self.read_port_source(self.path("palworld_server_config_path"))
        palworld_game_port = self.parse_palworld_setting(palworld_text, "PublicPort") or "8211"
        rows.append({"server": "Palworld", "purpose": "Game", "protocol": "UDP", "port": palworld_game_port, "port_numbers": self.port_numbers(palworld_game_port)})
        rest_port = self.parse_palworld_setting(palworld_text, "RESTAPIPort") or "8212"
        rest_enabled = (self.parse_palworld_setting(palworld_text, "RESTAPIEnabled") or "False").lower() == "true"
        rows.append({"server": "Palworld", "purpose": "REST API", "protocol": "TCP", "port": rest_port, "port_numbers": self.port_numbers(rest_port) if rest_enabled else [], "static_listener": "Disabled" if not rest_enabled else None, "static_firewall": "Disabled" if not rest_enabled else None})
        rcon_port = self.parse_palworld_setting(palworld_text, "RCONPort") or "25575"
        rcon_enabled = (self.parse_palworld_setting(palworld_text, "RCONEnabled") or "False").lower() == "true"
        rows.append({"server": "Palworld", "purpose": "RCON", "protocol": "TCP", "port": rcon_port, "port_numbers": self.port_numbers(rcon_port) if rcon_enabled else [], "static_listener": "Disabled" if not rcon_enabled else None, "static_firewall": "Disabled" if not rcon_enabled else None})

        valheim_text = self.valheim_launcher_text() or ""
        valheim_line = self.valheim_command_line(valheim_text) or ""
        valheim_port = self.parse_valheim_arg(valheim_line, "port") or "2456"
        base_port = self.port_numbers(valheim_port)
        if base_port:
            for offset in range(3):
                port = base_port[0] + offset
                rows.append({"server": "Valheim", "purpose": "Game" if offset == 0 else f"Game + {offset}", "protocol": "UDP", "port": str(port), "port_numbers": [port]})
        else:
            rows.append({"server": "Valheim", "purpose": "Game", "protocol": "UDP", "port": valheim_port, "port_numbers": []})

        abiotic_game_port = str(self.settings.get("abiotic_server_port", "9876"))
        abiotic_query_port = str(self.settings.get("abiotic_query_port", "25575"))
        rows.extend([
            {"server": "Abiotic Factor", "purpose": "Game", "protocol": "UDP", "port": abiotic_game_port, "port_numbers": self.port_numbers(abiotic_game_port)},
            {"server": "Abiotic Factor", "purpose": "Steam query", "protocol": "UDP", "port": abiotic_query_port, "port_numbers": self.port_numbers(abiotic_query_port)},
        ])
        minecraft_port = str(self.settings.get("minecraft_server_port", "25565"))
        try:
            minecraft_text = self.read_port_source(self.minecraft_path("minecraft_server_properties_path"))
            minecraft_port = self.parse_port_source_value(minecraft_text, "server-port") or minecraft_port
        except (AttributeError, OSError):
            pass
        rows.append({"server": "Minecraft", "purpose": "Java server", "protocol": "TCP", "port": minecraft_port, "port_numbers": self.port_numbers(minecraft_port)})
        return rows

    def port_numbers(self, value: str):
        try:
            port = int(str(value).strip())
        except (TypeError, ValueError):
            return []
        return [port] if 1 <= port <= 65535 else []

    def refresh_port_check_view(self):
        if not self.port_check_tree:
            return
        rows = self.configured_port_rows()
        self.port_check_rows = rows
        self.port_check_tree.delete(*self.port_check_tree.get_children())
        for row in rows:
            self.port_check_tree.insert("", "end", values=(row["server"], row["purpose"], row["protocol"], row["port"], "Not checked", "Not checked"))
        if self.port_check_status_var:
            self.port_check_status_var.set("Configured ports refreshed")

    def read_netstat_listeners(self):
        listeners = []
        try:
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
        except (OSError, subprocess.SubprocessError):
            return listeners
        for raw_line in result.stdout.splitlines():
            parts = raw_line.split()
            if not parts or parts[0].upper() not in {"TCP", "UDP"} or len(parts) < 4:
                continue
            protocol = parts[0].upper()
            if protocol == "TCP":
                if len(parts) < 5 or parts[3].upper() != "LISTENING":
                    continue
                pid_text = parts[4]
            else:
                pid_text = parts[3]
            port = self.port_numbers(parts[1].rsplit(":", 1)[-1])
            if port and pid_text.isdigit():
                listeners.append((protocol, port[0], pid_text))
        return listeners

    def read_firewall_port_rules(self):
        try:
            result = subprocess.run(["netsh", "advfirewall", "firewall", "show", "rule", "name=all", "dir=in"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
            if result.returncode != 0:
                return None
            rules = []
            for block in re.split(r"\r?\n\s*\r?\n", result.stdout):
                fields = {}
                for line in block.splitlines():
                    if ":" not in line:
                        continue
                    key, value = line.split(":", 1)
                    fields[key.strip().lower()] = value.strip()
                if fields.get("enabled", "").lower() == "yes" and fields.get("action", "").lower() == "allow":
                    rules.append({"Protocol": fields.get("protocol", "Any"), "LocalPort": fields.get("localport", "Any")})
            return rules
        except (OSError, subprocess.SubprocessError):
            return None

    def firewall_rule_matches(self, rules, protocol: str, port: int) -> bool:
        if rules is None:
            return False
        for rule in rules:
            rule_protocol = str(rule.get("Protocol", "Any")).upper()
            if rule_protocol not in {"ANY", protocol.upper(), "6" if protocol.upper() == "TCP" else "17"}:
                continue
            local_port = str(rule.get("LocalPort", "Any"))
            for part in re.split(r"[,;\s]+", local_port):
                part = part.strip()
                if not part or part.lower() in {"any", "*"}:
                    return True
                if "-" in part:
                    start, end = part.split("-", 1)
                    if start.isdigit() and end.isdigit() and int(start) <= port <= int(end):
                        return True
                elif part.isdigit() and int(part) == port:
                    return True
        return False

    def check_all_ports(self):
        if not self.port_check_tree:
            return
        rows = self.configured_port_rows()
        self.port_check_rows = rows
        self.port_check_button.configure(state="disabled")
        self.port_check_status_var.set("Checking local listeners and firewall...")
        threading.Thread(target=self.check_ports_worker, args=(rows,), daemon=True).start()

    def check_ports_worker(self, rows):
        listeners = self.read_netstat_listeners()
        firewall_rules = self.read_firewall_port_rules()
        results = []
        for row in rows:
            ports = row.get("port_numbers", [])
            if not ports:
                listener_status = row.get("static_listener") or "No port configured"
                firewall_status = row.get("static_firewall") or "Not checked"
            else:
                protocols = {row["protocol"]} if row["protocol"] in {"TCP", "UDP"} else {"TCP", "UDP"}
                matches = [(protocol, pid) for protocol, port, pid in listeners if port in ports and protocol in protocols]
                listener_status = "Listening" + " (PID " + ", ".join(sorted({pid for _protocol, pid in matches})) + ")" if matches else "Not listening"
                if firewall_rules is None:
                    firewall_status = "Unknown"
                elif any(self.firewall_rule_matches(firewall_rules, protocol, port) for protocol in protocols for port in ports):
                    firewall_status = "Allow rule found"
                else:
                    firewall_status = "No matching allow rule"
            results.append((row["server"], row["purpose"], row["protocol"], row["port"], listener_status, firewall_status))
        self.after(0, self.apply_port_check_results, results)

    def apply_port_check_results(self, results):
        if not self.port_check_tree:
            return
        self.port_check_tree.delete(*self.port_check_tree.get_children())
        for row in results:
            self.port_check_tree.insert("", "end", values=row)
        self.port_check_button.configure(state="normal")
        self.port_check_status_var.set(f"Checked {len(results)} entries")

    def build_backups_tab(self):
        top = ttk.Frame(self.backups_tab)
        top.pack(fill="x", pady=(0, 10))
        ttk.Button(top, text="Refresh", command=self.refresh_backups).pack(side="left")
        ttk.Button(top, text="Backup Now", style="Accent.TButton", command=lambda: self.run_threaded("Backup", self.create_backup)).pack(side="left", padx=8)
        ttk.Button(top, text="Restore Selected Backup", style="Danger.TButton", command=self.restore_selected_backup).pack(side="left")
        ttk.Button(top, text="Open Backup Folder", command=lambda: self.open_path(self.path("backup_folder_path"))).pack(side="left", padx=8)

        columns = ("server", "name", "date", "size")
        self.backup_tree = ttk.Treeview(self.backups_tab, columns=columns, show="headings", selectmode="browse")
        self.backup_tree.heading("server", text="Server")
        self.backup_tree.heading("name", text="Backup")
        self.backup_tree.heading("date", text="Date/time")
        self.backup_tree.heading("size", text="Approx size")
        self.backup_tree.column("server", width=130)
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

    def build_game_mods_tab(self, parent, game_name: str, install_path_key: str):
        container = self.panel(parent, f"{game_name} Mods")
        container.pack(fill="both", expand=True)
        ttk.Label(
            container,
            text=f"{game_name} has a dedicated Mods tab, but no game-specific mod manager is configured yet.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(0, 10))
        ttk.Label(
            container,
            text="Use this page for the game's future mod tools. The server install folder is available below for manual inspection.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(0, 14))
        ttk.Button(container, text="Open Install Folder", command=lambda key=install_path_key: self.open_path(self.path(key))).pack(anchor="w")

    def build_settings_tab(self):
        canvas = tk.Canvas(self.settings_tab, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.settings_tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        container = ttk.Frame(canvas, padding=14)
        window_id = canvas.create_window((0, 0), window=container, anchor="nw")

        def resize_container(event):
            canvas.itemconfigure(window_id, width=event.width)

        def update_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", resize_container)
        container.bind("<Configure>", update_scroll_region)

        form = ttk.Frame(container, style="Panel.TFrame", padding=14)
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

        opts = ttk.Frame(container, style="Panel.TFrame", padding=14)
        opts.pack(fill="x", pady=(14, 0))
        ttk.Label(opts, text="BACKUP POLICY", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.interval_var = tk.StringVar(value=str(self.settings.get("backup_interval_minutes", 60)))
        self.retention_var = tk.StringVar(value=str(self.settings.get("retention_hours", 24)))
        ttk.Label(opts, text="Backup interval minutes", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(opts, textvariable=self.interval_var, width=12).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(opts, text="Retention hours", style="Panel.TLabel").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(opts, textvariable=self.retention_var, width=12).grid(row=2, column=1, sticky="w", pady=5)
        ttk.Button(opts, text="Save Settings", style="Accent.TButton", command=self.save_settings_from_ui).grid(row=3, column=0, sticky="w", pady=(12, 0))

        nexus = ttk.Frame(container, style="Panel.TFrame", padding=14)
        nexus.pack(fill="x", pady=(14, 0))
        ttk.Label(nexus, text="NEXUS MODS", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.nexus_api_key_var = tk.StringVar(value=str(self.settings.get("nexus_api_key", "")))
        self.nexus_key_status_var = tk.StringVar()
        self.update_nexus_key_status()
        ttk.Label(nexus, text="Nexus API key", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(nexus, textvariable=self.nexus_api_key_var, show="*", width=52).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Label(nexus, textvariable=self.nexus_key_status_var, style="Panel.TLabel").grid(row=2, column=1, sticky="w", pady=(0, 5))
        ttk.Label(
            nexus,
            text="Optional. Used only for checking tracked Nexus mod metadata. Manual ZIP install works without it.",
            style="Panel.TLabel",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))
        nexus.columnconfigure(1, weight=1)

        startup = ttk.Frame(container, style="Panel.TFrame", padding=14)
        startup.pack(fill="x", pady=(14, 0))
        ttk.Label(startup, text="STARTUP AND WATCHDOG", style="Panel.TLabel", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.launch_on_startup_var = tk.BooleanVar(value=bool(self.settings.get("launch_on_windows_startup")))
        self.start_server_on_launch_var = tk.BooleanVar(value=bool(self.settings.get("start_server_on_app_launch")))
        self.auto_restart_var = tk.BooleanVar(value=bool(self.settings.get("auto_restart_server")))
        ttk.Checkbutton(startup, text="Launch Gaming Dads Server Manager when Windows starts", variable=self.launch_on_startup_var).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Checkbutton(startup, text="Start ASKA server when the manager opens", variable=self.start_server_on_launch_var).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Checkbutton(startup, text="Auto-restart ASKA server if it stops unexpectedly", variable=self.auto_restart_var).grid(row=3, column=0, sticky="w", pady=3)
        ttk.Label(
            startup,
            text="Auto-restart only acts when the app believes the server should be running. Clicking Stop Server disables that expectation.",
            style="Panel.TLabel",
        ).grid(row=4, column=0, sticky="w", pady=(8, 0))

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
        self.refresh_windrose_status()
        self.refresh_palworld_status()
        self.refresh_valheim_status()
        self.refresh_abiotic_status()
        self.refresh_minecraft_status()
        self.refresh_dashboard()
        self.refresh_windrose_dashboard()
        self.refresh_palworld_dashboard()
        self.refresh_valheim_dashboard()
        self.refresh_abiotic_dashboard()
        self.refresh_minecraft_dashboard()
        self.refresh_overview_status()
        self.refresh_backups()
        self.refresh_mods()
        self.refresh_minecraft_mods()
        self.load_config(silent=True)

    def refresh_overview_status(self):
        if not self.overview_status_vars:
            return
        checks = {
            "ASKA": self.is_server_running(),
            "Windrose": self.is_windrose_running(),
            "Palworld": self.is_palworld_running(),
            "Valheim": self.is_valheim_running(),
            "Abiotic Factor": self.is_abiotic_running(),
            "Minecraft": self.is_minecraft_running(),
        }
        for server, running in checks.items():
            self.overview_status_vars[server].set("Running" if running else "Stopped")

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
        return None

    def refresh_status(self):
        process_text = self.get_server_process_text()
        running = process_text is not None
        self.dashboard_vars["status"].set("Running" if running else "Stopped")
        if "detected_process" in self.dashboard_vars:
            self.dashboard_vars["detected_process"].set(process_text or "None")
        self.status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])
        if self.start_button:
            self.start_button.configure(style="TButton" if running else "Green.TButton")
        if self.stop_button:
            self.stop_button.configure(style="Danger.TButton" if running else "TButton")

    def schedule_status_refresh(self):
        self.refresh_status()
        self.refresh_windrose_status()
        self.refresh_palworld_status()
        self.refresh_valheim_status()
        self.refresh_abiotic_status()
        self.refresh_minecraft_status()
        self.refresh_overview_status()
        self.status_job = self.after(5000, self.schedule_status_refresh)

    def start_server(self):
        if self.is_server_running():
            self.server_should_be_running = True
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
            self.server_should_be_running = True
            self.log("Server start requested.")
            self.after(2000, self.refresh_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start server:\n{exc}")
            self.log(f"Start failed: {exc}")

    def stop_server(self, ask_force=True) -> bool:
        self.server_should_be_running = False
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
                self.server_should_be_running = True
                self.after(0, self.start_server)
        threading.Thread(target=work, daemon=True).start()

    def schedule_server_watchdog(self):
        if self.watchdog_job:
            self.after_cancel(self.watchdog_job)
            self.watchdog_job = None
        self.watchdog_job = self.after(30000, self.server_watchdog_tick)

    def server_watchdog_tick(self):
        if self.settings.get("auto_restart_server") and self.server_should_be_running and not self.is_server_running():
            self.log("Watchdog detected server stopped unexpectedly. Restarting server.")
            self.start_server()
        if self.settings.get("palworld_auto_restart_server") and self.palworld_should_be_running and not self.is_palworld_running():
            self.log("Palworld watchdog detected the server stopped unexpectedly. Restarting server.")
            self.send_discord_webhook("Palworld stopped unexpectedly. The manager is attempting an automatic restart.")
            self.start_palworld_server()
        if self.settings.get("valheim_auto_restart_server") and self.valheim_should_be_running and not self.is_valheim_running():
            self.log("Valheim watchdog detected the server stopped unexpectedly. Restarting server.")
            self.start_valheim_server()
        if self.settings.get("abiotic_auto_restart_server") and self.abiotic_should_be_running and not self.is_abiotic_running():
            self.log("Abiotic Factor watchdog detected the server stopped unexpectedly. Restarting server.")
            self.start_abiotic_server()
        self.minecraft_watchdog_tick()
        self.schedule_server_watchdog()

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

        if result.get("success") is False:
            error_text = result.get("error") or "Steam did not return update information."
            status_text = f"Check unavailable - {error_text}"
            self.log(f"Server update check unavailable: local={build_id}, error={error_text}")
            if "server_update_status" in self.dashboard_vars:
                self.after(0, self.dashboard_vars["server_update_status"].set, status_text)
            self.after(0, self.set_update_button_available, False)
            if show_dialog:
                self.after(
                    0,
                    messagebox.showinfo,
                    APP_NAME,
                    "Steam did not return update information for ASKA Dedicated Server.\n\n"
                    f"Local build: {build_id}\n"
                    f"Steam response: {error_text}\n\n"
                    "You can still use Update Server while the server is stopped.",
                )
            return

        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        steam_message = result.get("message", "")
        if up_to_date:
            status_text = f"Server is up to date - build {build_id}"
            message = f"ASKA Dedicated Server is up to date.\n\nLocal build: {build_id}"
        else:
            if required == "unknown":
                status_text = f"Update may be available - local {build_id}, latest unknown"
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
        self.after(0, self.set_update_button_available, (not up_to_date) and required != "unknown")
        if show_dialog:
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def set_update_button_available(self, available: bool):
        if self.update_server_button:
            self.update_server_button.configure(style="Green.TButton" if available else "TButton")

    def set_windrose_update_button_available(self, available: bool):
        if self.windrose_update_button:
            self.windrose_update_button.configure(style="Green.TButton" if available else "TButton")

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

    def get_named_process_text(self, exe_name: str, process_name: str):
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
            if exe_name.lower() in result.stdout.lower():
                return exe_name
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def get_windrose_process_text(self):
        return self.get_named_process_text(WINDROSE_EXE_NAME, "WindroseServer")

    def is_windrose_running(self) -> bool:
        return self.get_windrose_process_text() is not None

    def refresh_windrose_status(self):
        if not self.windrose_vars:
            return
        process_text = self.get_windrose_process_text()
        running = process_text is not None
        self.windrose_vars["status"].set("Running" if running else "Stopped")
        self.windrose_vars["detected_process"].set(process_text or "None")
        if hasattr(self, "windrose_status_label"):
            self.windrose_status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])
        if self.windrose_start_button:
            self.windrose_start_button.configure(style="TButton" if running else "Green.TButton")
        if self.windrose_stop_button:
            self.windrose_stop_button.configure(style="Danger.TButton" if running else "TButton")

    def refresh_windrose_dashboard(self):
        if not self.windrose_vars:
            return
        backup_dir = self.path("windrose_backup_folder_path")
        backups = self.list_windrose_backups()
        self.windrose_vars["install_path"].set(str(self.path("windrose_server_install_path")))
        self.windrose_vars["save_folder_path"].set(str(self.path("windrose_save_folder_path")))
        self.windrose_vars["backup_folder_path"].set(str(backup_dir))
        self.windrose_vars["config_path"].set(str(self.path("windrose_server_config_path")))
        self.windrose_vars["backup_count"].set(str(len(backups)))

    def start_windrose_server(self):
        self.sync_windrose_path_vars()
        if self.is_windrose_running():
            messagebox.showinfo(APP_NAME, "The Windrose server is already running.")
            self.log("Windrose start skipped: server already running.")
            return
        launcher = self.path("windrose_server_bat_path")
        executable = self.path("windrose_server_exe_path")
        start_path = launcher if launcher.exists() else executable
        if not start_path.exists():
            messagebox.showerror(APP_NAME, f"Windrose launcher was not found:\n{launcher}\n\nAlso checked:\n{executable}")
            self.log(f"Windrose start failed: launcher not found: {launcher}")
            return
        try:
            subprocess.Popen(
                [str(start_path)],
                cwd=str(start_path.parent),
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self.log("Windrose server start requested.")
            self.after(2500, self.refresh_windrose_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start Windrose server:\n{exc}")
            self.log(f"Windrose start failed: {exc}")

    def stop_windrose_server(self, ask_force=True) -> bool:
        if not self.is_windrose_running():
            self.log("Windrose stop skipped: server is not running.")
            self.refresh_windrose_status()
            return True
        self.log("Windrose server stop requested.")
        try:
            subprocess.run(
                ["taskkill", "/IM", WINDROSE_EXE_NAME, "/T"],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            self.log(f"Windrose graceful stop command failed: {exc}")

        deadline = time.time() + 15
        while time.time() < deadline:
            if not self.is_windrose_running():
                self.log("Windrose server stopped.")
                self.refresh_windrose_status()
                return True
            time.sleep(1)

        if ask_force and messagebox.askyesno(APP_NAME, "Windrose did not stop within 15 seconds. Force kill it?"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", WINDROSE_EXE_NAME, "/T"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                self.log("Windrose server force kill requested.")
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Windrose force kill failed: {exc}")
                messagebox.showerror(APP_NAME, f"Windrose force kill failed:\n{exc}")
                return False
            self.after(1500, self.refresh_windrose_status)
            return True
        self.log("Windrose stop incomplete: server is still running.")
        return False

    def restart_windrose_server(self, ask_force=True):
        def work():
            if self.stop_windrose_server(ask_force=ask_force):
                time.sleep(3)
                self.after(0, self.start_windrose_server)
        threading.Thread(target=work, daemon=True).start()

    def windrose_appmanifest_path(self) -> Path:
        install_dir = self.path("windrose_server_install_path")
        try:
            steamapps_dir = install_dir.parent.parent
        except IndexError:
            return Path()
        return steamapps_dir / f"appmanifest_{WINDROSE_DEDICATED_SERVER_APP_ID}.acf"

    def local_windrose_build_id(self) -> str:
        manifest = self.windrose_appmanifest_path()
        if not manifest.exists():
            return ""
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r'"buildid"\s+"(\d+)"', text, re.IGNORECASE)
        return match.group(1) if match else ""

    def check_windrose_update(self, show_dialog=True):
        if not self.windrose_vars:
            return
        self.windrose_vars["update_status"].set("Checking...")
        build_id = self.local_windrose_build_id()
        manifest = self.windrose_appmanifest_path()
        if not build_id:
            self.windrose_vars["update_status"].set("Unknown - app manifest not found")
            self.set_windrose_update_button_available(False)
            if show_dialog:
                messagebox.showerror(
                    APP_NAME,
                    "Could not find the local Windrose Dedicated Server build ID.\n\n"
                    f"Expected Steam app manifest:\n{manifest}",
                )
            self.log(f"Windrose update check failed: build ID not found in {manifest}")
            return
        self.run_threaded("Windrose Steam update check", lambda: self.do_check_windrose_update(build_id, show_dialog=show_dialog))

    def do_check_windrose_update(self, build_id: str, show_dialog=True):
        url = (
            "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/"
            f"?appid={WINDROSE_DEDICATED_SERVER_APP_ID}&version={build_id}"
        )
        request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            result = data.get("response", {})
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Windrose update check failed: {exc}")
            self.after(0, self.windrose_vars["update_status"].set, "Check failed")
            self.after(0, self.set_windrose_update_button_available, False)
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Windrose update check failed:\n{exc}")
            return

        if result.get("success") is False:
            error_text = result.get("error") or "Steam did not return update information."
            status_text = f"Check unavailable - {error_text}"
            self.log(f"Windrose update check unavailable: local={build_id}, error={error_text}")
            self.after(0, self.windrose_vars["update_status"].set, status_text)
            self.after(0, self.set_windrose_update_button_available, False)
            if show_dialog:
                self.after(
                    0,
                    messagebox.showinfo,
                    APP_NAME,
                    "Steam did not return update information for Windrose Dedicated Server.\n\n"
                    f"Local build: {build_id}\n"
                    f"Steam response: {error_text}\n\n"
                    "You can still use Update Windrose while the server is stopped.",
                )
            return

        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        if up_to_date:
            status_text = f"Server is up to date - build {build_id}"
            message = f"Windrose Dedicated Server is up to date.\n\nLocal build: {build_id}"
        else:
            status_text = f"Update available - local {build_id}, latest {required}"
            message = (
                "Windrose Dedicated Server update appears available.\n\n"
                f"Local build: {build_id}\n"
                f"Required build: {required}\n\n"
                "Use Update Windrose after stopping the server."
            )
        self.log(f"Windrose update check: local={build_id}, required={required}, up_to_date={up_to_date}")
        self.after(0, self.windrose_vars["update_status"].set, status_text)
        self.after(0, self.set_windrose_update_button_available, (not up_to_date) and required != "unknown")
        if show_dialog:
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def update_windrose_server_with_steamcmd(self):
        self.sync_windrose_path_vars()
        if self.is_windrose_running():
            messagebox.showwarning(APP_NAME, "Stop the Windrose server before running a SteamCMD update.")
            self.log("Windrose SteamCMD update refused: server is running.")
            return
        steamcmd = self.path("steamcmd_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet the SteamCMD executable path in Settings.")
            self.log(f"Windrose SteamCMD update failed: steamcmd not found: {steamcmd}")
            return
        install_dir = self.path("windrose_server_install_path")
        if not install_dir.exists():
            messagebox.showerror(APP_NAME, f"Windrose install folder was not found:\n{install_dir}")
            self.log(f"Windrose SteamCMD update failed: install folder missing: {install_dir}")
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Update Windrose Dedicated Server with SteamCMD?\n\n"
            "The app will create a Windrose save/config backup first if the configured paths exist.",
        ):
            return
        self.run_threaded("Windrose SteamCMD server update", self.do_update_windrose_server_with_steamcmd)

    def install_windrose_server_with_steamcmd(self):
        self.sync_windrose_path_vars()
        if self.is_windrose_running():
            messagebox.showwarning(APP_NAME, "Stop the Windrose server before installing or repairing it with SteamCMD.")
            self.log("Windrose SteamCMD install refused: server is running.")
            return
        steamcmd = self.path("steamcmd_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet the SteamCMD executable path in Settings.")
            self.log(f"Windrose SteamCMD install failed: steamcmd not found: {steamcmd}")
            return
        install_dir = self.path("windrose_server_install_path")
        if not self.validate_safe_folder(install_dir, "Windrose install folder"):
            return
        if not messagebox.askyesno(
            APP_NAME,
            "Install or repair Windrose Dedicated Server with SteamCMD?\n\n"
            f"Install folder:\n{install_dir}\n\n"
            "This downloads Steam app 4129620 using anonymous SteamCMD login.",
        ):
            return
        self.run_threaded("Windrose SteamCMD server install", self.do_install_windrose_server_with_steamcmd)

    def do_install_windrose_server_with_steamcmd(self):
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("windrose_server_install_path")
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.log(f"Windrose install failed: could not create install folder: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Could not create Windrose install folder:\n{exc}")
            return
        exit_code = self.run_windrose_steamcmd(steamcmd, install_dir, "install")
        if exit_code == 0:
            self.settings["windrose_server_bat_path"] = str(install_dir / "StartServerForeground.bat")
            self.settings["windrose_server_exe_path"] = str(install_dir / WINDROSE_EXE_NAME)
            self.settings["windrose_server_config_path"] = str(install_dir / "R5" / "ServerDescription.json")
            save_path = next((candidate for candidate in self.windrose_save_candidates(install_dir) if candidate.exists()), self.windrose_save_candidates(install_dir)[0])
            self.settings["windrose_save_folder_path"] = str(save_path)
            write_json(SETTINGS_FILE, self.settings)
            self.after(0, self.apply_windrose_settings_to_ui)
            self.after(0, self.refresh_windrose_dashboard)
            self.after(0, self.check_windrose_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Windrose Dedicated Server install/repair complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Windrose SteamCMD install exited with code {exit_code}. Check Logs.")

    def do_update_windrose_server_with_steamcmd(self):
        self.create_windrose_backup(prefix_override="before_windrose_update_", show_missing_error=False)
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("windrose_server_install_path")
        exit_code = self.run_windrose_steamcmd(steamcmd, install_dir, "update")

        if exit_code == 0:
            self.log("Windrose SteamCMD update completed successfully.")
            self.after(0, self.check_windrose_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Windrose server update complete.")
        else:
            self.log(f"Windrose SteamCMD update exited with code {exit_code}.")
            self.after(0, messagebox.showerror, APP_NAME, f"Windrose SteamCMD update exited with code {exit_code}. Check Logs.")

    def run_windrose_steamcmd(self, steamcmd: Path, install_dir: Path, action_label: str) -> int:
        command = [
            str(steamcmd),
            "+login",
            "anonymous",
            "+force_install_dir",
            str(install_dir),
            "+app_update",
            WINDROSE_DEDICATED_SERVER_APP_ID,
            "validate",
            "+quit",
        ]
        self.log(f"Running SteamCMD {action_label} for Windrose Dedicated Server app 4129620.")
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
                    self.log(f"Windrose SteamCMD: {clean}")
            exit_code = process.wait()
        except OSError as exc:
            self.log(f"Windrose SteamCMD {action_label} failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Windrose SteamCMD {action_label} failed:\n{exc}")
            return 1
        return exit_code

    def create_windrose_backup(self, prefix_override=None, show_missing_error=True) -> Path | None:
        self.sync_windrose_path_vars()
        save_dir = self.path("windrose_save_folder_path")
        config_path = self.path("windrose_server_config_path")
        backup_dir = self.path("windrose_backup_folder_path")
        if not save_dir.exists() and not config_path.exists():
            if show_missing_error:
                self.after(0, messagebox.showerror, APP_NAME, f"Windrose save/config paths do not exist yet:\n{save_dir}\n{config_path}")
            self.log(f"Windrose backup skipped: save/config missing: {save_dir}; {config_path}")
            return None
        if save_dir.exists() and not self.validate_safe_folder(save_dir, "Windrose save folder"):
            return None
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"{prefix_override or 'windrose_backup_'}{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"{prefix_override or 'windrose_backup_'}{now_stamp()}_{counter}"
            counter += 1
        try:
            target.mkdir(parents=True)
            if save_dir.exists():
                shutil.copytree(save_dir, target / "save")
            if config_path.exists() and config_path.is_file():
                shutil.copy2(config_path, target / config_path.name)
            self.log(f"Windrose backup created: {target}")
            self.after(0, self.refresh_windrose_dashboard)
            return target
        except OSError as exc:
            self.log(f"Windrose backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Windrose backup failed:\n{exc}")
            return None

    def list_windrose_backups(self):
        backup_dir = self.path("windrose_backup_folder_path")
        if not backup_dir.exists():
            return []
        items = []
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
            for prefix in ["windrose_backup_", "before_windrose_update_"]:
                if item.name.startswith(prefix):
                    timestamp = item.name.removeprefix(prefix)[:16]
                    try:
                        items.append((item, datetime.strptime(timestamp, BACKUP_TIME_FORMAT)))
                    except ValueError:
                        pass
                    break
        return sorted(items, key=lambda row: row[1], reverse=True)

    def load_windrose_config(self):
        self.sync_windrose_path_vars()
        config_path = self.path("windrose_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Windrose config file not found:\n{config_path}")
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not load Windrose config:\n{exc}")
            self.log(f"Windrose config load failed: {exc}")
            return
        self.windrose_config_text.configure(state="normal")
        self.windrose_config_text.delete("1.0", "end")
        self.windrose_config_text.insert("1.0", text)
        self.windrose_config_text.edit_reset()
        self.refresh_windrose_config_form(text, silent=True)
        self.log(f"Loaded Windrose config: {config_path}")

    def save_windrose_config(self):
        self.sync_windrose_path_vars()
        if self.is_windrose_running():
            messagebox.showwarning(APP_NAME, "Stop the Windrose server before editing ServerDescription.json.")
            self.log("Windrose config save refused: server is running.")
            return
        config_path = self.path("windrose_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Windrose config file not found:\n{config_path}")
            return
        text = self.windrose_config_text.get("1.0", "end-1c")
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            messagebox.showerror(APP_NAME, f"Windrose config is not valid JSON:\n{exc}")
            return
        try:
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            config_path.write_text(text, encoding="utf-8")
            self.refresh_windrose_config_form(text, silent=True)
            self.log(f"Saved Windrose config: {config_path}")
            messagebox.showinfo(APP_NAME, f"Windrose config saved.\nBackup created:\n{backup_path}")
        except OSError as exc:
            self.log(f"Windrose config save failed: {exc}")
            messagebox.showerror(APP_NAME, f"Windrose config save failed:\n{exc}")

    def get_palworld_process_text(self):
        return self.get_named_process_text(PALWORLD_EXE_NAME, PALWORLD_PROCESS_NAME)

    def is_palworld_running(self) -> bool:
        return self.get_palworld_process_text() is not None

    def refresh_palworld_status(self):
        if not self.palworld_vars:
            return
        process_text = self.get_palworld_process_text()
        running = process_text is not None
        self.palworld_vars["status"].set("Running" if running else "Stopped")
        self.palworld_vars["detected_process"].set(process_text or "None")
        if hasattr(self, "palworld_status_label"):
            self.palworld_status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])
        if self.palworld_start_button:
            self.palworld_start_button.configure(style="TButton" if running else "Green.TButton")
        if self.palworld_stop_button:
            self.palworld_stop_button.configure(style="Danger.TButton" if running else "TButton")

    def refresh_palworld_dashboard(self):
        if not self.palworld_vars:
            return
        backup_dir = self.path("palworld_backup_folder_path")
        backups = self.list_palworld_backups()
        self.palworld_vars["install_path"].set(str(self.path("palworld_server_install_path")))
        self.palworld_vars["save_folder_path"].set(str(self.path("palworld_save_folder_path")))
        self.palworld_vars["backup_folder_path"].set(str(backup_dir))
        self.palworld_vars["config_path"].set(str(self.path("palworld_server_config_path")))
        self.palworld_vars["backup_count"].set(str(len(backups)))
        if backups:
            self.palworld_vars["last_backup"].set(backups[0][1].strftime("%Y-%m-%d %H:%M"))
        else:
            self.palworld_vars["last_backup"].set("No backups found")

    def start_palworld_server(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            self.palworld_should_be_running = True
            messagebox.showinfo(APP_NAME, "The Palworld server is already running.")
            self.log("Palworld start skipped: server already running.")
            return
        executable = self.path("palworld_server_exe_path")
        if not executable.exists():
            executable = self.path("palworld_server_install_path") / PALWORLD_EXE_NAME
        if not executable.exists():
            messagebox.showerror(APP_NAME, f"Palworld server executable not found:\n{executable}\n\nUse Auto-detect or browse to the server install.")
            self.log(f"Palworld start failed: executable not found: {executable}")
            return
        try:
            subprocess.Popen(
                [str(executable)],
                cwd=str(executable.parent),
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self.palworld_should_be_running = True
            self.log("Palworld server start requested.")
            self.send_discord_webhook("Palworld server start requested.")
            self.after(2500, self.refresh_palworld_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start Palworld server:\n{exc}")
            self.log(f"Palworld start failed: {exc}")

    def stop_palworld_server(self, ask_force=True) -> bool:
        self.palworld_should_be_running = False
        if not self.is_palworld_running():
            self.log("Palworld stop skipped: server is not running.")
            self.refresh_palworld_status()
            return True
        self.log("Palworld server stop requested.")
        rest_stopped = False
        if self.settings.get("palworld_admin_password"):
            try:
                self.palworld_rest_request("POST", "shutdown")
                rest_stopped = True
                self.log("Palworld graceful shutdown requested through REST API.")
            except (OSError, urllib.error.URLError, ValueError) as exc:
                self.log(f"Palworld REST shutdown unavailable; using taskkill fallback: {exc}")
        if not rest_stopped:
            try:
                subprocess.run(
                    ["taskkill", "/IM", PALWORLD_EXE_NAME, "/T"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Palworld graceful stop command failed: {exc}")

        deadline = time.time() + 15
        while time.time() < deadline:
            if not self.is_palworld_running():
                self.log("Palworld server stopped.")
                self.refresh_palworld_status()
                self.send_discord_webhook("Palworld server stopped.")
                return True
            time.sleep(1)

        if ask_force and messagebox.askyesno(APP_NAME, "Palworld did not stop within 15 seconds. Force kill it?"):
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", PALWORLD_EXE_NAME, "/T"],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=10,
                )
                self.log("Palworld server force kill requested.")
                self.send_discord_webhook("Palworld server force kill requested.")
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Palworld force kill failed: {exc}")
                messagebox.showerror(APP_NAME, f"Palworld force kill failed:\n{exc}")
                return False
            self.after(1500, self.refresh_palworld_status)
            return True
        self.log("Palworld stop incomplete: server is still running.")
        return False

    def restart_palworld_server(self):
        def work():
            if self.stop_palworld_server():
                time.sleep(3)
                self.palworld_should_be_running = True
                self.after(0, self.start_palworld_server)
        threading.Thread(target=work, daemon=True).start()

    def palworld_appmanifest_path(self) -> Path:
        install_dir = self.path("palworld_server_install_path")
        try:
            steamapps_dir = install_dir.parent.parent
        except IndexError:
            return Path()
        return steamapps_dir / f"appmanifest_{PALWORLD_DEDICATED_SERVER_APP_ID}.acf"

    def local_palworld_build_id(self) -> str:
        manifest = self.palworld_appmanifest_path()
        if not manifest.exists():
            return ""
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r'"buildid"\s+"(\d+)"', text, re.IGNORECASE)
        return match.group(1) if match else ""

    def check_palworld_update(self, show_dialog=True):
        if not self.palworld_vars:
            return
        self.palworld_vars["update_status"].set("Checking...")
        build_id = self.local_palworld_build_id()
        manifest = self.palworld_appmanifest_path()
        if not build_id:
            self.palworld_vars["update_status"].set("Unknown - app manifest not found")
            self.set_palworld_update_button_available(False)
            if show_dialog:
                messagebox.showerror(APP_NAME, "Could not find the local Palworld Dedicated Server build ID.\n\nExpected Steam app manifest:\n" + str(manifest))
            self.log(f"Palworld update check failed: build ID not found in {manifest}")
            return
        self.run_threaded("Palworld Steam update check", lambda: self.do_check_palworld_update(build_id, show_dialog=show_dialog))

    def do_check_palworld_update(self, build_id: str, show_dialog=True):
        url = "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/" f"?appid={PALWORLD_DEDICATED_SERVER_APP_ID}&version={build_id}"
        request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8", errors="replace"))
            result = data.get("response", {})
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Palworld update check failed: {exc}")
            self.after(0, self.palworld_vars["update_status"].set, "Check failed")
            self.after(0, self.set_palworld_update_button_available, False)
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Palworld update check failed:\n{exc}")
            return
        if result.get("success") is False:
            error_text = result.get("error") or "Steam did not return update information."
            self.after(0, self.palworld_vars["update_status"].set, f"Check unavailable - {error_text}")
            self.after(0, self.set_palworld_update_button_available, False)
            if show_dialog:
                self.after(0, messagebox.showinfo, APP_NAME, f"Steam did not return update information for Palworld Dedicated Server.\n\n{error_text}")
            return
        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        status_text = f"Server is up to date - build {build_id}" if up_to_date else f"Update available - local {build_id}, latest {required}"
        self.log(f"Palworld update check: local={build_id}, required={required}, up_to_date={up_to_date}")
        self.after(0, self.palworld_vars["update_status"].set, status_text)
        self.after(0, self.set_palworld_update_button_available, (not up_to_date) and required != "unknown")
        if show_dialog:
            message = f"Palworld Dedicated Server is up to date.\n\nLocal build: {build_id}" if up_to_date else f"Palworld Dedicated Server update appears available.\n\nLocal build: {build_id}\nRequired build: {required}"
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def set_palworld_update_button_available(self, available: bool):
        if self.palworld_update_button:
            self.palworld_update_button.configure(style="Green.TButton" if available else "TButton")

    def update_palworld_server_with_steamcmd(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            messagebox.showwarning(APP_NAME, "Stop the Palworld server before running a SteamCMD update.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("palworld_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not install_dir.exists():
            messagebox.showerror(APP_NAME, f"Palworld install folder was not found:\n{install_dir}")
            return
        if messagebox.askyesno(APP_NAME, "Update Palworld Dedicated Server with SteamCMD?\n\nThe app will create a save/config backup first if the configured paths exist."):
            self.run_threaded("Palworld SteamCMD server update", self.do_update_palworld_server_with_steamcmd)

    def install_palworld_server_with_steamcmd(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            messagebox.showwarning(APP_NAME, "Stop the Palworld server before installing or repairing it with SteamCMD.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("palworld_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not self.validate_safe_folder(install_dir, "Palworld install folder"):
            return
        if messagebox.askyesno(APP_NAME, f"Install or repair Palworld Dedicated Server with SteamCMD?\n\nInstall folder:\n{install_dir}\n\nThis downloads Steam app {PALWORLD_DEDICATED_SERVER_APP_ID}."):
            self.run_threaded("Palworld SteamCMD server install", self.do_install_palworld_server_with_steamcmd)

    def do_install_palworld_server_with_steamcmd(self):
        install_dir = self.path("palworld_server_install_path")
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.after(0, messagebox.showerror, APP_NAME, f"Could not create Palworld install folder:\n{exc}")
            return
        exit_code = self.run_palworld_steamcmd(self.path("steamcmd_path"), install_dir, "install")
        if exit_code == 0:
            self.settings["palworld_server_exe_path"] = str(install_dir / PALWORLD_EXE_NAME)
            self.settings["palworld_server_config_path"] = str(install_dir / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini")
            self.settings["palworld_save_folder_path"] = str(install_dir / "Pal" / "Saved" / "SaveGames")
            write_json(SETTINGS_FILE, self.settings)
            self.after(0, self.apply_palworld_settings_to_ui)
            self.after(0, self.refresh_palworld_dashboard)
            self.after(0, self.check_palworld_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Palworld Dedicated Server install/repair complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Palworld SteamCMD install exited with code {exit_code}. Check Logs.")

    def do_update_palworld_server_with_steamcmd(self):
        self.create_palworld_backup(prefix_override="before_palworld_update_", show_missing_error=False)
        exit_code = self.run_palworld_steamcmd(self.path("steamcmd_path"), self.path("palworld_server_install_path"), "update")
        if exit_code == 0:
            self.log("Palworld SteamCMD update completed successfully.")
            self.after(0, self.check_palworld_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Palworld server update complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Palworld SteamCMD update exited with code {exit_code}. Check Logs.")

    def run_palworld_steamcmd(self, steamcmd: Path, install_dir: Path, action_label: str) -> int:
        command = [str(steamcmd), "+login", "anonymous", "+force_install_dir", str(install_dir), "+app_update", PALWORLD_DEDICATED_SERVER_APP_ID, "validate", "+quit"]
        self.log(f"Running SteamCMD {action_label} for Palworld Dedicated Server app {PALWORLD_DEDICATED_SERVER_APP_ID}.")
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(steamcmd.parent), creationflags=subprocess.CREATE_NO_WINDOW)
            assert process.stdout is not None
            for line in process.stdout:
                clean = line.rstrip()
                if clean:
                    self.log(f"Palworld SteamCMD: {clean}")
            return process.wait()
        except OSError as exc:
            self.log(f"Palworld SteamCMD {action_label} failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Palworld SteamCMD {action_label} failed:\n{exc}")
            return 1

    def create_palworld_backup(self, prefix_override=None, show_missing_error=True) -> Path | None:
        if threading.get_ident() == self.main_thread_id:
            self.sync_palworld_path_vars()
        save_dir = self.path("palworld_save_folder_path")
        config_path = self.path("palworld_server_config_path")
        backup_dir = self.path("palworld_backup_folder_path")
        if not save_dir.exists() and not config_path.exists():
            if show_missing_error:
                self.after(0, messagebox.showerror, APP_NAME, f"Palworld save/config paths do not exist yet:\n{save_dir}\n{config_path}")
            self.log(f"Palworld backup skipped: save/config missing: {save_dir}; {config_path}")
            return None
        if save_dir.exists() and not self.validate_safe_folder(save_dir, "Palworld save folder"):
            return None
        if self.is_palworld_running() and self.settings.get("palworld_admin_password"):
            try:
                self.palworld_rest_request("POST", "save")
                self.log("Palworld world save requested before backup.")
            except (OSError, urllib.error.URLError, ValueError) as exc:
                self.log(f"Palworld REST save before backup failed; copying current files: {exc}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        prefix = prefix_override or "palworld_backup_"
        target = backup_dir / f"{prefix}{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"{prefix}{now_stamp()}_{counter}"
            counter += 1
        try:
            target.mkdir(parents=True)
            if save_dir.exists():
                shutil.copytree(save_dir, target / "save")
            if config_path.exists() and config_path.is_file():
                shutil.copy2(config_path, target / config_path.name)
            self.log(f"Palworld backup created: {target}")
            self.after(0, self.refresh_palworld_dashboard)
            return target
        except OSError as exc:
            self.log(f"Palworld backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Palworld backup failed:\n{exc}")
            return None

    def backup_palworld_now(self):
        self.sync_palworld_path_vars()
        self.run_threaded("Palworld backup", self.create_palworld_backup)

    def list_palworld_backups(self):
        backup_dir = self.path("palworld_backup_folder_path")
        if not backup_dir.exists():
            return []
        items = []
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
            for prefix in ["palworld_backup_", "before_palworld_update_"]:
                if item.name.startswith(prefix):
                    try:
                        items.append((item, datetime.strptime(item.name.removeprefix(prefix)[:16], BACKUP_TIME_FORMAT)))
                    except ValueError:
                        pass
                    break
        return sorted(items, key=lambda row: row[1], reverse=True)

    def load_palworld_config(self):
        self.sync_palworld_path_vars()
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not load Palworld config:\n{exc}")
            return
        self.palworld_config_text.configure(state="normal")
        self.palworld_config_text.delete("1.0", "end")
        self.palworld_config_text.insert("1.0", text)
        self.palworld_config_text.edit_reset()
        self.set_palworld_config_form_values(text)
        self.log(f"Loaded Palworld config: {config_path}")

    def parse_palworld_setting(self, text: str, key: str):
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(key)}\s*=\s*(\"(?:\\.|[^\"])*\"|[^,\)\r\n]+)", re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return None
        value = match.group(1).strip()
        if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        return value

    def set_palworld_config_form_values(self, text: str):
        for key, _label, kind in PALWORLD_CONFIG_FIELDS:
            value = self.parse_palworld_setting(text, key)
            if value is None:
                value = ""
            self.palworld_config_vars[key].set(value)

    def load_palworld_config_form(self, silent=False):
        self.sync_palworld_path_vars()
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            if not silent:
                messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            if not silent:
                messagebox.showerror(APP_NAME, f"Could not load Palworld config:\n{exc}")
            return
        self.set_palworld_config_form_values(text)
        self.palworld_config_text.configure(state="normal")
        self.palworld_config_text.delete("1.0", "end")
        self.palworld_config_text.insert("1.0", text)
        self.palworld_config_text.edit_reset()
        if not silent:
            self.log(f"Loaded Palworld config into form: {config_path}")

    def palworld_config_value_for_save(self, key: str, kind: str) -> str:
        value = self.palworld_config_vars[key].get().strip()
        if kind == "text":
            return '"' + value.replace('"', '\\"') + '"'
        return value

    def save_palworld_config_form(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            messagebox.showwarning(APP_NAME, "Stop the Palworld server before editing PalWorldSettings.ini.")
            return
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
            if "OptionSettings=(" not in text:
                raise ValueError("OptionSettings block not found")
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            for key, _label, kind in PALWORLD_CONFIG_FIELDS:
                value = self.palworld_config_value_for_save(key, kind)
                if value or kind == "text":
                    text = self.replace_palworld_setting(text, key, value)
            config_path.write_text(text, encoding="utf-8")
            self.load_palworld_config_form(silent=True)
            self.log(f"Saved Palworld config form: {config_path}")
            messagebox.showinfo(APP_NAME, f"Palworld config saved.\nBackup created:\n{backup_path}")
        except (OSError, ValueError) as exc:
            self.log(f"Palworld config form save failed: {exc}")
            messagebox.showerror(APP_NAME, f"Palworld config form save failed:\n{exc}")

    def save_palworld_config(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            messagebox.showwarning(APP_NAME, "Stop the Palworld server before editing PalWorldSettings.ini.")
            return
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        text = self.palworld_config_text.get("1.0", "end-1c")
        if "OptionSettings=(" not in text:
            messagebox.showerror(APP_NAME, "The Palworld config does not contain an OptionSettings block. Load the official PalWorldSettings.ini first.")
            return
        try:
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            config_path.write_text(text, encoding="utf-8")
            self.log(f"Saved Palworld config: {config_path}")
            messagebox.showinfo(APP_NAME, f"Palworld config saved.\nBackup created:\n{backup_path}")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Palworld config save failed:\n{exc}")

    def open_palworld_config_notepad(self):
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        try:
            subprocess.Popen(["notepad.exe", str(config_path)])
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open Notepad:\n{exc}")

    def replace_palworld_setting(self, text: str, key: str, value: str) -> str:
        pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(key)}\s*=\s*(\"(?:\\.|[^\"])*\"|[^,\)\r\n]+)", re.IGNORECASE)
        replacement = f"{key}={value}"
        if pattern.search(text):
            return pattern.sub(replacement, text, count=1)
        option_end = text.find(")", text.find("OptionSettings=("))
        if option_end < 0:
            return text
        insert_at = option_end
        prefix = "," if insert_at > 0 and text[insert_at - 1] != "(" else ""
        return text[:insert_at] + prefix + replacement + text[insert_at:]

    def apply_palworld_kid_friendly_preset(self):
        self.sync_palworld_path_vars()
        if self.is_palworld_running():
            messagebox.showwarning(APP_NAME, "Stop the Palworld server before applying the creative preset.")
            return
        config_path = self.path("palworld_server_config_path")
        if not config_path.exists():
            messagebox.showerror(APP_NAME, f"Palworld config file not found:\n{config_path}")
            return
        if not messagebox.askyesno(APP_NAME, "Apply the kid-friendly creative preset?\n\nThis backs up PalWorldSettings.ini, then sets unlimited building, no death drops, no hardcore mode, no Pal loss, and easier captures."):
            return
        try:
            text = config_path.read_text(encoding="utf-8", errors="replace")
            if "OptionSettings=(" not in text:
                raise ValueError("OptionSettings block not found")
            backup_path = config_path.with_name(f"{config_path.stem}.backup_{now_stamp()}{config_path.suffix}")
            shutil.copy2(config_path, backup_path)
            for key, value in {
                "MaxBuildingLimitNum": "0",
                "DeathPenalty": "None",
                "bHardcore": "False",
                "bPalLost": "False",
                "PalCaptureRate": "3.0",
            }.items():
                text = self.replace_palworld_setting(text, key, value)
            config_path.write_text(text, encoding="utf-8")
            self.load_palworld_config()
            self.log(f"Applied Palworld kid-friendly preset. Config backup: {backup_path}")
            messagebox.showinfo(APP_NAME, "Kid-friendly creative preset applied.\n\nUnlimited Palballs are not a native Palworld config option; use an admin/mod solution separately if you need unlimited item grants.")
        except (OSError, ValueError) as exc:
            messagebox.showerror(APP_NAME, f"Could not apply Palworld preset:\n{exc}")

    def palworld_rest_request(self, method: str, endpoint: str, payload=None, timeout=5):
        base = str(self.settings.get("palworld_rest_base_url", "http://127.0.0.1:8212/v1/api")).strip().rstrip("/")
        if not base:
            raise ValueError("Palworld REST base URL is empty")
        urls = [f"{base}/{endpoint.lstrip('/')}" ]
        if "/v1/api" in base.lower():
            urls.append(f"{base[:base.lower().rfind('/v1/api')]}/{endpoint.lstrip('/')}" )
        username = str(self.settings.get("palworld_rest_username", "admin"))
        password = str(self.settings.get("palworld_admin_password", ""))
        headers = {"User-Agent": APP_NAME, "Accept": "application/json"}
        if username or password:
            token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        last_error = None
        for index, url in enumerate(urls):
            request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    try:
                        parsed = json.loads(raw) if raw else {}
                    except json.JSONDecodeError:
                        parsed = {"text": raw}
                    return response.status, parsed
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 404 and index + 1 < len(urls):
                    continue
                raise
            except urllib.error.URLError as exc:
                last_error = exc
                raise
        raise last_error or OSError("Palworld REST request failed")

    def test_palworld_rest_api(self):
        self.save_palworld_settings_values(write_file=True)
        def work():
            try:
                status, _ = self.palworld_rest_request("GET", "metrics")
                self.log(f"Palworld REST API test succeeded with HTTP {status}.")
                self.after(0, messagebox.showinfo, APP_NAME, f"Palworld REST API is reachable. HTTP {status}.")
            except (OSError, urllib.error.URLError, ValueError) as exc:
                self.log(f"Palworld REST API test failed: {exc}")
                self.after(0, messagebox.showerror, APP_NAME, f"Palworld REST API test failed:\n{exc}")
        threading.Thread(target=work, daemon=True).start()

    def save_palworld_world(self):
        self.save_palworld_settings_values(write_file=True)
        def work():
            try:
                status, _ = self.palworld_rest_request("POST", "save")
                self.log(f"Palworld world save requested through REST API: HTTP {status}.")
                self.after(0, messagebox.showinfo, APP_NAME, "Palworld world save requested.")
            except (OSError, urllib.error.URLError, ValueError) as exc:
                self.log(f"Palworld REST save failed: {exc}")
                self.after(0, messagebox.showerror, APP_NAME, f"Palworld REST save failed:\n{exc}\n\nEnable RESTAPIEnabled=True and configure the admin password.")
        threading.Thread(target=work, daemon=True).start()

    def sync_palworld_path_vars(self):
        for key, var in self.palworld_path_vars.items():
            self.settings[key] = var.get()
        write_json(SETTINGS_FILE, self.settings)

    def apply_palworld_settings_to_ui(self):
        for key, var in self.palworld_path_vars.items():
            var.set(str(self.settings.get(key, "")))

    def detect_palworld_install_from_steam(self):
        for steamapps in self.steam_library_paths():
            manifest = steamapps / f"appmanifest_{PALWORLD_DEDICATED_SERVER_APP_ID}.acf"
            if not manifest.exists():
                continue
            installdir = "PalServer"
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
                match = re.search(r'"installdir"\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    installdir = match.group(1)
            except OSError:
                pass
            install_path = steamapps / "common" / installdir
            if (install_path / PALWORLD_EXE_NAME).exists() or install_path.exists():
                return install_path
        return None

    def detect_palworld_install_from_process(self):
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name PalServer -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            path_text = result.stdout.strip()
            if path_text:
                path = Path(path_text)
                if path.exists():
                    return path.parent
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def autodetect_palworld_paths(self):
        detected = {}
        install_path = self.detect_palworld_install_from_process() or self.detect_palworld_install_from_steam()
        if install_path:
            detected["palworld_server_install_path"] = str(install_path)
            detected["palworld_server_exe_path"] = str(install_path / PALWORLD_EXE_NAME)
            detected["palworld_server_config_path"] = str(install_path / "Pal" / "Saved" / "Config" / "WindowsServer" / "PalWorldSettings.ini")
            detected["palworld_save_folder_path"] = str(install_path / "Pal" / "Saved" / "SaveGames")
        detected["palworld_backup_folder_path"] = self.palworld_path_vars.get("palworld_backup_folder_path", tk.StringVar(value=str(DEFAULT_PALWORLD_BACKUPS))).get() or str(DEFAULT_PALWORLD_BACKUPS)
        steamcmd_path = self.detect_steamcmd_path()
        if steamcmd_path:
            detected["steamcmd_path"] = str(steamcmd_path)
        for key, value in detected.items():
            if key in self.palworld_path_vars:
                self.palworld_path_vars[key].set(value)
            self.settings[key] = value
        write_json(SETTINGS_FILE, self.settings)
        self.refresh_palworld_status()
        self.refresh_palworld_dashboard()
        message = "Detected Palworld Dedicated Server paths and saved them." if install_path else "Could not auto-detect Palworld. Start PalServer once or browse to the install folder manually."
        if not steamcmd_path:
            message += "\n\nSteamCMD was not found. Set SteamCMD executable in Settings if you want server updates."
        self.log(f"Palworld auto-detect paths result: {detected}")
        messagebox.showinfo(APP_NAME, message)

    def save_palworld_settings_values(self, write_file=False):
        self.sync_palworld_path_vars()
        if self.palworld_rest_url_var:
            self.settings["palworld_rest_base_url"] = self.palworld_rest_url_var.get().strip()
            self.settings["palworld_rest_username"] = self.palworld_rest_user_var.get().strip()
            self.settings["palworld_admin_password"] = self.palworld_rest_password_var.get()
            self.settings["palworld_auto_restart_server"] = self.palworld_auto_restart_var.get()
            self.save_discord_settings_values()
        if write_file:
            write_json(SETTINGS_FILE, self.settings)

    def save_palworld_settings_and_start_discord(self):
        self.save_discord_settings_and_start()

    def save_discord_settings_values(self):
        self.ensure_discord_vars()
        values = {
            "monitor_enabled": self.discord_enabled_var.get(),
            "bot_token": self.discord_token_var.get().strip(),
            "channel_id": self.discord_channel_var.get().strip(),
            "webhook_url": self.discord_webhook_var.get().strip(),
            "allowed_user_ids": self.discord_allowed_users_var.get().strip(),
        }
        for name, value in values.items():
            self.settings[f"discord_{name}"] = value
            self.settings[f"palworld_discord_{name}"] = value

    def save_discord_settings_and_start(self):
        self.save_discord_settings_values()
        write_json(SETTINGS_FILE, self.settings)
        self.start_discord_monitor()
        self.log("Shared Discord settings saved and monitor refreshed.")
        messagebox.showinfo(APP_NAME, "Discord settings saved. The monitor starts only when enabled and both the bot token and channel ID are set.")

    def send_discord_webhook(self, message: str):
        webhook = str(self.get_discord_setting("webhook_url", "")).strip()
        if not webhook:
            return
        try:
            body = json.dumps({"content": message[:1900]}).encode("utf-8")
            request = urllib.request.Request(webhook, data=body, headers={"Content-Type": "application/json", "User-Agent": APP_NAME}, method="POST")
            with urllib.request.urlopen(request, timeout=10):
                pass
        except (OSError, urllib.error.URLError) as exc:
            self.log(f"Discord webhook failed: {exc}")

    def send_discord_channel_message(self, message: str):
        token = str(self.get_discord_setting("bot_token", "")).strip()
        channel_id = str(self.get_discord_setting("channel_id", "")).strip()
        if not token or not channel_id:
            self.send_discord_webhook(message)
            return
        try:
            body = json.dumps({"content": message[:1900]}).encode("utf-8")
            request = urllib.request.Request(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                data=body,
                headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": APP_NAME},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=10):
                pass
        except (OSError, urllib.error.URLError) as exc:
            self.log(f"Discord channel reply failed: {exc}")

    def start_discord_monitor(self):
        self.discord_monitor_stop.set()
        if self.discord_monitor_thread and self.discord_monitor_thread.is_alive():
            self.discord_monitor_thread.join(timeout=1)
        self.discord_monitor_thread = None
        if not self.get_discord_setting("monitor_enabled", False):
            return
        if not self.get_discord_setting("bot_token", "") or not self.get_discord_setting("channel_id", ""):
            self.log("Discord monitor not started: bot token or channel ID is missing.")
            return
        self.discord_monitor_stop.clear()
        self.discord_monitor_thread = threading.Thread(target=self.discord_monitor_loop, daemon=True)
        self.discord_monitor_thread.start()
        self.log("Shared Discord monitor started for Palworld, Windrose, Abiotic Factor, and Minecraft.")

    def start_palworld_discord_monitor(self):
        self.start_discord_monitor()

    def discord_monitor_loop(self):
        while not self.discord_monitor_stop.is_set():
            self.poll_discord_once()
            self.discord_monitor_stop.wait(10)

    def palworld_discord_monitor_loop(self):
        self.discord_monitor_loop()

    def poll_discord_once(self):
        token = str(self.get_discord_setting("bot_token", "")).strip()
        channel_id = str(self.get_discord_setting("channel_id", "")).strip()
        if not token or not channel_id:
            return
        last_id = str(self.get_discord_setting("last_message_id", "")).strip()
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=50"
        if last_id:
            url += f"&after={last_id}"
        request = urllib.request.Request(url, headers={"Authorization": f"Bot {token}", "User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                messages = json.loads(response.read().decode("utf-8", errors="replace"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Discord monitor poll failed: {exc}")
            return
        if not isinstance(messages, list) or not messages:
            return
        messages = sorted(messages, key=lambda item: int(item.get("id", "0")))
        if not last_id:
            newest = str(messages[-1].get("id", ""))
            self.settings["discord_last_message_id"] = newest
            self.settings["palworld_discord_last_message_id"] = newest
            write_json(SETTINGS_FILE, self.settings)
            self.log("Discord monitor baselined existing channel messages.")
            return
        allowed = {item.strip() for item in re.split(r"[,\s]+", str(self.get_discord_setting("allowed_user_ids", ""))) if item.strip()}
        for message in messages:
            message_id = str(message.get("id", ""))
            if message_id == last_id:
                continue
            author = message.get("author") or {}
            if not author.get("bot"):
                author_id = str(author.get("id", ""))
                if not allowed or author_id in allowed:
                    self.handle_discord_command(str(message.get("content", "")), author_id)
                else:
                    self.log(f"Ignored Discord command from unauthorized user {author_id}.")
            self.settings["discord_last_message_id"] = message_id
            self.settings["palworld_discord_last_message_id"] = message_id
        write_json(SETTINGS_FILE, self.settings)

    def poll_palworld_discord_once(self):
        self.poll_discord_once()

    def handle_discord_command(self, content: str, author_id=""):
        parts = content.strip().split()
        if len(parts) < 2:
            return
        target = parts[0].lower().lstrip("!/")
        command = parts[1].lower()
        if target in {"palworld", "pal"}:
            self.handle_palworld_discord_command(command, author_id)
        elif target == "windrose":
            self.handle_windrose_discord_command(command, author_id)
        elif target in {"abiotic", "abioticfactor", "abiotic-factor"}:
            self.handle_abiotic_discord_command(command, author_id, parts[2:])
        elif target in {"minecraft", "mc"}:
            self.handle_minecraft_discord_command(command, author_id)

    def handle_palworld_discord_command(self, command: str, author_id=""):
        if command == "status":
            status = "running" if self.is_palworld_running() else "stopped"
            self.send_discord_channel_message(f"Palworld is currently **{status}**.")
        elif command == "restart":
            self.send_discord_channel_message("Palworld restart requested.")
            self.after(0, self.restart_palworld_server)
        elif command == "start":
            self.send_discord_channel_message("Palworld start requested.")
            self.after(0, self.start_palworld_server)
        elif command == "stop":
            self.send_discord_channel_message("Palworld stop requested.")
            self.after(0, self.stop_palworld_server)
        elif command == "backup":
            self.send_discord_channel_message("Palworld backup requested.")
            self.after(0, self.backup_palworld_now)
        elif command == "save":
            self.send_discord_channel_message("Palworld world save requested.")
            self.after(0, self.save_palworld_world)
        elif command == "help":
            self.send_discord_channel_message("Commands: !palworld status, restart, start, stop, backup, save, help")
        else:
            return
        self.log(f"Discord Palworld command handled: {command} (user {author_id or 'unknown'}).")

    def handle_windrose_discord_command(self, command: str, author_id=""):
        if command == "status":
            status = "running" if self.is_windrose_running() else "stopped"
            self.send_discord_channel_message(f"Windrose is currently **{status}**.")
        elif command == "restart":
            self.send_discord_channel_message("Windrose restart requested.")
            self.after(0, lambda: self.restart_windrose_server(ask_force=False))
        elif command == "start":
            self.send_discord_channel_message("Windrose start requested.")
            self.after(0, self.start_windrose_server)
        elif command == "stop":
            self.send_discord_channel_message("Windrose stop requested.")
            self.after(0, lambda: self.stop_windrose_server(ask_force=False))
        elif command == "backup":
            self.send_discord_channel_message("Windrose backup requested.")
            self.after(0, lambda: self.run_threaded("Windrose backup", self.create_windrose_backup))
        elif command == "help":
            self.send_discord_channel_message("Commands: !windrose status, restart, start, stop, backup, help")
        else:
            return
        self.log(f"Discord Windrose command handled: {command} (user {author_id or 'unknown'}).")

    def handle_abiotic_discord_command(self, command: str, author_id="", arguments=None):
        arguments = arguments or []
        if command == "status":
            status = "running" if self.is_abiotic_running() else "stopped"
            self.send_discord_channel_message(f"Abiotic Factor is currently **{status}**.")
        elif command == "restart":
            self.send_discord_channel_message("Abiotic Factor restart requested.")
            self.after(0, lambda: self.restart_abiotic_server(ask_force=False))
        elif command == "start":
            self.send_discord_channel_message("Abiotic Factor start requested.")
            self.after(0, self.start_abiotic_server)
        elif command == "stop":
            self.send_discord_channel_message("Abiotic Factor stop requested.")
            self.after(0, lambda: self.stop_abiotic_server(ask_force=False))
        elif command == "backup":
            self.send_discord_channel_message("Abiotic Factor backup requested. Backups are refused while the server is running.")
            self.after(0, self.backup_abiotic_now)
        elif command in {"settings", "config"}:
            self.send_discord_channel_message(self.abiotic_discord_settings_summary())
        elif command in {"preset", "apply"}:
            preset = str(arguments[0]).lower() if arguments else "qol"
            if preset != "qol":
                self.send_discord_channel_message("Available Abiotic Factor preset: qol")
                return
            self.send_discord_channel_message("Abiotic Factor QoL preset requested. The server must be stopped and a backup will be created first.")
            self.after(0, lambda: self.run_threaded("Abiotic Factor Discord QoL preset", lambda: self.apply_abiotic_qol_preset(show_dialog=False)))
        elif command == "restore":
            if not arguments or str(arguments[0]).lower() != "latest":
                self.send_discord_channel_message("Use: !abiotic restore latest")
                return
            self.send_discord_channel_message("Abiotic Factor latest-backup restore requested. The server must be stopped and an emergency backup will be created first.")
            self.after(0, lambda: self.restore_latest_abiotic_backup(show_dialog=False))
        elif command == "help":
            self.send_discord_channel_message("Commands: !abiotic status, restart, start, stop, backup, settings, preset qol, restore latest, help")
        else:
            return
        self.log(f"Discord Abiotic Factor command handled: {command} (user {author_id or 'unknown'}).")

    def get_abiotic_process_text(self):
        return self.get_named_process_text(ABIOTIC_EXE_NAME, ABIOTIC_PROCESS_NAME)

    def is_abiotic_running(self) -> bool:
        return self.get_abiotic_process_text() is not None

    def refresh_abiotic_status(self):
        if not self.abiotic_vars:
            return
        process_text = self.get_abiotic_process_text()
        running = process_text is not None
        self.abiotic_vars["status"].set("Running" if running else "Stopped")
        self.abiotic_vars["detected_process"].set(process_text or "None")
        if hasattr(self, "abiotic_status_label"):
            self.abiotic_status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])
        if self.abiotic_start_button:
            self.abiotic_start_button.configure(style="TButton" if running else "Green.TButton")
        if self.abiotic_stop_button:
            self.abiotic_stop_button.configure(style="Danger.TButton" if running else "TButton")

    def refresh_abiotic_dashboard(self):
        if not self.abiotic_vars:
            return
        backups = self.list_abiotic_backups()
        self.abiotic_vars["install_path"].set(str(self.path("abiotic_server_install_path")))
        self.abiotic_vars["executable_path"].set(str(self.path("abiotic_server_exe_path")))
        self.abiotic_vars["config_path"].set(str(self.path("abiotic_server_config_path")))
        self.abiotic_vars["save_folder_path"].set(str(self.path("abiotic_save_folder_path")))
        self.abiotic_vars["backup_folder_path"].set(str(self.path("abiotic_backup_folder_path")))
        self.abiotic_vars["backup_count"].set(str(len(backups)))
        self.abiotic_vars["last_backup"].set(backups[0][1].strftime("%Y-%m-%d %H:%M") if backups else "No backups found")

    def create_abiotic_backup(self, prefix_override=None, show_missing_error=True) -> Path | None:
        if threading.get_ident() == self.main_thread_id:
            self.sync_abiotic_path_vars()
        if self.is_abiotic_running():
            self.log("Abiotic Factor backup refused: server is running; stop it first for a consistent world copy.")
            if show_missing_error:
                self.after(0, messagebox.showwarning, APP_NAME, "Stop the Abiotic Factor server before creating a backup.")
            return None
        save_dir = self.path("abiotic_save_folder_path")
        sandbox_path = self.path("abiotic_sandbox_settings_path")
        config_dir = self.path("abiotic_server_config_path")
        admin_path = self.path("abiotic_server_install_path") / "AbioticFactor" / "Saved" / "SaveGames" / "Server" / "Admin.ini"
        backup_dir = self.path("abiotic_backup_folder_path")
        if not save_dir.exists() and not config_dir.exists() and not admin_path.exists():
            if show_missing_error:
                self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor save/config paths do not exist yet:\n{save_dir}\n{sandbox_path}")
            self.log(f"Abiotic Factor backup skipped: save/config missing: {save_dir}; {sandbox_path}")
            return None
        if save_dir.exists() and not self.validate_safe_folder(save_dir, "Abiotic Factor save folder"):
            return None
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            prefix = prefix_override or "abiotic_backup_"
            target = backup_dir / f"{prefix}{now_stamp()}"
            counter = 1
            while target.exists():
                target = backup_dir / f"{prefix}{now_stamp()}_{counter}"
                counter += 1
            target.mkdir(parents=True)
            if save_dir.exists():
                shutil.copytree(save_dir, target / "save")
            if config_dir.exists() and config_dir.is_dir():
                shutil.copytree(config_dir, target / "config")
            elif sandbox_path.exists() and sandbox_path.is_file():
                shutil.copy2(sandbox_path, target / sandbox_path.name)
            if admin_path.exists() and admin_path.is_file():
                shutil.copy2(admin_path, target / admin_path.name)
            (target / "backup_manifest.json").write_text(json.dumps({
                "server": "Abiotic Factor",
                "created": datetime.now().isoformat(timespec="seconds"),
                "save_folder": str(save_dir),
                "config_folder": str(config_dir),
                "admin_file": str(admin_path),
            }, indent=2), encoding="utf-8")
            self.log(f"Abiotic Factor backup created: {target}")
            self.after(0, self.refresh_abiotic_dashboard)
            self.after(0, self.refresh_backups)
            return target
        except OSError as exc:
            self.log(f"Abiotic Factor backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor backup failed:\n{exc}")
            return None

    def backup_abiotic_now(self):
        self.sync_abiotic_path_vars()
        self.run_threaded("Abiotic Factor backup", self.create_abiotic_backup)

    def list_abiotic_backups(self):
        backup_dir = self.path("abiotic_backup_folder_path")
        if not backup_dir.exists():
            return []
        items = []
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
            for prefix in ["abiotic_backup_", "before_abiotic_update_", "before_abiotic_settings_", "before_abiotic_preset_", "before_abiotic_restart_", "emergency_before_abiotic_restore_"]:
                if item.name.startswith(prefix):
                    try:
                        items.append((item, datetime.strptime(item.name.removeprefix(prefix)[:16], BACKUP_TIME_FORMAT)))
                    except ValueError:
                        pass
                    break
        return sorted(items, key=lambda row: row[1], reverse=True)

    def restore_selected_abiotic_backup(self, backup_path: Path, show_dialog=True):
        if self.is_abiotic_running():
            if show_dialog:
                messagebox.showwarning(APP_NAME, "Stop the Abiotic Factor server before restoring a backup.")
            self.log("Abiotic Factor restore refused: server is running.")
            return False
        backup_root = self.path("abiotic_backup_folder_path").resolve()
        try:
            if backup_path.resolve().parent != backup_root or not backup_path.is_dir():
                raise ValueError("The selected backup is outside the configured Abiotic Factor backup folder.")
        except OSError as exc:
            if show_dialog:
                messagebox.showerror(APP_NAME, f"Could not validate the selected backup:\n{exc}")
            return False
        if not (backup_path / "save").exists() and not (backup_path / "config").exists() and not (backup_path / "SandboxSettings.ini").exists():
            if show_dialog:
                messagebox.showerror(APP_NAME, "This folder is not a recognised Abiotic Factor backup.")
            return False
        if show_dialog and not messagebox.askyesno(APP_NAME, f"Restore Abiotic Factor backup?\n\n{backup_path.name}\n\nAn emergency backup will be created first."):
            return False
        self.run_threaded("Abiotic Factor restore", lambda: self.restore_abiotic_backup(backup_path, show_dialog=show_dialog))
        return True

    def restore_abiotic_backup(self, backup_path: Path, show_dialog=True):
        save_dir = self.path("abiotic_save_folder_path")
        config_dir = self.path("abiotic_server_config_path")
        if not self.validate_safe_folder(save_dir, "Abiotic Factor save folder") or not self.validate_safe_folder(config_dir, "Abiotic Factor config folder"):
            return False
        emergency = self.create_abiotic_backup(prefix_override="emergency_before_abiotic_restore_", show_missing_error=False)
        if emergency is None and (save_dir.exists() or config_dir.exists()):
            self.log("Abiotic Factor restore aborted: emergency backup failed.")
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, "Restore aborted because the emergency backup failed.")
            return False
        try:
            save_backup = backup_path / "save"
            if save_backup.exists():
                if save_dir.exists():
                    shutil.rmtree(save_dir)
                shutil.copytree(save_backup, save_dir)
            config_backup = backup_path / "config"
            if config_backup.exists():
                if config_dir.exists():
                    shutil.rmtree(config_dir)
                shutil.copytree(config_backup, config_dir)
            else:
                sandbox_backup = backup_path / "SandboxSettings.ini"
                if sandbox_backup.exists():
                    config_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(sandbox_backup, self.path("abiotic_sandbox_settings_path"))
            admin_backup = backup_path / "Admin.ini"
            admin_path = self.path("abiotic_server_install_path") / "AbioticFactor" / "Saved" / "SaveGames" / "Server" / "Admin.ini"
            if admin_backup.exists():
                admin_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(admin_backup, admin_path)
            self.log(f"Abiotic Factor backup restored: {backup_path}")
            self.after(0, self.load_abiotic_sandbox_settings, True)
            self.after(0, self.refresh_all)
            if show_dialog:
                self.after(0, messagebox.showinfo, APP_NAME, f"Abiotic Factor backup restored successfully.\n\nEmergency backup:\n{emergency or 'not required'}")
            return True
        except OSError as exc:
            self.log(f"Abiotic Factor restore failed: {exc}")
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor restore failed:\n{exc}")
            return False

    def restore_latest_abiotic_backup(self, show_dialog=False):
        backups = self.list_abiotic_backups()
        if not backups:
            self.log("Abiotic Factor restore skipped: no backups found.")
            if show_dialog:
                messagebox.showinfo(APP_NAME, "No Abiotic Factor backups were found.")
            return False
        return self.restore_selected_abiotic_backup(backups[0][0], show_dialog=show_dialog)

    def start_abiotic_server(self):
        self.sync_abiotic_path_vars()
        if self.is_abiotic_running():
            self.abiotic_should_be_running = True
            messagebox.showinfo(APP_NAME, "The Abiotic Factor server is already running.")
            return
        executable = self.path("abiotic_server_exe_path")
        if not executable.exists():
            executable = self.path("abiotic_server_install_path") / "AbioticFactor" / "Binaries" / "Win64" / ABIOTIC_EXE_NAME
        if not executable.exists():
            messagebox.showerror(APP_NAME, f"Abiotic Factor server executable not found:\n{executable}\n\nInstall the server first or update the executable path.")
            self.log(f"Abiotic Factor start failed: executable not found: {executable}")
            return
        try:
            command = [
                str(executable),
                "-PORT=" + str(self.settings.get("abiotic_server_port", "9876")),
                "-QueryPort=" + str(self.settings.get("abiotic_query_port", "25575")),
                "-SteamServerName=" + str(self.settings.get("abiotic_server_name", "fleshraiders")),
                "-ServerPassword=" + str(self.settings.get("abiotic_server_password", "flesh123")),
            ]
            sandbox_path = self.path("abiotic_sandbox_settings_path")
            saved_root = self.path("abiotic_server_install_path") / "AbioticFactor" / "Saved"
            try:
                sandbox_argument = sandbox_path.relative_to(saved_root).as_posix()
            except ValueError:
                sandbox_argument = ""
            if sandbox_argument:
                command.append("-SandboxIniPath=" + sandbox_argument)
            subprocess.Popen(command, cwd=str(executable.parent), creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.abiotic_should_be_running = True
            self.log("Abiotic Factor server start requested.")
            self.after(2500, self.refresh_abiotic_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start Abiotic Factor server:\n{exc}")
            self.log(f"Abiotic Factor start failed: {exc}")

    def stop_abiotic_server(self, ask_force=True) -> bool:
        self.abiotic_should_be_running = False
        if not self.is_abiotic_running():
            self.log("Abiotic Factor stop skipped: server is not running.")
            self.refresh_abiotic_status()
            return True
        self.log("Abiotic Factor server stop requested.")
        try:
            subprocess.run(["taskkill", "/IM", ABIOTIC_EXE_NAME, "/T"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            self.log(f"Abiotic Factor graceful stop command failed: {exc}")
        deadline = time.time() + 15
        while time.time() < deadline:
            if not self.is_abiotic_running():
                self.log("Abiotic Factor server stopped.")
                self.refresh_abiotic_status()
                return True
            time.sleep(1)
        if ask_force and messagebox.askyesno(APP_NAME, "Abiotic Factor did not stop within 15 seconds. Force kill it?"):
            try:
                subprocess.run(["taskkill", "/F", "/IM", ABIOTIC_EXE_NAME, "/T"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                self.log("Abiotic Factor server force kill requested.")
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Abiotic Factor force kill failed: {exc}")
                messagebox.showerror(APP_NAME, f"Abiotic Factor force kill failed:\n{exc}")
                return False
            self.after(1500, self.refresh_abiotic_status)
            return True
        self.log("Abiotic Factor stop incomplete: server is still running.")
        return False

    def restart_abiotic_server(self, ask_force=True):
        def work():
            if self.stop_abiotic_server(ask_force=ask_force):
                if self.settings.get("abiotic_backup_before_restart", True):
                    backup = self.create_abiotic_backup(prefix_override="before_abiotic_restart_", show_missing_error=False)
                    if backup is None:
                        self.log("Abiotic Factor restart aborted: pre-restart backup failed.")
                        return
                time.sleep(3)
                self.abiotic_should_be_running = True
                self.after(0, self.start_abiotic_server)
        threading.Thread(target=work, daemon=True).start()

    def abiotic_appmanifest_path(self) -> Path:
        install_dir = self.path("abiotic_server_install_path")
        manifest_name = f"appmanifest_{ABIOTIC_DEDICATED_SERVER_APP_ID}.acf"
        standard_manifest = install_dir.parent.parent / manifest_name
        if standard_manifest.exists():
            return standard_manifest
        return install_dir / "steamapps" / manifest_name

    def local_abiotic_build_id(self) -> str:
        manifest = self.abiotic_appmanifest_path()
        if not manifest.exists():
            return ""
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r'"buildid"\s+"(\d+)"', text, re.IGNORECASE)
        return match.group(1) if match else ""

    def check_abiotic_update(self, show_dialog=True):
        if not self.abiotic_vars:
            return
        self.abiotic_vars["update_status"].set("Checking...")
        build_id = self.local_abiotic_build_id()
        manifest = self.abiotic_appmanifest_path()
        if not build_id:
            self.abiotic_vars["update_status"].set("Unknown - app manifest not found")
            self.set_abiotic_update_button_available(False)
            if show_dialog:
                messagebox.showerror(APP_NAME, f"Could not find the local Abiotic Factor Dedicated Server build ID.\n\nExpected Steam app manifest:\n{manifest}")
            self.log(f"Abiotic Factor update check failed: build ID not found in {manifest}")
            return
        self.run_threaded("Abiotic Factor Steam update check", lambda: self.do_check_abiotic_update(build_id, show_dialog=show_dialog))

    def do_check_abiotic_update(self, build_id: str, show_dialog=True):
        url = "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/" f"?appid={ABIOTIC_DEDICATED_SERVER_APP_ID}&version={build_id}"
        request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8", errors="replace")).get("response", {})
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Abiotic Factor update check failed: {exc}")
            self.after(0, self.abiotic_vars["update_status"].set, "Check failed")
            self.after(0, self.set_abiotic_update_button_available, False)
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor update check failed:\n{exc}")
            return
        if result.get("success") is False:
            error_text = result.get("error") or "Steam did not return update information."
            self.after(0, self.abiotic_vars["update_status"].set, f"Check unavailable - {error_text}")
            self.after(0, self.set_abiotic_update_button_available, False)
            return
        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        status_text = f"Server is up to date - build {build_id}" if up_to_date else f"Update available - local {build_id}, latest {required}"
        self.after(0, self.abiotic_vars["update_status"].set, status_text)
        self.after(0, self.set_abiotic_update_button_available, (not up_to_date) and required != "unknown")
        if show_dialog:
            message = f"Abiotic Factor Dedicated Server is up to date.\n\nLocal build: {build_id}" if up_to_date else f"Abiotic Factor Dedicated Server update appears available.\n\nLocal build: {build_id}\nRequired build: {required}"
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def set_abiotic_update_button_available(self, available: bool):
        if self.abiotic_update_button:
            self.abiotic_update_button.configure(style="Green.TButton" if available else "TButton")

    def update_abiotic_server_with_steamcmd(self):
        self.sync_abiotic_path_vars()
        if self.is_abiotic_running():
            messagebox.showwarning(APP_NAME, "Stop the Abiotic Factor server before running a SteamCMD update.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("abiotic_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not install_dir.exists():
            messagebox.showerror(APP_NAME, f"Abiotic Factor install folder was not found:\n{install_dir}")
            return
        if messagebox.askyesno(APP_NAME, "Update Abiotic Factor Dedicated Server with SteamCMD?"):
            self.run_threaded("Abiotic Factor SteamCMD server update", self.do_update_abiotic_server_with_steamcmd)

    def install_abiotic_server_with_steamcmd(self):
        self.sync_abiotic_path_vars()
        if self.is_abiotic_running():
            messagebox.showwarning(APP_NAME, "Stop the Abiotic Factor server before installing or repairing it with SteamCMD.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("abiotic_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not self.validate_safe_folder(install_dir, "Abiotic Factor install folder"):
            return
        if messagebox.askyesno(APP_NAME, f"Install or repair Abiotic Factor Dedicated Server with SteamCMD?\n\nInstall folder:\n{install_dir}\n\nThis downloads Steam app {ABIOTIC_DEDICATED_SERVER_APP_ID}."):
            self.run_threaded("Abiotic Factor SteamCMD server install", self.do_install_abiotic_server_with_steamcmd)

    def do_install_abiotic_server_with_steamcmd(self):
        install_dir = self.path("abiotic_server_install_path")
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.after(0, messagebox.showerror, APP_NAME, f"Could not create Abiotic Factor install folder:\n{exc}")
            return
        exit_code = self.run_abiotic_steamcmd(self.path("steamcmd_path"), install_dir, "install")
        if exit_code == 0:
            self.settings["abiotic_server_exe_path"] = str(install_dir / "AbioticFactor" / "Binaries" / "Win64" / ABIOTIC_EXE_NAME)
            self.settings["abiotic_server_config_path"] = str(install_dir / "AbioticFactor" / "Saved" / "Config" / "WindowsServer")
            self.settings["abiotic_sandbox_settings_path"] = str(install_dir / "AbioticFactor" / "Saved" / "Config" / "WindowsServer" / "SandboxSettings.ini")
            self.settings["abiotic_save_folder_path"] = str(install_dir / "AbioticFactor" / "Saved" / "SaveGames" / "Server" / "Worlds")
            write_json(SETTINGS_FILE, self.settings)
            self.after(0, self.apply_abiotic_settings_to_ui)
            self.after(0, self.refresh_abiotic_dashboard)
            self.after(0, self.check_abiotic_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Abiotic Factor Dedicated Server install/repair complete. The server was not started.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor SteamCMD install exited with code {exit_code}. Check Logs.")

    def do_update_abiotic_server_with_steamcmd(self):
        self.create_abiotic_backup(prefix_override="before_abiotic_update_", show_missing_error=False)
        exit_code = self.run_abiotic_steamcmd(self.path("steamcmd_path"), self.path("abiotic_server_install_path"), "update")
        if exit_code == 0:
            self.after(0, self.check_abiotic_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Abiotic Factor Dedicated Server update complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor SteamCMD update exited with code {exit_code}. Check Logs.")

    def run_abiotic_steamcmd(self, steamcmd: Path, install_dir: Path, action_label: str) -> int:
        command = [str(steamcmd), "+force_install_dir", str(install_dir), "+login", "anonymous", "+app_update", ABIOTIC_DEDICATED_SERVER_APP_ID, "validate", "+quit"]
        self.log(f"Running SteamCMD {action_label} for Abiotic Factor Dedicated Server app {ABIOTIC_DEDICATED_SERVER_APP_ID}.")
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(steamcmd.parent), creationflags=subprocess.CREATE_NO_WINDOW)
            assert process.stdout is not None
            for line in process.stdout:
                clean = line.rstrip()
                if clean:
                    self.log(f"Abiotic Factor SteamCMD: {clean}")
            return process.wait()
        except OSError as exc:
            self.log(f"Abiotic Factor SteamCMD {action_label} failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Abiotic Factor SteamCMD {action_label} failed:\n{exc}")
            return 1

    def sync_abiotic_path_vars(self):
        for key, var in self.abiotic_path_vars.items():
            self.settings[key] = var.get()
        write_json(SETTINGS_FILE, self.settings)

    def save_abiotic_settings(self):
        self.sync_abiotic_path_vars()
        if self.abiotic_auto_restart_var is not None:
            self.settings["abiotic_auto_restart_server"] = self.abiotic_auto_restart_var.get()
        if self.abiotic_backup_before_restart_var is not None:
            self.settings["abiotic_backup_before_restart"] = self.abiotic_backup_before_restart_var.get()
        write_json(SETTINGS_FILE, self.settings)
        self.log("Abiotic Factor settings saved.")
        self.refresh_abiotic_status()
        self.refresh_abiotic_dashboard()
        messagebox.showinfo(APP_NAME, "Abiotic Factor settings saved.")

    def apply_abiotic_settings_to_ui(self):
        for key, var in self.abiotic_path_vars.items():
            var.set(str(self.settings.get(key, "")))
        if self.abiotic_auto_restart_var is not None:
            self.abiotic_auto_restart_var.set(bool(self.settings.get("abiotic_auto_restart_server")))
        if self.abiotic_backup_before_restart_var is not None:
            self.abiotic_backup_before_restart_var.set(bool(self.settings.get("abiotic_backup_before_restart", True)))

    def get_valheim_process_text(self):
        return self.get_named_process_text(VALHEIM_EXE_NAME, VALHEIM_PROCESS_NAME)

    def is_valheim_running(self) -> bool:
        return self.get_valheim_process_text() is not None

    def refresh_valheim_status(self):
        if not self.valheim_vars:
            return
        process_text = self.get_valheim_process_text()
        running = process_text is not None
        self.valheim_vars["status"].set("Running" if running else "Stopped")
        self.valheim_vars["detected_process"].set(process_text or "None")
        if hasattr(self, "valheim_status_label"):
            self.valheim_status_label.configure(foreground=COLORS["ok"] if running else COLORS["muted"])
        if self.valheim_start_button:
            self.valheim_start_button.configure(style="TButton" if running else "Green.TButton")
        if self.valheim_stop_button:
            self.valheim_stop_button.configure(style="Danger.TButton" if running else "TButton")

    def refresh_valheim_dashboard(self):
        if not self.valheim_vars:
            return
        backups = self.list_valheim_backups()
        self.valheim_vars["install_path"].set(str(self.path("valheim_server_install_path")))
        self.valheim_vars["launcher_path"].set(str(self.path("valheim_server_bat_path")))
        self.valheim_vars["save_folder_path"].set(str(self.path("valheim_save_folder_path")))
        self.valheim_vars["backup_folder_path"].set(str(self.path("valheim_backup_folder_path")))
        self.valheim_vars["backup_count"].set(str(len(backups)))
        self.valheim_vars["last_backup"].set(backups[0][1].strftime("%Y-%m-%d %H:%M") if backups else "No backups found")

    def start_valheim_server(self):
        self.sync_valheim_path_vars()
        if self.is_valheim_running():
            self.valheim_should_be_running = True
            messagebox.showinfo(APP_NAME, "The Valheim server is already running.")
            return
        launcher = self.path("valheim_server_bat_path")
        if not launcher.exists():
            messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{launcher}\n\nUse Auto-detect or browse to start_headless_server.bat.")
            self.log(f"Valheim start failed: launcher not found: {launcher}")
            return
        try:
            subprocess.Popen([str(launcher)], cwd=str(launcher.parent), shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.valheim_should_be_running = True
            self.log("Valheim server start requested.")
            self.after(2500, self.refresh_valheim_status)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not start Valheim server:\n{exc}")
            self.log(f"Valheim start failed: {exc}")

    def stop_valheim_server(self, ask_force=True) -> bool:
        self.valheim_should_be_running = False
        if not self.is_valheim_running():
            self.log("Valheim stop skipped: server is not running.")
            self.refresh_valheim_status()
            return True
        self.log("Valheim server stop requested.")
        try:
            subprocess.run(["taskkill", "/IM", VALHEIM_EXE_NAME, "/T"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
        except (OSError, subprocess.SubprocessError) as exc:
            self.log(f"Valheim graceful stop command failed: {exc}")
        deadline = time.time() + 15
        while time.time() < deadline:
            if not self.is_valheim_running():
                self.log("Valheim server stopped.")
                self.refresh_valheim_status()
                return True
            time.sleep(1)
        if ask_force and messagebox.askyesno(APP_NAME, "Valheim did not stop within 15 seconds. Force kill it?"):
            try:
                subprocess.run(["taskkill", "/F", "/IM", VALHEIM_EXE_NAME, "/T"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                self.log("Valheim server force kill requested.")
            except (OSError, subprocess.SubprocessError) as exc:
                self.log(f"Valheim force kill failed: {exc}")
                messagebox.showerror(APP_NAME, f"Valheim force kill failed:\n{exc}")
                return False
            self.after(1500, self.refresh_valheim_status)
            return True
        self.log("Valheim stop incomplete: server is still running.")
        return False

    def restart_valheim_server(self):
        def work():
            if self.stop_valheim_server():
                time.sleep(3)
                self.valheim_should_be_running = True
                self.after(0, self.start_valheim_server)
        threading.Thread(target=work, daemon=True).start()

    def valheim_appmanifest_path(self) -> Path:
        install_dir = self.path("valheim_server_install_path")
        try:
            steamapps_dir = install_dir.parent.parent
        except IndexError:
            return Path()
        return steamapps_dir / f"appmanifest_{VALHEIM_DEDICATED_SERVER_APP_ID}.acf"

    def local_valheim_build_id(self) -> str:
        manifest = self.valheim_appmanifest_path()
        if not manifest.exists():
            return ""
        try:
            text = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        match = re.search(r'"buildid"\s+"(\d+)"', text, re.IGNORECASE)
        return match.group(1) if match else ""

    def check_valheim_update(self, show_dialog=True):
        if not self.valheim_vars:
            return
        self.valheim_vars["update_status"].set("Checking...")
        build_id = self.local_valheim_build_id()
        manifest = self.valheim_appmanifest_path()
        if not build_id:
            self.valheim_vars["update_status"].set("Unknown - app manifest not found")
            self.set_valheim_update_button_available(False)
            if show_dialog:
                messagebox.showerror(APP_NAME, f"Could not find the local Valheim Dedicated Server build ID.\n\nExpected Steam app manifest:\n{manifest}")
            self.log(f"Valheim update check failed: build ID not found in {manifest}")
            return
        self.run_threaded("Valheim Steam update check", lambda: self.do_check_valheim_update(build_id, show_dialog=show_dialog))

    def do_check_valheim_update(self, build_id: str, show_dialog=True):
        url = "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/" f"?appid={VALHEIM_DEDICATED_SERVER_APP_ID}&version={build_id}"
        request = urllib.request.Request(url, headers={"User-Agent": APP_NAME})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode("utf-8", errors="replace")).get("response", {})
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            self.log(f"Valheim update check failed: {exc}")
            self.after(0, self.valheim_vars["update_status"].set, "Check failed")
            self.after(0, self.set_valheim_update_button_available, False)
            if show_dialog:
                self.after(0, messagebox.showerror, APP_NAME, f"Valheim update check failed:\n{exc}")
            return
        if result.get("success") is False:
            error_text = result.get("error") or "Steam did not return update information."
            self.after(0, self.valheim_vars["update_status"].set, f"Check unavailable - {error_text}")
            self.after(0, self.set_valheim_update_button_available, False)
            return
        up_to_date = bool(result.get("up_to_date"))
        required = str(result.get("required_version", "unknown"))
        status_text = f"Server is up to date - build {build_id}" if up_to_date else f"Update available - local {build_id}, latest {required}"
        self.after(0, self.valheim_vars["update_status"].set, status_text)
        self.after(0, self.set_valheim_update_button_available, (not up_to_date) and required != "unknown")
        if show_dialog:
            message = f"Valheim Dedicated Server is up to date.\n\nLocal build: {build_id}" if up_to_date else f"Valheim Dedicated Server update appears available.\n\nLocal build: {build_id}\nRequired build: {required}"
            self.after(0, messagebox.showinfo, APP_NAME, message)

    def set_valheim_update_button_available(self, available: bool):
        if self.valheim_update_button:
            self.valheim_update_button.configure(style="Green.TButton" if available else "TButton")

    def update_valheim_server_with_steamcmd(self):
        self.sync_valheim_path_vars()
        if self.is_valheim_running():
            messagebox.showwarning(APP_NAME, "Stop the Valheim server before running a SteamCMD update.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("valheim_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not install_dir.exists():
            messagebox.showerror(APP_NAME, f"Valheim install folder was not found:\n{install_dir}")
            return
        if messagebox.askyesno(APP_NAME, "Update Valheim Dedicated Server with SteamCMD?\n\nThe app will create a save and launcher backup first."):
            self.run_threaded("Valheim SteamCMD server update", self.do_update_valheim_server_with_steamcmd)

    def install_valheim_server_with_steamcmd(self):
        self.sync_valheim_path_vars()
        if self.is_valheim_running():
            messagebox.showwarning(APP_NAME, "Stop the Valheim server before installing or repairing it with SteamCMD.")
            return
        steamcmd = self.path("steamcmd_path")
        install_dir = self.path("valheim_server_install_path")
        if not steamcmd.exists():
            messagebox.showerror(APP_NAME, f"SteamCMD was not found:\n{steamcmd}\n\nSet SteamCMD executable in Settings.")
            return
        if not self.validate_safe_folder(install_dir, "Valheim install folder"):
            return
        if messagebox.askyesno(APP_NAME, f"Install or repair Valheim Dedicated Server with SteamCMD?\n\nInstall folder:\n{install_dir}\n\nThis downloads Steam app {VALHEIM_DEDICATED_SERVER_APP_ID}."):
            self.run_threaded("Valheim SteamCMD server install", self.do_install_valheim_server_with_steamcmd)

    def do_install_valheim_server_with_steamcmd(self):
        install_dir = self.path("valheim_server_install_path")
        try:
            install_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.after(0, messagebox.showerror, APP_NAME, f"Could not create Valheim install folder:\n{exc}")
            return
        exit_code = self.run_valheim_steamcmd(self.path("steamcmd_path"), install_dir, "install")
        if exit_code == 0:
            self.settings["valheim_server_exe_path"] = str(install_dir / VALHEIM_EXE_NAME)
            self.settings["valheim_server_bat_path"] = str(install_dir / "start_headless_server.bat")
            write_json(SETTINGS_FILE, self.settings)
            self.after(0, self.apply_valheim_settings_to_ui)
            self.after(0, self.refresh_valheim_dashboard)
            self.after(0, self.check_valheim_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Valheim Dedicated Server install/repair complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Valheim SteamCMD install exited with code {exit_code}. Check Logs.")

    def do_update_valheim_server_with_steamcmd(self):
        self.create_valheim_backup(prefix_override="before_valheim_update_", show_missing_error=False)
        exit_code = self.run_valheim_steamcmd(self.path("steamcmd_path"), self.path("valheim_server_install_path"), "update")
        if exit_code == 0:
            self.after(0, self.check_valheim_update, False)
            self.after(0, messagebox.showinfo, APP_NAME, "Valheim server update complete.")
        else:
            self.after(0, messagebox.showerror, APP_NAME, f"Valheim SteamCMD update exited with code {exit_code}. Check Logs.")

    def run_valheim_steamcmd(self, steamcmd: Path, install_dir: Path, action_label: str) -> int:
        command = [str(steamcmd), "+login", "anonymous", "+force_install_dir", str(install_dir), "+app_update", VALHEIM_DEDICATED_SERVER_APP_ID, "validate", "+quit"]
        self.log(f"Running SteamCMD {action_label} for Valheim Dedicated Server app {VALHEIM_DEDICATED_SERVER_APP_ID}.")
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=str(steamcmd.parent), creationflags=subprocess.CREATE_NO_WINDOW)
            assert process.stdout is not None
            for line in process.stdout:
                clean = line.rstrip()
                if clean:
                    self.log(f"Valheim SteamCMD: {clean}")
            return process.wait()
        except OSError as exc:
            self.log(f"Valheim SteamCMD {action_label} failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Valheim SteamCMD {action_label} failed:\n{exc}")
            return 1

    def create_valheim_backup(self, prefix_override=None, show_missing_error=True) -> Path | None:
        if threading.get_ident() == self.main_thread_id:
            self.sync_valheim_path_vars()
        save_dir = self.path("valheim_save_folder_path")
        launcher = self.path("valheim_server_bat_path")
        backup_dir = self.path("valheim_backup_folder_path")
        if not save_dir.exists() and not launcher.exists():
            if show_missing_error:
                self.after(0, messagebox.showerror, APP_NAME, f"Valheim save/launcher paths do not exist yet:\n{save_dir}\n{launcher}")
            self.log(f"Valheim backup skipped: save/launcher missing: {save_dir}; {launcher}")
            return None
        if save_dir.exists() and not self.validate_safe_folder(save_dir, "Valheim save folder"):
            return None
        backup_dir.mkdir(parents=True, exist_ok=True)
        prefix = prefix_override or "valheim_backup_"
        target = backup_dir / f"{prefix}{now_stamp()}"
        counter = 1
        while target.exists():
            target = backup_dir / f"{prefix}{now_stamp()}_{counter}"
            counter += 1
        try:
            target.mkdir(parents=True)
            if save_dir.exists():
                shutil.copytree(save_dir, target / "save")
            if launcher.exists() and launcher.is_file():
                shutil.copy2(launcher, target / launcher.name)
            self.log(f"Valheim backup created: {target}")
            self.after(0, self.refresh_valheim_dashboard)
            return target
        except OSError as exc:
            self.log(f"Valheim backup failed: {exc}")
            self.after(0, messagebox.showerror, APP_NAME, f"Valheim backup failed:\n{exc}")
            return None

    def backup_valheim_now(self):
        self.sync_valheim_path_vars()
        self.run_threaded("Valheim backup", self.create_valheim_backup)

    def list_valheim_backups(self):
        backup_dir = self.path("valheim_backup_folder_path")
        if not backup_dir.exists():
            return []
        items = []
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
            for prefix in ["valheim_backup_", "before_valheim_update_"]:
                if item.name.startswith(prefix):
                    try:
                        items.append((item, datetime.strptime(item.name.removeprefix(prefix)[:16], BACKUP_TIME_FORMAT)))
                    except ValueError:
                        pass
                    break
        return sorted(items, key=lambda row: row[1], reverse=True)

    def valheim_launcher_text(self):
        launcher = self.path("valheim_server_bat_path")
        if not launcher.exists():
            return None
        try:
            return launcher.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def valheim_command_line(self, text: str):
        for line in text.splitlines():
            stripped = line.strip().lower()
            if stripped.startswith("rem ") or stripped.startswith("::"):
                continue
            if re.search(r"\bvalheim_server(?:\.exe)?\b", line, re.IGNORECASE):
                return line
        return None

    def parse_valheim_arg(self, line: str, key: str):
        if key == "crossplay":
            return "True" if re.search(r"(?:^|\s)-crossplay(?:\s|$)", line, re.IGNORECASE) else "False"
        match = re.search(rf"(?:^|\s)-{re.escape(key)}\s+(\"(?:\\.|[^\"])*\"|\S+)", line, re.IGNORECASE)
        if not match:
            return None
        value = match.group(1).strip()
        if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
            value = value[1:-1].replace('\\"', '"')
        return value

    def set_valheim_arg(self, line: str, key: str, value: str, kind: str):
        if key == "crossplay":
            line = re.sub(r"\s+-crossplay(?=\s|$)", "", line, flags=re.IGNORECASE)
            if value.strip().lower() == "true":
                return line.rstrip() + " -crossplay"
            return line.rstrip()
        formatted = value if kind == "number" or kind.startswith("choice:") else '"' + value.replace('"', '\\"') + '"'
        pattern = re.compile(rf"(\s-{re.escape(key)}\s+)(\"(?:\\.|[^\"])*\"|\S+)", re.IGNORECASE)
        if pattern.search(line):
            return pattern.sub(rf"\g<1>{formatted}", line, count=1)
        return line.rstrip() + f" -{key} {formatted}"

    def set_valheim_config_form_values(self, line: str):
        defaults = {"port": "2456", "public": "1", "saveinterval": "1800", "backups": "4", "backupshort": "7200", "backuplong": "43200", "crossplay": "False", "preset": "Normal"}
        for key, _label, _kind in VALHEIM_CONFIG_FIELDS:
            self.valheim_config_vars[key].set(self.parse_valheim_arg(line, key) or defaults.get(key, ""))

    def load_valheim_config(self):
        text = self.valheim_launcher_text()
        if text is None:
            messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{self.path('valheim_server_bat_path')}")
            return
        self.valheim_config_text.configure(state="normal")
        self.valheim_config_text.delete("1.0", "end")
        self.valheim_config_text.insert("1.0", text)
        self.valheim_config_text.edit_reset()
        line = self.valheim_command_line(text)
        if line:
            self.set_valheim_config_form_values(line)
        self.log(f"Loaded Valheim launcher: {self.path('valheim_server_bat_path')}")

    def load_valheim_config_form(self, silent=False):
        text = self.valheim_launcher_text()
        if text is None:
            if not silent:
                messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{self.path('valheim_server_bat_path')}")
            return
        line = self.valheim_command_line(text)
        if not line:
            if not silent:
                messagebox.showerror(APP_NAME, "Could not find a valheim_server command in the launcher batch file.")
            return
        self.set_valheim_config_form_values(line)
        self.valheim_config_text.configure(state="normal")
        self.valheim_config_text.delete("1.0", "end")
        self.valheim_config_text.insert("1.0", text)
        self.valheim_config_text.edit_reset()

    def save_valheim_config(self):
        self.sync_valheim_path_vars()
        if self.is_valheim_running():
            messagebox.showwarning(APP_NAME, "Stop the Valheim server before editing start_headless_server.bat.")
            return
        launcher = self.path("valheim_server_bat_path")
        if not launcher.exists():
            messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{launcher}")
            return
        text = self.valheim_config_text.get("1.0", "end-1c")
        if not self.valheim_command_line(text):
            messagebox.showerror(APP_NAME, "The launcher does not contain a valheim_server command.")
            return
        try:
            backup_path = launcher.with_name(f"{launcher.stem}.backup_{now_stamp()}{launcher.suffix}")
            shutil.copy2(launcher, backup_path)
            launcher.write_text(text, encoding="utf-8")
            self.load_valheim_config_form(silent=True)
            self.log(f"Saved Valheim launcher: {launcher}")
            messagebox.showinfo(APP_NAME, f"Valheim launcher saved.\nBackup created:\n{backup_path}")
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Valheim launcher save failed:\n{exc}")

    def save_valheim_config_form(self):
        self.sync_valheim_path_vars()
        if self.is_valheim_running():
            messagebox.showwarning(APP_NAME, "Stop the Valheim server before editing start_headless_server.bat.")
            return
        launcher = self.path("valheim_server_bat_path")
        if not launcher.exists():
            messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{launcher}")
            return
        try:
            text = launcher.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines(keepends=True)
            command_index = next((index for index, line in enumerate(lines) if self.valheim_command_line(line)), None)
            if command_index is None:
                raise ValueError("valheim_server command not found")
            line = lines[command_index]
            for key, _label, kind in VALHEIM_CONFIG_FIELDS:
                value = self.valheim_config_vars[key].get().strip()
                if key == "crossplay":
                    line = self.set_valheim_arg(line, key, value, kind)
                elif value:
                    line = self.set_valheim_arg(line, key, value, kind)
            lines[command_index] = line + ("\n" if not line.endswith(("\n", "\r")) else "")
            backup_path = launcher.with_name(f"{launcher.stem}.backup_{now_stamp()}{launcher.suffix}")
            shutil.copy2(launcher, backup_path)
            launcher.write_text("".join(lines), encoding="utf-8")
            self.load_valheim_config_form(silent=True)
            self.log(f"Saved Valheim config form: {launcher}")
            messagebox.showinfo(APP_NAME, f"Valheim config saved.\nBackup created:\n{backup_path}")
        except (OSError, ValueError) as exc:
            messagebox.showerror(APP_NAME, f"Valheim config form save failed:\n{exc}")

    def open_valheim_config_notepad(self):
        launcher = self.path("valheim_server_bat_path")
        if not launcher.exists():
            messagebox.showerror(APP_NAME, f"Valheim launcher batch file not found:\n{launcher}")
            return
        try:
            subprocess.Popen(["notepad.exe", str(launcher)])
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"Could not open Notepad:\n{exc}")

    def sync_valheim_path_vars(self):
        for key, var in self.valheim_path_vars.items():
            self.settings[key] = var.get()
        write_json(SETTINGS_FILE, self.settings)

    def save_valheim_settings(self):
        self.sync_valheim_path_vars()
        self.settings["valheim_auto_restart_server"] = self.valheim_auto_restart_var.get()
        write_json(SETTINGS_FILE, self.settings)
        self.log("Valheim settings saved.")
        self.refresh_valheim_status()
        self.refresh_valheim_dashboard()
        messagebox.showinfo(APP_NAME, "Valheim settings saved.")

    def apply_valheim_settings_to_ui(self):
        for key, var in self.valheim_path_vars.items():
            var.set(str(self.settings.get(key, "")))

    def detect_valheim_install_from_process(self):
        try:
            result = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name valheim_server -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            path_text = result.stdout.strip()
            if path_text:
                path = Path(path_text)
                if path.exists():
                    return path.parent
        except (OSError, subprocess.SubprocessError):
            pass
        return None

    def detect_valheim_install_from_steam(self):
        for steamapps in self.steam_library_paths():
            manifest = steamapps / f"appmanifest_{VALHEIM_DEDICATED_SERVER_APP_ID}.acf"
            if not manifest.exists():
                continue
            installdir = "Valheim dedicated server"
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
                match = re.search(r'"installdir"\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    installdir = match.group(1)
            except OSError:
                pass
            install_path = steamapps / "common" / installdir
            if (install_path / VALHEIM_EXE_NAME).exists() or install_path.exists():
                return install_path
        return None

    def valheim_launcher_candidate(self, install_path: Path) -> Path:
        for name in ("start_headless_server.bat", "start_headless_server - Copy.bat"):
            candidate = install_path / name
            if candidate.exists():
                return candidate
        return install_path / "start_headless_server.bat"

    def autodetect_valheim_paths(self):
        detected = {}
        install_path = self.detect_valheim_install_from_process() or self.detect_valheim_install_from_steam()
        if install_path:
            detected["valheim_server_install_path"] = str(install_path)
            detected["valheim_server_exe_path"] = str(install_path / VALHEIM_EXE_NAME)
            detected["valheim_server_bat_path"] = str(self.valheim_launcher_candidate(install_path))
        steamcmd_path = self.detect_steamcmd_path()
        if steamcmd_path:
            detected["steamcmd_path"] = str(steamcmd_path)
        for key, value in detected.items():
            if key in self.valheim_path_vars:
                self.valheim_path_vars[key].set(value)
            self.settings[key] = value
        write_json(SETTINGS_FILE, self.settings)
        self.refresh_valheim_status()
        self.refresh_valheim_dashboard()
        message = "Detected Valheim Dedicated Server paths and saved them." if install_path else "Could not auto-detect Valheim. Install the dedicated server or browse to its folder manually."
        if not steamcmd_path:
            message += "\n\nSteamCMD was not found. Set SteamCMD executable in Settings if you want server updates."
        self.log(f"Valheim auto-detect paths result: {detected}")
        messagebox.showinfo(APP_NAME, message)

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
        self.backup_size_generation += 1
        generation = self.backup_size_generation
        self.backup_tree.delete(*self.backup_tree.get_children())
        backups = self.list_all_backup_entries()
        for server, path, parsed in backups:
            self.backup_tree.insert("", "end", iid=str(path), values=(server, path.name, parsed.strftime("%Y-%m-%d %H:%M"), "Calculating..."))
        self.refresh_dashboard()
        if backups:
            threading.Thread(
                target=self.calculate_backup_sizes,
                args=(generation, backups),
                daemon=True,
            ).start()

    def list_all_backup_entries(self):
        entries = [("ASKA", path, parsed) for path, parsed in self.list_backups()]
        entries.extend(("Windrose", path, parsed) for path, parsed in self.list_windrose_backups())
        entries.extend(("Palworld", path, parsed) for path, parsed in self.list_palworld_backups())
        entries.extend(("Valheim", path, parsed) for path, parsed in self.list_valheim_backups())
        entries.extend(("Abiotic Factor", path, parsed) for path, parsed in self.list_abiotic_backups())
        return sorted(entries, key=lambda row: row[2], reverse=True)

    def calculate_backup_sizes(self, generation, backups):
        sizes = [(path, human_size(path)) for _server, path, _parsed in backups]
        self.after(0, self.apply_backup_sizes, generation, sizes)

    def apply_backup_sizes(self, generation, sizes):
        if generation != self.backup_size_generation or not self.backup_tree:
            return
        for path, size in sizes:
            if self.backup_tree.exists(str(path)):
                values = list(self.backup_tree.item(str(path), "values"))
                if len(values) >= 4:
                    values[3] = size
                    self.backup_tree.item(str(path), values=values)

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

    def update_nexus_key_status(self):
        if not self.nexus_key_status_var:
            return
        key = self.nexus_api_key_var.get().strip() if hasattr(self, "nexus_api_key_var") else self.settings.get("nexus_api_key", "")
        self.nexus_key_status_var.set(f"Saved key status: {'key entered' if key else 'no key entered'}")

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
        api_key = self.nexus_api_key_var.get().strip() if hasattr(self, "nexus_api_key_var") else self.settings.get("nexus_api_key", "").strip()
        if not api_key:
            pages = "\n".join(source.get("nexus_url", "") for source in tracked if source.get("nexus_url"))
            messagebox.showinfo(
                APP_NAME,
                "Nexus API key is not configured, so automatic metadata checks are unavailable.\n\n"
                "Use Open Nexus Page for each tracked mod, or add your API key in Settings.\n\n"
                f"Tracked pages:\n{pages}",
            )
            return
        self.settings["nexus_api_key"] = api_key
        write_json(SETTINGS_FILE, self.settings)
        self.update_nexus_key_status()
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
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                lines.append(f"{name}: check failed (HTTP {exc.code})")
                self.log(f"Nexus check failed for {name}: HTTP {exc.code} {detail}")
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
        selected_values = self.backup_tree.item(selected[0], "values")
        selected_server = selected_values[0] if selected_values else "ASKA"
        backup_path = Path(selected[0])
        if selected_server == "Abiotic Factor":
            self.restore_selected_abiotic_backup(backup_path)
            return
        if selected_server != "ASKA":
            messagebox.showinfo(APP_NAME, f"Restore is not implemented for {selected_server} yet. The backup remains available in its server-specific backup folder.")
            return
        if self.is_server_running():
            messagebox.showwarning(APP_NAME, "Stop the ASKA server before restoring a backup.")
            self.log("Restore refused: server is running.")
            return
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
                new_lines.append("\n# Added by Gaming Dads Server Manager\n")
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

    def sync_windrose_path_vars(self):
        for key, var in self.windrose_path_vars.items():
            self.settings[key] = var.get()
        write_json(SETTINGS_FILE, self.settings)

    def save_windrose_settings(self):
        self.sync_windrose_path_vars()
        self.log("Windrose settings saved.")
        self.refresh_windrose_status()
        self.refresh_windrose_dashboard()
        messagebox.showinfo(APP_NAME, "Windrose settings saved.")

    def apply_windrose_settings_to_ui(self):
        for key, var in self.windrose_path_vars.items():
            var.set(str(self.settings.get(key, "")))

    def windows_startup_script_path(self) -> Path:
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup_dir / "Gaming Dads Server Manager.bat"

    def legacy_windows_startup_script_path(self) -> Path:
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup_dir / "ASKA Server Manager.bat"

    def app_launch_command(self) -> str:
        if getattr(sys, "frozen", False):
            return f'start "" "{sys.executable}"'
        return f'start "" "{sys.executable}" "{Path(__file__).resolve()}"'

    def sync_windows_startup(self):
        script_path = self.windows_startup_script_path()
        if self.settings.get("launch_on_windows_startup"):
            try:
                script_path.parent.mkdir(parents=True, exist_ok=True)
                script_path.write_text("@echo off\n" + self.app_launch_command() + "\n", encoding="utf-8")
                legacy_path = self.legacy_windows_startup_script_path()
                if legacy_path.exists():
                    legacy_path.unlink()
                    self.log(f"Legacy Windows startup entry removed: {legacy_path}")
                self.log(f"Windows startup entry enabled: {script_path}")
            except OSError as exc:
                self.log(f"Could not enable Windows startup entry: {exc}")
                messagebox.showerror(APP_NAME, f"Could not enable Windows startup entry:\n{exc}")
        else:
            try:
                if script_path.exists():
                    script_path.unlink()
                    self.log(f"Windows startup entry removed: {script_path}")
                legacy_path = self.legacy_windows_startup_script_path()
                if legacy_path.exists():
                    legacy_path.unlink()
                    self.log(f"Legacy Windows startup entry removed: {legacy_path}")
            except OSError as exc:
                self.log(f"Could not remove Windows startup entry: {exc}")
                messagebox.showerror(APP_NAME, f"Could not remove Windows startup entry:\n{exc}")

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

    def detect_windrose_install_from_steam(self):
        for steamapps in self.steam_library_paths():
            manifest = steamapps / f"appmanifest_{WINDROSE_DEDICATED_SERVER_APP_ID}.acf"
            if not manifest.exists():
                continue
            installdir = "Windrose Dedicated Server"
            try:
                text = manifest.read_text(encoding="utf-8", errors="replace")
                match = re.search(r'"installdir"\s+"([^"]+)"', text, re.IGNORECASE)
                if match:
                    installdir = match.group(1)
            except OSError:
                pass
            install_path = steamapps / "common" / installdir
            if (install_path / WINDROSE_EXE_NAME).exists() or install_path.exists():
                return install_path
        return None

    def detect_windrose_install_from_process(self):
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-Process -Name WindroseServer -ErrorAction SilentlyContinue | "
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

    def windrose_save_candidates(self, install_path: Path):
        return [
            install_path / "R5" / "Saved" / "SaveProfiles" / "Default" / "RocksDB",
            install_path / "R5" / "Saved" / "SaveProfiles" / "Default",
            install_path / "R5" / "Saved" / "SaveProfiles",
            install_path / "R5" / "Saved",
        ]

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

    def autodetect_windrose_paths(self):
        detected = {}
        install_path = self.detect_windrose_install_from_process() or self.detect_windrose_install_from_steam()
        if install_path:
            detected["windrose_server_install_path"] = str(install_path)
            detected["windrose_server_bat_path"] = str(install_path / "StartServerForeground.bat")
            detected["windrose_server_exe_path"] = str(install_path / WINDROSE_EXE_NAME)
            detected["windrose_server_config_path"] = str(install_path / "R5" / "ServerDescription.json")
            save_path = next((candidate for candidate in self.windrose_save_candidates(install_path) if candidate.exists()), self.windrose_save_candidates(install_path)[0])
            detected["windrose_save_folder_path"] = str(save_path)

        detected["windrose_backup_folder_path"] = (
            self.windrose_path_vars.get("windrose_backup_folder_path", tk.StringVar(value=str(DEFAULT_WINDROSE_BACKUPS))).get()
            or str(DEFAULT_WINDROSE_BACKUPS)
        )

        steamcmd_path = self.detect_steamcmd_path()
        if steamcmd_path:
            detected["steamcmd_path"] = str(steamcmd_path)

        for key, value in detected.items():
            if key in self.path_vars:
                self.path_vars[key].set(value)
            self.settings[key] = value
        write_json(SETTINGS_FILE, self.settings)
        self.refresh_windrose_status()
        self.refresh_windrose_dashboard()

        if install_path:
            message = "Detected Windrose dedicated server paths and saved them."
        else:
            message = (
                "Could not auto-detect the Windrose Dedicated Server install folder.\n\n"
                "Install the Steam tool once, start the server once, or browse to the install folder manually."
            )
        if not steamcmd_path:
            message += "\n\nSteamCMD was not found. Set SteamCMD executable in Settings if you want server updates."
        self.log(f"Windrose auto-detect paths result: {detected}")
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
        self.settings["launch_on_windows_startup"] = self.launch_on_startup_var.get()
        self.settings["start_server_on_app_launch"] = self.start_server_on_launch_var.get()
        self.settings["auto_restart_server"] = self.auto_restart_var.get()
        self.save_palworld_settings_values(write_file=False)
        self.settings["valheim_auto_restart_server"] = self.valheim_auto_restart_var.get()
        write_json(SETTINGS_FILE, self.settings)
        self.update_nexus_key_status()
        self.sync_windows_startup()
        self.log("Settings saved.")
        self.refresh_all()
        self.schedule_auto_backup()
        self.start_palworld_discord_monitor()
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

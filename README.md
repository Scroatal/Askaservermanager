# Gaming Dads Server Manager

Version: `0.3.0`

Local Windows desktop manager for ASKA, Windrose, Palworld, Valheim, Abiotic Factor, and Minecraft Fabric dedicated servers. It is built with Python 3 and Tkinter, using only the Python standard library.

The UI uses colors inspired by the public ASKA site at <https://playaska.com/> and an original generated app emblem.

Each game has dedicated server controls and settings. Minecraft adds live console commands, `server.properties` editing, Fabric mod visibility, port checks, and world ZIP backups.

## Download And Install

1. Download the latest release zip from:

   <https://github.com/Scroatal/Askaservermanager/releases>

2. Extract the zip to a folder, for example:

   ```text
   C:\Tools\Gaming Dads Server Manager
   ```

3. Run:

   ```text
   Gaming Dads Server Manager.exe
   ```

Windows may show a SmartScreen warning because the app is not code-signed. Choose `More info` and `Run anyway` if you trust the download source.

The app creates local files beside the executable:

```text
settings.json
mods.json
```

Do not share those files if they contain private paths, a Nexus API key, a Palworld admin password, or a Discord bot token.

## First Run Setup

Open the relevant game tab and then `Settings` to confirm its paths match your machine. For ASKA, use `ASKA > Settings`:

```text
Server install folder
Launcher batch file
Server properties file
SteamCMD executable
BepInEx plugins folder
BepInEx config folder
Save folder
Backup folder
```

Click `Auto-detect Paths` to let the app find paths from the running `AskaServer.exe`, Steam library manifests, and common SteamCMD locations. Review the detected values, then click `Save Settings`, close and reopen the app once to confirm settings persist.

Recommended first test:

1. Stop the ASKA server.
2. Click `Backup Now`.
3. Confirm a backup appears in the Backups tab.
4. Start the server from the app.
5. Confirm `ASKA > Server` shows `Running`.

## Safety Rules

The app refuses to restore, wipe, edit server config, edit mod config, install mod ZIPs, or update the server while `AskaServer.exe` is running.

Before restore, wipe, server update, and mod ZIP install, the app creates backups. If the required pre-wipe backup fails, the wipe is aborted.

Windrose actions use the same cautious rule: stop `WindroseServer.exe` before editing config or updating with SteamCMD.

## Windows Startup And Auto-Restart

The `ASKA > Settings` page has three startup/watchdog options:

```text
Launch Gaming Dads Server Manager when Windows starts
Start ASKA server when the manager opens
Auto-restart ASKA server if it stops unexpectedly
```

When Windows startup is enabled, the app creates a startup batch file in the current user's Windows Startup folder. Disabling the option removes that file.

Auto-restart only acts when the manager believes the server should be running. Clicking `Start Server` or enabling `Start ASKA server when the manager opens` sets that expectation. Clicking `Stop Server` clears it so the app does not restart a server you intentionally stopped.

## Run

For normal users, use the release `.exe`.

For development, run from source:

```bat
python aska_server_manager.py
```

The app creates `settings.json` beside the script on first run.

## Paths

Default server install:

```text
E:\steam\steamapps\common\ASKA Dedicated Server
```

Default launcher:

```text
E:\steam\steamapps\common\ASKA Dedicated Server\AskaServer.bat
```

Default save folder:

```text
%USERPROFILE%\AppData\LocalLow\Sand Sailor Studio\Aska\data\server
```

Default backup folder:

```text
E:\aska_backups
```

Use `ASKA > Settings` to change the ASKA paths. Each other game keeps its own paths in its game tab.

## Backups

Manual backups are created with the `Backup Now` button. Automatic backups can be enabled from `ASKA > Settings`. By default, automatic backups run every 60 minutes while the app is open and old backups are deleted after 24 hours.

Backup names use:

```text
backup_YYYY-MM-DD_HH-mm
```

Logs are written to:

```text
E:\aska_backups\aska_manager.log
```

or to the backup folder configured in `ASKA > Settings`.

## Restore

Open the Backups tab, select a backup, and click `Restore Selected Backup`.

Important: stop the ASKA server before restoring or wiping. The app refuses restore and wipe actions while `AskaServer.exe` is running. Before restore or wipe, it creates an emergency backup in the backup folder.

Wiping the current save requires two confirmations. The first asks whether you are sure, and the second asks whether you are really sure and requires typing `DELETE`. By default, the app creates a clearly named secure before-wipe backup:

```text
secure_before_wipe_YYYY-MM-DD_HH-mm
```

If the before-wipe backup fails, the wipe is aborted.

## Config

The Config tab edits recognised keys in `server properties.txt` and preserves comments plus unknown settings. Before saving, it creates a timestamped backup next to the config file.

The bundled config fields follow the original app prompt plus Wimtzw's ASKA dedicated server guide 1.1. The guide notes that `steam game port`, `steam query port`, and `authentication token` must be set for a working public server. Steam game server tokens are created at:

```text
https://steamcommunity.com/dev/managegameservers
```

Use ASKA app ID:

```text
1898300
```

Keep the authentication token private.

The guide also recommends moving `AskaServer.bat` and `server properties.txt` outside the Steam install folder to avoid losing local edits during server updates. If you do that, update `Server launcher batch file` and `Server properties file` in `ASKA > Settings`.

## BepInEx Mods

The Mods tab manages the BepInEx folders:

```text
E:\steam\steamapps\common\ASKA Dedicated Server\BepInEx\plugins
E:\steam\steamapps\common\ASKA Dedicated Server\BepInEx\config
```

It lists installed `.dll` plugins and `.cfg` config files. Select a config file to edit it in the built-in text editor. Saving a mod config creates a timestamped backup beside the original config first.

The app refuses to save BepInEx config files while `AskaServer.exe` is running. Stop the server first so the server and app do not write the same config at the same time.

Use `Backup BepInEx Mods` to copy both `plugins` and `config` into:

```text
E:\aska_backups\bepinex_backup_YYYY-MM-DD_HH-mm
```

Use `Install Mod ZIP` after manually downloading a mod from Nexus Mods. The app stops if the server is running, backs up BepInEx first, then copies `.dll` files into `plugins` and `.cfg` files into `config`.

For Nexus tracking, select a plugin DLL and click `Set Nexus URL`. The app stores the source in `mods.json` beside the executable. `Open Nexus Page` opens the tracked page in your browser. `Check Nexus Updates` can query Nexus metadata if you add your own Nexus API key in `ASKA > Settings`.

Nexus SSO is not built into this app because Nexus requires an approved application slug for SSO clients. Manual API key entry is simpler and works without registering this app with Nexus.

## Windrose

The Windrose tab manages the Windrose Dedicated Server tool separately from ASKA.

It can:

```text
Start, stop, and restart WindroseServer.exe
Install or repair the Windrose Dedicated Server with SteamCMD
Back up the configured Windrose save folder and ServerDescription.json
Edit ServerDescription.json with JSON validation
Check the local Steam build against Steam
Update the server with SteamCMD
Auto-detect the install path from Steam manifests or a running WindroseServer.exe process
```

Default Windrose paths:

```text
E:\steam\steamapps\common\Windrose Dedicated Server
E:\steam\steamapps\common\Windrose Dedicated Server\StartServerForeground.bat
E:\steam\steamapps\common\Windrose Dedicated Server\R5\ServerDescription.json
E:\steam\steamapps\common\Windrose Dedicated Server\R5\Saved\SaveProfiles\Default\RocksDB
E:\windrose_backups
```

Windrose uses Steam dedicated server app ID:

```text
4129620
```

The first Windrose release deliberately does not include restore or wipe buttons. Confirm the generated save folder on the host first, then backups can be restored manually from the backup folder if needed.

If Windrose Dedicated Server is not installed yet, set `SteamCMD executable`, confirm the Windrose install folder, then click `Install Windrose Server`. The app runs the equivalent of:

```bat
steamcmd.exe +login anonymous +force_install_dir "E:\steam\steamapps\common\Windrose Dedicated Server" +app_update 4129620 validate +quit
```

## Palworld

The Palworld tab manages the Palworld Dedicated Server alongside ASKA and Windrose. It can:

```text
Start, stop, and restart PalServer.exe
Install or update the Palworld Dedicated Server with SteamCMD
Back up the SaveGames folder and PalWorldSettings.ini
Edit PalWorldSettings.ini with a backup before saving
Check the local Steam build against Steam
Apply a kid-friendly creative preset
Optionally auto-restart Palworld after an unexpected crash
Optionally monitor a shared Discord channel and accept restricted Palworld, Windrose, and Abiotic Factor control commands
```

Palworld does not start automatically when the manager opens. The Palworld crash watchdog is opt-in and only acts after the server was started from this tab, or if PalServer.exe was already running when the manager opened.

The kid-friendly preset applies the documented native settings for unlimited per-player building (`MaxBuildingLimitNum=0`), no death drops (`DeathPenalty=None`), no Hardcore mode, no permanent Pal loss, and easier captures (`PalCaptureRate=3.0`). Palworld's native server configuration does not document an unlimited Palball quantity setting, so true unlimited item grants require a separate admin or mod solution.

Palworld REST support uses the documented Basic Auth API for save, status, and graceful shutdown. Set `RESTAPIEnabled=True` and keep the API bound to localhost or a trusted LAN. Do not expose the REST API or Discord bot token publicly.

Discord commands are disabled by default. After configuring a bot token and channel ID, the monitor supports:

```text
!palworld status
!palworld restart
!palworld start
!palworld stop
!palworld backup
!palworld save
!palworld help
!windrose status
!windrose restart
!windrose start
!windrose stop
!windrose backup
!windrose help
!abiotic status
!abiotic restart
!abiotic start
!abiotic stop
!abiotic backup
!abiotic settings
!abiotic preset qol
!abiotic restore latest
!abiotic help
```

The Discord settings are shared on the Palworld Settings page, so the same bot can control Palworld, Windrose, and Abiotic Factor. The monitor also accepts command forms without `!`, such as `abiotic restart`. Set allowed Discord user IDs for a family/admin channel. When the allowed-user list is empty, any non-bot user who can post in the configured channel can issue commands.

Default Palworld paths:

```text
E:\steam\steamapps\common\PalServer
E:\steam\steamapps\common\PalServer\Pal\Saved\Config\WindowsServer\PalWorldSettings.ini
E:\steam\steamapps\common\PalServer\Pal\Saved\SaveGames
E:\palworld_backups
```

Palworld Dedicated Server uses Steam app ID:

```text
2394010
```

## Valheim

The Valheim tab manages the Valheim Dedicated Server alongside the other games. It can:

```text
Start, stop, and restart the Valheim server through start_headless_server.bat
Install or update the Valheim Dedicated Server with SteamCMD
Back up the Valheim save directory and launcher batch file
Edit common startup arguments with a Config Form
Edit the complete launcher with Raw BAT or Notepad
Check the local Steam build against Steam
Optionally auto-restart Valheim after an unexpected crash
```

Valheim's official Windows setup stores the main server configuration in `start_headless_server.bat`, including the server name, world, password, port, visibility, save interval, automatic backups, crossplay, and world modifier preset. The manager preserves the rest of the batch file and creates a timestamped backup before saving.

Valheim does not start automatically when the manager opens. Its crash watchdog is opt-in and only acts after the server was started from this tab, or if `valheim_server.exe` was already running when the manager opened.

Default Valheim paths:

```text
E:\steam\steamapps\common\Valheim dedicated server
E:\steam\steamapps\common\Valheim dedicated server\start_headless_server.bat
%USERPROFILE%\AppData\LocalLow\IronGate\Valheim
E:\valheim_backups
```

Valheim Dedicated Server uses Steam app ID:

```text
896660
```

## Abiotic Factor

The Abiotic Factor tab manages the Abiotic Factor Dedicated Server. It can:

```text
Start, stop, and restart AbioticFactorServer-Win64-Shipping.exe
Install or repair the dedicated server with SteamCMD
Update the server with SteamCMD
Check the local Steam build against Steam
Create safe world/config backups while the server is stopped
Edit all supported SandboxSettings.ini fields in the built-in editor
Apply the saved QoL preset with a backup before writing
Restore the latest Abiotic backup from the central Backups tab
Open the install, logs, saves, backups, and sandbox-settings folders
Optionally auto-restart the server after an unexpected crash
```

Abiotic Factor uses Steam app ID `2857200`. The server is not started automatically after installation.
The manager launches it with `-PORT=9876 -QueryPort=25575`, reusing Palworld's current game and RCON port numbers. Do not run both servers at the same time.

Default Abiotic Factor paths:

```text
E:\steam\steamapps\common\Abiotic Factor Dedicated Server
E:\steam\steamapps\common\Abiotic Factor Dedicated Server\AbioticFactor\Binaries\Win64\AbioticFactorServer-Win64-Shipping.exe
E:\steam\steamapps\common\Abiotic Factor Dedicated Server\AbioticFactor\Saved\Config\WindowsServer
E:\steam\steamapps\common\Abiotic Factor Dedicated Server\AbioticFactor\Saved\SaveGames\Server\Worlds
E:\abiotic_backups
```

Abiotic Factor backups are intentionally refused while the server is running so the world copy is consistent. Settings changes, QoL preset application, managed restarts, restores, and updates create a pre-change backup. The manager preserves unknown SandboxSettings entries and writes only the supported fields. Restore requires the server to be stopped and creates an emergency backup first.

The built-in QoL preset applies the current family settings: 42 base inventory slots, 30x stack size, zero item weight, no friendly fire, no death penalties, no durability loss on death, slower food spoilage, maximum sink refill, loot respawns, unrestricted storage tags, and the configured durability/structure options. The server must be restarted after applying settings.

Discord also supports `!abiotic settings`, `!abiotic preset qol`, and `!abiotic restore latest` in addition to the lifecycle and backup commands. These use the same bot channel and allowed-user list as Palworld and Windrose.

## Minecraft Fabric

The Minecraft tab manages the existing Cozy Family Fabric server without changing the client pack. It can:

```text
Start, gracefully stop, and restart the Fabric server with its portable Java runtime
Show live Minecraft console output and send server commands
Edit common server.properties fields while preserving unknown settings
List the server-side Fabric mod JARs
Sync installed server mods from the Cozy Family CurseForge profile before startup
Create ZIP backups of the world, including safe live backups for a server started here
Open the server, mods, world, and backup locations
Optionally start Minecraft with the manager and restart it after a crash
```

Default paths on this server computer:

```text
C:\Users\Scott\Documents\ChatGPT\minecraftserver\server
C:\Users\Scott\Documents\ChatGPT\minecraftserver\runtime\bin\java.exe
C:\Users\Scott\Documents\ChatGPT\minecraftserver\server\fabric-server-launch.jar
C:\Users\Scott\Documents\ChatGPT\minecraftserver\server\world
C:\Users\Scott\Documents\ChatGPT\minecraftserver\server\mods
C:\Users\Scott\curseforge\minecraft\Instances\Cozy Family 26.2 - Full
C:\GameBackups\Minecraft
```

The manager starts Minecraft with a 2 GB minimum and 8 GB maximum heap by default. Before each managed start, it matches mod IDs already installed on the server to the configured CurseForge profile, copies updated server JARs and newly required non-client dependencies, and creates a rollback ZIP under `C:\GameBackups\Minecraft\mod-backups`. Client-only and unrelated profile mods are not copied. It uses `stop` for graceful shutdown. Live backups send `save-off` and `save-all flush`, omit the locked `session.lock` file, create a validated ZIP, and then send `save-on`.

If a Fabric Java process was started by the previous manager or another console, this app reports `Running outside this app`. It deliberately refuses to force-stop that process. Stop it once from the old manager and then start Minecraft here to complete the handover and enable console commands.

Useful console commands include:

```text
op PlayerName
deop PlayerName
gamemode survival PlayerName
gamemode creative PlayerName
gamerule keepInventory true
say Dinner is ready
```

The shared Discord monitor also accepts `!minecraft status`, `start`, `stop`, `restart`, `backup`, and `help` when Discord control is enabled and properly restricted.

## Ports

The `Ports` tab reads the configured ports for ASKA, Windrose, Palworld, Valheim, Abiotic Factor, and Minecraft, then checks local listeners and enabled Windows inbound firewall rules. A stopped server is expected to show `Not listening`.

Windrose is currently configured for its P2P proxy and has no fixed inbound port. The `Apply ASKA Port Profile` action sets Palworld to game/REST ports `27015`/`27016` and Valheim to base port `27015` (Valheim uses `27015-27017`). Because these are shared ports, run only one of ASKA, Palworld, or Valheim at a time.

## Server Updates

The `ASKA > Server` page includes `Update Server`, which runs SteamCMD for the ASKA Dedicated Server Steam app ID:

```text
3246670
```

The `ASKA > Server` page also shows `Server update`. The app reads the local Steam build ID from:

```text
appmanifest_3246670.acf
```

Then it checks Steam's public `ISteamApps/UpToDateCheck` endpoint. The status will show `Latest`, `Update available`, `Checking`, or `Check failed`.

Configure `SteamCMD executable` in Settings. Default:

```text
C:\steamcmd\steamcmd.exe
```

The update command is equivalent to:

```bat
steamcmd.exe +login anonymous +force_install_dir "E:\steam\steamapps\common\ASKA Dedicated Server" +app_update 3246670 validate +quit
```

The app refuses to update while `AskaServer.exe` is running. Before updating, it creates:

```text
before_server_update_YYYY-MM-DD_HH-mm
server_update_preflight_YYYY-MM-DD_HH-mm
```

The preflight backup includes `server properties.txt`, `AskaServer.bat`, and BepInEx plugin/config folders where found.

## Package To EXE

Install PyInstaller if needed:

```bat
python -m pip install pyinstaller
```

Then run:

```bat
build_exe.bat
```

The build output will be:

```text
dist\Gaming Dads Server Manager.exe
```

When running the packaged `.exe`, `settings.json` is created beside the executable so the app can be shared as a folder containing the `.exe` and its local settings.

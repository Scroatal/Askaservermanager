import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from minecraft_support import MinecraftManagerMixin


def write_mod(path, mod_id, version, *, environment="*", depends=None):
    metadata = {
        "schemaVersion": 1,
        "id": mod_id,
        "version": version,
        "environment": environment,
        "depends": depends or {},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("fabric.mod.json", json.dumps(metadata))
        archive.writestr("version.txt", version)


class TestManager(MinecraftManagerMixin):
    def __init__(self, server_mods, profile, backups):
        self.settings = {
            "minecraft_mods_folder_path": str(server_mods),
            "minecraft_curseforge_profile_path": str(profile),
            "minecraft_backup_folder_path": str(backups),
        }
        self.minecraft_path_vars = {}
        self.minecraft_mod_tree = None
        self.minecraft_mod_sync_status_var = None
        self.messages = []

    def is_minecraft_running(self):
        return False

    def log(self, message):
        self.messages.append(message)


class MinecraftModSyncTests(unittest.TestCase):
    def test_metadata_accepts_control_characters_used_by_some_fabric_mods(self):
        with tempfile.TemporaryDirectory() as root:
            mod_path = Path(root) / "client-visual.jar"
            metadata = '{"schemaVersion":1,"id":"visual","version":"1.0","description":"line one\u0001line two"}'
            with zipfile.ZipFile(mod_path, "w") as archive:
                archive.writestr("fabric.mod.json", metadata)

            manager = TestManager(Path(root), Path(root), Path(root))
            parsed = manager._read_fabric_mod_metadata(mod_path)
            self.assertEqual("visual", parsed["id"])

    def test_sync_updates_installed_mod_and_adds_required_server_dependency(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            server_mods = root / "server" / "mods"
            profile = root / "profile"
            profile_mods = profile / "mods"
            backups = root / "backups"
            server_mods.mkdir(parents=True)
            profile_mods.mkdir(parents=True)

            write_mod(server_mods / "example-1.0.jar", "example", "1.0")
            write_mod(profile_mods / "example-2.0.jar", "example", "2.0", depends={"serverlib": ">=1.0"})
            write_mod(profile_mods / "serverlib-1.0.jar", "serverlib", "1.0")
            write_mod(profile_mods / "visual-1.0.jar", "visual", "1.0", environment="client")

            manager = TestManager(server_mods, profile, backups)
            self.assertTrue(manager.sync_minecraft_mods_from_curseforge(show_dialog=False))

            self.assertFalse((server_mods / "example-1.0.jar").exists())
            self.assertTrue((server_mods / "example-2.0.jar").exists())
            self.assertTrue((server_mods / "serverlib-1.0.jar").exists())
            self.assertFalse((server_mods / "visual-1.0.jar").exists())
            self.assertEqual(1, len(list((backups / "mod-backups").glob("*.zip"))))


if __name__ == "__main__":
    unittest.main()

"""Updater transactions, channel validation and Steam Deck launch wiring."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("deck_launcher", ROOT / "steam-deck/Studio Deck Launcher.py")
deck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deck)


def build(run, branch=deck.BRANCH):
    return {"channel": "sephira-test", "repository": deck.REPOSITORY, "branch": branch,
            "commit": "a" * 39 + str(run % 10), "run_id": run, "build": 15}


def fixture(root, run, embedded=None):
    metadata = build(run)
    archive = root / f"fixture-{run}.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("test-build.json", json.dumps(embedded or metadata))
        bundle.writestr("App/FFR Vision Studio.exe", f"MZ fixture {run}")
        bundle.writestr("App/flutter_windows.dll", "fixture runtime")
    update = {"build": metadata, "asset": {"name": "Sephira-Studio-Test.zip",
              "digest": "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest(),
              "browser_download_url": f"https://github.com/{deck.REPOSITORY}/releases/download/sephira-test-{run}/Sephira-Studio-Test.zip"}}
    def fetch(url, destination):
        shutil.copyfile(archive, destination)
    return update, fetch


def release(update):
    value = update["build"]
    return {"draft": False, "prerelease": True, "tag_name": f"sephira-test-{value['run_id']}",
            "target_commitish": value["commit"], "body": json.dumps(value), "assets": [update["asset"]]}


class DeckLauncherTests(unittest.TestCase):
    def test_selects_newest_tested_branch_and_rejects_other_channels_urls_and_digests(self):
        with tempfile.TemporaryDirectory() as directory:
            first, _ = fixture(Path(directory), 1)
            second, _ = fixture(Path(directory), 2)
            valid = release(second)
            malformed = []
            for field, value in (("draft", True), ("prerelease", False), ("tag_name", "sephira-test-3"),
                                 ("target_commitish", "b" * 40), ("body", "{}")):
                bad = copy.deepcopy(valid); bad[field] = value; malformed.append(bad)
            for field, value in (("digest", None), ("browser_download_url", "https://example.com/package.zip"),
                                 ("name", "FFR-Vision-Studio-windows.zip")):
                bad = copy.deepcopy(valid); bad["assets"][0][field] = value; malformed.append(bad)
            wrong = copy.deepcopy(valid); wrong["body"] = json.dumps(build(2, "master")); malformed.append(wrong)
            self.assertEqual(deck.select_release([release(first), *malformed, valid]), second)
            with self.assertRaises(deck.LauncherError): deck.select_release(malformed)

    def test_updates_keep_original_app_saved_visions_settings_and_proton_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, fetch = fixture(root, 1); deck.install_update(root, first, fetch)
            files = {"Studio Test Data/FFR Vision Studio/settings.json": "settings",
                     "Studio Test Data/FFR Vision Studio/engine/mods/EstherTsukiko/units.json": "units",
                     "Proton/pfx/drive_c/users/steamuser/sentinel.txt": "prefix",
                     "deck-proton.json": '{"proton":"saved"}'}
            for name, text in files.items():
                path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
            second, fetch = fixture(root, 2)
            result = deck.update_or_cached(root, lambda: second, fetch, say=lambda _: None)
            self.assertEqual(result["build"], build(2))
            self.assertEqual(deck.installed(root)["build"], build(2))
            self.assertTrue((root / "Versions/1/App/FFR Vision Studio.exe").is_file())
            for name, text in files.items(): self.assertEqual((root / name).read_text(), text)

    def test_current_release_needs_no_download_and_offline_launch_retains_cached_app(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); first, fetch = fixture(root, 1); deck.install_update(root, first, fetch)
            no_download = mock.Mock(side_effect=AssertionError("Should not download again"))
            self.assertEqual(deck.update_or_cached(root, lambda: first, no_download)["build"], build(1))
            offline = mock.Mock(side_effect=OSError("offline"))
            self.assertEqual(deck.update_or_cached(root, offline, no_download, say=lambda _: None)["build"], build(1))
            no_download.assert_not_called()

    def test_failed_checksum_interrupted_download_and_mismatched_metadata_keep_working_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); first, fetch = fixture(root, 1); deck.install_update(root, first, fetch)
            state = (root / "update-state.json").read_bytes()
            second, fetch = fixture(root, 2)
            damaged = copy.deepcopy(second); damaged["asset"]["digest"] = "sha256:" + "0" * 64
            result = deck.update_or_cached(root, lambda: damaged, fetch, say=lambda _: None)
            self.assertEqual(result["build"], build(1))
            def interrupted(url, destination):
                destination.write_bytes(b"partial")
                raise OSError("connection lost")
            self.assertEqual(deck.update_or_cached(root, lambda: second, interrupted, say=lambda _: None)["build"], build(1))
            mismatch, copy_wrong = fixture(root, 3, embedded=build(4))
            self.assertEqual(deck.update_or_cached(root, lambda: mismatch, copy_wrong, say=lambda _: None)["build"], build(1))
            self.assertEqual((root / "update-state.json").read_bytes(), state)
            self.assertFalse((root / "Versions/2").exists())
            self.assertFalse((root / "Versions/3").exists())
            self.assertFalse(list(root.glob(".deck-update-*")))

    def test_atomic_state_failure_keeps_previous_app_and_next_attempt_reuses_staged_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); first, fetch = fixture(root, 1); deck.install_update(root, first, fetch)
            second, fetch = fixture(root, 2); state = (root / "update-state.json").read_bytes()
            with mock.patch.object(deck.os, "replace", side_effect=OSError("disk full")):
                result = deck.update_or_cached(root, lambda: second, fetch, say=lambda _: None)
            self.assertEqual(result["build"], build(1))
            self.assertEqual((root / "update-state.json").read_bytes(), state)
            self.assertFalse(list(root.glob(".deck-state-*")))
            result = deck.update_or_cached(root, lambda: second, mock.Mock(side_effect=AssertionError("Already staged")), say=lambda _: None)
            self.assertEqual(result["build"], build(2))

    def test_first_install_error_is_reported_and_does_not_create_a_fake_installed_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(deck.LauncherError, "No installed app"):
                deck.update_or_cached(root, mock.Mock(side_effect=OSError("offline")))
            self.assertIsNone(deck.installed(root))
            self.assertFalse((root / "update-state.json").exists())

    def test_bundled_app_is_usable_offline_before_any_update(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); first, _ = fixture(root, 1)
            with zipfile.ZipFile(root / "fixture-1.zip") as bundle: bundle.extractall(root)
            self.assertEqual(deck.installed(root)["folder"], root)
            result = deck.update_or_cached(root, mock.Mock(side_effect=OSError("offline")), say=lambda _: None)
            self.assertEqual(result["build"], first["build"])

    def test_zip_paths_and_symlinks_cannot_escape_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("../escape.txt", "/absolute.txt", r"..\escape.txt", "C:/bad.txt"):
                with self.subTest(name=name):
                    archive = root / "unsafe.zip"
                    with zipfile.ZipFile(archive, "w") as bundle: bundle.writestr(name, "unsafe")
                    digest = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
                    with self.assertRaises(deck.LauncherError): deck.extract_checked(archive, root / "stage", digest)
            archive = root / "link.zip"
            info = zipfile.ZipInfo("link"); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, "w") as bundle: bundle.writestr(info, "../escape.txt")
            digest = "sha256:" + hashlib.sha256(archive.read_bytes()).hexdigest()
            with self.assertRaises(deck.LauncherError): deck.extract_checked(archive, root / "stage", digest)
            self.assertFalse((root / "stage").exists())

    def test_proton_launch_uses_a_private_prefix_and_windows_app_data_paths(self):
        root = PurePosixPath("/home/deck/Downloads/Studio test 100%")
        app = root / "Versions/20/App/FFR Vision Studio.exe"
        original = {"HOME": "/home/deck", "SteamAppId": "game", "HTTP_PROXY": "retained"}
        args, environment, batch = deck.launch_plan(root, app, PurePosixPath("/proton/proton"),
                                                    PurePosixPath("/home/deck/.steam/steam"), original)
        self.assertEqual(args[:4], ["/proton/proton", "run", "cmd.exe", "/d"])
        self.assertEqual(args[-1], r"Z:\home\deck\Downloads\Studio test 100%\Launch Studio Deck.cmd")
        self.assertEqual(environment["STEAM_COMPAT_DATA_PATH"], str(root / "Proton"))
        self.assertEqual(environment["STEAM_COMPAT_INSTALL_PATH"], str(app.parent))
        self.assertEqual(environment["SteamAppId"], "0")
        self.assertEqual(environment["HOME"], original["HOME"])
        self.assertEqual(environment["HTTP_PROXY"], "retained")
        self.assertEqual(original["SteamAppId"], "game")
        self.assertIn('set "LOCALAPPDATA=Z:\\home\\deck\\Downloads\\Studio test 100%%\\Studio Test Data"', batch)
        self.assertIn("chcp 65001", batch)
        self.assertIn("\r\n", batch)
        self.assertIn('"Z:\\home\\deck\\Downloads\\Studio test 100%%\\Versions\\20\\App\\FFR Vision Studio.exe"', batch)
        with self.assertRaises(deck.LauncherError): deck.wine_path("/home/deck/new\nfolder")

    def test_proton_detection_supports_additional_steam_libraries_and_saved_or_manual_choice(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); home = root / "home"; home.mkdir()
            steam = home / ".local/share/Steam"; (steam / "steamapps/common").mkdir(parents=True)
            external = root / "SD card"; (external / "steamapps/common").mkdir(parents=True)
            (steam / "steamapps/libraryfolders.vdf").write_text('"libraryfolders" { "1" { "path" "' + external.as_posix() + '" } }')
            stable = steam / "steamapps/common/Proton 10.0/proton"
            experimental = external / "steamapps/common/Proton - Experimental/proton"
            for file in (stable, experimental):
                file.parent.mkdir(parents=True); file.write_text("#!/bin/sh\n"); file.chmod(0o755)
            client, libraries = deck.steam_libraries(home)
            self.assertEqual(client, steam.resolve())
            self.assertIn(external.resolve(), libraries)
            self.assertEqual(deck.choose_proton(root, client, libraries, home=home), experimental.resolve())
            (root / "deck-proton.json").write_text(json.dumps({"proton": str(stable)}))
            self.assertEqual(deck.choose_proton(root, client, libraries, home=home), stable.resolve())
            self.assertEqual(deck.choose_proton(root, client, libraries, explicit=str(experimental.parent), home=home), experimental.resolve())
            with self.assertRaises(deck.LauncherError):
                deck.choose_proton(root, client, libraries, explicit=str(root / "missing"))

    def test_shortcut_runs_the_updater_and_quotes_paths_with_spaces_and_percent(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory); (home / "Desktop").mkdir()
            root = home / "Studio 100% test"; root.mkdir()
            deck.shortcuts(root, home)
            shortcut = home / "Desktop/Sephira Studio Test.desktop"
            text = shortcut.read_text()
            self.assertIn("Terminal=true", text)
            self.assertIn("Exec=python3 ", text)
            self.assertIn("Studio 100%% test", text)
            self.assertIn('" --root "', text)
            self.assertTrue((root / deck.LAUNCHER).is_file())
            self.assertTrue((home / ".local/share/applications/Sephira Studio Test.desktop").is_file())

#!/usr/bin/env python3
"""Update the Windows test package and launch it in a separate Proton prefix."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

REPOSITORY = "biscoBen/FFR-Vison-Studio"
BRANCH = "Sephira's-Update"
LAUNCHER = "Studio Deck Launcher.py"
API = f"https://api.github.com/repos/{REPOSITORY}/releases?per_page=100"
POINTERS = ("channel", "repository", "branch", "commit", "run_id", "build")


class LauncherError(RuntimeError):
    pass


def validate_build(value):
    if (not isinstance(value, dict) or value.get("channel") != "sephira-test"
            or value.get("repository") != REPOSITORY or value.get("branch") != BRANCH
            or not isinstance(value.get("commit"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", value["commit"])
            or type(value.get("run_id")) is not int or value["run_id"] <= 0
            or type(value.get("build")) is not int or value["build"] <= 0):
        raise LauncherError("This is not a Sephira test build.")
    return {key: value[key] for key in POINTERS}


def select_release(releases):
    candidates = []
    for release in releases:
        if not isinstance(release, dict):
            continue
        try:
            if release.get("draft") or not release.get("prerelease"):
                continue
            build = validate_build(json.loads(release["body"]))
            tag = f"sephira-test-{build['run_id']}"
            if release.get("tag_name") != tag or release.get("target_commitish") != build["commit"]:
                continue
            assets = [a for a in release["assets"] if isinstance(a, dict) and a.get("name") == "Sephira-Studio-Test.zip"]
            if len(assets) != 1:
                continue
            asset = assets[0]
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", asset.get("digest") or ""):
                continue
            if asset.get("browser_download_url") != (
                    f"https://github.com/{REPOSITORY}/releases/download/{tag}/Sephira-Studio-Test.zip"):
                continue
            candidates.append({"build": build, "asset": asset})
        except (KeyError, TypeError, ValueError, LauncherError):
            continue
    if not candidates:
        raise LauncherError("No tested branch release is available.")
    return max(candidates, key=lambda r: r["build"]["run_id"])


def published_release():
    request = urllib.request.Request(API, headers={
        "User-Agent": "Sephira-Studio-Test-Steam-Deck", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return select_release(json.load(response))


def download(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": "Sephira-Studio-Test-Steam-Deck"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as output:
        received = 0
        while chunk := response.read(1024 * 1024):
            received += len(chunk)
            if received > 2 * 1024**3:
                raise LauncherError("The test download exceeds 2 GiB.")
            output.write(chunk)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".deck-state-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(value, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def assert_package(folder, expected):
    actual = validate_build(read_json(folder / "test-build.json"))
    if actual != validate_build(expected):
        raise LauncherError("The package does not match the selected release.")
    for name in ("App/FFR Vision Studio.exe", "App/flutter_windows.dll"):
        path = folder / name
        if not path.is_file() or path.is_symlink():
            raise LauncherError(f"The package is missing {name}.")
    return actual


def extract_checked(archive, folder, digest):
    checksum = hashlib.sha256()
    with archive.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            checksum.update(chunk)
    actual = checksum.hexdigest()
    if digest != "sha256:" + actual:
        raise LauncherError("The downloaded package failed its checksum check.")
    with zipfile.ZipFile(archive) as bundle:
        seen = set()
        if sum(i.file_size for i in bundle.infolist()) > 8 * 1024**3:
            raise LauncherError("The extracted package exceeds 8 GiB.")
        for info in bundle.infolist():
            name = info.filename
            path = PurePosixPath(name)
            mode = stat.S_IFMT(info.external_attr >> 16)
            if (not name or "\\" in name or ":" in name or path.is_absolute()
                    or ".." in path.parts or "\x00" in name
                    or mode not in (0, stat.S_IFREG, stat.S_IFDIR)
                    or name.casefold() in seen):
                raise LauncherError("The package contains an unsafe or duplicate path.")
            seen.add(name.casefold())
        bundle.extractall(folder)


def installed(root):
    for folder, expected in ((None, None), (root, None)):
        try:
            if folder is None:
                expected = validate_build(read_json(root / "update-state.json"))
                folder = root / "Versions" / str(expected["run_id"])
            if expected is None:
                expected = validate_build(read_json(folder / "test-build.json"))
            return {"build": assert_package(folder, expected), "folder": folder}
        except (OSError, ValueError, LauncherError):
            continue
    return None


def install_update(root, update, fetch=download):
    build = validate_build(update["build"])
    versions = root / "Versions"
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / str(build["run_id"])
    try:
        assert_package(target, build)
    except (OSError, ValueError, LauncherError):
        with tempfile.TemporaryDirectory(prefix=".deck-update-", dir=root) as temporary:
            stage = Path(temporary)
            archive = stage / "download.zip"
            fetch(update["asset"]["browser_download_url"], archive)
            extracted = stage / "package"
            extract_checked(archive, extracted, update["asset"]["digest"])
            assert_package(extracted, build)
            if target.exists():
                backup = versions / f"{build['run_id']}.incomplete-{os.getpid()}"
                if backup.exists():
                    raise LauncherError("An incomplete-package backup already exists.")
                target.rename(backup)
            extracted.rename(target)
    atomic_json(root / "update-state.json", {
        **build, "app": f"Versions/{build['run_id']}/App/FFR Vision Studio.exe"})
    return {"build": build, "folder": target}


def update_or_cached(root, get_update=published_release, fetch=download, say=print):
    current = installed(root)
    try:
        update = get_update()
        build = validate_build(update["build"])
        if current and current["build"]["run_id"] >= build["run_id"]:
            if current["build"]["run_id"] == build["run_id"] and current["build"] != build:
                raise LauncherError("The release identity changed for an installed run.")
            return current
        say(f"Downloading tested update {build['run_id']}...")
        return install_update(root, update, fetch)
    except (OSError, ValueError, KeyError, LauncherError, zipfile.BadZipFile) as error:
        if not current:
            raise LauncherError(f"No installed app is available: {error}") from error
        say(f"Update unavailable ({error}); using installed run {current['build']['run_id']}.")
        return current


def steam_libraries(home):
    candidates = (home / ".local/share/Steam", home / ".steam/steam", home / ".steam/root")
    steam = next((p.resolve() for p in candidates if (p / "steamapps").is_dir()), None)
    if steam is None:
        raise LauncherError("Steam was not found. Open Steam in Desktop Mode first.")
    libraries = [steam]
    file = steam / "steamapps/libraryfolders.vdf"
    if file.is_file():
        for value in re.findall(r'"path"\s*"((?:\\.|[^"\\])*)"', file.read_text(encoding="utf-8")):
            path = Path(value.replace("\\\\", "\\").replace('\\"', '"')).expanduser()
            if path.is_dir() and path.resolve() not in libraries:
                libraries.append(path.resolve())
    return steam, libraries


def choose_proton(root, steam, libraries, explicit=None, home=None):
    choices = []
    if explicit:
        path = Path(explicit).expanduser()
        choices.append(path / "proton" if path.is_dir() else path)
    elif (root / "deck-proton.json").is_file():
        try:
            saved = read_json(root / "deck-proton.json").get("proton")
            if isinstance(saved, str):
                choices.append(Path(saved))
        except (OSError, ValueError):
            pass
    if not explicit:
        for library in libraries:
            choices.extend(sorted((library / "steamapps/common").glob("Proton*/proton"),
                                  key=lambda p: ("Experimental" in p.parent.name,
                                      [int(x) for x in re.findall(r"\d+", p.parent.name)]), reverse=True))
        if home:
            choices.extend(sorted((steam / "compatibilitytools.d").glob("*/proton"), reverse=True))
            choices.extend(sorted((home / ".local/share/Steam/compatibilitytools.d").glob("*/proton"), reverse=True))
    chosen = next((p.resolve() for p in choices if p.is_file() and os.access(p, os.X_OK)), None)
    if chosen is None:
        raise LauncherError("Install Proton Experimental from Steam's Library > Tools, then run this again. "
                            "You can also specify --proton '/path/to/proton'.")
    return chosen


def wine_path(path):
    path = PurePosixPath(str(path))
    if not path.is_absolute() or any(c in str(path) for c in '\r\n"<>|:?*\0\\'):
        raise LauncherError("This folder cannot be represented as a Windows Z: path.")
    return "Z:" + str(path).replace("/", "\\")


def launch_plan(root, app, proton, steam, environment):
    data = wine_path(root / "Studio Test Data").replace("%", "%%")
    executable = wine_path(app).replace("%", "%%")
    directory = wine_path(app.parent).replace("%", "%%")
    batch = "\r\n".join(("@echo off", "chcp 65001 >nul", "setlocal", f'set "LOCALAPPDATA={data}"',
                         f'cd /d "{directory}"', f'"{executable}"', "exit /b %errorlevel%", ""))
    env = dict(environment)
    env.update({"STEAM_COMPAT_CLIENT_INSTALL_PATH": str(steam),
                "STEAM_COMPAT_DATA_PATH": str(root / "Proton"),
                "STEAM_COMPAT_INSTALL_PATH": str(app.parent),
                "STEAM_COMPAT_APP_ID": "0", "SteamAppId": "0", "SteamGameId": "0",
                "PROTON_LOG": "1", "PROTON_LOG_DIR": str(root / "logs")})
    args = [str(proton), "run", "cmd.exe", "/d", "/c", wine_path(root / "Launch Studio Deck.cmd")]
    return args, env, batch


def desktop_quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"').replace(
        chr(96), "\\" + chr(96)).replace("$", "\\$").replace("%", "%%") + '"'


def shortcuts(root, home):
    bootstrap = root / LAUNCHER
    if not bootstrap.is_file():
        shutil.copyfile(Path(__file__).resolve(), bootstrap)
    content = ("[Desktop Entry]\nType=Application\nName=Sephira Studio Test\n"
               "Comment=Update and run Vision Studio through Proton\nTerminal=true\n"
               "Icon=applications-games\nCategories=Game;\n"
               f"Exec=python3 {desktop_quote(bootstrap)} --root {desktop_quote(root)}\n")
    directories = [home / ".local/share/applications"]
    if (home / "Desktop").is_dir():
        directories.append(home / "Desktop")
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        file = directory / "Sephira Studio Test.desktop"
        file.write_text(content, encoding="utf-8")
        file.chmod(0o755)


@contextmanager
def launch_lock(root):
    import fcntl
    with (root / ".deck-launcher.lock").open("a") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise LauncherError("Studio is already running. Close it before checking for updates.") from error
        yield


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--proton", help="An installed Proton folder or its proton executable.")
    parser.add_argument("--update-only", action="store_true")
    parser.add_argument("--no-shortcut", action="store_true")
    options = parser.parse_args(argv)
    root = options.root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if sys.platform != "linux":
        raise LauncherError("Use Start Studio Test.cmd on Windows. This launcher is for SteamOS/Linux.")
    with launch_lock(root):
        current = installed(root)
        # Updates may replace the helper as well as the app. Only use helpers
        # from the validated installed package, retaining the same data root.
        helper = current["folder"] / LAUNCHER if current else None
        if helper and helper.is_file() and helper.resolve() != Path(__file__).resolve():
            os.execv(sys.executable, [sys.executable, str(helper), "--root", str(root), *(argv if argv is not None else sys.argv[1:])])
        home = Path.home()
        steam, libraries = (None, []) if options.update_only else steam_libraries(home)
        proton = None if options.update_only else choose_proton(root, steam, libraries, options.proton, home)
        selected = update_or_cached(root)
        print(f"Studio run {selected['build']['run_id']}, commit {selected['build']['commit'][:7]}")
        if not options.no_shortcut:
            shortcuts(root, home)
        if options.update_only:
            return 0
        atomic_json(root / "deck-proton.json", {"proton": str(proton)})
        (root / "Proton").mkdir(exist_ok=True)
        (root / "logs").mkdir(exist_ok=True)
        (root / "Studio Test Data").mkdir(exist_ok=True)
        app = selected["folder"] / "App/FFR Vision Studio.exe"
        args, environment, batch = launch_plan(root, app, proton, steam, os.environ)
        (root / "Launch Studio Deck.cmd").write_bytes(batch.encode("utf-8"))
        for library in libraries:
            common = library / "steamapps/common"
            if common.is_dir():
                for folder in common.iterdir():
                    if folder.is_dir() and "FINAL FANTASY RESONANCE" in folder.name.upper():
                        print(f"Resonance folder (select this in Studio): {wine_path(folder)}")
        print("Starting Studio. Close Resonance before installing mods.")
        print(f"Proton logs: {root / 'logs'}")
        with (root / "logs/proton-console.log").open("a", encoding="utf-8") as log:
            result = subprocess.run(args, env=environment, cwd=app.parent, stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise LauncherError(f"Proton exited with code {result.returncode}. See {root / 'logs/proton-console.log'}.")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (LauncherError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)

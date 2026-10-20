#!/usr/bin/env python3
"""Package a validated Windows app with the portable test shortcut and updater."""

import argparse
import json
from pathlib import Path
import re
import zipfile


def package(app, output, commit, run_id, branch="Sephira's-Update", build=15):
    if branch != "Sephira's-Update" or not re.fullmatch(r"[0-9a-f]{40}", commit) or run_id <= 0:
        raise ValueError("Test downloads must identify a Sephira's-Update commit and run.")
    for name in ["FFR Vision Studio.exe", "flutter_windows.dll"]:
        if not (app / name).is_file():
            raise ValueError(f"App bundle is missing {name}")
    metadata = {
        "channel": "sephira-test", "repository": "biscoBen/FFR-Vison-Studio",
        "branch": branch, "commit": commit, "run_id": run_id, "build": build,
    }
    launchers = Path(__file__).resolve().parent.parent / "windows-test"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                bundle.write(path, "App/" + path.relative_to(app).as_posix())
        for path in sorted(launchers.iterdir()):
            if path.is_file():
                # Windows command files use CRLF even when checked out on Linux.
                bundle.writestr(path.name, path.read_text().replace("\r\n", "\n").replace("\n", "\r\n"))
        deck = launchers.parent / "steam-deck"
        for name in ("Start Studio Test.sh", "Studio Deck Launcher.py", "Update my mod.sh", "Deck Mod Sync.py"):
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = (0o100755 << 16)
            source = launchers.parent / 'assets/existing_visions/payload/_ffr_deck_sync.py' if name == 'Deck Mod Sync.py' else deck / name
            bundle.writestr(info, source.read_text(encoding="utf-8").replace("\r\n", "\n"))
        bundle.writestr("test-build.json", json.dumps(metadata, indent=2) + "\n")
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    # The Deck only needs this small native installer, not the Windows app ZIP.
    with zipfile.ZipFile(output.parent / 'Resonance-Deck-Sync.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
        for name, source in (
            ('Update my mod.sh', deck / 'Update my mod.sh'),
            ('Deck Mod Sync.py', launchers.parent / 'assets/existing_visions/payload/_ffr_deck_sync.py'),
        ):
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = 0o100755 << 16
            bundle.writestr(info, source.read_text(encoding='utf-8').replace('\r\n', '\n'))
        bundle.writestr('test-build.json', json.dumps(metadata, indent=2) + '\n')
        bundle.writestr('Read me.txt', 'On PC: build successfully, then Export / import snapshots > Export Deck snapshot.\n'
                        'Copy/extract Resonance-Mod-Snapshot.zip on Deck and run its Install snapshot.sh; no GitHub or build is needed.\n'
                        'On Steam Deck: extract this ZIP into Downloads/FFR Mod/Installer.\n'
                        'In Desktop Mode, run: bash "$HOME/Downloads/FFR Mod/Installer/Update my mod.sh"\n'
                        'Choose 1, then enter your private owner/repository and a Contents: read token.\n'
                        'Close Resonance. The installer detects the game and creates a desktop shortcut.\n'
                        'Settings/backups/helper stay in Downloads/FFR Mod/Deck Sync.\n'
                        'Optional GitHub publishing is separate. See the launch/snapshot guide for local import and runtime launch options.\n')
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--branch", default="Sephira's-Update")
    parser.add_argument("--build", type=int, default=15)
    args = parser.parse_args()
    package(args.app_dir, args.output, args.commit, args.run_id, args.branch, args.build)
    print(f"Packaged {args.output}")

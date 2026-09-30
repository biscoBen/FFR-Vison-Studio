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
        bundle.writestr("test-build.json", json.dumps(metadata, indent=2) + "\n")
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
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

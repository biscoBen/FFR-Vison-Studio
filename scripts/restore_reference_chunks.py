#!/usr/bin/env python3
"""Restore large reference files after extracting all collector ZIPs together."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


def _path(root: Path, value: object) -> Path:
    if not isinstance(value, str) or "\\" in value or ":" in value:
        raise ValueError(f"Invalid reference path: {value!r}")
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError(f"Invalid reference path: {value!r}")
    result = root.joinpath(*relative.parts).resolve()
    if result == root or not result.is_relative_to(root):
        raise ValueError(f"Reference path escapes collection: {value!r}")
    return result


def _size(value: object) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"Invalid byte length: {value!r}")
    return value


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(root: Path) -> int:
    root = root.resolve(strict=True)
    ledger = json.loads((root / "split-files.json").read_text(encoding="utf-8-sig"))
    if ledger.get("schema") != 1 or not isinstance(ledger.get("files"), list):
        raise ValueError("Unsupported split-file ledger")
    plans = []
    destinations: set[Path] = set()
    all_chunks: set[Path] = set()
    for entry in ledger["files"]:
        destination = _path(root, entry["path"])
        if destination in destinations or destination.is_relative_to(root / "_reference_chunks"):
            raise ValueError(f"Duplicate or reserved destination: {entry['path']}")
        destinations.add(destination)
        size = _size(entry["bytes"])
        digest = entry["sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid SHA256")
        if not isinstance(entry.get("parts"), list) or not entry["parts"]:
            raise ValueError("Missing chunk list")
        chunks = []
        for part in entry["parts"]:
            path = _path(root, part["path"])
            if not path.is_relative_to(root / "_reference_chunks") or path in all_chunks:
                raise ValueError(f"Duplicate or invalid chunk: {part['path']}")
            all_chunks.add(path)
            length = _size(part["bytes"])
            if not path.is_file() or path.stat().st_size != length:
                raise ValueError(f"Missing or incomplete chunk: {part['path']}")
            chunks.append((path, length))
        if sum(length for _, length in chunks) != size:
            raise ValueError(f"Chunk lengths do not match {entry['path']}")
        if destination.exists():
            if not destination.is_file() or destination.stat().st_size != size or _hash(destination) != digest:
                raise ValueError(f"Existing destination differs: {entry['path']}")
            continue
        plans.append((destination, size, digest, chunks))

    restored = 0
    for destination, size, digest, chunks in plans:
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation preserves existing files; delete only our incomplete output.
        stream = destination.open("xb")
        try:
            hasher = hashlib.sha256()
            written = 0
            with stream:
                for path, length in chunks:
                    remaining = length
                    with path.open("rb") as source:
                        while remaining:
                            block = source.read(min(1024 * 1024, remaining))
                            if not block:
                                raise ValueError(f"Chunk ended early: {path}")
                            remaining -= len(block)
                            stream.write(block)
                            hasher.update(block)
                            written += len(block)
            if written != size or hasher.hexdigest() != digest:
                raise ValueError(f"Restored length/SHA256 differs: {destination}")
        except BaseException:
            stream.close()
            destination.unlink()
            raise
        restored += 1
    return restored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Folder containing all extracted ZIP parts and split-files.json")
    args = parser.parse_args()
    print(f"Restored {restore(args.root)} files; original lengths and SHA256 verified.")


if __name__ == "__main__":
    main()

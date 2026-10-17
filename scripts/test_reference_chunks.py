import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from restore_reference_chunks import restore


class ReferenceChunkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.body = b"native package\x00\xff"
        self.destination = self.root / "legacy/FFRS/Content/example.uexp"
        parts = []
        for number, body in enumerate((self.body[:7], self.body[7:])):
            name = f"_reference_chunks/000001/{number:06}.bin"
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            parts.append({"path": name, "bytes": len(body)})
        self.ledger = {"schema": 1, "files": [{
            "path": self.destination.relative_to(self.root).as_posix(),
            "bytes": len(self.body), "sha256": hashlib.sha256(self.body).hexdigest(),
            "parts": parts,
        }]}

    def save(self):
        (self.root / "split-files.json").write_text(json.dumps(self.ledger), encoding="utf-8-sig")

    def test_exact_restoration_and_repeat(self):
        self.save()
        self.assertEqual(restore(self.root), 1)
        self.assertEqual(self.destination.read_bytes(), self.body)
        self.assertEqual(restore(self.root), 0)

    def test_hash_failure_removes_incomplete_destination(self):
        self.ledger["files"][0]["sha256"] = "0" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "SHA256"):
            restore(self.root)
        self.assertFalse(self.destination.exists())

    def test_missing_or_truncated_chunk_creates_no_output(self):
        chunk = self.root / self.ledger["files"][0]["parts"][0]["path"]
        for body in (b"short", None):
            with self.subTest(body=body):
                if body is None:
                    chunk.unlink()
                else:
                    chunk.write_bytes(body)
                self.save()
                with self.assertRaisesRegex(ValueError, "Missing or incomplete"):
                    restore(self.root)
                self.assertFalse(self.destination.exists())

    def test_existing_different_file_is_preserved(self):
        self.destination.parent.mkdir(parents=True)
        self.destination.write_bytes(b"keep existing")
        self.save()
        with self.assertRaisesRegex(ValueError, "Existing destination differs"):
            restore(self.root)
        self.assertEqual(self.destination.read_bytes(), b"keep existing")

    def test_path_escape_and_reserved_destination_are_rejected(self):
        for value in ("../escape", "/absolute", "C:/absolute", "..\\escape", "_reference_chunks/new"):
            with self.subTest(value=value):
                self.ledger["files"][0]["path"] = value
                self.save()
                with self.assertRaises(ValueError):
                    restore(self.root)
        self.assertFalse(self.destination.exists())

    def test_duplicate_chunks_and_wrong_lengths_are_rejected(self):
        entry = self.ledger["files"][0]
        entry["parts"][1] = dict(entry["parts"][0])
        self.save()
        with self.assertRaisesRegex(ValueError, "Duplicate or invalid chunk"):
            restore(self.root)
        entry["parts"] = entry["parts"][:1]
        self.save()
        with self.assertRaisesRegex(ValueError, "Chunk lengths"):
            restore(self.root)
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()

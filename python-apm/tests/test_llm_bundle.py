"""Build-time bundle tests; ELF headers here are synthetic fixtures, not agents."""

import hashlib
import io
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest

IMAGE_DIR = Path(__file__).resolve().parents[1]


def elf_fixture(machine):
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", header, 18, machine)
    return bytes(header) + b"test-only-payload"


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.archive = self.root / "module.tar.gz"
        self.dest = self.root / "staging" / "dist"
        self.members = [
            ("linux/amd64/whatap_python", elf_fixture(62)),
            ("linux/arm64/whatap_python", elf_fixture(183)),
            ("linux/amd64/._whatap_python", b"AppleDouble metadata"),
            ("darwin/arm64/whatap_python", b"not a Linux payload"),
        ]

    def make_archive(self):
        with tarfile.open(self.archive, "w:gz") as archive:
            for name, payload in self.members:
                member = tarfile.TarInfo(name)
                member.mode = 0o644
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def install(self, digest):
        return subprocess.run(
            [sys.executable, str(IMAGE_DIR / "bundle_llm.py"),
             "--archive", str(self.archive), "--sha256", digest,
             "--destination", str(self.dest)],
            text=True, capture_output=True, timeout=10,
        )

    def test_installs_only_linux_binaries_at_sdk_paths(self):
        result = self.install(self.make_archive())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        paths = sorted(str(p.relative_to(self.dest)) for p in self.dest.rglob("*") if p.is_file())
        self.assertEqual(paths, ["linux/amd64/whatap_python", "linux/arm64/whatap_python"])
        for name, payload in self.members[:2]:
            self.assertEqual((self.dest / name).read_bytes(), payload)
            self.assertEqual((self.dest / name).stat().st_mode & 0o777, 0o755)

    def test_rejects_checksum_mismatch_before_writing_files(self):
        self.make_archive()
        result = self.install("0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertFalse(self.dest.exists())

    def test_rejects_missing_or_duplicate_linux_binary_before_writing(self):
        for members in ([self.members[0]], self.members + [self.members[0]]):
            with self.subTest(members=len(members)):
                self.members = members
                result = self.install(self.make_archive())
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Missing, duplicate or non-regular", result.stderr)
                self.assertFalse(self.dest.exists())

    def test_rejects_wrong_elf_architecture_before_writing(self):
        self.members[1] = ("linux/arm64/whatap_python", elf_fixture(62))
        result = self.install(self.make_archive())
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid Linux ELF architecture", result.stderr)
        self.assertFalse(self.dest.exists())

    def test_never_extracts_unselected_paths_or_links(self):
        self.members.append(("../../escaped-file", b"must-not-be-written"))
        self.make_archive()
        # Build a link fixture separately because make_archive writes regular files.
        with tarfile.open(self.archive, "w:gz") as archive:
            for name, payload in self.members:
                member = tarfile.TarInfo(name)
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
            link = tarfile.TarInfo("ignored-symlink")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc/passwd"
            archive.addfile(link)
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        result = self.install(digest)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.root / "escaped-file").exists())
        self.assertFalse((self.dest / "ignored-symlink").exists())
        self.assertEqual(len([p for p in self.dest.rglob("*") if p.is_file()]), 2)

    def test_rejects_symlink_in_place_of_required_binary(self):
        with tarfile.open(self.archive, "w:gz") as archive:
            link = tarfile.TarInfo("linux/amd64/whatap_python")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc/passwd"
            archive.addfile(link)
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        result = self.install(digest)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("non-regular", result.stderr)
        self.assertFalse(self.dest.exists())


if __name__ == "__main__":
    unittest.main()

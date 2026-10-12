"""Bundle the official, separately distributed LLM collector at SDK 2.2.1 paths.

Only Linux executables are copied. Never extract archive paths or replace the
normal APM collector in whatap/agent or WHATAP_HOME/whatap_python.
"""

import argparse
import hashlib
from pathlib import Path
import shutil
import struct
import tarfile
import tempfile
import urllib.request


LLM_URL = "https://repo.whatap.io/python/llm/whatap-python-llm.tar.gz"
# The upstream URL is mutable. Changing this pin requires revalidating the SDK
# path contract and both Linux binaries; never silently accept a changed bundle.
LLM_SHA256 = "090ddd8af06c504c2fddaacb41b7830c1ab5f5b8c0e4e291b23c3115927c090e"
LINUX_MACHINES = {"amd64": 62, "arm64": 183}
DOWNLOAD_TIMEOUT_SECONDS = 60


def bundle(archive_path, expected_sha256, destination):
    digest = hashlib.sha256()
    with archive_path.open("rb") as archive_file:
        for chunk in iter(lambda: archive_file.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise ValueError("LLM archive SHA-256 mismatch")

    # Validate both payloads before writing either; fixed destinations mean
    # ignored archive members (including AppleDouble files) are never extracted.
    payloads = {}
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        for arch, machine in LINUX_MACHINES.items():
            name = "linux/{}/whatap_python".format(arch)
            matches = [member for member in members if member.name == name]
            if len(matches) != 1 or not matches[0].isfile():
                raise ValueError("Missing, duplicate or non-regular LLM binary: " + name)
            source = archive.extractfile(matches[0])
            if source is None:
                raise ValueError("Unreadable LLM binary: " + name)
            with source:
                payload = source.read()
            if (len(payload) < 64 or payload[:6] != b"\x7fELF\x02\x01"
                    or struct.unpack_from("<H", payload, 18)[0] != machine):
                raise ValueError("Invalid Linux ELF architecture: " + name)
            payloads[name] = payload

    for name, payload in payloads.items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        target.chmod(0o755)
        print("Bundled " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Use a previously downloaded archive")
    parser.add_argument("--sha256", default=LLM_SHA256)
    parser.add_argument("--destination", type=Path, default=Path("/opt/whatap-agent-dist"))
    args = parser.parse_args()
    if args.archive:
        bundle(args.archive, args.sha256, args.destination)
    else:
        with tempfile.TemporaryDirectory() as temporary:
            archive_path = Path(temporary) / "whatap-python-llm.tar.gz"
            with urllib.request.urlopen(LLM_URL, timeout=DOWNLOAD_TIMEOUT_SECONDS) as source:
                with archive_path.open("wb") as target:
                    shutil.copyfileobj(source, target)
            bundle(archive_path, args.sha256, args.destination)


if __name__ == "__main__":
    main()

"""Run only inside the built Linux image, without network or real credentials.

Exercises non-root init, immutable payload identity, and the actual Python
sitecustomize -> SDK -> native APM/LLM startup path. It does NOT prove telemetry.
"""

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

HOME = Path("/whatap-agent")
EXPECTED = {
    "amd64": "227d7343cecbb4a37c0380918e491f0dcd85fcfa9cd824ef518feb3d793432a3",
    "arm64": "388187a035a0c3adcd51948457b7743e7b2d0f5272421d0a8602541ea0674409",
}

assert os.getuid() == 1001, "Run the image as its default non-root UID"
assert not (HOME / "whatap.conf").exists(), "Use a fresh isolated tmpfs"
env = dict(os.environ, WHATAP_HOME=str(HOME), WHATAP_LICENSE="test-only", WHATAP_HOST="127.0.0.1", WHATAP_PORT="6600")
subprocess.run(["/init.sh"], env=env, check=True)
assert "llm_enabled=" not in (HOME / "whatap.conf").read_text()
for arch, digest in EXPECTED.items():
    binary = HOME / "linux" / arch / "whatap_python"
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == digest
    assert os.access(binary, os.X_OK)
# Repair an existing volume without touching the Python package.
(HOME / "whatap" / "preserve-test-marker").write_text("keep")
(HOME / "linux" / "amd64" / "whatap_python").unlink()
subprocess.run(["/init.sh"], env=env, check=True)
assert (HOME / "whatap" / "preserve-test-marker").read_text() == "keep"
assert (HOME / "linux" / "amd64" / "whatap_python").is_file()

# Synthetic credentials plus Docker --network none prohibit collector traffic.
(HOME / "whatap.conf").write_text(
    "license=test-only\nwhatap.server.host=127.0.0.1\nwhatap.server.port=6600\n"
    "app_name=llm-init-smoke\napp_process_name=python\n"
    "whatap_code_start=true\napm_enabled=true\nllm_enabled=true\n"
    "llm_accesskey=test-only-llm\nllm.whatap.server.host=127.0.0.1\n"
    "counter_thread_enabled=true\n"
)
probe = r'''
import json, os, pathlib, platform, time
home = pathlib.Path(os.environ['WHATAP_HOME'])
started = {}
limit = time.monotonic() + 8
while time.monotonic() < limit:
    for kind, name in [('apm','whatap_python.pid'), ('llm','whatap_python.pid.llm')]:
        f = home / name
        if f.exists():
            try:
                pid = int(f.read_text().strip())
                proc = pathlib.Path('/proc') / str(pid)
                argv = (proc / 'cmdline').read_bytes().split(b'\0')
                exe = os.readlink(proc / 'exe')
                if not argv or not argv[0]:
                    continue
                started[kind] = {'pid':pid,'exe':exe,'cwd':os.readlink(proc / 'cwd'),'argv':[v.decode() for v in argv if v]}
            except (OSError, ValueError):
                pass
    if len(started) == 2:
        break
    time.sleep(0.1)
print('PROCESS_OBSERVATIONS=' + json.dumps(started, sort_keys=True), flush=True)
assert set(started) == {'apm','llm'}, 'Expected native processes not observed: ' + json.dumps(started)
assert '--llm' in started['llm']['argv']
assert '--llm' not in started['apm']['argv']
arch = {'x86_64':'amd64','aarch64':'arm64'}[platform.machine()]
for kind, process in started.items():
    relative = 'linux/{}/whatap_python' if kind == 'llm' else 'whatap/agent/linux/{}/whatap_python'
    expected = home / relative.format(arch)
    if process['exe'] == '/usr/bin/qemu-aarch64-static':
        assert arch == 'arm64'
        assert process['argv'][0] == process['exe']
        guest_binary = (pathlib.Path(process['cwd']) / process['argv'][1]).resolve()
        assert guest_binary == expected, process
        process['execution'] = 'qemu-arm64'
    else:
        assert process['exe'] == str(expected), process
        process['execution'] = 'native'
assert started['apm']['pid'] != started['llm']['pid']
print('STARTUP_PROOF=' + json.dumps(started, sort_keys=True), flush=True)
'''
env["PYTHONPATH"] = str(HOME) + ":" + str(HOME / "whatap" / "bootstrap")
env["PYTHONUNBUFFERED"] = "1"
# Cross-architecture emulation can spend much longer importing the SDK before
# the probe itself starts. Keep an explicit bound rather than treating it as PASS.
startup_timeout = int(os.environ.get("SMOKE_STARTUP_TIMEOUT_SECONDS", "20"))
try:
    result = subprocess.run([sys.executable, "-c", probe], env=env, text=True, capture_output=True, timeout=startup_timeout)
except subprocess.TimeoutExpired as error:
    print("SDK startup exceeded {} seconds".format(startup_timeout), flush=True)
    print(error.stdout or b"")
    print(error.stderr or b"")
    raise SystemExit(1)
print(result.stdout)
if result.returncode:
    print(result.stderr)
    raise SystemExit(result.returncode)
print(json.dumps({"passed": True, "uid": os.getuid(), "architecture": platform.machine(), "sdk": "2.2.1", "telemetry_verified": False}))

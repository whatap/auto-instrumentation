"""Run the image's generated init script with only filesystem roots redirected.

The fixture payload is not an agent binary. Real-image/runtime verification is
separate; these tests exercise offline copying and configuration preservation.
"""

import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest


IMAGE_DIR = Path(__file__).resolve().parents[1]


class InitScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.home = self.root / "home"
        self.dist = self.root / "dist"
        self.home.mkdir()
        (self.dist / "whatap").mkdir(parents=True)
        (self.dist / "whatap" / "__init__.py").write_text("# fixture package\n")
        self.module = self.dist / "linux"
        for arch in ("amd64", "arm64"):
            directory = self.module / arch
            directory.mkdir(parents=True)
            binary = directory / "whatap_python"
            binary.write_bytes(b"fixture-llm-payload\n")
            binary.chmod(0o755)

        # Execute the Dockerfile's actual echo-based /init.sh generator, not a
        # handwritten approximation. Its output is redirected into scratch.
        dockerfile = (IMAGE_DIR / "Dockerfile").read_text()
        start = dockerfile.index("RUN echo '#!/bin/sh'")
        end = dockerfile.index("chmod +x /init.sh", start) + len("chmod +x /init.sh")
        generated = self.root / "init.sh"
        command = dockerfile[start + len("RUN "):end].replace("/init.sh", str(generated))
        subprocess.run(["/bin/sh", "-ec", command], check=True, cwd=self.root)
        script = generated.read_text()
        script = script.replace("/opt/whatap-agent-dist", str(self.dist))
        script = script.replace("/whatap-agent", str(self.home))
        generated.write_text(script)
        self.script = generated

    def run_init(self):
        return subprocess.run(
            ["/bin/sh", str(self.script)],
            cwd=self.root,
            env={"PATH": os.defpath, "WHATAP_LICENSE": "test-only", "WHATAP_HOST": "127.0.0.1", "WHATAP_PORT": "6600"},
            text=True,
            capture_output=True,
            timeout=10,
        )

    def test_seeds_llm_module_when_python_package_already_exists(self):
        (self.home / "whatap").mkdir()
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        target = self.home / "linux" / "amd64" / "whatap_python"
        self.assertTrue(target.is_file(), "Existing whatap package must not suppress LLM module injection")
        self.assertEqual(target.read_bytes(), b"fixture-llm-payload\n")

    def test_empty_volume_gets_both_packages_and_executable_permissions(self):
        payload = self.module / "amd64" / "whatap_python"
        payload.chmod(0o755)
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / "whatap" / "__init__.py").is_file())
        installed = self.home / "linux" / "amd64" / "whatap_python"
        self.assertEqual(installed.read_bytes(), payload.read_bytes())
        self.assertTrue(os.access(installed, os.X_OK))
        self.assertIn("whatap_code_start=true", (self.home / "whatap.conf").read_text())

    def test_preserves_custom_llm_configuration_and_repeated_init(self):
        (self.home / "whatap.conf").write_text(
            "llm_accesskey=test-only-llm\nllm.whatap.server.host=127.0.0.2\n"
            "llm_enabled=true\napp_name=custom-app\n"
            "whatap_code_start=false\napm_enabled=false\n"
        )
        for _ in range(2):
            result = self.run_init()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        config = (self.home / "whatap.conf").read_text()
        self.assertIn("llm_accesskey=test-only-llm\n", config)
        self.assertIn("llm.whatap.server.host=127.0.0.2\n", config)
        self.assertIn("llm_enabled=true\n", config)
        self.assertIn("app_name=custom-app\n", config)
        self.assertIn("whatap_code_start=true\n", config)
        # Preserve the existing APM init gate policy; this change only bundles LLM.
        self.assertIn("apm_enabled=true\n", config)
        self.assertEqual(sorted(p.name for p in (self.home / "linux").iterdir()), ["amd64", "arm64"])

    def test_does_not_enable_llm_or_replace_existing_apm_binary(self):
        (self.home / "whatap").mkdir()
        apm_binary = self.home / "whatap_python"
        apm_binary.write_bytes(b"existing-apm-binary")
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(apm_binary.read_bytes(), b"existing-apm-binary")
        config = (self.home / "whatap.conf").read_text()
        self.assertNotIn("llm_enabled=", config)
        self.assertNotIn("llm_accesskey=", config)
        self.assertFalse((self.home / "whatap_python.pid.llm").exists())

    def test_repairs_partial_llm_directory(self):
        (self.home / "whatap").mkdir()
        directory = self.home / "linux" / "amd64"
        directory.mkdir(parents=True)
        (directory / "whatap_python").write_bytes(b"old-or-incomplete-binary")
        result = self.run_init()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for arch in ("amd64", "arm64"):
            self.assertEqual((self.home / "linux" / arch / "whatap_python").read_bytes(), b"fixture-llm-payload\n")

    def test_empty_first_arch_binary_is_fatal_even_if_second_arch_is_valid(self):
        (self.module / "amd64" / "whatap_python").write_bytes(b"")
        result = self.run_init()
        self.assertNotEqual(result.returncode, 0, "An empty amd64 payload must not be hidden by a valid arm64 payload")
        self.assertNotIn("done. whatap.conf", result.stdout)

    def test_missing_module_bundle_fails_instead_of_reporting_success(self):
        (self.home / "whatap").mkdir()
        shutil.rmtree(self.module)
        result = self.run_init()
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("done. whatap.conf", result.stdout)


if __name__ == "__main__":
    unittest.main()

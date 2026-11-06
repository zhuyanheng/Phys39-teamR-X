"""Release verification must tolerate raster changes but detect evidence changes."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from analysis import build_a4_pdf as a4


class A4ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        for name in a4.SOURCE_INPUTS + a4.RENDERED_ASSETS:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((name + "\n").encode())
        self.patch = patch.multiple(
            a4, ROOT=root, SOURCE=root / a4.SOURCE.relative_to(a4.ROOT),
            PDF=root / a4.PDF.relative_to(a4.ROOT),
            BUILD_RECORD=root / a4.BUILD_RECORD.relative_to(a4.ROOT),
            RELEASE_RECORD=root / a4.RELEASE_RECORD.relative_to(a4.ROOT))
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "source")
        source_commit = self.git("rev-parse", "HEAD")
        a4.PDF.parent.mkdir(parents=True, exist_ok=True)
        a4.PDF.write_bytes(b"fixture: exact delivered PDF bytes")
        build = {
            "git_source_checkpoint": source_commit,
            "source_input_sha256": a4.check_source(source_commit),
            "source_sha256": a4.digest(a4.SOURCE),
            "pdf_sha256": a4.digest(a4.PDF),
            "rendered_asset_sha256": {name: a4.digest(root / name)
                                       for name in a4.RENDERED_ASSETS},
        }
        a4.BUILD_RECORD.write_text(json.dumps(build))
        self.git("add", ".")
        self.git("commit", "-qm", "PDF artifact")
        self.record = {"source_checkpoint": source_commit,
                       "pdf_commit": self.git("rev-parse", "HEAD"),
                       "pdf_sha256": a4.digest(a4.PDF)}

    def git(self, *args):
        return subprocess.check_output(
            ["git", "-c", "user.name=A4 Test", "-c", "user.email=a4@example.test",
             "-c", "commit.gpgsign=false", *args], cwd=a4.ROOT, text=True).strip()

    def test_regenerated_png_does_not_invalidate_release(self):
        a4.verify_release(self.record)
        for name in a4.RENDERED_ASSETS:
            (a4.ROOT / name).write_bytes(b"different rasterizer output")
        a4.verify_release(self.record)

    def test_each_changed_source_or_numerical_input_is_rejected(self):
        for name in a4.SOURCE_INPUTS:
            with self.subTest(name=name):
                path = a4.ROOT / name
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b"changed")
                    with self.assertRaisesRegex(ValueError, "Source/checkpoint mismatch"):
                        a4.verify_release(self.record)
                finally:
                    path.write_bytes(original)

    def test_changed_pdf_is_rejected(self):
        a4.PDF.write_bytes(b"different PDF")
        with self.assertRaisesRegex(ValueError, "PDF bytes"):
            a4.verify_release(self.record)

    def test_tampered_build_record_is_rejected(self):
        build = json.loads(a4.BUILD_RECORD.read_text())
        build["rendered_asset_sha256"] = {}
        a4.BUILD_RECORD.write_text(json.dumps(build))
        with self.assertRaisesRegex(ValueError, "Build record differs"):
            a4.verify_release(self.record)


if __name__ == "__main__":
    unittest.main()

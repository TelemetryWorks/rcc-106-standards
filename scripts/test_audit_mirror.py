"""Offline checks for mirror-only hashing, discrepancy detection and resume."""

import contextlib
import hashlib
import http.client
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

import audit_mirror as audit


class Response(io.BytesIO):
    status = 200
    url = "https://release-assets.githubusercontent.com/example?secret=not-recorded"
    headers = {"Content-Length": "3", "Content-Type": "application/octet-stream"}


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.output = self.root / "evidence"
        self.sha = hashlib.sha256(b"abc").hexdigest()
        self.doc = {
            "edition": "test", "asset": "a_local.bin", "path": "files/test/a local.bin",
            "mirror_url": f"https://github.com/{audit.REPO}/releases/download/test/a_local.bin",
            "size": 3, "sha256": self.sha,
            "kind": "companion", "title": "Fixture", "retrieved": "2026-11-03",
            "distribution": "unknown", "original_urls": ["https://example.com/source.bin"],
            "original_filenames": ["source.bin"],
        }
        self.asset = {"id": 1, "name": "a_local.bin", "size": 3, "state": "uploaded",
                      "digest": "sha256:" + self.sha, "browser_download_url": self.doc["mirror_url"]}
        self.releases = [{"id": 1, "tag": "test", "draft": False, "prerelease": False,
                          "assets": [self.asset]}]

    def run_audit(self, resume=False, final=None, body=b"abc"):
        content = "[[document]]\n" + "\n".join(f"{k} = {json.dumps(v)}" for k, v in self.doc.items())
        (self.root / "manifest.toml").write_text(content)
        argv = ["audit", "--output", str(self.output)] + (["--resume"] if resume else [])
        with mock.patch.object(audit, "ROOT", self.root), \
                mock.patch("sys.argv", argv), \
                mock.patch.object(audit.subprocess, "check_output", return_value=b"commit\n"), \
                mock.patch.object(audit, "inventory", side_effect=[self.releases, final or self.releases]), \
                mock.patch.object(audit.urllib.request, "urlopen", side_effect=lambda *a, **k: Response(body)) as network, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = audit.main()
        return code, json.loads((self.output / "summary.json").read_text()), network

    def test_real_received_bytes_and_local_name_mapping(self):
        code, summary, network = self.run_audit()
        self.assertEqual(code, 0)
        self.assertEqual(summary["passing_records"], 1)
        self.assertEqual(summary["local_filename_mappings"], 1)
        self.assertEqual(network.call_args.args[0].full_url, self.doc["mirror_url"])
        self.assertNotIn("secret", (self.output / "downloads.jsonl").read_text())

    def test_wrong_bytes_same_size_fail(self):
        code, summary, _ = self.run_audit(body=b"xyz")
        self.assertEqual(code, 1)
        self.assertIn("sha256_mismatch", summary["failed_records"][0]["failures"])

    def test_truncated_bytes_fail(self):
        code, summary, _ = self.run_audit(body=b"ab")
        self.assertEqual(code, 1)
        self.assertEqual(summary["download_statuses"], {"size_mismatch": 1})

    def test_missing_asset_fails(self):
        self.releases[0]["assets"] = []
        code, summary, network = self.run_audit()
        self.assertEqual(code, 1)
        self.assertIn("missing_asset", summary["failed_records"][0]["failures"])
        network.assert_not_called()

    def test_extra_asset_is_downloaded_and_reported(self):
        self.releases[0]["assets"].append({**self.asset, "id": 2, "name": "extra.bin"})
        code, summary, network = self.run_audit()
        self.assertEqual(code, 1)
        self.assertEqual(len(summary["extra_assets"]), 1)
        self.assertEqual(network.call_count, 2)

    def test_missing_download_evidence_fails(self):
        with mock.patch.object(audit.concurrent.futures.ThreadPoolExecutor, "map", return_value=iter([])):
            code, summary, network = self.run_audit()
        self.assertEqual(code, 1)
        self.assertEqual(summary["missing_download_asset_ids"], [1])
        self.assertIn("missing_download_evidence", summary["failed_records"][0]["failures"])
        network.assert_not_called()

    def test_duplicate_extra_asset_names_fail(self):
        extra = {**self.asset, "id": 2, "name": "extra.bin"}
        self.releases[0]["assets"].extend([extra, {**extra, "id": 3}])
        code, summary, _ = self.run_audit()
        self.assertEqual(code, 1)
        self.assertEqual(summary["duplicate_release_asset_names"], [["test", "extra.bin"]])

    def test_duplicate_asset_names_fail(self):
        self.releases[0]["assets"].append({**self.asset, "id": 2})
        code, summary, _ = self.run_audit()
        self.assertEqual(code, 1)
        self.assertEqual(summary["duplicate_release_asset_names"], [["test", "a_local.bin"]])

    def test_resume_reuses_only_bound_successful_evidence(self):
        self.run_audit()
        code, summary, network = self.run_audit(resume=True)
        self.assertEqual(code, 0)
        self.assertEqual(summary["reused_checkpoints"], 1)
        network.assert_not_called()
        self.doc["size"] = 4
        with self.assertRaises(SystemExit):
            self.run_audit(resume=True)

    def test_corrupt_checkpoint_is_rejected_without_network(self):
        self.run_audit()
        (self.output / "downloads.jsonl").write_text("corrupt checkpoint\n")
        with self.assertRaises(SystemExit), mock.patch.object(audit, "download") as download:
            self.run_audit(resume=True)
        download.assert_not_called()

    def test_failed_checkpoint_is_retried(self):
        self.run_audit(body=b"ab")
        code, summary, network = self.run_audit(resume=True)
        self.assertEqual(code, 0)
        self.assertEqual(summary["reused_checkpoints"], 0)
        self.assertEqual(network.call_count, 1)

    def test_download_error_is_sanitized_and_bounded(self):
        for exc in [OSError("secret=do-not-record"), http.client.IncompleteRead(b"x")]:
            with self.subTest(exception=type(exc).__name__), \
                    mock.patch.object(audit.urllib.request, "urlopen", side_effect=exc) as network:
                row = audit.download(("test", self.asset))
            self.assertEqual(network.call_count, 3)
            self.assertEqual(row["status"], "download_error")
            self.assertNotIn("do-not-record", json.dumps(row))

    def test_invalid_manifest_fails_before_inventory(self):
        self.doc["mirror_url"] = "https://example.com/wrong"
        with self.assertRaises(SystemExit), mock.patch.object(audit, "download") as download:
            self.run_audit()
        download.assert_not_called()

    def test_inventory_change_fails(self):
        code, summary, _ = self.run_audit(final=[{**self.releases[0], "draft": True}])
        self.assertEqual(code, 1)
        self.assertFalse(summary["inventory_unchanged"])


if __name__ == "__main__":
    unittest.main()

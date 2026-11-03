"""Offline regression tests for provenance, identity and portable paths."""

import contextlib
import copy
import hashlib
import io
import pathlib
import tempfile
import unittest

import validate_manifest as validator


def document():
    return {"edition": "106-test", "kind": "companion", "title": "Fixture",
            "path": "files/106-test/a local.bin", "asset": "a_local.bin",
            "mirror_url": f"https://github.com/{validator.REPO}/releases/download/106-test/a_local.bin",
            "original_urls": ["https://example.com/a.bin", "http://old.example.com/a.bin"],
            "original_filenames": ["a.bin"], "size": 3,
            "sha256": hashlib.sha256(b"abc").hexdigest(),
            "retrieved": "2026-11-03", "distribution": "unknown"}


class ManifestTests(unittest.TestCase):
    def test_real_manifest_and_dynamic_totals(self):
        docs = validator.load_manifest(validator.ROOT / "manifest.toml")
        self.assertEqual(validator.totals(docs)["records"], len(docs))
        self.assertEqual(validator.totals(docs)["bytes"], sum(d["size"] for d in docs))
        one = document()
        two = {**one, "path": "files/106-test/b.bin", "asset": "b.bin",
               "mirror_url": f"https://github.com/{validator.REPO}/releases/download/106-test/b.bin"}
        self.assertEqual(validator.validate({"document": [one, two]}), [])
        self.assertEqual(validator.totals([one, two]), {
            "records": 2, "releases": 1, "bytes": 6, "unique_blobs": 1, "unique_blob_bytes": 3})

    def test_required_fields(self):
        for field in document():
            with self.subTest(field=field):
                doc = document()
                del doc[field]
                self.assertTrue(validator.validate({"document": [doc]}))

    def test_types_dates_and_hashes(self):
        invalid = {"size": [0, -1, True, "3"], "pages": [False, 0, "1"],
                   "sha256": ["a" * 63, "G" * 64, "A" * 64],
                   "retrieved": ["2026-02-30", "20261103", 20261103],
                   "original_urls": [[], "https://example.com", [None]],
                   "original_filenames": [[], [1]], "kind": ["unrecognized"],
                   "distribution": ["assumed"], "note": [42]}
        for field, values in invalid.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertTrue(validator.validate({"document": [{**document(), field: value}]}))

    def test_unsafe_paths_and_asset_names(self):
        for path in ["../escape", "/files/a", "files/../escape", "files/a/../../escape",
                     "files/a//b", "files/a/./b", "files/a/C:escape", "files/a/CON.pdf",
                     "files/a/trailing. ", "files/a/back\\slash", "files/a/null\x00.bin"]:
            with self.subTest(path=path):
                self.assertTrue(validator.validate({"document": [{**document(), "path": path}]}))
        for field in ["asset", "edition"]:
            for value in ["../x", "C:escape", "CON", "a/b", "a\\b", "a?b"]:
                self.assertTrue(validator.validate({"document": [{**document(), field: value}]}))

    def test_sources_and_mirror_identity(self):
        for url in ["file:///tmp/x", "ftp://example.com/x", "https://user:password@example.com/x",
                    "https:///x", "https://example.com:bad/x", "https://example.com/a b"]:
            self.assertTrue(validator.validate({"document": [{**document(), "original_urls": [url]}]}))
        for url in [document()["mirror_url"] + "?token=hidden",
                    document()["mirror_url"].replace("106-test/", "other/"),
                    document()["mirror_url"].replace("TelemetryWorks", "other")]:
            self.assertTrue(validator.validate({"document": [{**document(), "mirror_url": url}]}))

    def test_collisions_and_inconsistent_blob_size(self):
        for changes in [{}, {"path": "FILES/106-TEST/A LOCAL.BIN"},
                        {"path": "files/elsewhere/a.bin"}, {"path": "files/b/c.bin", "size": 4}]:
            with self.subTest(changes=changes):
                self.assertTrue(validator.validate({"document": [document(), {**document(), **changes}]}))
        other = {**document(), "path": "files/106-test/other.bin", "asset": "other.bin", "size": 4,
                 "mirror_url": f"https://github.com/{validator.REPO}/releases/download/106-test/other.bin"}
        self.assertIn("identical hashes must have identical sizes",
                      "\n".join(validator.validate({"document": [document(), other]})))

    def test_distribution_requires_recorded_evidence(self):
        doc = {**document(), "distribution": "A"}
        self.assertTrue(validator.validate({"document": [doc]}))
        doc["note"] = "Marking seen on cover"
        self.assertEqual(validator.validate({"document": [doc]}), [])

    def test_inventory_reconciliation(self):
        doc = document()
        asset = {"name": doc["asset"], "size": 3, "state": "uploaded",
                 "browser_download_url": doc["mirror_url"]}
        inventory = [{"tag": doc["edition"], "assets": [asset]}]
        self.assertEqual(validator.inventory_errors([doc], inventory), [])
        self.assertTrue(validator.inventory_errors([doc], []))
        self.assertTrue(validator.inventory_errors([], inventory))
        doubled = copy.deepcopy(inventory)
        doubled[0]["assets"].append(asset)
        self.assertTrue(validator.inventory_errors([doc], doubled))
        for field, value in [("size", True), ("size", 4), ("state", "new"),
                             ("browser_download_url", "https://example.com/wrong")]:
            wrong = copy.deepcopy(inventory)
            wrong[0]["assets"][0][field] = value
            self.assertTrue(validator.inventory_errors([doc], wrong))
        for malformed in [{}, [None], [{"tag": "test"}]]:
            self.assertTrue(validator.inventory_errors([doc], malformed))

    def test_cli_malformed_input_returns_failure(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stderr(io.StringIO()):
            path = pathlib.Path(temp) / "bad.toml"
            path.write_text("not valid = [")
            self.assertEqual(validator.main(["--manifest", str(path)]), 1)
            path.write_text("document = []")
            self.assertEqual(validator.main(["--manifest", str(path)]), 1)


if __name__ == "__main__":
    unittest.main()

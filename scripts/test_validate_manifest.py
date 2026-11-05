"""Offline regression tests for provenance, identity and portable paths."""

import contextlib
import copy
import hashlib
import io
import importlib.util
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

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
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stderr(io.StringIO()), \
                mock.patch.object(validator, "ROOT", pathlib.Path(temp).resolve()):
            path = pathlib.Path(temp) / "manifest.toml"
            path.write_text("not valid = [")
            self.assertEqual(validator.main(["--manifest", str(path)]), 1)
            path.write_text("document = []")
            self.assertEqual(validator.main(["--manifest", str(path)]), 1)

    def test_malformed_tables_do_not_reserve_identity(self):
        malformed = {**document(), "size": "not an integer"}
        errors = validator.validate({"document": [None, malformed, document()]})
        self.assertEqual(errors, ["document[0]: must be a table",
                                  "document[1].size: expected positive integer"])

    def test_semantic_errors_preserve_identity_checks_and_diagnostic_order(self):
        invalid = {**document(), "kind": "unsupported", "retrieved": "2026-02-30"}
        errors = validator.validate({"document": [invalid, document()]})
        self.assertEqual(errors, ["document[0].kind: unrecognized document kind",
                                  "document[0].retrieved: expected YYYY-MM-DD date",
                                  "document[1]: duplicate path or edition/asset pair"])

    def test_structural_errors_prevent_unsafe_semantic_operations(self):
        invalid = {**document(), "sha256": [], "size": "bad", "retrieved": None}
        errors = validator.validate({"document": [invalid]})
        self.assertEqual(errors, ["document[0].retrieved: required nonempty string",
                                  "document[0].sha256: required nonempty string",
                                  "document[0].size: expected positive integer"])

    def test_approved_staged_inputs_replace_outside_repository_contract(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = pathlib.Path(temp).resolve()
            staged = root / "files" / "validation-inputs"
            staged.mkdir(parents=True)
            doc = document()
            manifest = staged / "selected.toml"
            manifest.write_text("[[document]]\n" + "\n".join(
                f"{key} = {json.dumps(value)}" for key, value in doc.items()))
            inventory = staged / "selected.json"
            inventory.write_text(json.dumps([{"tag": doc["edition"], "assets": [{
                "name": doc["asset"], "size": doc["size"], "state": "uploaded",
                "browser_download_url": doc["mirror_url"]}]}]))
            with mock.patch.object(validator, "ROOT", root):
                self.assertEqual(validator.main(["--manifest", str(manifest),
                                                 "--inventory", str(inventory)]), 0)

    def test_malformed_input_does_not_echo_file_contents(self):
        with tempfile.TemporaryDirectory() as temp, \
                mock.patch.object(validator, "ROOT", pathlib.Path(temp).resolve()):
            manifest = pathlib.Path(temp) / "manifest.toml"
            manifest.write_text("SECRET_FIXTURE_CONTENT [not toml")
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(validator.main(["--manifest", str(manifest)]), 1)
            self.assertNotIn("SECRET_FIXTURE_CONTENT", stderr.getvalue())


class InputBoundaryTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = pathlib.Path(temp.name).resolve()
        self.root = self.base / "repo"
        self.staged = self.root / "files" / "validation-inputs"
        self.audits = self.root / "files" / "audits"
        self.staged.mkdir(parents=True)
        self.audits.mkdir()
        self.manifest = self.root / "manifest.toml"
        self.manifest.write_bytes(b"document = []")
        self.inventory = self.audits / "inventory.json"
        self.inventory.write_bytes(b"[]")
        patch = mock.patch.object(validator, "ROOT", self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def assert_blocked(self, path, kind):
        # Content access, not just a schema error, must be prevented.
        with mock.patch.object(pathlib.Path, "read_bytes") as read:
            with self.assertRaises(ValueError):
                validator.read_input(path, kind)
            read.assert_not_called()

    def assert_link_blocked(self, path, kind, link):
        original_lstat = pathlib.Path.lstat
        with mock.patch.object(pathlib.Path, "read_bytes") as read, \
                mock.patch.object(pathlib.Path, "lstat", autospec=True, side_effect=original_lstat) as checked:
            with self.assertRaisesRegex(ValueError, "link or Windows reparse point"):
                validator.read_input(path, kind)
            read.assert_not_called()
            self.assertEqual(checked.call_args.args[0], link)

    def test_absolute_relative_and_staged_canonical_inputs(self):
        self.assertEqual(validator.read_input(self.manifest, "manifest"), b"document = []")
        self.assertEqual(validator.read_input(self.inventory, "inventory"), b"[]")
        candidate = self.staged / "candidate.toml"
        candidate.write_bytes(b"bad but permitted")
        self.assertEqual(validator.read_input(candidate, "manifest"), b"bad but permitted")
        saved = self.staged / "candidate.json"
        saved.write_bytes(b"[]")
        self.assertEqual(validator.read_input(saved, "inventory"), b"[]")
        with contextlib.chdir(self.root):
            self.assertEqual(validator.read_input("./manifest.toml", "manifest"), b"document = []")
            self.assertEqual(validator.read_input("files/audits/inventory.json", "inventory"), b"[]")
            if os.name == "nt":
                self.assertEqual(validator.read_input(r"files\audits/inventory.json", "inventory"), b"[]")

    def test_traversal_absolute_escape_and_sibling_prefix_never_read(self):
        outside = self.base / "outside.toml"
        outside.write_bytes(b"SECRET")
        sibling = self.base / "repo-extra" / "manifest.toml"
        sibling.parent.mkdir()
        sibling.write_bytes(b"SECRET")
        for path in [outside, sibling, self.root / "files/../manifest.toml",
                     "../manifest.toml", "files/audits/../audits/inventory.json",
                     "files\\audits/..\\audits/inventory.json"]:
            for kind in ["manifest", "inventory"]:
                with self.subTest(path=path, kind=kind):
                    self.assert_blocked(path, kind)

    def test_windows_drive_unc_device_ads_and_reserved_names_never_read(self):
        paths = ["C:manifest.toml", "Z:/outside.toml", r"\manifest.toml",
                 r"\\server\share\manifest.toml", r"\\?\C:\manifest.toml",
                 r"\\.\C:\manifest.toml", "//server/share/inventory.json",
                 self.staged / "candidate.toml:stream", self.staged / "CON.toml",
                 self.staged / "trailing .toml.", "files/validation-inputs/../candidate.toml"]
        for path in paths:
            with self.subTest(path=path):
                self.assert_blocked(path, "manifest")

    def test_wrong_location_extension_and_kind_never_read(self):
        for path, kind in [(self.inventory, "manifest"), (self.manifest, "inventory"),
                           (self.root / "README.md", "manifest"),
                           (self.audits / "other.toml", "manifest"),
                           (self.staged / "candidate.json", "manifest"),
                           (self.staged / "candidate.toml", "inventory"),
                           (self.manifest, "unknown")]:
            with self.subTest(path=path, kind=kind):
                self.assert_blocked(path, kind)

    def test_directory_and_missing_permitted_file_fail_before_read(self):
        folder = self.staged / "directory.toml"
        folder.mkdir()
        self.assert_blocked(folder, "manifest")
        self.assert_blocked(self.staged / "missing.toml", "manifest")

    def test_cli_inventory_and_manifest_enforce_boundary(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with mock.patch.object(pathlib.Path, "read_bytes") as read:
                self.assertEqual(validator.main(["--manifest", str(self.base / "outside.toml")]), 1)
                read.assert_not_called()
            with mock.patch.object(validator, "load_manifest", return_value=[document()]), \
                    mock.patch.object(pathlib.Path, "read_bytes") as read:
                self.assertEqual(validator.main(["--inventory", str(self.base / "outside.json")]), 1)
                read.assert_not_called()

    def test_pure_parser_remains_independent_of_input_policy(self):
        data = "[[document]]\n" + "\n".join(
            f"{key} = {json.dumps(value)}" for key, value in document().items())
        with mock.patch.object(pathlib.Path, "read_bytes") as read:
            self.assertEqual(validator.parse_manifest(data.encode()), [document()])
            read.assert_not_called()

    def test_malformed_permitted_inventory_is_read_then_rejected(self):
        for contents in [b"not JSON", b"{}", b"\xef\xbb\xbf[]", b"\xff"]:
            self.inventory.write_bytes(contents)
            stderr = io.StringIO()
            with mock.patch.object(validator, "load_manifest", return_value=[document()]), \
                    contextlib.redirect_stderr(stderr):
                self.assertEqual(validator.main(["--inventory", str(self.inventory)]), 1)
            self.assertNotIn("outside the fixed", stderr.getvalue())
            self.assertNotIn("Cannot read", stderr.getvalue())

    def make_symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError as exc:
            if os.name == "nt" and exc.winerror == 1314:
                self.skipTest("Windows symlink privilege unavailable; junction test is separate")
            raise
        self.addCleanup(link.unlink)

    def test_symlink_file_inside_or_outside_never_read(self):
        outside = self.base / "outside.toml"
        outside.write_bytes(b"SECRET")
        for index, target in enumerate([outside, self.manifest]):
            link = self.staged / f"link{index}.toml"
            self.make_symlink(link, target)
            self.assert_link_blocked(link, "manifest", link)

    def test_symlink_intermediate_directory_never_read(self):
        link = self.staged / "nested"
        self.make_symlink(link, self.audits, directory=True)
        self.assert_link_blocked(link / "inventory.json", "inventory", link)

    def test_symlink_allowed_root_never_redefines_authority(self):
        self.inventory.unlink()
        self.audits.rmdir()
        self.make_symlink(self.audits, self.base, directory=True)
        (self.base / "outside.json").write_bytes(b"SECRET")
        self.assert_link_blocked(self.audits / "outside.json", "inventory", self.audits)

    def make_junction(self, link, target):
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(os.name == "nt", "Windows junction/reparse test")
    def test_windows_junction_roots_and_intermediate_directory_never_read(self):
        # mklink /J requires no Developer Mode or symlink privilege.
        (self.base / "outside.json").write_bytes(b"SECRET")
        for link in [self.staged / "junction", self.root / "files" / "audits"]:
            if link == self.audits:
                self.inventory.unlink()
                link.rmdir()
            self.make_junction(link, self.base)
            try:
                self.assert_link_blocked(link / "outside.json", "inventory", link)
            finally:
                # Remove only our junction, never traverse its target.
                link.rmdir()

    @unittest.skipUnless(os.name == "nt", "Windows junction/reparse test")
    def test_windows_junction_files_staging_and_repository_roots_never_read(self):
        for index, suffix in enumerate(["", "files", "files/validation-inputs"]):
            root = self.base / f"junction-repo{index}"
            link = root / suffix
            remaining = pathlib.Path("files/validation-inputs/outside.toml").relative_to(suffix or ".")
            target = self.base / remaining
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"SECRET")
            link.parent.mkdir(parents=True, exist_ok=True)
            self.make_junction(link, self.base)
            try:
                with mock.patch.object(validator, "ROOT", root):
                    self.assert_link_blocked(root / "files/validation-inputs/outside.toml", "manifest", link)
            finally:
                link.rmdir()

    def test_real_module_and_cli_entry_through_linked_checkout_reject_root(self):
        scripts = self.root / "scripts"
        scripts.mkdir()
        shutil.copyfile(validator.__file__, scripts / "validate_manifest.py")
        linked = self.base / "linked-checkout"
        if os.name == "nt":
            self.make_junction(linked, self.root)
            self.addCleanup(linked.rmdir)
        else:
            self.make_symlink(linked, self.root, directory=True)
        entry = linked / "scripts" / "validate_manifest.py"
        spec = importlib.util.spec_from_file_location("linked_validator", entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.ROOT, linked)
        with mock.patch.object(validator, "ROOT", module.ROOT):
            self.assert_link_blocked(linked / "manifest.toml", "manifest", linked)
        original_lstat = pathlib.Path.lstat
        with mock.patch.object(pathlib.Path, "read_bytes") as read, \
                mock.patch.object(pathlib.Path, "lstat", autospec=True, side_effect=original_lstat) as checked, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(module.main([]), 1)
            read.assert_not_called()
            self.assertEqual(checked.call_args.args[0], linked)
        result = subprocess.run([sys.executable, str(entry)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("link or Windows reparse point", result.stderr)


if __name__ == "__main__":
    unittest.main()

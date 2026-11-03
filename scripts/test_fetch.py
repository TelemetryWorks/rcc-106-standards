"""Offline download/fallback and verify-mode regression tests."""

import contextlib
import hashlib
import http.client
import io
import pathlib
import tempfile
import unittest
from unittest import mock

import fetch
from test_validate_manifest import document


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.doc = document()
        self.target = self.root / self.doc["path"]

    def test_valid_local_file_skips_all_network(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"abc")
        with mock.patch.object(fetch, "download") as download:
            self.assertEqual(fetch.fetch(self.doc, self.root), "present")
        download.assert_not_called()

    def test_corrupt_local_file_and_bad_mirror_use_verified_fallback(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"xyz")
        calls = []

        def download(url, dest):
            calls.append(url)
            dest.write_bytes(b"xyz" if len(calls) == 1 else b"abc")

        with mock.patch.object(fetch, "download", side_effect=download), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.fetch(self.doc, self.root), "fetched")
        self.assertEqual(calls, [self.doc["mirror_url"], self.doc["original_urls"][0]])
        self.assertEqual(self.target.read_bytes(), b"abc")
        self.assertFalse(self.target.with_name(self.target.name + ".part").exists())

    def test_network_and_incomplete_http_errors_fall_back(self):
        for error in [OSError("unavailable"), http.client.IncompleteRead(b"a")]:
            calls = []

            def download(url, dest):
                calls.append(url)
                if len(calls) == 1:
                    raise error
                dest.write_bytes(b"abc")

            with self.subTest(error=type(error).__name__), \
                    mock.patch.object(fetch, "verifies", wraps=fetch.verifies) as verifies, \
                    mock.patch.object(fetch, "download", side_effect=download), \
                    contextlib.redirect_stderr(io.StringIO()):
                self.target.unlink(missing_ok=True)
                self.assertEqual(fetch.fetch(self.doc, self.root), "fetched")
                self.assertGreaterEqual(verifies.call_count, 2)
                self.assertEqual(len(calls), 2)

    def test_all_corrupt_sources_fail_without_replacing_existing_file(self):
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(b"old")
        with mock.patch.object(fetch, "download", side_effect=lambda url, dest: dest.write_bytes(b"bad")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.fetch(self.doc, self.root), "FAILED")
        self.assertEqual(self.target.read_bytes(), b"old")
        self.assertFalse(self.target.with_name(self.target.name + ".part").exists())

    def test_verify_mode_fails_on_missing_and_corrupt_files_without_network(self):
        with mock.patch.object(fetch, "load_manifest", return_value=[self.doc]), \
                mock.patch.object(fetch, "download") as download, \
                contextlib.redirect_stdout(io.StringIO()):
            args = ["--verify", "--dest", str(self.root)]
            self.assertEqual(fetch.main(args), 1)
            self.target.parent.mkdir(parents=True)
            self.target.write_bytes(b"xyz")
            self.assertEqual(fetch.main(args), 1)
            self.target.write_bytes(b"abc")
            self.assertEqual(fetch.main(args), 0)
        download.assert_not_called()

    def test_empty_selection_and_invalid_manifest_fail_without_network(self):
        with mock.patch.object(fetch, "load_manifest", return_value=[self.doc]), \
                mock.patch.object(fetch, "download") as download, \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main(["--edition", "absent"]), 1)
        download.assert_not_called()
        with mock.patch.object(fetch, "load_manifest", side_effect=ValueError("invalid metadata")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(fetch.main([]), 1)

    def test_stream_download_hashes_actual_bytes(self):
        response = io.BytesIO(b"abc")
        with mock.patch.object(fetch.urllib.request, "urlopen", return_value=response):
            path = self.root / "download.bin"
            fetch.download(self.doc["mirror_url"], path)
        self.assertEqual(fetch.sha256_of(path), hashlib.sha256(b"abc").hexdigest())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import hashlib
import tempfile
import unittest
from pathlib import Path
from download_actions_artifact import download

REPO = "celticmusic-nagoya/the-windbound-oath"
URL = "https://example.blob.core.windows.net/artifacts/blob?sig=mock"


class FakeResponse:
    def __init__(self, status, data=b"", location=None):
        self.status = status
        self.data = data
        self.pos = 0
        self.headers = {"Location": location} if location else {}

    def read(self, n):
        chunk = self.data[self.pos:self.pos + n]
        self.pos += len(chunk)
        return chunk

    def close(self):
        pass


class FakeOpener:
    def __init__(self, payload=b"zip-fixture", location=URL):
        self.payload = payload
        self.location = location
        self.calls = []

    def open(self, request, timeout=None):
        self.calls.append(request)
        if len(self.calls) == 1:
            return FakeResponse(302, location=self.location)
        return FakeResponse(200, data=self.payload)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "candidate.zip"
        self.data = b"zip-fixture"
        self.digest = hashlib.sha256(self.data).hexdigest()

    def run_download(self, opener=None, digest=None, max_bytes=100):
        opener = opener or FakeOpener()
        return download(REPO, 123, "token", self.out, digest or self.digest,
                        max_bytes=max_bytes, opener=opener)

    def test_valid_zip_bytes(self):
        result = self.run_download()
        self.assertTrue(result["zip_sha256_verified"])
        self.assertFalse(result["safe_to_reuse"])

    def test_no_token_sent_to_storage(self):
        opener = FakeOpener()
        self.run_download(opener)
        self.assertIn("Authorization", opener.calls[0].headers)
        self.assertNotIn("Authorization", opener.calls[1].headers)

    def test_mismatched_hash_removes_file(self):
        with self.assertRaises(ValueError):
            self.run_download(digest="0"*64)
        self.assertFalse(self.out.exists())

    def test_oversize_removes_file(self):
        with self.assertRaises(ValueError):
            self.run_download(max_bytes=3)
        self.assertFalse(self.out.exists())

    def test_bad_redirect_host(self):
        with self.assertRaises(ValueError):
            self.run_download(FakeOpener(location="https://evil.example/archive"))

    def test_http_redirect_rejected(self):
        with self.assertRaises(ValueError):
            self.run_download(FakeOpener(location="http://example.blob.core.windows.net/archive"))

    def test_existing_file_preserved(self):
        self.out.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            self.run_download()
        self.assertEqual(self.out.read_bytes(), b"keep")

    def test_race_does_not_delete_other_process_file(self):
        output = self.out

        class RacingOpener(FakeOpener):
            def open(self, request, timeout=None):
                if len(self.calls) == 1:
                    output.write_bytes(b"another-process")
                return super().open(request, timeout=timeout)

        with self.assertRaises(FileExistsError):
            self.run_download(RacingOpener())
        self.assertEqual(self.out.read_bytes(), b"another-process")

    def test_invalid_digest(self):
        with self.assertRaises(ValueError):
            self.run_download(digest="not-a-digest")

    def test_empty_archive(self):
        with self.assertRaises(ValueError):
            self.run_download(FakeOpener(payload=b""))
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()

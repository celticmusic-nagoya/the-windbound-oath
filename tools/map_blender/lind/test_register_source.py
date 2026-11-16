import hashlib
from pathlib import Path
import tempfile
import unittest

from register_source import verified_bytes


class SourceIntegrityTests(unittest.TestCase):
    def test_mismatch_preserves_input_and_creates_no_registered_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "preview.png"
            raw = b"\x89PNG\r\n\x1a\npreview is not the adopted original"
            source.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                verified_bytes(source)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(list(Path(tmp).iterdir()), [source])

    def test_integrity_check_returns_original_bytes_without_decoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.png"
            raw = b"\x89PNG\r\n\x1a\nfixture bytes; not canon"
            source.write_bytes(raw)
            self.assertEqual(verified_bytes(source, hashlib.sha256(raw).hexdigest()), raw)

    def test_non_png_rejected_even_when_digest_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "test.png"
            raw = b"not a png"
            source.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "not a PNG"):
                verified_bytes(source, hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()

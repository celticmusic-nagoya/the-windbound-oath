import hashlib
import unittest
from scripts.verify_morwen_master import jpeg_dimensions, verify


def minimal_jpeg(width=1536, height=1024):
    # Minimal JPEG header fixture, sufficient for header parsing only.
    return (b"\xff\xd8\xff\xc0\x00\x11\x08" +
            height.to_bytes(2, "big") + width.to_bytes(2, "big") +
            b"\x03" + b"\x00" * 9 + b"\xff\xd9")


class MasterVerifierTests(unittest.TestCase):
    def test_dimensions(self):
        self.assertEqual(jpeg_dimensions(minimal_jpeg()), (1536, 1024))

    def test_exact_hash_and_size(self):
        data = minimal_jpeg()
        self.assertEqual(verify(data, hashlib.sha256(data).hexdigest()), [])

    def test_wrong_hash(self):
        self.assertIn("SHA256_MISMATCH", verify(minimal_jpeg()))

    def test_wrong_size(self):
        data = minimal_jpeg(100, 100)
        self.assertIn("DIMENSION_MISMATCH", verify(data, hashlib.sha256(data).hexdigest()))

    def test_invalid_jpeg(self):
        self.assertIn("INVALID_JPEG", verify(b"not jpeg"))


if __name__ == "__main__":
    unittest.main()

from datetime import datetime, timezone
import unittest

from shared_g2_review import review_passes


class ReviewTests(unittest.TestCase):
    def test_requires_current_independent_review_of_exact_native(self):
        now = datetime(2026, 11, 22, tzinfo=timezone.utc)
        native = "a" * 64
        verified = dict(authenticated=True, independent=True, status="PASS", native_sha256=native,
                        expires_at="2026-11-23T00:00:00+00:00")
        self.assertTrue(review_passes(verified, native, now=now))
        for invalid in (
            {"native_sha256": "b"*64}, {"status": "FAIL"}, {"authenticated": False},
            {"independent": False}, {"expires_at": "2026-11-22T00:00:00+00:00"},
            {"expires_at": "2026-11-23T00:00:00"},
        ):
            with self.subTest(invalid=invalid):
                self.assertFalse(review_passes({**verified, **invalid}, native, now=now))

import unittest
from scripts.qa_morwen_rig_source import inspect, EXPECTED, EXPECTED_SPRITE_STATUS


def valid():
    return {
        "characterId": "morwen",
        "canonical": dict(EXPECTED),
        "productionSpriteStatus": EXPECTED_SPRITE_STATUS,
        "keepLegacySourceUnchanged": True,
    }


class SourceGateTests(unittest.TestCase):
    def test_expected_metadata(self):
        self.assertEqual(inspect(valid()), [])

    def test_wrong_sha_rejected(self):
        d = valid()
        d["canonical"]["sha256"] = "bad"
        self.assertTrue(inspect(d))

    def test_unapproved_promotion_rejected(self):
        d = valid()
        d["productionSpriteStatus"] = "APPROVED"
        self.assertTrue(inspect(d))

    def test_missing_binary_flag_rejected(self):
        d = valid()
        del d["canonical"]["binaryInGitHub"]
        self.assertTrue(inspect(d))


if __name__ == "__main__":
    unittest.main()

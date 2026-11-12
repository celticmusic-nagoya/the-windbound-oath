import unittest
from scripts.pr_diff_review import summarize


class ReportTests(unittest.TestCase):
    def test_empty(self):
        self.assertIn("No changed files", summarize([]))

    def test_source_and_secret(self):
        report = summarize([("M", "js/game.js"), ("A", "config/.env")])
        self.assertIn("Review behavior and regressions", report)
        self.assertIn("Check for credentials", report)

    def test_escapes_markdown_and_limits(self):
        report = summarize([("A", "foo|bar.js"), ("A", "x.js")] * 60)
        self.assertIn("foo\\|bar.js", report)
        self.assertIn("truncated", report)


if __name__ == "__main__":
    unittest.main()

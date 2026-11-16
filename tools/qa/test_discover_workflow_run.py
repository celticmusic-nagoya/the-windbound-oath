import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from discover_workflow_run import select
class DiscoveryTests(unittest.TestCase):
 def test_latest_matching_completed(self):
  rows=[{"id":1,"head_branch":"feature/test","path":".github/workflows/example.yml","status":"completed","created_at":"2026-01-01T00:00:00Z"},{"id":2,"head_branch":"feature/test","path":".github/workflows/example.yml","status":"in_progress","created_at":"2026-01-03T00:00:00Z"},{"id":3,"head_branch":"other","path":".github/workflows/example.yml","status":"completed","created_at":"2026-01-04T00:00:00Z"},{"id":4,"head_branch":"feature/test","path":".github/workflows/example.yml","status":"completed","created_at":"2026-01-02T00:00:00Z"}]
  self.assertEqual(select(rows,"feature/test","example.yml")["run_id"],4)
 def test_exclude_current_run(self):
  rows=[{"id":5,"head_branch":"feature/test","path":".github/workflows/example.yml","status":"completed","created_at":"2026-01-05T00:00:00Z"},{"id":4,"head_branch":"feature/test","path":".github/workflows/example.yml","status":"completed","created_at":"2026-01-04T00:00:00Z"}]
  self.assertEqual(select(rows,"feature/test","example.yml",exclude_run_id=5)["run_id"],4)
 def test_missing_is_blocked(self):self.assertEqual(select([],"feature/test","example.yml")["status"],"BLOCKED_RUN_DISCOVERY")
if __name__=="__main__":unittest.main()

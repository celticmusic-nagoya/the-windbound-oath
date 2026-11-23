"""TWO shared Blueprint Engine (Claude, common infrastructure).

Design sources -> structured geometry blueprint -> native/official measurement ->
residual (PASS/OUTSIDE/HOLD) -> correction contract handed to the #468 Factory.

The execution contract (target/request/observation envelope, metric_state and
the Factory/Session Controller) is owned by Codex in PR #468
(tools/production_qa). This package imports it and never redefines it.
"""
import sys
from pathlib import Path

ENGINE_VERSION = "1.0.0"
SCHEMA = "two.blueprint_engine/1"
_QA = Path(__file__).resolve().parents[1] / "production_qa"
if str(_QA) not in sys.path:
    sys.path.insert(0, str(_QA))

from shared_blueprint_contract import (  # noqa: E402  (#468 contract is authoritative)
    digest_record, finite, matches_digest, measurement_issues, metric_state, present,
    target_issues,
)

__all__ = ["ENGINE_VERSION", "SCHEMA", "digest_record", "finite", "matches_digest",
           "measurement_issues", "metric_state", "present", "target_issues"]

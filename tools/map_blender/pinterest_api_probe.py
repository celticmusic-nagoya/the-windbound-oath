"""Read-only Pinterest token/board audit; writes sanitized JSON, never logs secrets."""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(os.environ.get("PINTEREST_AUDIT_OUTPUT", "/tmp/pinterest-audit"))
OUT.mkdir(parents=True, exist_ok=True)
REPORT = OUT / "pinterest_api_report.json"
SELECTION = Path(__file__).with_name("pinterest_roof_reference_selection.json")


def finish(status, reason, **extra):
    report = {
        "status": status,
        "reason": reason,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        **extra,
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("Pinterest API audit:", status, "-", reason)
    return 0 if status == "PASS" else 1


def main():
    token = os.environ.get("PINTEREST_ACCESS_TOKEN", "").strip()
    if not token:
        return finish("FAIL", "SECRET_MISSING")
    try:
        selection = json.loads(SELECTION.read_text())
        board_id = str(selection["board_id"])
        expected = {x["pin"].rstrip("/").split("/")[-1] for x in selection["selected"]}
    except (OSError, ValueError, KeyError, TypeError):
        return finish("FAIL", "INVALID_REFERENCE_SELECTION")

    url = "https://api.pinterest.com/v5/boards/" + board_id + "/pins?page_size=100"
    found = set()
    try:
        for _ in range(10):
            req = urllib.request.Request(
                url, headers={"Authorization": "Bearer " + token, "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                payload = json.load(response)
            for pin in payload.get("items", []):
                found.add(str(pin.get("id", "")))
            bookmark = payload.get("bookmark")
            if not bookmark:
                break
            from urllib.parse import urlencode
            url = "https://api.pinterest.com/v5/boards/" + board_id + "/pins?" + urlencode(
                {"page_size": 100, "bookmark": bookmark}
            )
    except urllib.error.HTTPError as exc:
        # Never print the response body or URL: they may contain provider diagnostics.
        return finish("FAIL", "PINTEREST_HTTP_ERROR", http_status=exc.code)
    except (urllib.error.URLError, TimeoutError):
        return finish("FAIL", "NETWORK_OR_TIMEOUT")
    except (ValueError, KeyError, TypeError):
        return finish("FAIL", "INVALID_API_RESPONSE")

    matched = expected & found
    return finish(
        "PASS", "BOARD_READ_SUCCESS",
        board_id=board_id,
        board_pin_count=len(found),
        selected_count=len(expected),
        matched_count=len(matched),
        unmatched_pin_ids=sorted(expected - found),
        reference_only=True,
    )


if __name__ == "__main__":
    sys.exit(main())

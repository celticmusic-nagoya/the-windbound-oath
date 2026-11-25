"""Strict, read-only intake for the existing production reservation path."""
import re

def parse(event, permission):
    issue = event.get("issue", {})
    comment = event.get("comment", {})
    if event.get("action") != "created" or issue.get("number") != 427 or not issue.get("pull_request"):
        return None
    if permission not in ("admin", "maintain", "write"):
        return None
    if comment.get("user", {}).get("type") != "User":
        return None
    match = re.fullmatch(r"/two preflight MORWEN ([0-9a-f]{40})", comment.get("body", ""))
    if not match:
        return None
    return {"asset":"MORWEN","head":match[1],"comment_id":comment["id"],"mode":"READ_ONLY"}

if __name__ == "__main__":
    import json, os
    with open(os.environ["GITHUB_EVENT_PATH"]) as f:
        event = json.load(f)
    print(json.dumps(parse(event, os.environ.get("TWO_ACTOR_PERMISSION"))))

"""Observe canonical lease without acquiring, releasing or authorizing a writer."""
import json
import os
import re
import subprocess
from shared_asset_reservation import ref_for

def observe(remote, asset, head):
    ref = ref_for(asset)
    result = subprocess.run(["git","ls-remote",remote,ref,ref+"^{}"],check=True,capture_output=True,text=True,timeout=30)
    entries = {}
    for line in result.stdout.splitlines():
        sha, name = line.split("\t")
        if name not in (ref,ref+"^{}") or name in entries or not re.fullmatch("[0-9a-f]{40}",sha):
            raise ValueError("unexpected lease response")
        entries[name] = sha
    if not entries:
        state = "ABSENT_OBSERVED"
    elif ref in entries and entries.get(ref+"^{}") == head:
        state = "PRESENT_MATCHING_REVISION"
    else:
        state = "PRESENT_OR_AMBIGUOUS"
    return {"state":state,"ref":ref,"head":head,"production_authorized":False}

if __name__ == "__main__":
    import sys
    print(json.dumps(observe("origin","MORWEN",sys.argv[1])))

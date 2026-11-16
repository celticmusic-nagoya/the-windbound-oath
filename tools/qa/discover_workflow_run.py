#!/usr/bin/env python3
"""Find latest matching GitHub Actions run using REST, with explicit branch/workflow filters."""
import argparse,json,os,sys,urllib.parse,urllib.request
def select(runs,branch,workflow,completed=True):
    found=[r for r in runs if r.get("head_branch")==branch and r.get("path","").endswith("/"+workflow) and (not completed or r.get("status")=="completed")]
    found.sort(key=lambda r:(r.get("created_at",""),r.get("id",0)),reverse=True)
    if not found:return {"status":"BLOCKED_RUN_DISCOVERY","reason":"No matching run in retrieved page"}
    r=found[0]
    return {"status":"PASS","run_id":r["id"],"head_sha":r.get("head_sha"),"head_branch":r.get("head_branch"),"event":r.get("event"),"conclusion":r.get("conclusion"),"created_at":r.get("created_at"),"html_url":r.get("html_url"),"workflow":workflow}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",required=True);p.add_argument("--branch",required=True);p.add_argument("--workflow",required=True);p.add_argument("--output",required=True)
    a=p.parse_args()
    if len(a.repo.split("/"))!=2 or "/" in a.workflow or not a.workflow.endswith((".yml",".yaml")):p.error("invalid repo/workflow")
    params=urllib.parse.urlencode({"branch":a.branch,"per_page":100})
    url=f"https://api.github.com/repos/{a.repo}/actions/workflows/{a.workflow}/runs?{params}"
    headers={"Accept":"application/vnd.github+json","User-Agent":"TWO-production-run-discovery","X-GitHub-Api-Version":"2022-11-28"}
    if os.getenv("GITHUB_TOKEN"):headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=20) as resp:
            data=json.load(resp)
        result=select(data.get("workflow_runs",[]),a.branch,a.workflow)
    except Exception as exc:
        result={"status":"BLOCKED_RUN_DISCOVERY","reason":type(exc).__name__+": "+str(exc)}
    from pathlib import Path
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
    return 0 if result["status"]=="PASS" else 2
if __name__=="__main__":sys.exit(main())

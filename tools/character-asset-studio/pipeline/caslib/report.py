"""QA results: PASS / FAIL / BLOCKED / NOT_RUN, aggregation and Markdown for Draft PRs.

Overall rule (strictest wins): any FAIL -> FAIL; else any BLOCKED -> BLOCKED; else any NOT_RUN -> NOT_RUN;
else PASS. Human-only checks are NOT_RUN unless a human record exists, so an automated run alone can never
reach an overall PASS when human checks are part of the subject.
"""
from .core import RESULTS

ORDER = {"FAIL": 0, "BLOCKED": 1, "NOT_RUN": 2, "PASS": 3}


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, cid, scope, result, kind="automated", detail=None, reason=None):
        assert result in RESULTS, result
        row = {"id": cid, "scope": scope, "result": result, "kind": kind}
        if detail is not None:
            row["detail"] = detail
        if reason:
            row["reason"] = reason
        self.rows.append(row)
        return row


def overall(rows):
    if not rows:
        return "NOT_RUN"
    return min((r["result"] for r in rows), key=lambda r: ORDER[r])


def counts(rows):
    c = {k: 0 for k in RESULTS}
    for r in rows:
        c[r["result"]] += 1
    return c


def make_report(subject, rows, qa_kind="automated_self_qa", source=None, note=None):
    rep = {"schema": "cas/qa-report/0.5", "subject": subject, "qaKind": qa_kind,
           "overall": overall(rows), "counts": counts(rows), "checks": rows}
    if source:
        rep["source"] = source
    if note:
        rep["note"] = note
    return rep


def to_markdown(reports, title="Pipeline QA summary"):
    lines = [f"### {title}", "", "| subject | QA kind | overall | PASS | FAIL | BLOCKED | NOT_RUN |", "|---|---|---|---|---|---|---|"]
    for name, r in reports:
        c = r["counts"]
        lines.append(f"| {name} | {r['qaKind']} | **{r['overall']}** | {c['PASS']} | {c['FAIL']} | {c['BLOCKED']} | {c['NOT_RUN']} |")
    issues = [(name, x) for name, r in reports for x in r["checks"] if x["result"] in ("FAIL", "BLOCKED")]
    if issues:
        lines += ["", "FAIL / BLOCKED:"]
        for name, x in issues[:40]:
            why = x.get("reason") or (str(x.get("detail"))[:140] if x.get("detail") is not None else "")
            lines.append(f"- `{name}` {x['scope']} · {x['id']}: **{x['result']}** {why}")
        if len(issues) > 40:
            lines.append(f"- … {len(issues) - 40} more (see JSON)")
    nr = sorted({x["id"] for _, r in reports for x in r["checks"] if x["result"] == "NOT_RUN"})
    if nr:
        lines += ["", "NOT_RUN (needs a human or a missing input): " + ", ".join(f"`{i}`" for i in nr)]
    return "\n".join(lines) + "\n"

"""Select gallery records, never delete source files or git history."""
from datetime import datetime, timedelta, timezone

def select(records, now, budget=256*1024*1024, recent_days=90):
    cutoff=now-timedelta(days=recent_days)
    def stamp(e):
        try:
            t=datetime.fromisoformat(e.get("created_at","").replace("Z","+00:00"))
            return t if t.tzinfo else datetime.min.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError, AttributeError):
            return datetime.min.replace(tzinfo=timezone.utc)
    def protected(e):
        return e.get("adoption")=="ADOPTED" or e.get("milestone") is True or e.get("blueprint") is True
    ranked=sorted(records,key=lambda e:(protected(e),stamp(e)>=cutoff,stamp(e)),reverse=True)
    unique={}
    for e in ranked:
        unique.setdefault(e["sha256"],e)
    keep=[]; omitted=[]; total=0
    for e in unique.values():
        if protected(e) or total+e["bytes"]<=budget:
            keep.append(e);total+=e["bytes"]
        else:
            omitted.append(e)
    return {"entries":keep,"omitted":omitted,"bytes":total,"over_budget":total>budget}

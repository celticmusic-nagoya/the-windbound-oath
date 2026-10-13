"""Inventory movement/prelude source evidence; manual review is required."""
import ast,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
rows=[]
for p in sorted((ROOT/'tests').rglob('*.py')):
    if '__pycache__' in p.parts:continue
    s=p.read_text();lines=s.splitlines();tree=ast.parse(s)
    scopes=[(n.lineno,n.end_lineno,n.name) for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
    def evidence(token):
        out=[]
        for i,line in enumerate(lines,1):
            if re.search(token,line):out.append(dict(line=i,text=line.strip(),helper=[name for lo,hi,name in scopes if lo<=i<=hi]))
        return out
    rows.append(dict(test=str(p.relative_to(ROOT)),dialogue=evidence(r'closeDialogue|keyboard.press\([\"\']Enter'),movement=evidence(r'keyboard.down|\.goFeet\(|pointerdown|mouse.down'),devHarness='dev/moss-forest.html' in s,indirectClose='enterWorldMap(' in s or 'devJump(' in s))
print(json.dumps(dict(note='Static candidates, not execution order/proof. Helper definitions must be reviewed; indirect DEV reset is not guaranteed close.',files=len(rows),rows=rows),ensure_ascii=False,indent=2))

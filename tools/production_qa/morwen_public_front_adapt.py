"""Bounded W120 worker adaptation; exact source and exact single replacement."""
import hashlib,sys
from pathlib import Path
PIN='4e83be76cee5929c8b3fe0ebdaefef625cdbf4da'
BEGIN="\"$py\" tools/w110_camera_register.py support \"$anchor\" evidence/W110-before-brush-rows.json \"$registration\" \"$anchor\" \"$design\" evidence/W110-fit.json\n"
END="args=$(\"$py\" tools/w107_brush.py stroke "
REPLACEMENT='source "$GITHUB_WORKSPACE/tools/production_qa/morwen_public_front_visibility.sh"\n'
def git_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
def adapt(raw,expected=PIN):
    if git_sha(raw)!=expected:raise ValueError('source identity')
    s=raw.decode('utf-8')
    if s.count(BEGIN)!=1 or s.count(END)!=1:raise ValueError('anchor uniqueness')
    start=s.index(BEGIN);end=s.index(END)
    if not start<end or s[start:end]!=BEGIN+'eyes W110-before-brush 5 0\nready=W110-before-brush\nhidden=0\n':raise ValueError('unexpected worker segment')
    s=s[:start]+REPLACEMENT+s[end:]
    old=END+'"$anchor" evidence/W110-before-brush-rows.json'
    new=END+'"$anchor" "evidence/$ready-rows.json"'
    if s.count(old)!=1:raise ValueError('stroke row anchor')
    return s.replace(old,new).encode()
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit(2)
    raw=Path(sys.argv[1]).read_bytes()
    with Path(sys.argv[2]).open('xb') as f:f.write(adapt(raw))

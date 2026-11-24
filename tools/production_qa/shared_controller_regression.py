"""Controller safety regression, local mocks only."""
import tempfile,time
from pathlib import Path
from unittest.mock import patch
from session_plan import ready,sha
import shared_session_controller as c

def main():
    with tempfile.TemporaryDirectory() as d:
        base=Path(d); root=base/"root"; root.mkdir()
        outside=base/"outside"; outside.write_bytes(b"fixture")
        stage=dict(id="face",deps=[],fingerprint="fixture",qualified=True,seconds=5)
        record=dict(path="../outside",fingerprint="fixture",reopened=True,sha256=sha(outside))
        assert ready([stage],{"face":record},root,20,2)==["face"]
        native=root/"native"; native.write_bytes(b"fixture")
        record["path"]="native"
        calls=[]
        def execute(s,t,deadline):
            assert deadline>time.monotonic()
            return record
        def persist(records,t,deadline):
            assert deadline>time.monotonic()
            calls.append(dict(records)); return True
        with patch.object(c,"acquire",return_value="token") as acquire, patch.object(c,"assert_owned"), patch.object(c,"release") as release:
            try: c.run("local","UNKNOWN","head",root,[stage],{},execute,persist,20,2)
            except ValueError: pass
            else: raise AssertionError("unknown asset accepted")
            acquire.assert_not_called()
            assert c.run("local","MORWEN","head",root,[stage],{},execute,persist,20,2)==["face"]
            assert len(calls)==2
            release.assert_called_once()
            release.reset_mock()
            try: c.run("local","MORWEN","head",root,[stage],{},execute,lambda *a:False,20,2)
            except RuntimeError: pass
            else: raise AssertionError("unconfirmed persistence accepted")
            release.assert_not_called()
        child=dict(id="hair",deps=["face"],fingerprint="fixture",qualified=True,seconds=5)
        grand=dict(id="export",deps=["hair"],fingerprint="fixture",qualified=True,seconds=5)
        stale={"hair":dict(record),"export":dict(record)}
        with patch.object(c,"acquire",return_value="token"), patch.object(c,"assert_owned"), patch.object(c,"release"):
            assert c.run("local","MORWEN","head",root,[stage,child,grand],stale,execute,persist,30,2)==["face","hair","export"]
        print("CONTROLLER_SAFETY_PASS")
        print("TRANSITIVE_INVALIDATION_PASS")
        from shared_session_contract import verified_file_hashes
        assert verified_file_hashes(root,{"native":sha(native)})=={"native":sha(native)}
        for manifest in ({"native":"0"*64},{"../outside":sha(outside)},{"missing":"0"*64}):
            try: verified_file_hashes(root,manifest)
            except ValueError: pass
            else: raise AssertionError("unsafe manifest accepted")
        print("INPUT_BYTES_PASS")
if __name__=="__main__": main()

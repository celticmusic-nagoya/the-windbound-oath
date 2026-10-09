from pathlib import Path
import subprocess,json
r=Path('/workspace/the-windbound-oath');base='e9b5c952a1ad11b07f4fd26d7bb63b3ec19c4a62'
files=subprocess.check_output(['git','ls-tree','-r','--name-only',base],cwd=r,text=True).splitlines();protected=[f for f in files if f.startswith(('img/','css/','js/')) and f not in ['js/field/field-movement.js','js/field/lind-river.js','js/field/lind-review.js']]
changes=[f for f in protected if subprocess.check_output(['git','show',base+':'+f],cwd=r)!=(r/f).read_bytes()];assert not changes,changes
old=subprocess.check_output(['git','show',base+':index.html'],cwd=r,text=True);new=(r/'index.html').read_text();anchor='let ipx=485,ipy=575,itarget=null;';assert old[old.index(anchor):]==new[new.index(anchor):]
refs=subprocess.run(['rg','-n','battle/embedded|asset_[0-9]+_|battle/support/lou','index.html','css','js'],cwd=r,capture_output=True,text=True);assert refs.returncode==1,refs.stdout
assert not (r/'img/battle/embedded').exists()
print(json.dumps({'protectedExistingFiles':len(protected),'unchanged':True,'inlineRoomStoryBattleCodeUnchanged':True,'legacyReferences':0,'embeddedAbsent':True},indent=2))

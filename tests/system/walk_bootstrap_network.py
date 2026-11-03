"""Negative controls: no blanket ERR_ABORTED/network-error suppression."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tests/helpers'))
from walk_bootstrap_network import expected_retarget
old='http://local/img/battle/enemies/goblin_raider/goblin_raider_battle_idle.png'
new='http://local/img/battle/enemies/goblin_raider/motion/goblin_raider_idle_01.png'
assert (ROOT/new.split('http://local/')[1]).is_file()
event={'url':old,'failure':'net::ERR_ABORTED','resource_type':'image','before_dev':True}
image={'url':new,'loaded':True,'registered':[new]}
assert expected_retarget(event,old,image);print('PASS verified unused bootstrap retarget')
for name,ev,im in [
 ('different URL',{**event,'url':new},image),
 ('real network error',{**event,'failure':'net::ERR_CONNECTION_RESET'},image),
 ('HTTP failure',{**event,'failure':'net::ERR_HTTP_RESPONSE_CODE_FAILURE'},image),
 ('after DEV opened',{**event,'before_dev':False},image),
 ('not an image',{**event,'resource_type':'fetch'},image),
 ('failed replacement decode',event,{**image,'loaded':False}),
 ('old source still active',event,{**image,'url':old,'registered':[old]}),
 ('unregistered replacement',event,{**image,'registered':[]})]:
 assert not expected_retarget(ev,old,im),name;print('PASS rejects '+name)
print('FAILS 0')

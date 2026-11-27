"""Offline tests using the authenticated real source archive; no private API writes."""
import pathlib
import sys
from restore_morwen_preserved import *

raw = pathlib.Path(sys.argv[1]).read_bytes()
class API:
    def __init__(self, case='ok'):
        self.case = case
        self.calls = []
    def __call__(self, token, method, url, **kwargs):
        assert token == 'fixture-only' and method == 'GET'
        self.calls.append(url)
        if url == BASE:
            return dict(full_name=DEST, private=self.case != 'public')
        if url == BASE + '/releases/tags/' + TAG:
            return dict(id=RELEASE_ID if self.case != 'release' else 0, tag_name=TAG,
                        draft=self.case == 'draft', prerelease=True, target_commitish='241760938b0901b95a11ecbe31736ff89ad32661',
                        assets=[dict(id=ASSET_ID if self.case != 'asset' else 0, name='15018109141.zip',
                                     state='uploaded', size=ARCHIVE_BYTES, digest='sha256:' + (ARCHIVE_SHA if self.case != 'digest' else '0'*64))])
        assert url == BASE + f'/releases/assets/{ASSET_ID}' and kwargs == dict(binary=True, limit=ARCHIVE_BYTES)
        if self.case == 'corrupt': return raw[:-1] + bytes([raw[-1] ^ 1])
        if self.case == 'truncated': return raw[:-1]
        return raw

api = API()
assert sha(restore(api, 'fixture-only')) == NATIVE_SHA and len(api.calls) == 3
cases = ['exact native archive and nested CRC']
for name in ('public', 'release', 'draft', 'asset', 'digest', 'corrupt', 'truncated'):
    api = API(name)
    try: restore(api, 'fixture-only')
    except ValueError: pass
    else: raise AssertionError(name)
    if name not in ('corrupt', 'truncated'): assert len(api.calls) < 3
    cases.append(name + ' rejected')
api = API()
try: restore(api, '')
except ValueError: pass
else: raise AssertionError('missing token')
assert not api.calls
cases.append('missing credential rejected before request')
print(f'{len(cases)}/{len(cases)} PASS', *cases, sep='\n')

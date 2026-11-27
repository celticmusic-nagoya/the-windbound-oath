"""Narrow REST transport for the pinned preservation engine's Release calls."""
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

DEST = 'celticmusic-nagoya/the-windbound-oath-handoff'
CAP = 128 * 1024 * 1024

class TransportError(ValueError):
    def __init__(self, status=0):
        self.status = status if type(status) is int and 400 <= status <= 599 else 0
        super().__init__('release transport blocked')

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def require(ok):
    if not ok:
        raise TransportError()

def request(token, method, url, body=None, content_type='application/json', binary=False, limit=CAP):
    require(urllib.parse.urlsplit(url).hostname in ('api.github.com','uploads.github.com') and url.startswith('https://'))
    headers = {'Authorization':'Bearer '+token, 'Accept':'application/octet-stream' if binary else 'application/vnd.github+json', 'X-GitHub-Api-Version':'2022-11-28', 'User-Agent':'TWO-preservation'}
    if body is not None:
        headers['Content-Type'] = content_type
    opener = urllib.request.build_opener(NoRedirect())
    try:
        try:
            response = opener.open(urllib.request.Request(url, data=body, headers=headers, method=method), timeout=90)
        except urllib.error.HTTPError as exc:
            if not (binary and method == 'GET' and exc.code in (301,302,303,307,308)):
                raise TransportError(exc.code) from None
            location = exc.headers.get('Location','')
            parsed = urllib.parse.urlsplit(location)
            require(parsed.scheme == 'https' and parsed.hostname is not None and parsed.hostname.endswith('.githubusercontent.com') and not parsed.username and not parsed.password and parsed.port in (None,443))
            # Signed asset URL is used without the private repository credential.
            response = opener.open(urllib.request.Request(location, headers={'User-Agent':'TWO-preservation'}), timeout=90)
        with response:
            data = response.read(limit+1)
        require(len(data) <= limit)
        return data if binary else json.loads(data)
    except urllib.error.HTTPError as exc:
        raise TransportError(exc.code) from None
    except (OSError, ValueError) as exc:
        if isinstance(exc, TransportError):
            raise
        raise TransportError() from None

class ReleaseTransport:
    def __init__(self, original_gh, dest_token, stage, api=request):
        self.original = original_gh
        self.token = dest_token
        self.stage = stage
        self.api = api
        self.records = {}
        self.base = 'https://api.github.com/repos/'+DEST+'/releases'

    def __call__(self, token, args, output=None, missing_ok=False):
        if args[0] != 'release':
            return self.original(token, args, output=output, missing_ok=missing_ok)
        require(token == self.token and output is None and not missing_ok)
        action, tag = args[1:3]
        require(re.fullmatch(r'preserved-artifact-[0-9]+',tag) and args[args.index('--repo')+1] == DEST)
        if action == 'create':
            self.stage('RELEASE_CREATE')
            path = pathlib.Path(args[3])
            require(path.name == tag.removeprefix('preserved-artifact-')+'.zip' and path.is_file() and 0 < path.stat().st_size <= CAP and tag not in self.records)
            target = args[args.index('--target')+1]
            require(re.fullmatch('[0-9a-f]{40}',target) and '--draft' in args and '--prerelease' in args)
            payload = dict(tag_name=tag,target_commitish=target,name=tag,body=args[args.index('--notes')+1],draft=True,prerelease=True,make_latest='false')
            release = self.api(token,'POST',self.base,json.dumps(payload).encode())
            rid = release.get('id')
            require(type(rid) is int and rid > 0 and release.get('tag_name') == tag and release.get('draft') is True)
            self.stage('RELEASE_UPLOAD')
            upload = 'https://uploads.github.com/repos/'+DEST+f'/releases/{rid}/assets?name='+urllib.parse.quote(path.name,safe='')
            asset = self.api(token,'POST',upload,path.read_bytes(),'application/zip')
            aid=asset.get('id')
            require(type(aid) is int and aid > 0 and asset.get('name') == path.name and asset.get('state') == 'uploaded' and asset.get('size') == path.stat().st_size)
            self.records[tag]=(rid,aid,path.name,path.stat().st_size,False)
        elif action == 'download':
            require(tag in self.records)
            rid,aid,name,size,published=self.records[tag]
            self.stage('RELEASE_FINAL_READBACK' if published else 'RELEASE_DRAFT_READBACK')
            require(args[args.index('--pattern')+1] == name)
            directory=pathlib.Path(args[args.index('--dir')+1]); require(directory.is_dir())
            data=self.api(token,'GET',self.base+f'/assets/{aid}',binary=True,limit=size)
            require(len(data)==size)
            with (directory/name).open('xb') as f:
                f.write(data)
        elif action == 'edit':
            self.stage('RELEASE_PUBLISH')
            require(tag in self.records and '--draft=false' in args and '--prerelease' in args)
            rid,aid,name,size,published=self.records[tag]; require(not published)
            release=self.api(token,'PATCH',self.base+f'/{rid}',json.dumps(dict(draft=False,prerelease=True,make_latest='false')).encode())
            require(release.get('id')==rid and release.get('tag_name')==tag and release.get('draft') is False and release.get('prerelease') is True)
            self.records[tag]=(rid,aid,name,size,True)
        else:
            raise TransportError()
        return b''

"""Resolve official TV/mobile APK, verify version/ABI and patch decoded smali literals."""
import hashlib, json, os, pathlib, re, subprocess, urllib.request, zipfile
REPO = 'MediaBrowser/Emby.Releases'
CLIENT_PATHS = {
    'tv': 'androidtv/app-google-release.apk',
    'mobile': 'android/emby-android-google-arm64-v8a-release.apk',
}

def source_path(client):
    if client not in CLIENT_PATHS:
        raise ValueError('Unknown client: '+client)
    return CLIENT_PATHS[client]

def api(path):
    req = urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path, headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'], 'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)

def valid_domain(value):
    value = value.strip().lower()
    if len(value)>253 or '.' not in value or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',x) for x in value.split('.')):
        raise ValueError('Enter a DNS hostname only, without scheme, path, port or wildcard')
    return value

def patch(folder, domain):
    changes=[]
    for path in sorted(pathlib.Path(folder).glob('smali*/**/*.smali')):
        text=path.read_text(encoding='utf-8')
        # Patch hostname literals only, not arbitrary binary files or unrelated domains.
        pattern=r'(?<![A-Za-z0-9_.-])mb3admin\.com(?![A-Za-z0-9_.-])'
        updated,count=re.subn(pattern,lambda _:domain,text)
        if count:
            path.write_text(updated,encoding='utf-8'); changes.append({'file':str(path),'occurrences':count})
    if not changes: raise RuntimeError('No expected hostname literals found; manual review required')
    return changes

def main():
    client=os.environ.get('CLIENT','tv')
    path=source_path(client)
    domain=valid_domain(os.environ['TARGET_DOMAIN'])
    version=os.environ.get('APK_VERSION','').strip()
    latest=not version or version.lower()=='latest'
    commits=api('commits?path='+path+'&per_page='+('1' if latest else '100'))
    if not commits: raise RuntimeError('No official client history available')
    pathlib.Path('out').mkdir(exist_ok=True)
    selected=None
    for entry in commits:
        sha=entry['sha']; url='https://raw.githubusercontent.com/'+REPO+'/'+sha+'/'+path
        with urllib.request.urlopen(url,timeout=120) as response, open('original.apk','wb') as output:
            import shutil
            shutil.copyfileobj(response,output)
        badging=subprocess.check_output([os.environ['AAPT'],'dump','badging','original.apk'],text=True)
        match=re.search(r"versionName='([^']+)'",badging)
        if not match: raise RuntimeError('Cannot read APK version')
        actual=match.group(1)
        if not latest and actual!=version: continue
        with zipfile.ZipFile('original.apk') as apk:
            abis=sorted({p.split('/')[1] for p in apk.namelist() if p.startswith('lib/') and p.endswith('.so')})
        if abis and 'arm64-v8a' not in abis: raise RuntimeError('Selected APK lacks arm64-v8a: '+str(abis))
        selected={'client':client,'source_path':path,'version':actual,'requested_version':version or 'latest','domain':domain,'source_url':url,'source_commit':sha,'abis':abis,'original_sha256':hashlib.sha256(pathlib.Path('original.apk').read_bytes()).hexdigest()}
        break
    if selected is None: raise RuntimeError('Version not found in latest 100 client file revisions; refusing fallback')
    subprocess.run(['apktool','d','-r','-f','original.apk','-o','decoded'],check=True)
    selected['changes']=patch('decoded',domain)
    subprocess.run(['apktool','b','decoded','-o','rebuilt.apk'],check=True)
    pathlib.Path('out/report.json').write_text(json.dumps(selected,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()

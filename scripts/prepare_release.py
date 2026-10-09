"""Collect both client artifacts, verify hashes, and prepare Release attachments."""
import argparse, hashlib, json, pathlib, shutil

def prepare(source, output, run_id):
    source=pathlib.Path(source); output=pathlib.Path(output)
    clients={}
    for client in ('tv','mobile'):
        folder=source / ('emby-'+client+'-test-'+str(run_id))
        report=json.loads((folder/'report.json').read_text(encoding='utf-8'))
        if report['client']!=client: raise ValueError('Artifact client mismatch')
        apk=folder/('emby-'+client+'-test.apk')
        digest=hashlib.sha256(apk.read_bytes()).hexdigest()
        if digest!=report['test_apk_sha256']: raise ValueError('APK hash mismatch: '+client)
        clients[client]=(folder,report)
    if clients['tv'][1]['domain']!=clients['mobile'][1]['domain']:
        raise ValueError('Client test domains differ')
    output.mkdir(parents=True,exist_ok=True)
    assets=[]
    for client,(folder,report) in clients.items():
        for name in ('emby-'+client+'-test.apk','report.json','signature.txt','alignment.txt','environment.txt'):
            target=output/(name if name.endswith('.apk') else client+'-'+name)
            shutil.copyfile(folder/name,target); assets.append(target)
    (output/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in assets),encoding='utf-8')
    tv=clients['tv'][1]; mobile=clients['mobile'][1]
    notes=(f"# Authorized test APK build {run_id}\n\n"
           f"- Android TV: {tv['version']}\n- Android mobile ARM64: {mobile['version']}\n"
           f"- Test endpoint: {tv['domain']}\n"
           "- Both APKs use the fixed PUBLIC TEST signing key, not the official signing key.\n"
           "- APK hashes, signing and alignment were verified; device behavior is not yet verified.\n"
           "- For authorized testing only. Public signing material is not a trusted identity.\n"
           "- Cannot overwrite an installation signed with the official key.\n\n"
           "Download emby-tv-test.apk or emby-mobile-test.apk. Per-client reports and SHA256SUMS.txt are attached.\n")
    (output/'release-notes.md').write_text(notes,encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',required=True); parser.add_argument('--output',required=True); parser.add_argument('--run-id',required=True)
    args=parser.parse_args(); prepare(args.source,args.output,args.run_id)

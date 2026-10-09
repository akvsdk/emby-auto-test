import hashlib,json,pathlib,tempfile,unittest
from prepare_release import prepare
class ReleaseTests(unittest.TestCase):
    def fixtures(self,base):
        for client in ('tv','mobile'):
            folder=base/('emby-'+client+'-test-42'); folder.mkdir(parents=True)
            data=client.encode(); (folder/('emby-'+client+'-test.apk')).write_bytes(data)
            report={'client':client,'version':'1.0','domain':'test.example.com','test_apk_sha256':hashlib.sha256(data).hexdigest()}
            (folder/'report.json').write_text(json.dumps(report))
            for name in ('signature.txt','alignment.txt','environment.txt'): (folder/name).write_text('test')
    def test_complete_assets(self):
        with tempfile.TemporaryDirectory() as temp:
            base=pathlib.Path(temp); self.fixtures(base/'artifacts'); prepare(base/'artifacts',base/'release',42)
            self.assertEqual(len(list((base/'release').glob('*.apk'))),2)
            self.assertEqual(len((base/'release'/'SHA256SUMS.txt').read_text().splitlines()),10)
    def test_reject_modified_apk(self):
        with tempfile.TemporaryDirectory() as temp:
            base=pathlib.Path(temp); self.fixtures(base/'artifacts')
            (base/'artifacts'/'emby-tv-test-42'/'emby-tv-test.apk').write_bytes(b'changed')
            with self.assertRaises(ValueError):prepare(base/'artifacts',base/'release',42)
if __name__=='__main__':unittest.main()

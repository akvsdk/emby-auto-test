import pathlib,tempfile,unittest
from prepare_tv import valid_domain,patch,source_path
class Tests(unittest.TestCase):
    def test_client_sources(self):
        self.assertEqual(source_path('tv'),'androidtv/app-google-release.apk')
        self.assertEqual(source_path('mobile'),'android/emby-android-google-arm64-v8a-release.apk')
        with self.assertRaises(ValueError): source_path('unknown')
    def test_domain(self):
        self.assertEqual(valid_domain('Emby.nasa.us.ci'),'emby.nasa.us.ci')
        for value in ['https://a.b','a.b/path','a.b:443','a..b','-a.b','a.b;echo bad']:
            with self.assertRaises(ValueError): valid_domain(value)
    def test_patch(self):
        with tempfile.TemporaryDirectory() as folder:
            p=pathlib.Path(folder)/'smali';p.mkdir(); f=p/'Test.smali'
            f.write_text('const-string v0, "https://mb3admin.com/admin"\nconst-string v1, "evilmb3admin.com"',encoding='utf-8')
            changes=patch(folder,'emby.nasa.us.ci')
            self.assertEqual(changes[0]['occurrences'],1)
            self.assertIn('https://emby.nasa.us.ci/admin',f.read_text())
            self.assertIn('evilmb3admin.com',f.read_text())
    def test_no_match(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):patch(folder,'a.b')
if __name__=='__main__': unittest.main()

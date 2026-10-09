"""Fail if apksigner reports any certificate other than the public test fixture."""
import pathlib,re,sys
expected=pathlib.Path('test-signing/certificate-sha256.txt').read_text().strip().replace(':','').lower()
report=pathlib.Path(sys.argv[1]).read_text()
actual=re.findall(r'Signer #\d+ certificate SHA-256 digest:\s*([0-9a-fA-F:]+)',report)
if len(actual)!=1 or actual[0].replace(':','').lower()!=expected:
    raise SystemExit('Unexpected signing certificate; refusing upload')
print('Public test signing certificate verified:',expected)

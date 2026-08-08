#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess,zipfile,shutil,sys,base64,zlib

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'function-package-v79.zip'
PATCH=ROOT/'_v80_patch.tmp'
WORK=ROOT/'_build_function_v80'
OUT=ROOT/'function-package-v80.zip'
EXPECTED_BASE='36dcd6aff78ad87f140649ef763bfb538923a9fb9bf1839b068f2f261011b416'
EXPECTED_OUT='bde8f58732a8f0320c75816a68a5b19dffb436b6d99cc141235bec5a346b457c'
LATEST_TEXT='{\n  "schemaVersion": 1,\n  "packageType": "stadslass-web-module-zip-v1",\n  "packageVersion": 80,\n  "minHostVersionCode": 18,\n  "payloadUrl": "https://raw.githubusercontent.com/Gagge007/stadslass-3.0-updates/main/function-package-v80.zip",\n  "payloadSha256": "bde8f58732a8f0320c75816a68a5b19dffb436b6d99cc141235bec5a346b457c",\n  "payloadSignature": "Yx2XBFLCam+CzAX6cpqM79rxWz9A4eSxZw+tBiRWT9uYkimpYxZmDwuxqCr1HOmKH0CLTO41jus9mzy8JnqTtCfZ4nlcQKh8Kenz92uqSUpwdTZIz/GbwwlQhhBboPkuUhLAp29tE1jabypdZAx5FNgxPq3WLL7efqxDBxyJAS49OtBbWXHBL4SQK9YZIhKYfiXV6+rKovWIK2FiuoQTeKzp9tRYIX3zJaUAxGwCDdKupq1RMyTQ98C1UxFeLjEEIxJNijVWUtU44kymR0q2fI5w7zR2XDQcKnOGzOmKWLKT0ZDGQo3YuNX9mu7RVd4qTTnj2VdFnEpeFsbjO9DxFQ9f1U2aRRR7i4VAa5swBPiNL6xkhPMmxCUl9JUK0NNQqmLVS+z0yEpNXv5j6VXrSydLXNQGTwWVmXfqdQez0s3IMwOQQLtK0V4b+tY2TYFX4dQICokpy0bFsF1zAOO+skL5AtZrWdEKwEo9HD0XqWvH5r4n0tspEQMMgqpDbSoJ",\n  "publishedAt": "2026-08-08T21:23:25.000Z"\n}\n'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if not BASE.is_file() or sha(BASE)!=EXPECTED_BASE: raise SystemExit('Fel eller saknad function-package-v79.zip')
if WORK.exists(): shutil.rmtree(WORK)
WORK.mkdir()
with zipfile.ZipFile(BASE) as z: z.extractall(WORK)
renames={
'CHANGELOG-v79.txt':'CHANGELOG-v80.txt','TECHNICAL-TEST-REPORT-v79.txt':'TECHNICAL-TEST-REPORT-v80.txt','css/app-v79.css':'css/app-v80.css','index-v79.html':'index-v80.html','js/app-v79.js':'js/app-v80.js','js/driftsync-handshake-service-v79.js':'js/driftsync-handshake-service-v80.js','js/performance-monitor-v79.js':'js/performance-monitor-v80.js','js/sync-diagnostic-v79.js':'js/sync-diagnostic-v80.js','js/sync-service-v79.js':'js/sync-service-v80.js'}
for a,b in renames.items(): (WORK/a).rename(WORK/b)
for p in WORK.rglob('*'):
    if not p.is_file() or p.name=='module.json': continue
    try: t=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    t=t.replace('v79','v80').replace('V79','V80').replace('package 79','package 80').replace('Paket 79','Paket 80').replace('paket 79','paket 80').replace('const PACKAGE_VERSION = 79','const PACKAGE_VERSION = 80')
    p.write_text(t,encoding='utf-8')
m=json.loads((WORK/'module.json').read_text())
m['packageVersion']=80;m['entryPoint']='index-v80.html'
for f in m['files']: f['path']=f['path'].replace('v79','v80')
(WORK/'module.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
chunks=[]
for i in range(1,6):
    chunks.append((ROOT/f'tools/v80-patch-b64-{i}.txt').read_text(encoding='ascii').strip())
PATCH.write_bytes(zlib.decompress(base64.b64decode(''.join(chunks))))
try:
    subprocess.run(['patch','-s','-p1','-d',str(WORK),'-i',str(PATCH)],check=True)
finally:
    PATCH.unlink(missing_ok=True)
# regenerate manifest after patch
m=json.loads((WORK/'module.json').read_text())
for rec in m['files']:
    p=WORK/rec['path']
    if not p.is_file(): raise SystemExit('Manifestfil saknas: '+rec['path'])
    b=p.read_bytes();rec['size']=len(b);rec['sha256']=hashlib.sha256(b).hexdigest()
(WORK/'module.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
# exact file set
manifest={r['path'] for r in m['files']}
actual={p.relative_to(WORK).as_posix() for p in WORK.rglob('*') if p.is_file() and p.name!='module.json'}
if manifest!=actual: raise SystemExit(f'Filuppsättning avviker: {manifest-actual} / {actual-manifest}')
# deterministic uncompressed ZIP; exact same bytes on all runners
if OUT.exists(): OUT.unlink()
with zipfile.ZipFile(OUT,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as z:
    for p in sorted([x for x in WORK.rglob('*') if x.is_file()],key=lambda x:x.relative_to(WORK).as_posix()):
        rel=p.relative_to(WORK).as_posix();info=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_STORED;info.create_system=3;info.external_attr=(0o100644<<16);info.flag_bits=0
        z.writestr(info,p.read_bytes())
if sha(OUT)!=EXPECTED_OUT: raise SystemExit(f'v80 SHA avviker: {sha(OUT)} != {EXPECTED_OUT}')
(ROOT/'latest.json').write_text(LATEST_TEXT,encoding='utf-8')
print('FUNCTION_PACKAGE_V80_BUILD_PASS',sha(OUT),OUT.stat().st_size)
shutil.rmtree(WORK)

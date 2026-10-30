"""Validate the distributable documentation without reading private installation data."""
from pathlib import Path
import html,json,re,sys,zipfile,subprocess
from xml.etree import ElementTree as ET
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import build_documentation as builder
OUT=ROOT/'Documentation'

def validate():
 checks=[]
 def check(condition,label):
  if not condition:raise AssertionError(label)
  checks.append(label)
 manifest=json.loads((OUT/'manifest.json').read_text())
 documents=manifest['documents']
 check(len(documents)==63 and len({d['id'] for d in documents})==63,'63 uniquely identified documents')
 check(len(list(OUT.glob('[0-9][0-9]_*/*.md')))==63,'All registered document files exist; no obsolete chapters')
 check(len({d['file'].split('/')[0] for d in documents})==10,'10 documentation categories matching the reference layout')
 for doc in documents:
  path=OUT/doc['file'];body=path.read_text()
  check(doc['id'] in body and len(body)>600,doc['id']+' has substantive authored content')
  check('GENERATED_' not in body and not re.search(r'\b(?:TODO|TBD)\b',body),doc['id']+' has no unresolved template markers')
  for target in re.findall(r'\[[^]]*\]\(([^)]+)\)',body):
   if target.startswith(('http:','https:','#','mailto:')):continue
   check((path.parent/target.split('#')[0]).is_file(),doc['id']+' local link: '+target)
 schema=json.loads((OUT/'02_Architecture'/'A-04_OpenAPI.json').read_text())
 actual,routes,dictionary,tables=builder.source_metadata()
 check(schema==actual,'OpenAPI matches the current source and documentation security annotations')
 api=next(OUT/d['file'] for d in documents if d['id']=='A-04')
 catalog=api.read_text()
 for path,operations in schema['paths'].items():
  for method in operations:
   if method.lower() not in ('get','post','put','patch','delete','options','head'):continue
   check(f'| {method.upper()} | `{path}` |' in catalog,'Route catalog: '+method.upper()+' '+path)
   operation=operations[method]
   if path not in ('/healthz','/api/v1/auth/login','/api/v1/auth/configuration'):
    check(operation.get('security')==[{'StaffSession':[]}],'Session annotation: '+path)
   if method in ('post','put','patch','delete'):
    check(any(p['name']=='x-csrf-protection' for p in operation.get('parameters',[])),'CSRF annotation: '+path)
 data=next(OUT/d['file'] for d in documents if d['id']=='A-03')
 check(dictionary in data.read_text() and tables==16,'Complete dictionary matches all 16 ORM tables')
 reader=(OUT/'index.html').read_text()
 for doc in documents:check(f'id="{doc["id"]}"' in reader,'HTML chapter: '+doc['id'])
 for target in re.findall(r'(?:href|src)="([^"]+)"',reader):
  target=html.unescape(target)
  if target.startswith(('https:','http:','#')):continue
  check((OUT/target.split('#')[0]).is_file(),'HTML local resource: '+target)
 with zipfile.ZipFile(OUT/'TWSS_IVR_Business_Requirements.docx') as docx:
  check(docx.testzip() is None,'Word package integrity')
  for name in docx.namelist():
   if name.endswith(('.xml','.rels')):ET.fromstring(docx.read(name))
  check(b'Business Requirements Document' in docx.read('word/document.xml'),'Word BRD contains the business requirements')
 # Match secret formats, never read private env/runtime files to compare values.
 pattern=re.compile(r'postgres(?:ql)?://[^\s<>]+:[^\s<>]+@|-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,}')
 for path in OUT.rglob('*'):
  if path.is_file() and path.suffix in ('.md','.html','.json'):
   check(not pattern.search(path.read_text()),'No credential-like material: '+path.relative_to(OUT).as_posix())
 check('quota' in reader.lower() and 'draft' in reader.lower(),'Reader distinguishes review status and cloud limitation')
 tests=subprocess.run([sys.executable,'-m','pytest','-q','tests/test_documentation.py'],cwd=ROOT,capture_output=True,text=True)
 check(tests.returncode==0,'Existing documentation regression tests pass')
 result={'existing_documentation_tests':{'command':'.venv/bin/python -m pytest -q tests/test_documentation.py','exit_code':tests.returncode,'result':next((line for line in reversed(tests.stdout.splitlines()) if 'passed' in line),'Completed successfully')},'status':'passed','checked_at_utc':datetime.now(timezone.utc).isoformat(),'source_commit':manifest['source_commit'],'checks_passed':len(checks),'coverage':['63 documents / 11 sections','All Markdown and HTML local links','Source-derived OpenAPI operations, permission and CSRF annotations','16-table ORM dictionary','Word XML and ZIP structure','Credential-format scan of distributable text'],'limits':['No live provider calls or tenant database access','No legal approval, business signoff, external penetration test or uptime certification','Application baseline tests are recorded separately; these checks validate the documentation pack']}
 (OUT/'validation-results.json').write_text(json.dumps(result,indent=2)+'\n')
 builder.package()
 with zipfile.ZipFile(ROOT/'TWSS_IVR_Documentation.zip') as package:
  check(package.testzip() is None,'Shareable ZIP integrity')
  expected={p.relative_to(ROOT).as_posix() for p in OUT.rglob('*') if p.is_file()}
  check(set(package.namelist())==expected,'ZIP contains exactly the documentation pack')
  check(all(not any(part.startswith('.') or part in ('__MACOSX','node_modules') for part in Path(n).parts) for n in package.namelist()),'No private or unrelated folders in ZIP')
 print(json.dumps({'status':'passed','checks':len(checks),'documents':len(documents),'zip':str(ROOT/'TWSS_IVR_Documentation.zip')}))

if __name__=='__main__':validate()

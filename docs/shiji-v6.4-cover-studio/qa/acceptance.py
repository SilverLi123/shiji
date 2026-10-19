"""Delivery evidence gate; actual suites/runs remain separate recorded executions."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];doc=Path(__file__).resolve().parent.parent;e=doc/'evidence'
ci=json.loads((e/'ci.json').read_text());assert ci['conclusion']=='success' and ci['sha'].startswith('7bc01cb');assert len(ci['jobs'])==5 and all(j['conclusion']=='success' for j in ci['jobs'])
native=json.loads((e/'native-ui.json').read_text());assert native['passed'] and native['cases']==2 and native['codeSubtitleOCR'] and native['originalV5CodeSubtitleOCR'];assert native['physicalDeviceAccepted'] is False
art=json.loads((e/'art-manifest.json').read_text());assert art['actualPage'] and len(art['rows'])==15;assert len({(r['style'],r['template']) for r in art['rows']})==15
scale=json.loads((e/'scale-optimized-summary.json').read_text());assert len(scale['runs'])==16 and all(r['rounds']==3 for r in scale['runs'])
for a in scale['artifacts']:
 p=ROOT/a['file'];assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
for name in ['REPORT.md','PERFORMANCE.md','COMPATIBILITY.md','API.md','ART_CATALOG.md','CODE_REVIEW.md','VISUAL_VERDICT.md','DESIGN_EXTENSION.md','RULINGS.md']:
 assert (doc/name).is_file(),name
for name in ['board-before.png','board-after.png','desktop-editor.png','mobile-editor.png','mobile-editor-controls.png','native-code-subtitle.png','native-v5-code-subtitle.png']:
 assert (e/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),name
print('PASS: verified five-job optimized CI, actual native2-case acceptance,15 compositions,48 matched baseline/optimized rounds and hashed raw evidence; physical-device/motion gaps retained')

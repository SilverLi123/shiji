"""Prove the actual name-sort browser race rejects removal of the press fence."""
import shutil,subprocess,sys,tempfile
from pathlib import Path
repo=Path(__file__).resolve().parents[3];sys.path.insert(0,str(repo/'desktop-app/tests'))
import run_gallery_browser as suite
with tempfile.TemporaryDirectory(prefix='shiji-v63-press-mutation-') as scratch:
 root=Path(scratch);shutil.copytree(repo/'desktop-app/static',root/'static')
 app=root/'static/app.js';source=app.read_text();guard='  if(galleryWindow?.deferWhilePressed(render))return;'
 assert source.count(guard)==1;app.write_text(source.replace(guard,'',1));suite.server.ROOT=root
 original=subprocess.run
 def captured(*args,**kwargs):return original(*args,**kwargs,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 subprocess.run=captured
 try:
  try:suite.run()
  except subprocess.CalledProcessError as error:
   print(error.stderr)
   assert 'Timeout 3000ms exceeded' in error.stderr and "#drawer:not([hidden])" in error.stderr,'Mutation failed for an unrelated reason'
   print('PASS: exact single-click name-sort regression rejects missing press fence')
  else:raise SystemExit('Mutation unexpectedly passed')
 finally:subprocess.run=original

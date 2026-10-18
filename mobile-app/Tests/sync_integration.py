"""Actual production Swift URLSession client against temporary desktop TLS Store."""
from pathlib import Path
import json,subprocess,sys,tempfile
root=Path(__file__).resolve().parents[1]
desktop=root.parent/'desktop-app'
sys.path.insert(0,str(desktop))
from storage import Store
from sync_transport import SyncService
(root/'build').mkdir(exist_ok=True)
subprocess.run(['xcrun','clang','-c',str(root/'Shared/Codec.c'),'-o',str(root/'build/SyncCodec.o')],check=True)
sources=[root/'Shared'/name for name in ['Library.swift','CoverConfiguration.swift','Archive.swift','SyncMerge.swift','SyncClient.swift']]
binary=root/'build/SyncIntegration'
subprocess.run(['xcrun','swiftc','-parse-as-library','-swift-version','5','-import-objc-header',str(root/'Shared/Codec.h'),*[str(p) for p in sources],str(root/'Tests/SyncIntegration.swift'),str(root/'build/SyncCodec.o'),'-lz','-o',str(binary)],check=True)
with tempfile.TemporaryDirectory(prefix='shiji-real-sync-') as folder:
 path=Path(folder);store=Store(path/'computer');service=SyncService(store,port=0,bind='127.0.0.1');service.start()
 try:
  desktop_record=store.save({'title':'Computer resource','url':'https://example.com/computer-sync','notes':'Computer original','tags':['New, exact']})['resource']
  image=(desktop/'static/previews/polyhaven.jpg').read_bytes();(path/'fixture.jpg').write_bytes(image);store.attachment(desktop_record['id'],image,{'name':'computer.jpg','cover':True})
  store.update_cover(desktop_record['id'],{'config':{'style':'spatial','customTitle':'Desktop sync cover'},'coverId':store.get(desktop_record['id'])['coverId'],'expected':{'coverConfig':None,'coverId':store.get(desktop_record['id'])['coverId']}})
  (path/'pairing-code.txt').write_text(service.pairing('127.0.0.1')['code']);(path/'pairing-code.txt').chmod(0o600)
  def run(mode):subprocess.run([str(binary),str(path),mode],check=True)
  run('first');assert len(store.state()['resources'])==2
  assert next(r for r in store.state()['resources'] if r['url']=='https://example.com/phone-sync')['coverConfig']['customTitle']=='Phone sync cover'
  store.save({'notes':'Computer second edit'},desktop_record['id']);run('second')
  phone=next(r for r in store.state()['resources'] if r['url']=='https://example.com/phone-sync');assert phone['notes']=='Phone second edit'
  store.save({'notes':'Computer conflict edit'},phone['id']);run('conflict');assert store.get(phone['id'])['notes']=='Computer conflict edit'
  before=service.engine.snapshot()['revision'];run('pin');run('race');assert service.engine.snapshot()['revision']==before
  # Existing records are unrelated to this controlled capture roundtrip.
  for task in store.capture_status()['tasks']:
   if task['status'] in ('pending','running','retry'):store.capture_action({'action':'cancel','id':task['id']})
  sys.path.insert(0,str(desktop/'tests'))
  from capture_fixture import Fixture,png_bytes
  fixture=Fixture()
  try:
   run('capture')
   with fixture.route():assert store.capture_step()
   (path/'enriched.png').write_bytes(png_bytes());run('enriched')
  finally:fixture.close()
  print('PASS: both directions, initial union, explicit conflicts, TLS pin failure and late-capture protection; disposable data only')
 finally:service.stop()

import json,sys,tempfile,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'desktop-app'))
from storage import Store
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='shiji-ios-interop-') as temp:
 store=Store(temp)
 with zipfile.ZipFile(root/'build/fixtures/mobile-roundtrip.zip') as archive:
  staging=Path(temp)/'staging';staging.mkdir();items,attachments,collections,meta,smart=store._validate_archive(archive,staging)
  assert items[0]['tags']==['New, exact'] and items[0]['projectNotes']=={'__proto__':'kept'}
 assert len(attachments)==1
 with zipfile.ZipFile(root/"build/fixtures/mobile-trash.zip") as archive:
  staging2=Path(temp)/"trash-staging";staging2.mkdir();trash,*_=store._validate_archive(archive,staging2)
  assert trash[0]["deleted"] is True
 record=store.save({'url':'https://example.com/from-desktop','title':'From desktop','tags':['New, exact'],'notes':'Desktop note'})['resource']
 cover=Path(__file__).resolve().parents[2]/'desktop-app/static/previews/polyhaven.jpg'
 store.attachment(record['id'],cover.read_bytes(),{'name':'preview.jpg'})
 store.attachment(record['id'],b'%PDF-1.4\nfixture only',{'name':'reference.pdf'})
 store.attachment(record['id'],b'UI notes',{'name':'reference.txt'})
 (root/'build/fixtures/desktop-deflated.zip').write_bytes(store.backup_bytes())
print('Mobile ZIP accepted by existing desktop manifest2 validator; desktop compressed fixture generated using temp Store')

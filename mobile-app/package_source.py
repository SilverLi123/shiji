#!/usr/bin/env python3
"""Create a source-only, unsigned Xcode delivery; no test stores/build products."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parent
destination=root/'dist/Shiji-iPhone-source.zip'
destination.parent.mkdir(exist_ok=True)
directories=['App','ShareExtension','Shared','Shiji.xcodeproj','Tests','docs']
files=[root/name for name in ['README.md','PRODUCT.md','DESIGN.md','generate_project.py','package_source.py']]
files.extend(root/name for name in ['.impeccable/design.json'] if (root/name).is_file())
for name in directories:
 files.extend(p for p in (root/name).rglob('*') if p.is_file() and not any(
  part in {'__pycache__','xcuserdata','.DS_Store'} for part in p.parts))
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
 for path in sorted(set(files)):
  archive.write(path,'Shiji-iPhone/'+str(path.relative_to(root)))
with zipfile.ZipFile(destination) as archive:
 assert archive.testzip() is None
 assert 'Shiji-iPhone/Shiji.xcodeproj/project.pbxproj' in archive.namelist()
 assert all('/build/' not in name and '/data/' not in name for name in archive.namelist())
print(destination)

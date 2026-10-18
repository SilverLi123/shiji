#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,sys
root=Path(__file__).resolve().parents[1]
(root/'build/fixtures').mkdir(parents=True,exist_ok=True)
subprocess.run(['xcrun','clang','-c','Shared/Codec.c','-o','build/Codec.o'],cwd=root,check=True)
subprocess.run(['xcrun','swiftc','-swift-version','5','-import-objc-header','Shared/Codec.h','Shared/CoverConfiguration.swift','Shared/Archive.swift','Shared/SyncMerge.swift','Shared/Library.swift','Tests/CoverTests.swift','build/Codec.o','-lz','-o','build/CoverTests'],cwd=root,check=True)
vectors=root/'Tests/fixtures/cover-config.json'
desktop_vectors=root.parent/'desktop-app/tests/fixtures/cover-config.json'
if desktop_vectors.exists():assert json.loads(vectors.read_text())==json.loads(desktop_vectors.read_text()),'native and desktop cover contracts differ'
args=['build/CoverTests',str(vectors),'build/fixtures']+sys.argv[1:]
subprocess.run(args,cwd=root,check=True)

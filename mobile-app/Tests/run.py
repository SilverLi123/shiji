#!/usr/bin/env python3
"""Native Foundation tests + real desktop ZIP interoperability; temporary stores only."""
from pathlib import Path
import argparse,subprocess,sys
parser=argparse.ArgumentParser()
parser.add_argument('--core-only',action='store_true',help='Run self-contained tests without the adjacent desktop project')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
(root/'build/fixtures').mkdir(parents=True,exist_ok=True)
def run(*cmd): subprocess.run([str(x) for x in cmd],cwd=root,check=True)
run('xcrun','clang','-c','Shared/Codec.c','-o','build/Codec.o')
run('xcrun','swiftc','-swift-version','5','-import-objc-header','Shared/Codec.h','Shared/Archive.swift','Shared/CoverConfiguration.swift','Shared/SyncMerge.swift','Shared/Library.swift','Tests/main.swift','build/Codec.o','-lz','-o','build/CoreTests')
run('build/CoreTests','build/fixtures')
run(sys.executable,'Tests/run_cover.py')
if not args.core_only:
 run(sys.executable,'Tests/interop.py')
 run('build/CoreTests','build/fixtures','build/fixtures/desktop-deflated.zip')
 run('build/CoverTests','Tests/fixtures/cover-config.json','build/fixtures','build/fixtures/desktop-deflated.zip')
print('PASS: native core checks' if args.core_only else 'PASS: all native core and desktop exchange checks')

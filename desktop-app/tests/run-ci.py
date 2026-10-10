"""Partition the complete suite by platform without dropping any test IDs."""
import argparse,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tests'))
p=argparse.ArgumentParser();p.add_argument('--suite',choices=['portable','native'],required=True);args=p.parse_args()
native={'test_native_lifecycle','test_phone_sync_model'}
def cases(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite):yield from cases(item)
  else:yield item
all_cases=list(cases(unittest.defaultTestLoader.discover(str(ROOT/'tests'))))
chosen=[t for t in all_cases if (t.__class__.__module__ in native)==(args.suite=='native')]
if not chosen:raise SystemExit('Empty suite partition')
print(f'{args.suite}: {len(chosen)} / {len(all_cases)} tests; the complementary job covers the remaining IDs',flush=True)
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(chosen))
raise SystemExit(not result.wasSuccessful())

"""Summarize buffered native events; missing evidence never qualifies a run."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
runs = []
current = None
for line in args.source.read_text().splitlines():
    row = json.loads(line)
    if row['event'] == 'webview.create':
        current = {'createTime': row['time'], 'samples': []}
        runs.append(current)
    if current is None:
        continue
    if row['event'] == 'qa.process':
        current.update(host=row['host'], web=row['pid'])
    if row['event'] != 'qa.v52-result':
        continue
    value = json.loads(row['phase'])
    gaps = [frame['gap'] for frame in value.get('frames', [])]
    value['maxGap'] = max(gaps, default=None)
    value['firstGap'] = gaps[0] if gaps else None
    value['visibleRendering'] = bool(
        not value.get('hidden', True) and gaps and value.get('open', False))
    value['validForeground'] = bool(
        value['visibleRendering'] and value.get('focus', False))
    pointer = value.get('pointer') or {}
    value['validPhysicalMouse'] = bool(
        value['validForeground'] and value.get('trusted', False)
        and all(pointer.get(event, {}).get('trusted', False)
                and pointer.get(event, {}).get('pointerType') == 'mouse'
                for event in ('pointerdown', 'pointerup')))
    current['samples'].append(value)

summary = {
    'runs': runs,
    'source': str(args.source),
    'valid': sum(s['validForeground'] for r in runs for s in r['samples']),
    'physicalMouse': sum(s['validPhysicalMouse'] for r in runs for s in r['samples']),
}
args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
for index, run in enumerate(runs, 1):
    print(index, run.get('host'), run.get('web'), [
        (sample.get('sequence'), round(sample.get('handlerMs', 0), 1),
         round(sample['maxGap'], 1) if sample['maxGap'] is not None else None,
         sample['validForeground'], sample['validPhysicalMouse'])
        for sample in run['samples']])

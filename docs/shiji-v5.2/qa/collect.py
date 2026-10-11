"""Summarize immutable buffered native experiment events, keeping every sample."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
rows=[json.loads(line) for line in a.source.read_text().splitlines()];runs=[];current=None
for row in rows:
 if row['event']=='webview.create':current={'createTime':row['time'],'samples':[]};runs.append(current)
 if current is not None and row['event']=='qa.process':current['host']=row['host'];current['web']=row['pid']
 if current is not None and row['event']=='qa.v52-result':
  value=json.loads(row['phase']);gaps=[f['gap'] for f in value.get('frames',[])];value['maxGap']=max(gaps,default=None);value['firstGap']=gaps[0] if gaps else None;value['validForeground']=not value.get('hidden',True) and bool(gaps) and value.get('open',False);current['samples'].append(value)
summary={'runs':runs,'source':str(a.source),'valid':sum(s['validForeground'] for r in runs for s in r['samples'])}
a.output.write_text(json.dumps(summary,indent=2,ensure_ascii=False))
for i,run in enumerate(runs):
 print(i+1,run.get('host'),run.get('web'),[(s.get('sequence'),round(s.get('handlerMs',0),1),round(s.get('maxGap') or 0,1),s['validForeground']) for s in run['samples']])

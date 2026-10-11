"""Regression for evidence attribution and exclusion of background / unrelated samples."""
import gzip,json,subprocess,sys,tempfile,unittest
from pathlib import Path
QA=Path(__file__).resolve().parent
class TraceEvidenceTests(unittest.TestCase):
 def test_background_and_empty_frames_are_not_foreground_evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'events.jsonl';output=Path(tmp)/'summary.json'
   rows=[dict(event='webview.create',time=1),dict(event='qa.process',host=101,pid=202)]
   for hidden,frames,opened,focus in [(True,[dict(gap=250)],True,True),(False,[],True,True),(False,[dict(gap=42)],False,True),(False,[dict(gap=20)],True,False),(False,[dict(gap=30),dict(gap=48)],True,True)]:rows.append(dict(event='qa.v52-result',phase=json.dumps(dict(hidden=hidden,frames=frames,open=opened,focus=focus))))
   source.write_text('\n'.join(map(json.dumps,rows)));subprocess.run([sys.executable,str(QA/'collect.py'),str(source),str(output)],check=True,capture_output=True)
   result=json.loads(output.read_text());self.assertEqual(result['valid'],1);self.assertEqual(result['runs'][0]['web'],202);self.assertEqual(result['runs'][0]['samples'][-1]['maxGap'],48)
 def test_trusted_click_without_pointer_is_not_physical_mouse_evidence(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'events.jsonl';output=Path(tmp)/'summary.json'
   base=dict(hidden=False,focus=True,frames=[dict(gap=30)],open=True)
   rows=[dict(event='webview.create',time=1)]
   for trusted,pointer in [(False,None),(True,None),(True,dict(pointerdown=dict(trusted=False,pointerType='mouse'),pointerup=dict(trusted=True,pointerType='mouse'))),(True,dict(pointerdown=dict(trusted=True,pointerType='touch'),pointerup=dict(trusted=True,pointerType='touch'))),(True,dict(pointerdown=dict(trusted=True,pointerType='mouse'),pointerup=dict(trusted=True,pointerType='mouse')))]:
    rows.append(dict(event='qa.v52-result',phase=json.dumps(dict(base,trusted=trusted,pointer=pointer))))
   source.write_text('\n'.join(map(json.dumps,rows)));subprocess.run([sys.executable,str(QA/'collect.py'),str(source),str(output)],check=True,capture_output=True)
   result=json.loads(output.read_text());self.assertEqual([s['validPhysicalMouse'] for s in result['runs'][0]['samples']],[False,False,False,False,True]);self.assertEqual(result['physicalMouse'],1)
 def test_process_export_resolves_references_and_excludes_other_processes(self):
  with tempfile.TemporaryDirectory() as tmp:
   source=Path(tmp)/'trace.xml';output=Path(tmp)/'qa.json.gz'
   source.write_text('''<table><row><sample-time id="t">1200000000</sample-time><thread id="th" fmt="QA main"/><process id="p"><pid id="pid">202</pid></process><core id="c" fmt="P core"/><weight id="w">1000000</weight><tagged-backtrace id="st"><frame id="f" name="layout"><binary id="b" name="WebCore"/></frame><frame name="unknown"/></tagged-backtrace></row><row><sample-time ref="t"/><thread ref="th"/><process ref="p"/><core ref="c"/><weight ref="w"/><tagged-backtrace ref="st"/></row><row><sample-time ref="t"/><thread ref="th"/><process><pid>999</pid></process><core ref="c"/><weight ref="w"/><tagged-backtrace><frame name="unrelated-secret"/></tagged-backtrace></row><row><sample-time>5000000000</sample-time><thread ref="th"/><process ref="p"/><core ref="c"/><weight ref="w"/></row></table>''')
   subprocess.run([sys.executable,str(QA/'extract_process_trace.py'),str(source),str(output),'--pids','202','--start','1','--end','2'],check=True,capture_output=True)
   with gzip.open(output,'rt') as f:result=json.load(f)
   self.assertEqual(len(result['samples']),2);self.assertTrue(all(r['pid']==202 for r in result['samples']));self.assertEqual(result['samples'][1]['modules'],['WebCore','']);self.assertNotIn('unrelated-secret',json.dumps(result))
if __name__=='__main__':unittest.main()

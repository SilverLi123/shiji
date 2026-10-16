/* QA only: bounded buffered measurements, published after interaction/sampling. */
(()=>{
 const data={version:1,firstInteractiveMs:null,renders:[],queries:[],samples:[],resources:[]};let inputAt=null,active=null;
 const percentile=(xs,p)=>xs.length?[...xs].sort((a,b)=>a-b)[Math.min(xs.length-1,Math.floor(xs.length*p))]:null;
 function publish(){
  let node=document.getElementById('qa-v62-results');if(!node){node=document.createElement('script');node.id='qa-v62-results';node.type='application/json';document.body.append(node);}node.textContent=JSON.stringify(data);
  const payload={event:'v62',phase:JSON.stringify(data)};
  if(window.webkit?.messageHandlers?.libraryDiagnostics)window.webkit.messageHandlers.libraryDiagnostics.postMessage(payload);
  else fetch('/api/qa-v62',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}).catch(()=>{});
 }
 document.addEventListener('shiji:rendered',e=>{
  const cards=document.querySelectorAll('#resource-grid .resource-card').length;
  if(data.firstInteractiveMs===null)data.firstInteractiveMs=performance.now();
  data.renders.push({at:performance.now(),ms:e.detail.ms,total:e.detail.total,cards});if(data.renders.length>80)data.renders.shift();
  if(inputAt!==null){data.queries.push({ms:performance.now()-inputAt,cards});inputAt=null;}publish();
 });
 document.addEventListener('input',e=>{if(e.target.id==='search')inputAt=performance.now();});
 try{new PerformanceObserver(list=>{for(const e of list.getEntries())if(e.name.includes('/api/')&&!e.name.includes('qa-v62'))data.resources.push({path:new URL(e.name).pathname,ms:e.duration,bytes:e.encodedBodySize});data.resources=data.resources.slice(-100);}).observe({type:'resource',buffered:true});}catch{}
 function sample(){
  if(active)return;const record={mode:document.documentElement.dataset.shijiMotion,space:document.documentElement.dataset.shijiSpace,hidden:document.hidden,frames:[],scrolls:0,started:performance.now()};active=record;
  const button=document.getElementById('qa-v62-sample');if(button)button.textContent='QA · 采样中';let last=null;
  const onscroll=()=>record.scrolls++;window.addEventListener('scroll',onscroll,{passive:true});
  function frame(now){if(last!==null)record.frames.push(now-last);last=now;if(now-record.started<30000&&!document.hidden)requestAnimationFrame(frame);else{
   window.removeEventListener('scroll',onscroll);record.ended=now;record.hiddenEnd=document.hidden;record.p50=percentile(record.frames,.5);record.p95=percentile(record.frames,.95);record.max=Math.max(0,...record.frames);record.over33=record.frames.filter(x=>x>33.4).length;record.running=document.getAnimations().filter(a=>a.playState==='running').length;data.samples.push(record);data.samples=data.samples.slice(-6);active=null;if(button)button.textContent='QA · 采样30秒';publish();
  }}requestAnimationFrame(frame);
 }
 document.addEventListener('DOMContentLoaded',()=>{const button=document.createElement('button');button.id='qa-v62-sample';button.type='button';button.textContent='QA · 采样30秒';button.style.cssText='position:fixed;bottom:10px;right:10px;z-index:2000;font:11px monospace;background:#1a1a1a;color:#c5ff63;border:1px solid #666;padding:7px;border-radius:6px';button.addEventListener('click',sample);document.body.append(button);});
})();

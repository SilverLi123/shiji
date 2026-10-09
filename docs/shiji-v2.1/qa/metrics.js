/* QA-only injection; not linked or bundled as an app entry point. */
(()=>{
 const bins=new Map(),events=[],longTasks=[];let last=0,phase='idle',phaseUntil=0,scrollUntil=0,hiddenFrames=0;
 const output=document.createElement('script');output.type='application/json';output.id='qa-motion-metrics';document.body.append(output);
 let longTaskSupported=false;
 try{if(PerformanceObserver.supportedEntryTypes.includes('longtask')){new PerformanceObserver(list=>{for(const e of list.getEntries())longTasks.push({start:e.startTime,duration:e.duration});}).observe({type:'longtask',buffered:true});longTaskSupported=true;}}catch{}
 function summary(){
  const samples={};for(const [name,values] of bins){const sorted=[...values].sort((a,b)=>a-b),n=sorted.length;samples[name]={count:n,p50:sorted[Math.floor(n*.5)],p95:sorted[Math.floor(n*.95)],max:sorted[n-1],over25ms:values.filter(v=>v>25).length};}
  const loops=document.getAnimations().filter(a=>a.effect?.getTiming().iterations===Infinity).map(a=>({target:a.effect?.target?.className||a.effect?.target?.id,state:a.playState}));
  output.textContent=JSON.stringify({userAgent:navigator.userAgent,viewport:{width:innerWidth,height:innerHeight},resources:document.querySelector('#resource-total')?.textContent,cards:document.querySelectorAll('#resource-grid .resource-card').length,hidden:document.hidden,hiddenFrames,longTaskSupported,longTasks,events,samples,loops});
 }
 function tick(t){if(last){const name=performance.now()<scrollUntil?'scroll':performance.now()<phaseUntil?phase:'idle',values=bins.get(name)||[];if(values.length<6000)values.push(t-last);bins.set(name,values);}last=t;if(document.hidden)hiddenFrames++;requestAnimationFrame(tick);}
 document.addEventListener('click',e=>{const el=e.target.closest('button');if(!el)return;phase=el.dataset.action||el.id||'button';phaseUntil=performance.now()+1200;events.push({time:performance.now(),phase,label:el.getAttribute('aria-label')||el.textContent.slice(0,80)});summary();},true);
 document.addEventListener('scroll',()=>{scrollUntil=performance.now()+250;},{passive:true,capture:true});
 document.addEventListener('visibilitychange',()=>{events.push({time:performance.now(),visibility:document.visibilityState});last=0;setTimeout(summary,50);});
 requestAnimationFrame(tick);setInterval(summary,1000);summary();
})();

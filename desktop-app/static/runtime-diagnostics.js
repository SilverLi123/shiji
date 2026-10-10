/* Opt-in native QA probe. Bounded numbers only, no content or credentials. */
(()=>{
 'use strict';
 const start=performance.now(),bins=new Map();let phase='startup',until=start+8000,last=0,frame=0,published=false,actionAt=0;
 const records=[];
 function publish(row){records.push(row);if(records.length>240)records.shift();let output=document.getElementById('qa-runtime-metrics');if(!output&&document.body){output=document.createElement('script');output.type='application/json';output.id='qa-runtime-metrics';document.body.append(output);}if(output)output.textContent=JSON.stringify(records);}
 function report(event,extra={}){
  const hero=document.querySelector('#hero-title');
  const row={event,ms:performance.now()-start,cards:document.querySelectorAll('.resource-card').length,hidden:document.hidden,backgroundPaused:document.body?.classList.contains('v5-background')||false,mode:document.documentElement.dataset.shijiMotion||'',animations:document.getAnimations().length,running:document.getAnimations().filter(a=>a.playState==='running').length,cssRunning:document.getAnimations().filter(a=>a.constructor.name==='CSSAnimation'&&a.playState==='running').length,transitionRunning:document.getAnimations().filter(a=>a.constructor.name==='CSSTransition'&&a.playState==='running').length,ghosts:document.querySelectorAll('.shiji-detail-ghost,.shiji-leaving-ghost,.shiji-modal-exit').length,...(hero?{heroOpacity:getComputedStyle(hero).opacity,heroFilter:getComputedStyle(hero).filter}:{}),...extra};
  publish(row);window.webkit?.messageHandlers?.libraryDiagnostics?.postMessage(row);
 }
 function finish(){const values=(bins.get(phase)||[]).slice().sort((a,b)=>a-b);if(values.length)report('frames',{phase,frames:values.length,p50:values[Math.floor(values.length*.5)],p95:values[Math.floor(values.length*.95)],max:values.at(-1),over33:values.filter(v=>v>33.34).length});last=0;frame=0;}
 function tick(t){if(document.hidden||performance.now()>until){finish();return;}if(last){const values=bins.get(phase)||[];if(values.length<600)values.push(t-last);bins.set(phase,values);}last=t;frame=requestAnimationFrame(tick);}
 function begin(name){if(frame){cancelAnimationFrame(frame);finish();}phase=name;bins.set(phase,[]);until=performance.now()+3000;last=0;frame=requestAnimationFrame(tick);}
 document.addEventListener('shiji:rendered',e=>{report(published?'render':'interactive',{renderMs:e.detail.ms,total:e.detail.total,...(actionAt?{responseMs:performance.now()-actionAt}:{})});actionAt=0;published=true;queueMicrotask(()=>report('settled'));});
 document.addEventListener('input',e=>{if(e.target.id==='search'){actionAt=performance.now();begin('search');report('search-input');}},true);
 document.addEventListener('click',e=>{const el=e.target.closest('button');if(el){actionAt=performance.now();begin(el.dataset.action==='detail'?'detail':el.id==='motion-mode'?'mode':el.dataset.action==='category'?'category':'control');report('action');}},true);
 document.addEventListener('scroll',()=>{if(phase!=='scroll'||!frame)begin('scroll');until=performance.now()+1000;},{capture:true,passive:true});
 document.addEventListener('visibilitychange',()=>{report('visibility');if(document.hidden){if(frame)cancelAnimationFrame(frame);finish();}else begin('foreground');});
 window.addEventListener('pagehide',()=>{if(frame)cancelAnimationFrame(frame);finish();report('pagehide');});
 document.addEventListener('DOMContentLoaded',()=>{report('dom-ready');frame=requestAnimationFrame(tick);},{once:true});
})();

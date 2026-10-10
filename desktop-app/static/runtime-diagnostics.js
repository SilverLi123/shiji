/* Opt-in native QA probe. Bounded numbers only, no content or credentials. */
(()=>{
 'use strict';
 const start=performance.now(),bins=new Map();let phase='startup',until=start+8000,last=0,frame=0,published=false;
 function report(event,extra={}){
  const hero=document.querySelector('#hero-title');
  const row={event,ms:performance.now()-start,cards:document.querySelectorAll('.resource-card').length,hidden:document.hidden,mode:document.documentElement.dataset.shijiMotion||'',animations:document.getAnimations().length,running:document.getAnimations().filter(a=>a.playState==='running').length,ghosts:document.querySelectorAll('.shiji-detail-ghost,.shiji-leaving-ghost,.shiji-modal-exit').length,...(hero?{heroOpacity:getComputedStyle(hero).opacity,heroFilter:getComputedStyle(hero).filter}:{}),...extra};
  window.webkit?.messageHandlers?.libraryDiagnostics?.postMessage(row);
 }
 function finish(){const values=(bins.get(phase)||[]).slice().sort((a,b)=>a-b);if(values.length)report('frames',{phase,frames:values.length,p50:values[Math.floor(values.length*.5)],p95:values[Math.floor(values.length*.95)],max:values.at(-1),over33:values.filter(v=>v>33.34).length});last=0;frame=0;}
 function tick(t){if(document.hidden||performance.now()>until){finish();return;}if(last){const values=bins.get(phase)||[];if(values.length<600)values.push(t-last);bins.set(phase,values);}last=t;frame=requestAnimationFrame(tick);}
 function begin(name){if(frame){cancelAnimationFrame(frame);finish();}phase=name;bins.set(phase,[]);until=performance.now()+3000;last=0;frame=requestAnimationFrame(tick);}
 document.addEventListener('shiji:rendered',e=>{report(published?'render':'interactive',{renderMs:e.detail.ms,total:e.detail.total});published=true;});
 document.addEventListener('input',e=>{if(e.target.id==='search'){begin('search');report('search-input');}},true);
 document.addEventListener('click',e=>{const el=e.target.closest('button');if(el){begin(el.dataset.action==='detail'?'detail':el.id==='motion-mode'?'mode':el.dataset.action==='category'?'category':'control');report('action');}},true);
 document.addEventListener('scroll',()=>{if(phase!=='scroll'||!frame)begin('scroll');until=performance.now()+1000;},{capture:true,passive:true});
 document.addEventListener('visibilitychange',()=>{report('visibility');if(document.hidden){if(frame)cancelAnimationFrame(frame);finish();}else begin('foreground');});
 window.addEventListener('pagehide',()=>{if(frame)cancelAnimationFrame(frame);finish();report('pagehide');});
 document.addEventListener('DOMContentLoaded',()=>{report('dom-ready');frame=requestAnimationFrame(tick);},{once:true});
})();

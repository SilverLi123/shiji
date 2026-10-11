/* Opt-in QA only: buffer until after the measured animation. No DOM writes per frame. */
(()=>{
 'use strict';
 const rawNow=()=>performance.now();let current=null,sequence=0,pointer=null;
 const originalRect=Element.prototype.getBoundingClientRect;
 function part(name,prototype,key){const original=prototype[key];prototype[key]=function(...args){if(!current)return original.apply(this,args);const start=rawNow();try{return original.apply(this,args);}finally{const p=current.parts[name]||(current.parts[name]={ms:0,count:0});p.ms+=rawNow()-start;p.count++;}};}
 part('rect',Element.prototype,'getBoundingClientRect');part('clone',Node.prototype,'cloneNode');part('animate',Element.prototype,'animate');
 const descriptor=Object.getOwnPropertyDescriptor(Element.prototype,'innerHTML');Object.defineProperty(Element.prototype,'innerHTML',{...descriptor,set(value){if(!current)return descriptor.set.call(this,value);const start=rawNow();try{return descriptor.set.call(this,value);}finally{const p=current.parts.html||(current.parts.html={ms:0,count:0});p.ms+=rawNow()-start;p.count++;}}});
 function send(row){window.webkit?.messageHandlers?.libraryDiagnostics?.postMessage({event:'v52-result',phase:JSON.stringify(row)});fetch('/api/qa-v52-result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(row)}).catch(()=>{});}
 window.ShijiQATrace={begin(){current={start:rawNow(),parts:{}};performance.mark('v52-detail-handler-start');},end(){if(!current)return;current.handlerMs=rawNow()-current.start;performance.mark('v52-detail-handler-end');performance.measure('v52-detail-handler','v52-detail-handler-start','v52-detail-handler-end');window.__qaLastDetail=current;current=null;}};
 for(const type of ['pointerdown','pointerup'])document.addEventListener(type,e=>{if(e.target.closest?.('[data-action="detail"]'))pointer={...(pointer||{}),[type]:{ms:rawNow(),trusted:e.isTrusted,pointerType:e.pointerType}};},true);
 document.addEventListener('click',e=>{if(!e.target.closest?.('[data-action="detail"]'))return;const row={sequence:++sequence,clickMs:rawNow(),wallTime:Date.now(),trusted:e.isTrusted,pointer,frames:[],parts:{},hidden:document.hidden,mode:document.documentElement.dataset.shijiMotion,space:document.documentElement.dataset.shijiSpace,viewport:[innerWidth,innerHeight]};pointer=null;performance.mark('v52-click-'+sequence);let last=row.clickMs;const tick=t=>{row.frames.push({ms:rawNow(),raf:t,gap:rawNow()-last});last=rawNow();if(rawNow()-row.clickMs<1100)requestAnimationFrame(tick);};requestAnimationFrame(tick);setTimeout(()=>{const detail=window.__qaLastDetail;row.handlerMs=detail?.handlerMs;row.parts=detail?.parts;row.open=!document.getElementById('drawer').hidden;row.ghosts=document.querySelectorAll('.shiji-detail-ghost').length;row.animations=document.getAnimations().length;row.images=[...document.querySelectorAll('#detail-content img')].map(i=>({complete:i.complete,width:i.naturalWidth}));send(row);},1500);},true);
 window.ShijiQAReady=()=>Promise.all([document.fonts.ready,new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))]).then(()=>{document.getElementById('resource-grid').scrollIntoView({block:'start'});});
 window.ShijiQARun=async()=>{
  await document.fonts.ready;
  if(document.getElementById('drawer').hidden===false)document.querySelector('[data-action=close]').click();
  const source=document.querySelector('#resource-grid [data-action=detail]');
  source.scrollIntoView({block:'center',behavior:'instant'});
  await new Promise(resolve=>{let n=0;const step=()=>{if(++n<90)requestAnimationFrame(step);else resolve();};requestAnimationFrame(step);});
  if(document.hidden)return send({error:'hidden-before-run'});
  source.click();
};
})();

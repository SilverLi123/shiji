/* Opt-in QA only: buffer until after the measured animation. No DOM writes per frame. */
(()=>{
 'use strict';
 const rawNow=()=>performance.now();let current=null,currentClick=null,inputTask=null,sequence=0,pointer=null;
 const originalRect=Element.prototype.getBoundingClientRect;
 function part(name,prototype,key){const original=prototype[key];prototype[key]=function(...args){if(!current)return original.apply(this,args);const start=rawNow();try{return original.apply(this,args);}finally{const p=current.parts[name]||(current.parts[name]={ms:0,count:0});p.ms+=rawNow()-start;p.count++;}};}
 part('rect',Element.prototype,'getBoundingClientRect');part('clone',Node.prototype,'cloneNode');part('animate',Element.prototype,'animate');const qaAnimate=Element.prototype.animate;Element.prototype.animate=function(...args){if(window.ShijiQAGeometry&&current&&this.classList.contains('shiji-detail-ghost')){const source=document.querySelector('#resource-grid .art-copy');const ghost=this.querySelector('.art-copy');current.geometry={sourceFont:source&&getComputedStyle(source).fontSize,ghostFont:ghost&&getComputedStyle(ghost).fontSize,ghostContainer:getComputedStyle(this).containerType,sourceWidth:source?.closest('.card-preview')?.getBoundingClientRect().width,ghostWidth:this.getBoundingClientRect().width};}return qaAnimate.apply(this,args);};

 const descriptor=Object.getOwnPropertyDescriptor(Element.prototype,'innerHTML');Object.defineProperty(Element.prototype,'innerHTML',{...descriptor,set(value){if(!current)return descriptor.set.call(this,value);const start=rawNow();try{return descriptor.set.call(this,value);}finally{const p=current.parts.html||(current.parts.html={ms:0,count:0});p.ms+=rawNow()-start;p.count++;}}});
 function send(row){window.webkit?.messageHandlers?.libraryDiagnostics?.postMessage({event:'v52-result',phase:JSON.stringify(row)});fetch('/api/qa-v52-result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(row)}).catch(()=>{});}
 window.ShijiQATrace={begin(){current={start:rawNow(),parts:{},click:currentClick};performance.mark('v52-detail-handler-start');},end(){if(!current)return;current.handlerMs=rawNow()-current.start;performance.mark('v52-detail-handler-end');performance.measure('v52-detail-handler','v52-detail-handler-start','v52-detail-handler-end');if(current.click){current.click.handlerMs=current.handlerMs;current.click.parts=current.parts;current.click.geometry=current.geometry;}currentClick=null;current=null;}};
 for(const type of ['pointerdown','pointerup'])document.addEventListener(type,e=>{if(e.target.closest?.('[data-action="detail"]'))pointer={...(pointer||{}),[type]:{ms:rawNow(),trusted:e.isTrusted,pointerType:e.pointerType}};},true);
 document.addEventListener('click',e=>{if(!e.target.closest?.('[data-action="detail"]'))return;const row={sequence:++sequence,clickMs:rawNow(),wallTime:Date.now(),trusted:e.isTrusted,inputTask,pointer,frames:[],parts:{},hidden:document.hidden,focus:document.hasFocus(),resourceId:e.target.closest('[data-action="detail"]')?.dataset.id,mode:document.documentElement.dataset.shijiMotion,space:document.documentElement.dataset.shijiSpace,viewport:[innerWidth,innerHeight]};pointer=null;currentClick=row;performance.mark('v52-click-'+sequence);let last=row.clickMs;const tick=t=>{row.frames.push({ms:rawNow(),raf:t,gap:rawNow()-last});last=rawNow();if(rawNow()-row.clickMs<1100)requestAnimationFrame(tick);};requestAnimationFrame(tick);setTimeout(()=>{row.open=!document.getElementById('drawer').hidden;row.ghosts=document.querySelectorAll('.shiji-detail-ghost').length;row.animations=document.getAnimations().length;row.images=[...document.querySelectorAll('#detail-content img')].map(i=>({complete:i.complete,width:i.naturalWidth}));send(row);},1500);},true);
 window.ShijiQAReady=()=>Promise.all([document.fonts.ready,new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))]).then(()=>{document.getElementById('resource-grid').scrollIntoView({block:'start'});});
 window.ShijiQARun=async({task='event-task'}={})=>{
  await document.fonts.ready;
  if(document.getElementById('drawer').hidden===false)document.querySelector('[data-action=close]').click();
  const selector='#resource-grid [data-action=detail]';
  if(!document.querySelector(selector))await new Promise(resolve=>{const observer=new MutationObserver(()=>{if(document.querySelector(selector)){observer.disconnect();resolve();}});observer.observe(document.getElementById('resource-grid'),{childList:true,subtree:true});});
  const source=document.querySelector(selector);
  source.scrollIntoView({block:'center',behavior:'instant'});
  await new Promise(resolve=>{let n=0;const step=()=>{if(++n<90)requestAnimationFrame(step);else resolve();};requestAnimationFrame(step);});
  if(document.hidden)return send({error:'hidden-before-run'});
  const click=()=>{if(document.hidden||!source.isConnected)return send({error:'not-ready-before-click'});inputTask=task;source.click();inputTask=null;};
  // A zero-delay event task separates the automated input from prepaint RAF work.
  if(task==='raf')click();else setTimeout(click,0);
};
})();
// Explicit browser test entry; visible QA control only in a disposable server.
document.addEventListener('DOMContentLoaded',()=>{
 if(window.ShijiNative && window.webkit?.messageHandlers?.libraryDiagnostics)return;
 const button=document.createElement('button');button.id='qa-browser-run';button.textContent='QA · buffered detail run';Object.assign(button.style,{position:'fixed',bottom:'8px',left:'8px',zIndex:'100'});button.addEventListener('click',()=>window.ShijiQARun());document.body.append(button);
});
// Separate input diagnostic group; not enabled in quiet frame-time samples.
if(location.search.includes('input-trace')){
 const input=[];
 for(const type of ['pointerdown','pointermove','pointerup','click','gotpointercapture','lostpointercapture'])document.addEventListener(type,e=>{
  const card=e.target.closest?.('#resource-grid .resource-card');if(!card)return;
  const row={type,ms:performance.now(),trusted:e.isTrusted,x:e.clientX,y:e.clientY,target:e.target.className,card:card.className,id:card.dataset.resourceId};input.push(row);queueMicrotask(()=>row.prevented=e.defaultPrevented);
  if(type==='pointerup')setTimeout(()=>fetch('/api/qa-v52-result',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event:'input-trace',events:input.splice(0),open:!document.getElementById('drawer').hidden})}),2000);
 },true);
}

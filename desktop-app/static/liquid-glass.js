(function(root){
 'use strict';
 function bind(doc,win){
  const nav=doc.getElementById('browse-categories');if(!nav)return {destroy(){}};
  const reduced=win.matchMedia('(prefers-reduced-motion: reduce)');let indicator=null,previous=null,animation=null,frame=0,dead=false;
  function update(){
   frame=0;if(dead)return;
   const active=nav.querySelector('.browse-category.active');if(!active){indicator?.remove();indicator=null;previous=null;delete nav.dataset.glassReady;return;}
   if(!indicator||!indicator.isConnected){indicator=doc.createElement('span');indicator.className='glass-indicator';indicator.setAttribute('aria-hidden','true');nav.prepend(indicator);}
   const rect={x:active.offsetLeft,y:active.offsetTop,w:active.offsetWidth,h:active.offsetHeight};
   if(rect.w===0)return;
   const changed=previous&&Object.keys(rect).some(key=>rect[key]!==previous[key]);
   animation?.cancel();animation=null;
   Object.assign(indicator.style,{width:rect.w+'px',height:rect.h+'px',transform:`translate(${rect.x}px,${rect.y}px)`});nav.dataset.glassReady='true';
   if(changed&&!reduced.matches&&indicator.animate){animation=indicator.animate([{transform:`translate(${previous.x}px,${previous.y}px) scale(${previous.w/rect.w},${previous.h/rect.h})`},{transform:`translate(${rect.x}px,${rect.y}px) scale(1,1)`}],{duration:320,easing:'cubic-bezier(.16,1,.3,1)'});indicator.style.transformOrigin='top left';}
   previous=rect;
  }
  function schedule(){if(!frame&&!dead)frame=win.requestAnimationFrame(update);}
  const observer=new win.MutationObserver(schedule);observer.observe(nav,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
  const resize=new win.ResizeObserver(schedule);resize.observe(nav);
  function preference(){animation?.cancel();animation=null;schedule();}
  reduced.addEventListener('change',preference);schedule();
  return {destroy(){dead=true;observer.disconnect();resize.disconnect();win.cancelAnimationFrame(frame);animation?.cancel();indicator?.remove();delete nav.dataset.glassReady;reduced.removeEventListener('change',preference);}};
 }
 const api={bind};if(typeof module==='object')module.exports=api;else{root.ShijiGlass=api;const ui=bind(document,root);root.addEventListener('pagehide',()=>ui.destroy(),{once:true});}
})(typeof window==='object'?window:globalThis);

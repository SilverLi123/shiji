/* Motion orchestration only. Bits exclusively owns resource-card FLIP and tilt. */
(function(root){
 'use strict';
 function init({document:doc,window:win}){
  const reduced=win.matchMedia('(prefers-reduced-motion: reduce)'),fine=win.matchMedia('(hover:hover) and (pointer:fine)'),html=doc.documentElement;
  const $=s=>doc.querySelector(s),modeButton=$('#motion-mode'),replay=$('#motion-replay'),skip=$('#motion-skip'),stage=$('.shiji-brand-stage');
  let mode='studio',dead=false,signature='',frame=0,pointer={x:0,y:0},ghost=null,flight=null,introTimer=0,stageRect=null,stageVisible=true,stamp=null,searchOrigin=null;
  const finite=new Set(),loops=new Set(),particles=new Set(),fxAnimations=new Set(),detailAnimations=new Set(),listeners=[];
  const modalAnimations=new Map(),modalRects=new WeakMap();let modalExit=null,searchAnimation=null;
  try{if(win.localStorage.getItem('shiji-v2-motion-mode')==='calm')mode='calm';}catch{}
  const enabled=()=>!dead&&mode==='studio'&&!reduced.matches;
  function listen(el,type,fn,options){if(!el)return;el.addEventListener(type,fn,options);listeners.push(()=>el.removeEventListener(type,fn,options));}
  function animate(el,frames,options,collection=finite){if(!enabled()||!el?.animate)return null;const a=el.animate(frames,options);collection.add(a);if(options.iterations!==Infinity)a.finished?.then(()=>collection.delete(a),()=>collection.delete(a));else a.finished?.catch(()=>{});return a;}
  function closeDetail(){for(const a of detailAnimations){a.cancel();finite.delete(a);}detailAnimations.clear();if(ghost){ghost.animation?.cancel();ghost.el.remove();ghost=null;}}
  function clearParticles(){flight?.animation?.cancel();flight?.el.remove();flight=null;for(const a of fxAnimations)a.cancel();fxAnimations.clear();for(const el of particles)el.remove();particles.clear();}
  function stopIntro(){win.clearTimeout(introTimer);introTimer=0;if(skip)skip.hidden=true;if($('#shiji-intro'))$('#shiji-intro').hidden=true;}
  function clearStamp(){stamp?.animation?.cancel();stamp?.el.remove();stamp=null;}
  function clearModalExit(){modalExit?.animation?.cancel();modalExit?.el.remove();modalExit=null;}
  function stopModal(el){for(const a of modalAnimations.get(el)||[])a.cancel();modalAnimations.delete(el);}
  function cancel(){clearStamp();clearModalExit();searchAnimation?.cancel();searchAnimation=null;for(const el of modalAnimations.keys())stopModal(el);for(const a of finite)a.cancel();finite.clear();closeDetail();clearParticles();stopIntro();win.cancelAnimationFrame(frame);frame=0;$('.shiji-parallax')?.style.removeProperty('transform');stage?.style.removeProperty('--mouse-x');stage?.style.removeProperty('--mouse-y');}
  function paused(){return !stageVisible||doc.hidden||!!doc.querySelector('#drawer:not([hidden]),dialog[open]')||stage?.closest('[hidden]');}
  function updateLoops(){for(const a of loops){if(enabled()&&!paused())a.play();else a.pause();}}
  function startLoops(){for(const a of loops)a.cancel();loops.clear();if(!enabled())return;
   animate($('.shiji-bookmark'),[{transform:'translateY(0) rotate(-25deg)'},{transform:'translateY(-14px) rotate(-17deg)'},{transform:'translateY(0) rotate(-25deg)'}],{duration:7600,iterations:Infinity,easing:'ease-in-out'},loops);
   animate($('.shiji-orbit'),[{transform:'rotate(0deg)'},{transform:'rotate(360deg)'}],{duration:18000,iterations:Infinity,easing:'linear'},loops);
   animate($('.shiji-stage-grid'),[{transform:'rotate(-14deg) translateX(0)'},{transform:'rotate(-14deg) translateX(32px)'}],{duration:18000,iterations:Infinity,easing:'linear'},loops);
   animate($('.shiji-cutout'),[{transform:'rotate(-28deg) scale(1)',borderRadius:'7% 52% 15% 44%'},{transform:'rotate(95deg) scale(.82)',borderRadius:'50% 11% 58% 17%'},{transform:'rotate(230deg) scale(1.1)',borderRadius:'18% 48% 12% 60%'}],{duration:6000,direction:'alternate',iterations:Infinity,easing:'cubic-bezier(.45,0,.4,1)'},loops);
   animate($('.shiji-tracer'),[{transform:'rotate(-30deg)'},{transform:'rotate(35deg) translateY(20px)'}],{duration:9000,direction:'alternate',iterations:Infinity,easing:'ease-in-out'},loops);
   animate($('.shiji-spark'),[{transform:'scale(.9) rotate(-12deg)'},{transform:'scale(1.3) rotate(20deg)'},{transform:'scale(.9) rotate(-12deg)'}],{duration:4000,iterations:Infinity,easing:'ease-in-out'},loops);
   animate(modeButton,[{opacity:1},{opacity:.75},{opacity:1}],{duration:1500,iterations:Infinity,easing:'ease-in-out'},loops);
   animate($('#shiji-ticker span'),[{transform:'translateX(0)'},{transform:'translateX(-50%)'}],{duration:22000,iterations:Infinity,easing:'linear'},loops);updateLoops();
  }
  function apply(){html.dataset.shijiMotion=enabled()?'studio':'calm';if(modeButton){modeButton.textContent=reduced.matches?'CALM · 系统减少动态':mode==='studio'?'MOTION STUDIO':'CALM';modeButton.setAttribute('aria-pressed',String(enabled()));modeButton.setAttribute('aria-label','动效模式：'+(enabled()?'Motion Studio，切换为 Calm':'Calm，切换为 Motion Studio'));}if(replay)replay.disabled=!enabled();cancel();startLoops();win.dispatchEvent(new win.Event('shiji:motion'));}
  function setMode(next){mode=next==='calm'?'calm':'studio';try{win.localStorage.setItem('shiji-v2-motion-mode',mode);}catch{}apply();}
  function replayIntro(){cancel();if(!enabled())return;if(skip)skip.hidden=false;
   const intro=$('#shiji-intro');if(intro){intro.hidden=false;animate(intro,[{clipPath:'inset(0 0 100% 0)',offset:0},{clipPath:'inset(0 0 0 0)',offset:.21},{clipPath:'inset(0 0 0 0)',offset:.65},{clipPath:'inset(0 0 100% 0)',offset:1}],{duration:1370,easing:'cubic-bezier(.65,0,.25,1)'});animate(intro.querySelector('strong'),[{transform:'translateY(-60px) rotate(-6deg) scale(.3)',opacity:.1},{transform:'translateY(0) rotate(-6deg) scale(1)',opacity:1}],{duration:800,easing:'cubic-bezier(.22,1,.36,1)'});}
   animate($('#shiji-hero h2'),[{transform:'translateY(30px) skewY(3deg)',opacity:.12,filter:'blur(9px)'},{transform:'translateY(0) skewY(0)',opacity:1,filter:'blur(0px)'}],{duration:840,delay:650,easing:'cubic-bezier(.22,1,.36,1)',fill:'backwards'});
   animate(stage,[{clipPath:'inset(4% 0 4% 0 round 30px)',opacity:.7},{clipPath:'inset(0 0 0 0 round 16px)',opacity:1}],{duration:1300,easing:'cubic-bezier(.22,1,.36,1)'});introTimer=win.setTimeout(stopIntro,1400);
  }
  function beforeListUpdate(){closeDetail();}
  function stagger(container,selector,collection=finite){if(!enabled()||!container)return;[...container.querySelectorAll(selector)].slice(0,8).forEach((el,i)=>animate(el,[{opacity:.55,transform:'translateY(12px)',filter:'blur(3px)'},{opacity:1,transform:'translateY(0)',filter:'blur(0px)'}],{duration:420,delay:Math.min(i*30,140),easing:'cubic-bezier(.16,1,.22,1)',fill:'backwards'},collection));}
  function copyPresentation(source,el){
   for(const child of source.children){if(child.hidden)continue;el.append(child.cloneNode(true));}
   for(const node of [el,...el.querySelectorAll('*')]){node.removeAttribute('id');node.removeAttribute('data-action');node.removeAttribute('autofocus');node.removeAttribute('aria-labelledby');node.removeAttribute('aria-describedby');if(node.matches('button,a,input,select,textarea,[tabindex]'))node.setAttribute('tabindex','-1');}
   el.inert=true;el.setAttribute('aria-hidden','true');
  }
  function rememberModal(el){const r=el.getBoundingClientRect();if(r.width&&r.height)modalRects.set(el,r);}
  function modalClosed(el){
   stopModal(el);clearModalExit();if(!enabled()||doc.hidden||doc.querySelector('dialog[open]'))return;const r=modalRects.get(el);if(!r)return;
   const proxy=doc.createElement('div');proxy.className='shiji-dialog-exit';copyPresentation(el,proxy);Object.assign(proxy.style,{left:r.left+'px',top:r.top+'px',width:r.width+'px',height:r.height+'px'});doc.body.append(proxy);
   const a=animate(proxy,[{transform:'translateY(0) scale(1)',opacity:.9},{transform:'translateY(12px) scale(.98)',opacity:0}],{duration:160,easing:'cubic-bezier(.4,0,1,1)'});modalExit={el:proxy,animation:a};a?.finished?.then(()=>{proxy.remove();if(modalExit?.el===proxy)modalExit=null;},()=>proxy.remove());
  }
  function burstAt(r,kind='filter'){if(!enabled()||!r?.width)return;clearParticles();const count=kind==='save'?15:6,x=r.left+r.width/2,y=r.top+Math.min(r.height/2,32),colors=['#d7ff65','#a58cff','#79dfff','#ff9d87'];
   const ring=doc.createElement('span');ring.className='shiji-fx-ring';ring.setAttribute('aria-hidden','true');Object.assign(ring.style,{left:x+'px',top:y+'px'});doc.body.append(ring);particles.add(ring);const ra=animate(ring,[{transform:'translate(-50%,-50%) scale(.2)',opacity:.95},{transform:'translate(-50%,-50%) scale(5.2)',opacity:0}],{duration:650,easing:'cubic-bezier(.2,.9,.4,1)'},fxAnimations);ra?.finished?.then(()=>{ring.remove();particles.delete(ring);},()=>{ring.remove();particles.delete(ring);});
   for(let i=0;i<count;i++){const el=doc.createElement('span');el.className='shiji-capture-particle';el.setAttribute('aria-hidden','true');Object.assign(el.style,{left:x+'px',top:y+'px',background:colors[i%4],borderRadius:i%4===0?'50%':'1px'});doc.body.append(el);particles.add(el);const angle=i*Math.PI*2/count,radius=kind==='save'?80+(i*17)%50:28+(i*11)%26;const a=animate(el,[{transform:'translate(-50%,-50%) scale(.3) rotate(0deg)',opacity:1},{transform:`translate(${Math.cos(angle)*radius}px,${Math.sin(angle)*radius}px) scale(.8) rotate(${i*36}deg)`,opacity:0}],{duration:650+(i%3)*100,easing:'cubic-bezier(.18,1,.4,1)'},fxAnimations);a?.finished?.then(()=>{el.remove();particles.delete(el);},()=>{el.remove();particles.delete(el);});}
  }
  function favoriteConfirmed({sourceRect}={}){burstAt(sourceRect,'normal');}
  function afterListUpdate(next){if(signature&&signature!==next){
   animate($('#page-title'),[{transform:'translateY(8px)',opacity:.5},{transform:'translateY(0)',opacity:1}],{duration:360,easing:'cubic-bezier(.22,1,.36,1)'});
   clearStamp();if(enabled()){const el=doc.createElement('div');el.className='shiji-motion-stamp';el.setAttribute('aria-hidden','true');el.inert=true;el.textContent=$('#page-title')?.textContent||'';doc.body.append(el);const a=animate(el,[{transform:'translate(-50%,-35%) rotate(8deg) scale(1.45)',opacity:0,filter:'blur(11px)'},{transform:'translate(-50%,-50%) rotate(-4deg) scale(1)',opacity:.96,filter:'blur(0px)',offset:.16},{transform:'translate(-50%,-50%) rotate(-3deg) scale(1)',opacity:.92,filter:'blur(0px)',offset:.52},{transform:'translate(-50%,-60%) rotate(-10deg) scale(.78)',opacity:0,filter:'blur(10px)'}],{duration:910,easing:'cubic-bezier(.22,1,.36,1)'});stamp={el,animation:a};a?.finished?.then(()=>{el.remove();if(stamp?.el===el)stamp=null;},()=>el.remove());}
  }signature=next;updateLoops();}
  function openDetail({sourceElement,detailElement}){closeDetail();updateLoops();if(!enabled()||!sourceElement||!detailElement)return;
   stagger($('#drawer'),'.drawer-header h2,.detail-domain,.detail-actions,.detail-grid,.detail-block,.drawer-footer',detailAnimations);
   const from=sourceElement.getBoundingClientRect(),to=detailElement.getBoundingClientRect();if(!from.width||!to.width||from.bottom<0||from.top>win.innerHeight)return;
   const el=doc.createElement('div');el.className='shiji-detail-ghost';el.setAttribute('aria-hidden','true');el.inert=true;
   copyPresentation(sourceElement,el);
   Object.assign(el.style,{left:from.left+'px',top:from.top+'px',width:from.width+'px',height:from.height+'px'});doc.body.append(el);
   const end=`translate(${to.left-from.left}px,${to.top-from.top}px) scale(${to.width/from.width},${to.height/from.height})`;const a=animate(el,[{transform:'translate(0,0) scale(1)',opacity:1},{transform:end,opacity:1,offset:.8},{transform:end,opacity:0}],{duration:560,easing:'cubic-bezier(.2,.85,.25,1)'});ghost={el,animation:a};a?.finished?.then(()=>{el.remove();if(ghost?.el===el)ghost=null;},()=>el.remove());
  }
  function captureConfirmed({resourceId,sourceElement,sourceRect}={}){if(!enabled())return;clearParticles();let target=[...doc.querySelectorAll('.resource-card')].find(e=>e.dataset.resourceId===resourceId);const candidate=target?.getBoundingClientRect();if(!candidate||candidate.top<0||candidate.bottom>win.innerHeight)target=$('.brand-mark')||modeButton;const r=target?.getBoundingClientRect();if(!r)return;
   if(sourceRect&&sourceRect.width){const el=doc.createElement('span');el.className='shiji-capture-flight';el.setAttribute('aria-hidden','true');const x=Math.max(54,Math.min(win.innerWidth-64,sourceRect.left+sourceRect.width/2)),y=Math.max(80,Math.min(win.innerHeight-72,sourceRect.top+sourceRect.height/2));Object.assign(el.style,{left:x+'px',top:y+'px'});doc.body.append(el);const dx=r.left+r.width/2-x,dy=r.top+Math.min(r.height/2,32)-y;const a=animate(el,[{transform:'translate(-50%,-50%) rotate(-15deg)',opacity:1},{transform:`translate(calc(-50% + ${dx*.4}px),calc(-50% + ${dy*.2-65}px)) scale(1.35) rotate(13deg)`,opacity:1,offset:.42},{transform:`translate(calc(-50% + ${dx}px),calc(-50% + ${dy}px)) scale(.1) rotate(210deg)`,opacity:0}],{duration:900,easing:'cubic-bezier(.25,.84,.28,1)'});flight={el,animation:a};a?.finished?.then(()=>{el.remove();if(flight?.el===el){flight=null;burstAt(r,'save');}},()=>el.remove());}else burstAt(r,'save');
   animate(target,[{filter:'brightness(1)'},{filter:'brightness(1.35)'},{filter:'brightness(1)'}],{duration:600});
  }
  function move(e){if(!enabled()||!fine.matches||paused()||e.pointerType==='touch')return;if(!stageRect)return;pointer={x:((e.clientX-stageRect.left)/Math.max(1,stageRect.width)-.5)*14,y:((e.clientY-stageRect.top)/Math.max(1,stageRect.height)-.5)*14};if(frame)return;frame=win.requestAnimationFrame(()=>{frame=0;if(enabled()&&!paused()){$('.shiji-parallax').style.transform=`translate(${pointer.x}px,${pointer.y}px)`;stage.style.setProperty('--mouse-x',(50+pointer.x/14*100)+'%');stage.style.setProperty('--mouse-y',(50+pointer.y/14*100)+'%');}});}
  listen(stage,'pointerenter',()=>{stageRect=stage.getBoundingClientRect();});listen(win,'resize',()=>{stageRect=null;});listen(stage,'pointermove',move);listen(stage,'pointerleave',()=>{$('.shiji-parallax')?.style.removeProperty('transform');});
  listen(modeButton,'click',()=>setMode(mode==='studio'?'calm':'studio'));listen(replay,'click',replayIntro);listen(skip,'click',()=>{cancel();});listen(doc,'visibilitychange',()=>{if(doc.hidden)cancel();updateLoops();});listen(doc,'keydown',e=>{if(e.key==='Escape'&&introTimer)cancel();});listen(doc,'click',e=>{const el=e.target.closest?.('.browse-category,.primary');if(el&&!el.disabled)burstAt(el.getBoundingClientRect());});listen(reduced,'change',apply);
  function searchFocus(active){const el=$('.search-field');if(!el)return;const from=el.getBoundingClientRect();searchAnimation?.cancel();el.classList.toggle('shiji-search-focused',active);const to=el.getBoundingClientRect();if(from.width&&to.width)searchAnimation=animate(el,[{transform:`translateX(${from.left-to.left}px) scaleX(${from.width/to.width})`,transformOrigin:'left center'},{transform:'translateX(0) scaleX(1)',transformOrigin:'left center'}],{duration:220,easing:'cubic-bezier(.22,1,.36,1)'});}
  listen($('#search'),'focus',e=>{searchOrigin=e.relatedTarget;searchFocus(true);});
  listen($('#search'),'blur',()=>searchFocus(false));
  listen($('#search'),'keydown',e=>{if(e.key!=='Escape')return;e.preventDefault();$('#search').blur();if(searchOrigin?.isConnected&&!searchOrigin.closest('[hidden],dialog:not([open])'))searchOrigin.focus();else modeButton?.focus();searchOrigin=null;});
  listen(doc,'close',e=>{if(e.target.matches('dialog'))modalClosed(e.target);},true);
  listen(doc,'pointerdown',()=>{for(const el of doc.querySelectorAll('dialog[open]'))rememberModal(el);},true);
  listen(win,'resize',()=>{for(const el of doc.querySelectorAll('dialog[open]'))rememberModal(el);});
  const observer=new win.MutationObserver(records=>{for(const record of records){const el=record.target;if(record.attributeName==='open'&&el.matches('dialog[open]')){stopModal(el);clearModalExit();rememberModal(el);const owned=new Set();modalAnimations.set(el,owned);animate(el,[{transform:'translateY(16px) scale(.97)',opacity:.4},{transform:'translateY(0) scale(1)',opacity:1}],{duration:320,easing:'cubic-bezier(.22,1,.36,1)'},owned);stagger(el,'h2,p,label,.dialog-actions,.management-actions',owned);}}updateLoops();});observer.observe(doc.body,{subtree:true,attributes:true,attributeFilter:['hidden','open']});
  const visible=win.IntersectionObserver&&stage?new win.IntersectionObserver(entries=>{stageVisible=entries[0].isIntersecting;updateLoops();}):null;visible?.observe(stage);
  function destroy(){if(dead)return;dead=true;cancel();for(const a of loops)a.cancel();loops.clear();observer.disconnect();visible?.disconnect();for(const off of listeners)off();$('.search-field')?.classList.remove('shiji-search-focused');delete html.dataset.shijiMotion;}
  listen(win,'pagehide',destroy);apply();let first=true;try{first=!win.sessionStorage.getItem('shiji-v2-intro');win.sessionStorage.setItem('shiji-v2-intro','1');}catch{}if(first)replayIntro();
  return {beforeListUpdate,afterListUpdate,openDetail,closeDetail,captureConfirmed,favoriteConfirmed,setMode,replayIntro,destroy};
 }
 const api={init};if(typeof module==='object')module.exports=api;else root.ShijiMotion=api;
})(typeof window==='object'?window:globalThis);

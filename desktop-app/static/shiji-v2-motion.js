/* Motion orchestration only. Bits exclusively owns resource-card FLIP and tilt. */
(function(root){
 'use strict';
 function init({document:doc,window:win}){
  const reduced=win.matchMedia('(prefers-reduced-motion: reduce)'),fine=win.matchMedia('(hover:hover) and (pointer:fine)'),html=doc.documentElement;
  const $=s=>doc.querySelector(s),modeButton=$('#motion-mode'),replay=$('#motion-replay'),skip=$('#motion-skip'),stage=$('.shiji-brand-stage');
  let mode='studio',dead=false,signature='',frame=0,pointer={x:0,y:0},ghost=null,introTimer=0,stageRect=null,stageVisible=true;
  const finite=new Set(),loops=new Set(),particles=new Set(),listeners=[];
  try{if(win.localStorage.getItem('shiji-v2-motion-mode')==='calm')mode='calm';}catch{}
  const enabled=()=>!dead&&mode==='studio'&&!reduced.matches;
  function listen(el,type,fn,options){if(!el)return;el.addEventListener(type,fn,options);listeners.push(()=>el.removeEventListener(type,fn,options));}
  function animate(el,frames,options,collection=finite){if(!enabled()||!el?.animate)return null;const a=el.animate(frames,options);collection.add(a);if(options.iterations!==Infinity)a.finished?.then(()=>collection.delete(a),()=>collection.delete(a));return a;}
  function closeDetail(){if(ghost){ghost.animation?.cancel();ghost.el.remove();ghost=null;}}
  function clearParticles(){for(const el of particles)el.remove();particles.clear();}
  function stopIntro(){win.clearTimeout(introTimer);introTimer=0;if(skip)skip.hidden=true;}
  function cancel(){for(const a of finite)a.cancel();finite.clear();closeDetail();clearParticles();stopIntro();win.cancelAnimationFrame(frame);frame=0;$('.shiji-parallax')?.style.removeProperty('transform');}
  function paused(){return !stageVisible||doc.hidden||!!doc.querySelector('#drawer:not([hidden]),dialog[open]')||stage?.closest('[hidden]');}
  function updateLoops(){for(const a of loops){if(enabled()&&!paused())a.play();else a.pause();}}
  function startLoops(){for(const a of loops)a.cancel();loops.clear();if(!enabled())return;
   animate($('.shiji-bookmark'),[{transform:'translateY(0) rotate(-25deg)'},{transform:'translateY(-14px) rotate(-17deg)'},{transform:'translateY(0) rotate(-25deg)'}],{duration:7600,iterations:Infinity,easing:'ease-in-out'},loops);
   animate($('.shiji-orbit'),[{transform:'scale(1)'},{transform:'scale(.92)'},{transform:'scale(1)'}],{duration:6000,iterations:Infinity,easing:'ease-in-out'},loops);
   animate($('#shiji-ticker span'),[{transform:'translateX(0)'},{transform:'translateX(-50%)'}],{duration:22000,iterations:Infinity,easing:'linear'},loops);updateLoops();
  }
  function apply(){html.dataset.shijiMotion=enabled()?'studio':'calm';if(modeButton){modeButton.textContent=reduced.matches?'CALM · 系统减少动态':mode==='studio'?'MOTION STUDIO':'CALM';modeButton.setAttribute('aria-pressed',String(enabled()));modeButton.setAttribute('aria-label','动效模式：'+(enabled()?'Motion Studio，切换为 Calm':'Calm，切换为 Motion Studio'));}if(replay)replay.disabled=!enabled();cancel();startLoops();win.dispatchEvent(new win.Event('shiji:motion'));}
  function setMode(next){mode=next==='calm'?'calm':'studio';try{win.localStorage.setItem('shiji-v2-motion-mode',mode);}catch{}apply();}
  function replayIntro(){cancel();if(!enabled())return;if(skip)skip.hidden=false;
   animate($('#shiji-hero h2'),[{transform:'translateY(16px)',opacity:.65,clipPath:'inset(0 0 8% 0)'},{transform:'translateY(0)',opacity:1,clipPath:'inset(0 0 0 0)'}],{duration:1100,easing:'cubic-bezier(.22,1,.36,1)'});
   animate(stage,[{clipPath:'inset(4% 0 4% 0 round 30px)',opacity:.7},{clipPath:'inset(0 0 0 0 round 16px)',opacity:1}],{duration:1300,easing:'cubic-bezier(.22,1,.36,1)'});introTimer=win.setTimeout(stopIntro,1400);
  }
  function beforeListUpdate(){closeDetail();}
  function afterListUpdate(next){if(signature&&signature!==next)animate($('#page-title'),[{transform:'translateY(8px)',opacity:.5},{transform:'translateY(0)',opacity:1}],{duration:360,easing:'cubic-bezier(.22,1,.36,1)'});signature=next;updateLoops();}
  function openDetail({sourceElement,detailElement}){closeDetail();updateLoops();if(!enabled()||!sourceElement||!detailElement)return;
   const from=sourceElement.getBoundingClientRect(),to=detailElement.getBoundingClientRect();if(!from.width||!to.width||from.bottom<0||from.top>win.innerHeight)return;
   const el=doc.createElement('div');el.className='shiji-detail-ghost';el.setAttribute('aria-hidden','true');el.inert=true;
   const image=sourceElement.querySelector('img.cover-image:not([hidden]),img:not([hidden])');if(image){const copy=image.cloneNode();copy.removeAttribute('id');copy.alt='';el.append(copy);}else{el.textContent=sourceElement.textContent.slice(0,160);}
   Object.assign(el.style,{left:from.left+'px',top:from.top+'px',width:from.width+'px',height:from.height+'px'});doc.body.append(el);
   const a=animate(el,[{transform:'translate(0,0) scale(1)',opacity:1},{transform:`translate(${to.left-from.left}px,${to.top-from.top}px) scale(${to.width/from.width},${to.height/from.height})`,opacity:0}],{duration:560,easing:'cubic-bezier(.22,1,.36,1)'});ghost={el,animation:a};a?.finished?.then(()=>{el.remove();if(ghost?.el===el)ghost=null;},()=>el.remove());
  }
  function captureConfirmed({resourceId,sourceElement}={}){if(!enabled())return;clearParticles();const target=[...doc.querySelectorAll('.resource-card')].find(e=>e.dataset.resourceId===resourceId)||$('.brand-mark')||modeButton;const r=(sourceElement||target)?.getBoundingClientRect();if(!r)return;
   for(let i=0;i<8;i++){const el=doc.createElement('span');el.className='shiji-capture-particle';el.setAttribute('aria-hidden','true');Object.assign(el.style,{left:(r.left+r.width/2)+'px',top:(r.top+Math.min(r.height/2,32))+'px'});doc.body.append(el);particles.add(el);const angle=i*Math.PI/4;const a=animate(el,[{transform:'translate(0,0) scale(1)',opacity:1},{transform:`translate(${Math.cos(angle)*54}px,${Math.sin(angle)*54}px) scale(.2)`,opacity:0}],{duration:700,easing:'cubic-bezier(.22,1,.36,1)'});a?.finished?.then(()=>{el.remove();particles.delete(el);},()=>{el.remove();particles.delete(el);});}
   animate(target,[{filter:'brightness(1)'},{filter:'brightness(1.35)'},{filter:'brightness(1)'}],{duration:600});
  }
  function move(e){if(!enabled()||!fine.matches||paused()||e.pointerType==='touch')return;if(!stageRect)return;pointer={x:((e.clientX-stageRect.left)/Math.max(1,stageRect.width)-.5)*14,y:((e.clientY-stageRect.top)/Math.max(1,stageRect.height)-.5)*14};if(frame)return;frame=win.requestAnimationFrame(()=>{frame=0;if(enabled()&&!paused())$('.shiji-parallax').style.transform=`translate(${pointer.x}px,${pointer.y}px)`;});}
  listen(stage,'pointerenter',()=>{stageRect=stage.getBoundingClientRect();});listen(win,'resize',()=>{stageRect=null;});listen(stage,'pointermove',move);listen(stage,'pointerleave',()=>{$('.shiji-parallax')?.style.removeProperty('transform');});
  listen(modeButton,'click',()=>setMode(mode==='studio'?'calm':'studio'));listen(replay,'click',replayIntro);listen(skip,'click',()=>{cancel();});listen(doc,'visibilitychange',updateLoops);listen(reduced,'change',apply);
  listen($('#search'),'focus',()=>animate($('.search-field'),[{boxShadow:'inset 0 -2px #d7ff6500'},{boxShadow:'inset 0 -2px #d7ff65'}],{duration:220}));
  const observer=new win.MutationObserver(updateLoops);observer.observe(doc.body,{subtree:true,attributes:true,attributeFilter:['hidden','open']});
  const visible=win.IntersectionObserver&&stage?new win.IntersectionObserver(entries=>{stageVisible=entries[0].isIntersecting;updateLoops();}):null;visible?.observe(stage);
  function destroy(){if(dead)return;dead=true;cancel();for(const a of loops)a.cancel();loops.clear();observer.disconnect();visible?.disconnect();for(const off of listeners)off();delete html.dataset.shijiMotion;}
  listen(win,'pagehide',destroy);apply();let first=true;try{first=!win.sessionStorage.getItem('shiji-v2-intro');win.sessionStorage.setItem('shiji-v2-intro','1');}catch{}if(first)replayIntro();
  return {beforeListUpdate,afterListUpdate,openDetail,closeDetail,captureConfirmed,setMode,replayIntro,destroy};
 }
 const api={init};if(typeof module==='object')module.exports=api;else root.ShijiMotion=api;
})(typeof window==='object'?window:globalThis);

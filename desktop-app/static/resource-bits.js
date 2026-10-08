/* Adapted from React Bits Masonry, AnimatedContent, Magnet, Dock and TiltedCard by David Haz.
 * Upstream commit 4d6a46d3f401736695c495f1e72ed429e0ed1b93.
 * MIT + Commons Clause; see licenses/react-bits.md and THIRD-PARTY.md.
 * Integrated into this app; React/GSAP lifecycle is replaced with native DOM/WAAPI.
 */
(function(root){
  'use strict';
  function pack(heights,width,columns,gap=22){
    columns=Math.max(1,Math.floor(columns));
    const w=Math.max(0,(width-gap*(columns-1))/columns),ends=Array(columns).fill(0);
    const items=heights.map(h=>{const col=ends.indexOf(Math.min(...ends)),y=ends[col];ends[col]+=Math.max(0,h)+gap;return {x:col*(w+gap),y,w,h};});
    return {items,height:heights.length?Math.max(...ends)-gap:0};
  }
  function magnetPoint(x,y,rect,strength=9,padding=20){
    const dx=x-rect.left-rect.width/2,dy=y-rect.top-rect.height/2;
    if(Math.abs(dx)>rect.width/2+padding||Math.abs(dy)>rect.height/2+padding)return {x:0,y:0};
    return {x:Math.max(-8,Math.min(8,dx/strength)),y:Math.max(-8,Math.min(8,dy/strength))};
  }
  // TiltedCard's centered pointer mapping. The stable preview button owns input;
  // only its image rotates, so gallery positions and controls never move.
  function tiltPoint(x,y,rect,amplitude=3){
    if(!(rect.width>0&&rect.height>0)||!Number.isFinite(x)||!Number.isFinite(y))return {x:0,y:0};
    const bounded=v=>Math.max(-1,Math.min(1,v));
    return {x:-bounded((y-rect.top-rect.height/2)/(rect.height/2))*amplitude,
      y:bounded((x-rect.left-rect.width/2)/(rect.width/2))*amplitude};
  }
  function columns(viewport){return viewport<=480?1:viewport<=900?2:3;}
  function imageRatio(width,height){return width>0&&height>0&&Number.isFinite(width)&&Number.isFinite(height)?Math.max(.125,Math.min(16,width/height)):1.6;}
  function readPreviewMode(storage){try{return storage.getItem('shiji-preview-mode')==='fit'?'fit':'frame';}catch{return 'frame';}}
  function savePreviewMode(storage,mode){try{storage.setItem('shiji-preview-mode',mode==='fit'?'fit':'frame');}catch{}}
  function create(grid,button){
    const reduce=matchMedia('(prefers-reduced-motion: reduce)'),fine=matchMedia('(hover: hover) and (pointer: fine)');
    let previous=new Map(),lastWidth=0,frame=0,destroyed=false;
    const seen=new Set(),animations=new Set();
    let tilted=null;
    function resetTilt(){
      if(!tilted)return;
      tilted.classList.remove('bits-tilt-active');
      tilted.style.removeProperty('--tilt-x');tilted.style.removeProperty('--tilt-y');tilted=null;
    }
    function tiltMove(e){
      if(reduce.matches||!fine.matches||e.pointerType!=='mouse'||!grid.classList.contains('bits-masonry')||grid.classList.contains('preview-fit')||grid.hidden){resetTilt();return;}
      const preview=e.target.closest?.('.card-preview');
      const img=preview?.querySelector('.cover-image');
      if(!preview||!grid.contains(preview)||preview.matches(':focus-visible')||preview.disabled||!img?.complete||!img.naturalWidth){resetTilt();return;}
      if(tilted!==preview){resetTilt();tilted=preview;}
      const p=tiltPoint(e.clientX,e.clientY,preview.getBoundingClientRect());
      preview.style.setProperty('--tilt-x',p.x+'deg');preview.style.setProperty('--tilt-y',p.y+'deg');
      preview.classList.add('bits-tilt-active');
    }
    function tiltOut(e){if(tilted&&!tilted.contains(e.relatedTarget))resetTilt();}
    function animate(el,frames,options){
      if(reduce.matches||!el.animate)return;
      const a=el.animate(frames,options);animations.add(a);
      a.finished.then(()=>animations.delete(a),()=>animations.delete(a));return a;
    }
    function begin(){
      resetTilt();
      previous=new Map();
      for(const el of grid.querySelectorAll(':scope > .resource-card'))previous.set(el.dataset.resourceId,el.getBoundingClientRect());
      for(const a of animations)a.cancel();animations.clear();
    }
    function layout(enter=false){
      if(destroyed)return;
      if(grid.classList.contains('preview-fit'))for(const preview of grid.querySelectorAll('.card-preview')){
        const img=preview.querySelector('.cover-image');
        preview.style.setProperty('--image-ratio',imageRatio(img?.naturalWidth,img?.naturalHeight));
      }
      const eligible=!grid.hidden&&!grid.classList.contains('list-layout')&&!grid.classList.contains('board-layout');
      grid.classList.toggle('bits-masonry',eligible);
      if(!eligible){grid.style.height='';for(const el of grid.querySelectorAll(':scope > .resource-card')){el.style.width='';el.style.left='';el.style.top='';}return;}
      const width=grid.clientWidth,n=grid.dataset?.galleryColumns==='2'&&innerWidth>480?2:columns(innerWidth),gap=innerWidth<=760?18:22;
      if(!width)return;
      lastWidth=width;
      const cards=Array.from(grid.children),w=Math.max(0,(width-gap*(n-1))/n);
      cards.forEach(el=>el.style.width=w+'px');
      const positions=pack(cards.map(el=>el.offsetHeight),width,n,gap);
      grid.style.height=positions.height+'px';
      // Set every position before measuring again, so layout is resolved once.
      cards.forEach((el,i)=>{
        const p=positions.items[i];el.style.left=p.x+'px';el.style.top=p.y+'px';
      });
      const rects=cards.map(el=>el.getBoundingClientRect());
      cards.forEach((el,i)=>{
        const id=el.dataset.resourceId;
        const old=previous.get(id),now=rects[i];
        if(old&&(Math.abs(old.left-now.left)>1||Math.abs(old.top-now.top)>1)){
          animate(el,[{transform:`translate(${old.left-now.left}px,${old.top-now.top}px)`},{transform:'translate(0,0)'}],{duration:320,easing:'cubic-bezier(.16,1,.3,1)'});
        }else if(enter&&!seen.has(id)){
          animate(el,[{transform:'translateY(8px)',opacity:1},{transform:'translateY(0)',opacity:1}],{duration:360,delay:Math.min(i*30,120),easing:'cubic-bezier(.16,1,.3,1)'});
        }
        seen.add(id);
      });
      previous=new Map();
    }
    function schedule(){cancelAnimationFrame(frame);frame=requestAnimationFrame(()=>{begin();layout();});}
    function imageReady(e){if(grid.classList.contains('preview-fit')&&e.target.matches('.cover-image'))schedule();}
    const ro=typeof ResizeObserver==='function'?new ResizeObserver(entries=>{if(Math.abs(entries[0].contentRect.width-lastWidth)>1)schedule();}):null;
    ro?.observe(grid);
    function resetButton(){if(button)button.style.transform='';}
    function move(e){
      if(!button||reduce.matches||!fine.matches||e.pointerType==='touch'||button.matches(':focus-visible')||button.disabled){resetButton();return;}
      const p=magnetPoint(e.clientX,e.clientY,button.getBoundingClientRect());
      button.style.transform=`translate3d(${p.x}px,${p.y}px,0)`;
    }
    function preference(){resetTilt();for(const a of animations)a.cancel();animations.clear();resetButton();}
    root.addEventListener('resize',schedule);
    root.addEventListener('pointermove',move,{passive:true});
    root.addEventListener('blur',preference);
    root.addEventListener('scroll',resetTilt,true);
    grid.addEventListener('pointermove',tiltMove,{passive:true});grid.addEventListener('pointerout',tiltOut);grid.addEventListener('focusin',resetTilt);
    grid.addEventListener('load',imageReady,true);grid.addEventListener('error',imageReady,true);
    button?.addEventListener('focus',resetButton);
    reduce.addEventListener('change',preference);fine.addEventListener('change',preference);
    return {begin,render(){layout(true);},destroy(){destroyed=true;cancelAnimationFrame(frame);ro?.disconnect();preference();grid.removeEventListener('load',imageReady,true);grid.removeEventListener('error',imageReady,true);root.removeEventListener('resize',schedule);root.removeEventListener('pointermove',move);root.removeEventListener('blur',preference);root.removeEventListener('scroll',resetTilt,true);grid.removeEventListener('pointermove',tiltMove);grid.removeEventListener('pointerout',tiltOut);grid.removeEventListener('focusin',resetTilt);button?.removeEventListener('focus',resetButton);reduce.removeEventListener('change',preference);fine.removeEventListener('change',preference);}};
  }
  // Dock's distance-to-magnification mapping, adapted to stable native buttons.
  // Only the icon scales: labels and hit targets keep their positions.
  function dockScale(distance,radius=110){return 1+.28*Math.max(0,1-Math.abs(distance)/radius);}
  function createDock(nav){
    const reduce=matchMedia('(prefers-reduced-motion: reduce)'),fine=matchMedia('(hover: hover) and (pointer: fine)');
    function reset(){for(const el of nav.querySelectorAll('.category-art'))el.style.transform='';}
    function move(e){
      if(reduce.matches||!fine.matches||e.pointerType==='touch'||nav.querySelector(':focus-visible')){reset();return;}
      const items=Array.from(nav.querySelectorAll('.browse-category'));
      const centers=items.map(el=>{const rect=el.getBoundingClientRect();return rect.left+rect.width/2;});
      items.forEach((el,i)=>{const scale=dockScale(e.clientX-centers[i]);el.querySelector('.category-art').style.transform=`translateY(${-3*(scale-1)/.28}px) scale(${scale})`;});
    }
    nav.addEventListener('pointermove',move,{passive:true});nav.addEventListener('pointerleave',reset);nav.addEventListener('focusin',reset);
    root.addEventListener('blur',reset);reduce.addEventListener('change',reset);fine.addEventListener('change',reset);
    return {reset,destroy(){reset();nav.removeEventListener('pointermove',move);nav.removeEventListener('pointerleave',reset);nav.removeEventListener('focusin',reset);root.removeEventListener('blur',reset);reduce.removeEventListener('change',reset);fine.removeEventListener('change',reset);}};
  }
  const api={pack,magnetPoint,tiltPoint,columns,imageRatio,readPreviewMode,savePreviewMode,create,dockScale,createDock};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiBits=api;
})(typeof window==='object'?window:globalThis);

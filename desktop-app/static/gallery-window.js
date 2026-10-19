/* Geometry and DOM residency only. Resource/query state and Bits retain ownership. */
(function(root){
 'use strict';
 function lowerBound(rows,value,read){let lo=0,hi=rows.length;while(lo<hi){const mid=(lo+hi)>>>1;if(read(rows[mid])<value)lo=mid+1;else hi=mid;}return lo;}
 function createGeometry(pack){
  let entries=[],positions=[],byId=new Map(),ordered=[],bottoms=[];
  const api={height:0,
   rebuild(items,config,height){
    entries=items;const result=pack(items.map(height),config.width,config.columns,config.gap,items.map(r=>r.span),config.rowGap);
    positions=result.items;api.height=result.height;byId=new Map(items.map((r,i)=>[r.id,i]));
    ordered=positions.map((p,i)=>({...p,index:i})).sort((a,b)=>a.y-b.y||a.index-b.index);
    let end=-Infinity;bottoms=ordered.map(p=>end=Math.max(end,p.y+p.h));
   },
   position(id){return positions[byId.get(id)];},
   visible(top,bottom,overscan=0,pins=new Set()){
    const start=lowerBound(bottoms,top-overscan,v=>v),end=lowerBound(ordered,bottom+overscan+1e-6,p=>p.y),indices=new Set();
    for(let i=start;i<end;i++){const p=ordered[i];if(p.y+p.h>=top-overscan)indices.add(p.index);}
    for(const id of pins)if(byId.has(id))indices.add(byId.get(id));
    return [...indices].sort((a,b)=>a-b);
   },
   anchor(top,bottom){const i=api.visible(top,bottom).find(i=>positions[i].y+positions[i].h>top);return i===undefined?null:{id:entries[i].id,y:positions[i].y};},
   anchorDelta(anchor){const p=anchor&&api.position(anchor.id);return p?p.y-anchor.y:0;}
  };return api;
 }
 function create({grid,pack,reconcile,renderCard,span,cover,version=()=>'',onMount=()=>{},schedule}){
  const doc=grid.ownerDocument,win=doc.defaultView,geometry=createGeometry(pack);
  let rows=[],entries=[],key=null,context='',config=null,profileKey='',profiles=null,dirty=true,enabled=false,dead=false,frame=0,anchor=null,lastAnchor=null,windowKey='',entryIndex=new Map(),pendingRender=null;
  const htmlCache=new Map(),ratios=new Map(),measured=new Map(),pins=new Map();
  function viewport(){const rect=grid.getBoundingClientRect();return {top:-rect.top,bottom:win.innerHeight-rect.top,rect};}
  function capture(){if(enabled&&!anchor){const v=viewport();const a=geometry.anchor(v.top,v.bottom);anchor=a?{...a,screenY:v.rect.top+a.y}:null;}}
  function html(r){const stamp=version(r);let cached=htmlCache.get(r.id);if(!cached||cached.ref!==r||cached.context!==context||cached.stamp!==stamp){cached={ref:r,context,stamp,html:renderCard(r)};htmlCache.set(r.id,cached);}else{htmlCache.delete(r.id);htmlCache.set(r.id,cached);}while(htmlCache.size>240)htmlCache.delete(htmlCache.keys().next().value);return cached.html;}
  function ratio(r){const old=ratios.get(r.id);if(!old)return 1.6;return old.cover===cover(r)?old.ratio:1.6;}
  function sizeKey(entry){return [profileKey,entry.span,cover(entry.ref),entry.ref.coverConfig?.version===1?entry.ref.coverConfig.imageFit:''].join('|');}
  function height(entry){const saved=measured.get(entry.id);if(saved&&saved.key===sizeKey(entry))return saved.height;return config.fit?profiles.chrome+Math.max(profiles.min,Math.min(profiles.max,entry.width/ratio(entry.ref))):profiles[entry.span];}
  function measureProfiles(){
   // Same CSS boxes as the real pure-cover grid; no art/layers or fake resources.
   const nodes=[1,2].map(s=>{const el=doc.createElement('article');el.className='resource-card';el.dataset.galleryWide=String(s===2);el.style.cssText='position:absolute;visibility:hidden;pointer-events:none;left:0;top:0';el.style.width=((config.width-config.gap*(config.columns-1))/config.columns*s+config.gap*(s-1))+'px';const surface=doc.createElement('div');surface.className='card-motion-surface';const preview=doc.createElement('button');preview.className='card-preview';surface.append(preview);el.append(surface);grid.append(el);return el;});
   const style=win.getComputedStyle(nodes[0].querySelector('.card-preview'));
   const result={min:parseFloat(style.minHeight)||0,max:parseFloat(style.maxHeight)||Infinity,1:nodes[0].offsetHeight,2:nodes[1].offsetHeight,chrome:nodes[0].offsetHeight-nodes[0].querySelector('.card-preview').offsetHeight};nodes.forEach(el=>el.remove());return result;
  }
  function rebuild(){geometry.rebuild(entries,config,height);grid.style.height=geometry.height+'px';}
  function updateAnchor(){if(!anchor||doc.body.classList.contains('drawer-open'))return;const p=geometry.position(anchor.id),delta=p?grid.getBoundingClientRect().top+p.y-anchor.screenY:0;anchor=null;if(Math.abs(delta)>.5)win.scrollBy({top:delta,left:0,behavior:'instant'});}
  function activePins(){const result=new Set(pins.values()),focused=doc.activeElement?.closest?.('.resource-card');if(focused&&grid.contains(focused))result.add(focused.dataset.resourceId);return result;}
  function layout(next){
   if(dead)return null;
   enabled=Boolean(rows.length&&doc.documentElement.dataset.shijiVersion==='v5'&&grid.clientWidth>0&&!grid.classList.contains('list-layout')&&!grid.classList.contains('board-layout'));
   grid.classList.toggle('gallery-windowed',enabled);
   if(!enabled)return null;
   const nextKey=JSON.stringify([next.width,next.columns,next.gap,grid.classList.contains('density-compact'),grid.classList.contains('preview-fit'),win.innerWidth<=620]);
   if(nextKey!==profileKey){capture();if(lastAnchor)anchor=lastAnchor;profileKey=nextKey;config={...next,fit:grid.classList.contains('preview-fit')};profiles=measureProfiles();dirty=true;}
   if(!profiles[1]){enabled=false;grid.classList.remove('gallery-windowed');return null;} // no real layout (e.g. JSDOM)
   const repacked=dirty;
   if(dirty){const width=(config.width-config.gap*(config.columns-1))/config.columns;entries=rows.map(r=>{const s=config.feature&&span(r)===2?2:1;return {id:r.id,span:s,width:width*s+config.gap*(s-1),ref:r};});entryIndex=new Map(entries.map((e,i)=>[e.id,i]));rebuild();dirty=false;updateAnchor();}
   updateAnchor();
   let cards=[];
   // A decoded image can change height. One correction/reconcile pass preserves
   // the visible ID anchor; newly exposed neighbours are measured next frame.
   for(let pass=0;pass<2;pass++){
    const v=viewport(),indices=geometry.visible(v.top,v.bottom,Math.max(500,win.innerHeight*.8),activePins());
    const residency=indices.join(',');
    if(pass===0&&!repacked&&residency===windowKey){const a=geometry.anchor(v.top,v.bottom);lastAnchor=a?{...a,screenY:v.rect.top+a.y}:null;const cards=[...grid.children].filter(el=>el.matches('.resource-card'));return {unchanged:true,cards,height:geometry.height,items:cards.map(el=>geometry.position(el.dataset.resourceId))};}
    windowKey=residency;
    reconcile(grid,indices.map(i=>({id:entries[i].id,html:html(entries[i].ref)})));
    cards=[...grid.children].filter(el=>el.matches('.resource-card'));
    const lookup=entryIndex;
    for(const el of cards){const e=entries[lookup.get(el.dataset.resourceId)],p=geometry.position(e.id);el.style.width=p.w+'px';el.dataset.galleryWide=String(e.span===2);el.setAttribute('role','listitem');el.setAttribute('aria-posinset',String(lookup.get(e.id)+1));el.setAttribute('aria-setsize',String(rows.length));const preview=el.querySelector('.card-preview');if(config.fit&&preview){const img=preview.querySelector('.cover-image');if(img?.complete){ratios.set(e.id,{cover:cover(e.ref),ratio:root.ShijiBits.imageRatio(img.naturalWidth,img.naturalHeight)});}preview.style.setProperty('--image-ratio',ratio(e.ref));}el.style.left=p.x+'px';el.style.top=p.y+'px';}
    let changed=false;
    for(const el of cards){const e=entries[lookup.get(el.dataset.resourceId)],h=el.offsetHeight;if(h>0&&Math.abs(h-geometry.position(e.id).h)>.5){if(!changed)capture();measured.set(e.id,{key:sizeKey(e),height:h});changed=true;}}
    if(!changed)break;rebuild();updateAnchor();
   }
   onMount();grid.setAttribute('role','list');const v=viewport(),a=geometry.anchor(v.top,v.bottom);lastAnchor=a?{...a,screenY:v.rect.top+a.y}:null;
   return {cards,height:geometry.height,items:cards.map(el=>geometry.position(el.dataset.resourceId))};
  }
  function queue(){if(dead||frame||doc.hidden||!enabled)return;frame=win.requestAnimationFrame(()=>{frame=0;schedule();});}
  function imageReady(e){if(!enabled||!config?.fit||!e.target.matches('.cover-image'))return;const id=e.target.closest('.resource-card')?.dataset.resourceId,r=rows.find(r=>r.id===id);if(!r)return;const img=e.target,value=root.ShijiBits.imageRatio(img.naturalWidth,img.naturalHeight),old=ratios.get(id);if(old?.cover===cover(r)&&old.ratio===value)return;capture();ratios.set(id,{cover:cover(r),ratio:value});measured.delete(id);dirty=true;queue();}
  function visibility(){if(doc.hidden){win.cancelAnimationFrame(frame);frame=0;released();}else queue();}
  function pin(reason,id){if(id)pins.set(reason,id);else if(pins.delete(reason))queue();}
  function pressed(e){const card=e.target.closest('.resource-card');if(card)pin('pointer',card.dataset.resourceId);}
  function released(){if(!pins.has('pointer'))return;win.setTimeout(()=>{if(dead)return;pin('pointer');const render=pendingRender;pendingRender=null;if(render)render();else queue();},0);}
  function ensure(id){if(!enabled||!geometry.position(id))return false;pin('keyboard',id);schedule();win.setTimeout(()=>{if(pins.get('keyboard')===id)pin('keyboard');},0);const node=[...grid.children].find(el=>el.dataset.resourceId===id);node?.scrollIntoView({block:'nearest',behavior:'instant'});return node;}
  function keydown(e){
   if(!enabled||e.key!=='Tab'||e.altKey||e.ctrlKey||e.metaKey)return;
   const card=e.target.closest('.resource-card');if(!card)return;const controls=[...card.querySelectorAll('button,a[href],input')].filter(el=>!el.disabled&&el.getClientRects().length),boundary=e.shiftKey?controls[0]:controls.at(-1);
   if(e.target!==boundary)return;const index=rows.findIndex(r=>r.id===card.dataset.resourceId),next=rows[index+(e.shiftKey?-1:1)];if(!next)return;
   const node=ensure(next.id);if(!node)return;e.preventDefault();const candidates=[...node.querySelectorAll('button,a[href],input')].filter(el=>!el.disabled&&el.getClientRects().length);(e.shiftKey?candidates.at(-1):candidates[0])?.focus();pin('keyboard');queue();
  }
  win.addEventListener('scroll',queue,{passive:true});doc.addEventListener('visibilitychange',visibility);grid.addEventListener('load',imageReady,true);grid.addEventListener('error',imageReady,true);grid.addEventListener('pointerdown',pressed,true);win.addEventListener('pointerup',released);win.addEventListener('pointercancel',released);win.addEventListener('blur',released);grid.addEventListener('keydown',keydown);
  return {layout,capture,pin,ensure,
   refresh(item){
    const index=rows.findIndex(r=>r.id===item.id);if(index<0)return false;
    capture();const before=rows[index],entry=entries[index],oldKey=entry&&sizeKey(entry);
    rows=rows.slice();rows[index]=item;htmlCache.delete(item.id);
    if(entry){entries[index]={...entry,ref:item};if(oldKey!==sizeKey(entries[index])||span(before)!==span(item)){measured.delete(item.id);ratios.delete(item.id);dirty=true;}}
    else dirty=true;
    windowKey='';queue();return true;
   },
   // Keep both the attached pointer target and its hit area through click.
   // State may advance meanwhile; the latest global presentation runs once.
   deferWhilePressed(render){if(dead||!pins.has('pointer'))return false;pendingRender=render;return true;},
   setItems(items,nextKey,nextContext=''){
    capture();if(nextKey!==key){anchor=null;lastAnchor=null;pins.clear();key=nextKey;htmlCache.clear();}dirty=dirty||rows.length!==items.length||rows.some((r,i)=>r!==items[i]);rows=items;context=nextContext;windowKey='';if(!rows.length){enabled=false;grid.classList.remove('gallery-windowed');grid.removeAttribute('role');reconcile(grid,[]);grid.style.height='';}
    const ids=new Set(items.map(r=>r.id));for(const map of [ratios,measured])for(const id of map.keys())if(!ids.has(id))map.delete(id);for(const [reason,id]of pins)if(!ids.has(id))pins.delete(reason);
   },
   active:()=>enabled,has:id=>entryIndex.has(id),
   destroy(){dead=true;pendingRender=null;win.cancelAnimationFrame(frame);htmlCache.clear();ratios.clear();measured.clear();pins.clear();win.removeEventListener('scroll',queue);doc.removeEventListener('visibilitychange',visibility);grid.removeEventListener('load',imageReady,true);grid.removeEventListener('error',imageReady,true);grid.removeEventListener('pointerdown',pressed,true);win.removeEventListener('pointerup',released);win.removeEventListener('pointercancel',released);win.removeEventListener('blur',released);grid.removeEventListener('keydown',keydown);}
  };
 }
 const api={createGeometry,create};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiGalleryWindow=api;
})(typeof window==='object'?window:globalThis);

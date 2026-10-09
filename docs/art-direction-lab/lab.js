/* Art review only. No application imports, writes, hashing or storage simulation. */
(function(root){
 'use strict';
 const escape=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const domain=r=>{try{return new URL(r.url).hostname.replace(/^www\./,'');}catch{return r.kind==='code'?'JavaScript / 本地代码':'本地 Prompt';}};
 function mesh(id="${id}"){
  const project=(u,v)=>[210+u*108+v*52,152+v*73-54*Math.cos(u*1.55)*Math.cos(v*1.4)];
  let paths='';
  for(let axis=0;axis<2;axis++)for(let i=0;i<=16;i++){
   const points=[];for(let j=0;j<=50;j++){const a=-1+i/8,b=-1+j/25;points.push(project(axis?a:b,axis?b:a));}
   paths+=`<path d="${points.map((p,j)=>(j?'L':'M')+p.map(n=>n.toFixed(2)).join(' ')).join('')}"/>`;
  }
  return `<svg class="mesh foreground" viewBox="0 0 420 320" aria-hidden="true"><defs><linearGradient id="${id}"><stop stop-color="#72352c"/><stop offset=".5" stop-color="#ff6954"/><stop offset="1" stop-color="#5d2544"/></linearGradient></defs><g fill="none" stroke="url(#${id})" stroke-width="1.25">${paths}</g></svg>`;
 }
 function art(item,scope="board"){
  const svgId=(scope+"-"+item.resource.id).replace(/[^a-zA-Z0-9_-]/g,"_");
  const r=item.resource,t=escape(r.title),source=escape(domain(r));let content='';
  switch(item.master){
   case 'shiji':content=`<svg class="brand-frame foreground" viewBox="0 0 420 340" aria-hidden="true"><defs><linearGradient id="lime-${svgId}" x2=".8" y2="1"><stop stop-color="#f0ffb0"/><stop offset=".5" stop-color="#d7ff65"/><stop offset="1" stop-color="#8fbb2c"/></linearGradient></defs><path d="M83 54 318 20 376 110 348 250 117 302 38 181Z" fill="none" stroke="#364622" stroke-width="47" transform="translate(12 17)"/><path d="M83 54 318 20 376 110 348 250 117 302 38 181Z" fill="none" stroke="url(#lime-${svgId})" stroke-width="35"/><path d="m306 22 31 57-38 9" fill="none" stroke="#f4ffd6" stroke-width="9"/></svg><h2 class="shiji-type">${t}</h2><div class="tech-ticket foreground"><b>${escape(r.language)}</b><span>${r.tags.map(escape).join(' / ')}</span></div>`;break;
   case 'vscode':content=`<div class="editor-depth back"><div class="editor-lines"></div><b>${source}</b></div><div class="editor-depth front foreground"><span>${t}</span><div class="cursor-bars"><i></i><i></i><i></i><i></i></div><div class="editor-caret"></div></div><h2 class="vscode-type">${t.replace(' ','<br>')}</h2>`;break;
   case 'godot':content=`<svg class="stage foreground" viewBox="0 0 420 340" aria-hidden="true"><defs><linearGradient id="block-${svgId}"><stop stop-color="#e9f0ff"/><stop offset="1" stop-color="#a4aafa"/></linearGradient></defs><path d="M-20 272 230 126 450 250 180 417Z" fill="#284db2"/><path d="M-20 272 230 126 450 250 180 417Z" fill="none" stroke="#89adf5" stroke-width="1"/><g stroke="#729cea" stroke-width="1"><path d="m70 222 220 124M140 181l220 124M210 139l220 124M77 328l244-143M148 370l244-143"/></g><path d="M168 124 244 80 319 124 242 169Z" fill="url(#block-${svgId})"/><path d="M168 124v111l74 44V169Z" fill="#637cdd"/><path d="M242 169v110l77-44V124Z" fill="#3c47ad"/><path d="M80 214 126 187 172 214 126 241Z" fill="#b5d7ff"/><path d="M80 214v38l46 27v-38Z" fill="#88ace9"/><path d="M126 241v38l46-27v-38Z" fill="#4968cb"/><path d="M290 215 335 189 380 215 335 241Z" fill="#d7ff65"/><path d="M290 215v39l45 26v-39Z" fill="#a6c848"/><path d="M335 241v39l45-26v-39Z" fill="#739832"/></svg><h2 class="godot-type">${t}<span>${source}</span></h2>`;break;
   case 'react':content=`<div class="specimen-rule"></div><div class="component-tab foreground">${escape(r.tags.join(' / '))}</div><h2 class="react-type">${t.replace(' ','<br>')}</h2><div class="component-block foreground"><span>${escape(r.tags[0])}</span><svg viewBox="0 0 100 70" aria-hidden="true"><path d="M10 35h75m-20-20 20 20-20 20" fill="none" stroke="currentColor" stroke-width="7"/></svg></div><div class="type-swatch"><i>Aa</i><i>Rr</i><i>Bb</i></div>`;break;
   case 'olla':content=`<div class="print-page foreground"><span>${source}</span><h2>${t.replace(' — ','<br><em>')}</em></h2><div class="print-circles"><i></i><i></i><i></i></div><span class="print-foot">${escape(r.category)} / 收藏参考</span></div><div class="registration" aria-hidden="true"></div>`;break;
   case 'motion':content=`<h2 class="motion-type">${t.replace(' ','<br>')}</h2><svg class="motion-disc foreground" viewBox="0 0 300 300" aria-hidden="true"><circle cx="150" cy="150" r="132" fill="#171526"/><circle cx="150" cy="150" r="98" fill="#9267f6"/><circle cx="150" cy="150" r="65" fill="#ff896f"/><path d="M150 44V6M256 150h38M150 256v38M44 150H6" stroke="#d7ff65" stroke-width="5"/><circle cx="150" cy="150" r="40" stroke="#ffd4c6" stroke-width="2" fill="none"/></svg><div class="motion-strip foreground"><span>${t}</span><span>${t}</span><span>${t}</span></div>`;break;
   case 'polyhaven':content=`<div class="photo-sheet foreground"><div class="photo-window"><img class="site-preview" src="/polyhaven.jpg" alt="Poly Haven 实际网站预览的建筑局部，来自仓库已有截图"></div><span>网站预览 · 局部</span></div><h2 class="polyhaven-type">${t.replace(' ','<br>')}</h2><div class="photo-category">${escape(r.category)}</div>`;break;
   case 'hugging':content=`<h2 class="hugging-type">${t.replace(' ','<br>')}</h2>${mesh("mesh-"+svgId)}<div class="mesh-label">AI / ML<span>抽象曲面 · 非模型输出</span></div>`;break;
   case 'pytorch':content=`<div class="tensor-space foreground"><i class="tensor-slice one"></i><i class="tensor-slice two"></i><i class="tensor-slice three"></i><i class="tensor-slice four"></i></div><h2 class="pytorch-type">${t}</h2><div class="tensor-label">AI / ML<span>抽象张量切片</span></div>`;break;
   case 'article':content=`<div class="article-sheet foreground"><span>MDN / CSS REFERENCE</span><h2>${t.replace(' ','<br>')}</h2><p>transform</p><p>transform</p><code>transform: rotate(-8deg);</code></div><div class="article-stamp">${escape(r.category)}</div>`;break;
   case 'code':content=`<div class="code-title"><h2>${t}</h2><span>${escape(r.language)}</span></div><pre class="code-paper foreground">${r.snippet.split('\n').map((line,i)=>`<span><i aria-hidden="true">${i+1}</i><code>${escape(line)||' '}</code></span>`).join('')}</pre><div class="code-watermark" aria-hidden="true">{ }</div>`;break;
   case 'prompt':content=`<div class="prompt-back"></div><div class="prompt-page foreground"><h2>${t.replace("创作","创作<br>")}</h2><p>${escape(r.snippet)}</p><div class="prompt-fold" aria-hidden="true"></div></div><span class="prompt-format">${escape(r.kind.toUpperCase())}</span>`;break;
   default:throw new Error('Unknown curated master');
  }
  return `<div class="art art-${item.master}" data-resource-id="${escape(r.id)}"><div class="poster-source">${source}</div>${content}<div class="poster-footer">${escape(item.group)}<span>SHIJI / ART LAB</span></div></div>`;
 }
 const api={escape,domain,mesh,art};
 if(typeof module==='object')module.exports=api;else{root.ShijiArtLab=api;boot();}
 async function boot(){
  if(new URLSearchParams(location.search).has('phone')){
   // A fixed-width, same-origin review frame makes the tested CSS viewport explicit.
   document.body.replaceChildren();document.body.style.width='390px';
   const frame=document.createElement('iframe');frame.title='390 px 手机设计板评审';frame.src='/';frame.style.cssText='border:0;display:block;width:390px;height:5500px';
   frame.addEventListener('load',()=>{frame.style.height=(frame.contentDocument.documentElement.scrollHeight+8)+'px';});
   document.body.append(frame);return;
  }
  const $=s=>document.querySelector(s);let records=[],active='board';const reduced=matchMedia('(prefers-reduced-motion: reduce)');let spatial=false,raf=0,pending=null,last=null;
  function reset(){cancelAnimationFrame(raf);raf=0;pending=null;if(last){last.style.removeProperty('--px');last.style.removeProperty('--py');last=null;}}
  function update(){reset();document.body.classList.toggle('spatial',spatial&&!reduced.matches&&!document.hidden);$('#spatial').setAttribute('aria-pressed',String(spatial&&!reduced.matches));$('#spatial').disabled=reduced.matches;$('#spatial').textContent=reduced.matches?'系统已减少动态效果':spatial?'关闭空间预览':'开启空间预览';}
  $('#spatial').addEventListener('click',()=>{spatial=!spatial;update();});reduced.addEventListener('change',update);document.addEventListener('visibilitychange',update);
  document.addEventListener('pointermove',e=>{
   if(!document.body.classList.contains('spatial')||e.pointerType==='touch')return;
   const el=e.target.closest('.art');if(!el){reset();return;}if(last&&last!==el)reset();last=el;pending={el,x:e.clientX,y:e.clientY};if(raf)return;
   raf=requestAnimationFrame(()=>{raf=0;if(!pending)return;const {el,x,y}=pending;const b=el.getBoundingClientRect();el.style.setProperty('--px',String(Math.max(-1,Math.min(1,(x-b.left)/b.width-.5))));el.style.setProperty('--py',String(Math.max(-1,Math.min(1,(y-b.top)/b.height-.5))));pending=null;});
  });document.addEventListener('pointerleave',reset);
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{active=b.dataset.view;reset();for(const key of ['board','compare','reference'])$('#'+key).hidden=key!==active;document.querySelectorAll('[data-view]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));$('#status').textContent=active==='reference'?'原始参考文件 · 字节一致，未修改':'12 份真实保存的测试资源 · '+(active==='board'?'逐张手工美术指导':'相同资源前后对照');}));
  function label(item){const h=document.createElement('h3');h.textContent=item.resource.title;const p=document.createElement('p');p.textContent=item.group+' · '+item.direction;return[h,p];}
  function master(item,scope="board"){const frame=document.createElement('div');frame.className='poster';frame.innerHTML=art(item,scope);return frame;}
  function old(item,css,renderer){const frame=document.createElement('div');frame.className='poster';const shadow=frame.attachShadow({mode:'open'});shadow.innerHTML='<style>'+css.replace(/:root/g,':host')+'\n:host{--shiji-lime:#d7ff65;--shiji-ink:#13171a} .card-preview{position:absolute;inset:0;container-type:inline-size;overflow:hidden} img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:10}</style><div class="card-preview">'+renderer.coverMarkup(item.resource)+'</div>';if(item.resource.coverId){const img=document.createElement('img');img.src='/polyhaven.jpg';img.alt=item.resource.title+' · 同一实际网站预览';shadow.querySelector('.card-preview').append(img);}return frame;}
  try{
   const response=await fetch('/lab-data');if(!response.ok)throw new Error('临时资源读取失败，刷新页面重试。');records=await response.json();
   const css2=await(await fetch('/compare2.css')).text(),cssOld=await(await fetch('/restoration.css')).text();
   for(const item of records){const card=document.createElement('article');card.append(master(item),...label(item));$('#board').append(card);
    const pair=document.createElement('article');const head=document.createElement('h3');head.textContent=item.resource.title;const cols=document.createElement('div');cols.className='paired';for(const [name,poster] of [['Cover Studio 2.0',old(item,css2,ShijiV2)],['Art Direction Lab',master(item,'compare')]]){const fig=document.createElement('figure'),cap=document.createElement('figcaption');cap.textContent=name;fig.append(cap,poster);cols.append(fig);}pair.append(head,cols);$('#pairs').append(pair);
   }
   const shiji=records[0],cols=document.createElement('div');cols.className='paired';for(const [name,poster] of [['card-restoration / 3327d44',old(shiji,cssOld,ShijiBaseline)],['Art Direction Lab',master(shiji,'restoration')]]){const fig=document.createElement('figure'),cap=document.createElement('figcaption');cap.textContent=name;fig.append(cap,poster);cols.append(fig);}$('#restoration-pair').append(cols);
   $('#status').textContent='12 份真实保存的测试资源 · 逐张手工美术指导';update();
  }catch(e){$('#status').setAttribute('role','alert');$('#status').textContent=e.message;}
 }
})(typeof window==='object'?window:globalThis);

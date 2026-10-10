/* Spatial Poster presentation port of the user's SHIJI V5 Demo.
 * Resource persistence, filtering and mutations remain in app.js / the local service.
 * No seed records, simulated metadata or parallel card animation controller.
 */
(function(root){
 'use strict';
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function host(r){try{return new URL(r.url).hostname.replace(/^www\./,'');}catch{return '';}}
 function posterKind(r){
  if(r.kind==='code'||r.kind==='prompt')return r.kind;
  const site=host(r),words=[r.title,r.description,...(Array.isArray(r.tags)?r.tags:[])].join(' ');
  if(site==='reactbits.dev')return 'retro';
  if(/motion|animat|gsap/.test(site)||r.category==='视频')return /kinetic|typograph|逐帧|字体/i.test(words)?'kinetic':'motion';
  if(site==='spline.design'||r.category==='3D')return 'spline';
  if(site==='huggingface.co'||site==='openai.com'||site==='anthropic.com'||site.endsWith('.ai')||/\b(AI|ML|LLM)\b|人工智能|机器学习/i.test(words))return 'hf';
  if(site==='linear.app')return 'linear';
  if(site==='ui.shadcn.com'||/components?|设计系统|组件/i.test(words))return 'components';
  if(site==='github.com'||site==='gitlab.com')return 'github';
  if(r.category==='开发工具')return 'linear';
  if(r.category==='音频')return 'retro';
  if(r.category==='美术素材'||/color|palette|颜色|配色/i.test(words))return 'atlas';
  if(r.category==='UI / 设计')return 'components';
  return 'article';
 }
 function coverMarkup(r,composition){
  const type=composition||posterKind(r),title=String(r.title||host(r)||'资源'),source=host(r)||({code:'代码片段',prompt:'提示词',file:'本地素材'}[r.kind]||'收藏资源');
  const metrics=root.ShijiV2?.titleMetrics?.(title);
  const units=metrics?.emLine||Math.max(3,[...title].reduce((n,c)=>n+(/[\u3400-\u9fff]/u.test(c)?1:.56),0)/Math.min(4,Math.ceil(title.length/12)));
  const font=Math.min(25,Math.max(6.8,84/units)),tags=(Array.isArray(r.tags)?r.tags:[]).slice(0,3);
  const name=`<span class="art-copy" style="--poster-title-size:${font.toFixed(2)}cqw">${esc(title)}</span>`;
  const base=`<span class="art-index"><span>${esc(source)}</span><b>${esc(r.language||r.category||'收藏')}</b></span>`;
  const foot=`<span class="art-foot">${esc(r.category||'资源')}${tags.length?' / '+tags.map(esc).join(' · '):''}</span>`;
  const stack=String(r.language||'').trim()||tags.join(' · ');
  const excerpt=String(r.snippet||r.description||r.notes||'');
  let art='';
  switch(type){
   case 'components':art=`<span class="art-grid"></span><span class="art-block"></span>${name}<span class="art-edition">${esc(r.category||'UI / 设计')}</span><span class="art-miniapp"><strong>${esc(title)}</strong><small>${esc(r.description||source)}</small><span class="m-row">${tags.slice(0,2).map(t=>`<i>${esc(t)}</i>`).join('')}</span></span>`;break;
   case 'motion':art=`<span class="art-grid"></span>${name}<span class="art-plate art-anim"></span><span class="art-side">${esc(source)}</span>`;break;
   case 'spline':art=`<span class="art-grid"></span><span class="orb-body art-anim"></span>${name}`;break;
   case 'hf':art=`<span class="art-dotfield"></span>${name}<span class="art-asterisk art-anim" aria-hidden="true">✳</span>`;break;
   case 'linear':art=`<span class="art-grid"></span><span class="art-ring art-anim"></span>${name}`;break;
   case 'prompt':art=`${name}<span class="art-star art-anim" aria-hidden="true">✳</span><span class="art-stripe"></span><span class="art-excerpt">${esc(excerpt.slice(0,180))}</span>`;break;
   case 'retro':art=`<span class="art-vinyl art-anim"></span>${name}`;break;
   case 'github':art=`<span class="art-grid"></span>${name}${stack?`<span class="art-terminal"><span class="term-dots" aria-hidden="true">●●●</span><span class="term-source">${esc(source)}</span><span class="term-stack">${esc(stack)}</span></span>`:''}`;break;
   case 'kinetic':art=`<span class="art-grid"></span>${name}<span class="filmstrip" aria-hidden="true"><i>↗</i><i>✳</i><i>↗</i><i>✳</i></span>`;break;
   case 'atlas':art=`<span class="art-grid"></span>${name}<span class="art-fold art-anim"></span>`;break;
   case 'code':art=`<span class="art-grid"></span><span class="art-code-name">${esc(title)}</span><span class="art-terminal"><span class="term-dots" aria-hidden="true">●●●</span><pre>${esc(String(r.snippet||'').split('\n').slice(0,9).map(line=>line.slice(0,160)).join('\n'))}</pre></span>`;break;
   default:art=`<span class="art-grid"></span>${name}<span class="art-circle art-anim"></span><span class="art-sticker">${esc(r.category||'阅读')}</span>`;
  }
  return `<span class="cover-art art-v3 art-${esc(type)}" data-poster-kind="${esc(type)}" aria-hidden="true">${base}${art}${foot}<span class="art-grain"></span><span class="art-ink-flash"></span><span class="art-sheen"></span></span>`;
 }
 function create({document:doc,window:win,preview,changed,reconcile}){
  const button=doc.getElementById('poster-mode'),deck=doc.getElementById('scene-stack'),section=doc.getElementById('space-showcase');
  let classic=false,dead=false;
  try{classic=win.localStorage.getItem('shiji-v5-poster-mode')==='classic';}catch{}
  function apply(){doc.documentElement.dataset.cardMode=classic?'classic':'v3';doc.documentElement.dataset.shijiCover=classic?'classic':'poster';if(button){button.setAttribute('aria-pressed',String(!classic));button.setAttribute('aria-label',classic?'封面模式：经典，切换为 V5 海报':'封面模式：V5 海报，切换为经典');button.innerHTML='<span class="art-led" aria-hidden="true"></span><span>POSTER LAB</span><b>'+(classic?'V2':'V5')+'</b>';}}
  function toggle(){if(dead)return;classic=!classic;try{win.localStorage.setItem('shiji-v5-poster-mode',classic?'classic':'poster');}catch{}apply();changed?.();}
  button?.addEventListener('click',toggle);apply();
  function render({resources=[],scope='all'}={}){
   if(dead)return;
   // No filler duplicates: the spatial deck is exactly up to three matched records.
   const rows=resources.slice(0,3),visible=rows.length>0&&!['trash','health'].includes(scope);
   if(section)section.hidden=!visible;
   if(deck){const panes=visible?rows.map((r,i)=>({id:r.id,html:`<button type="button" class="space-pane pane-${['a','b','c'][i]}" data-resource-id="${esc(r.id)}" data-action="detail" data-id="${esc(r.id)}" aria-label="查看 ${esc(r.title)}"><span class="space-pane-shell"><span class="space-pane-preview">${preview(r)}</span><span class="space-meta"><span><strong>${esc(r.title)}</strong><span>${esc(host(r)||r.language||r.kind||'')}</span></span><span class="space-badge">${esc(r.category||'')}</span></span></span></button>`})):[];reconcile(deck,panes,'.space-pane');deck.dataset.paneCount=String(panes.length);}
   for(const el of doc.querySelectorAll('#v5-mobile-nav [data-scope]')){const active=el.dataset.scope===scope;el.classList.toggle('active',active);el.setAttribute('aria-current',active?'page':'false');}
  }
  return {render,destroy(){dead=true;button?.removeEventListener('click',toggle);}};
 }
 const api={posterKind,coverMarkup,create};if(typeof module==='object')module.exports=api;else root.ShijiV5=api;
})(typeof window==='object'?window:globalThis);

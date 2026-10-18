'use strict';
const $=s=>document.querySelector(s), CATEGORIES=['开发工具','美术素材','UI / 设计','音频','视频','字体','3D','灵感','其他'];
const VISUALS={'开发工具':['code','#e1e9e4','#176b9a'],'美术素材':['image','#f2e5ce','#a23c12'],'UI / 设计':['palette','#e9e5de','#6256a7'],'音频':['music','#e7e8cf','#657400'],'视频':['video','#e1e9e4','#176b9a'],'字体':['type','#eee8d5','#586e75'],'3D':['box','#dce9df','#157b77'],'灵感':['lightbulb','#f1e7c8','#856600'],'其他':['bookmark','#eee8d5','#486168']};
const KINDS={website:'网站',file:'本地素材',code:'代码片段',prompt:'提示词'}, LINK_STATUS={unchecked:'未检查',ok:'可访问',broken:'疑似失效',unknown:'暂时无法判断'};
const freshFilters=()=>({search:'',tags:[],category:'',collection:'',price:'',license:'',kind:'',linkStatus:'',color:''});
const readCollapsed=()=>{try{const value=JSON.parse(localStorage.getItem('shiji-collapsed-projects')||'[]');return new Set(Array.isArray(value)?value.filter(v=>typeof v==='string'):[]);}catch{return new Set();}};
const state={collectionMeta:[],collapsedProjects:readCollapsed(),resources:[],trash:[],collections:[],smartCollections:[],scope:'all',scopeValue:'',filters:freshFilters(),view:localStorage.getItem('shiji-view')||'grid',density:localStorage.getItem('shiji-density')==='compact'?'compact':'comfortable',previewMode:ShijiBits.readPreviewMode(localStorage),sort:'new',selectMode:false,selected:new Set(),editing:null,detail:null,pending:[],formBase:{},formProjects:Object.create(null),formTags:[],metadataRun:0,formBusy:false,formConflict:null};
let libraryReady=false;
let lastFocus=null,toastTimer,dragDepth=0,backupBusy=false,backupMessage='';
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>`<img src="icons/${name}.svg" alt="">`;
const domain=url=>{try{return new URL(url).hostname.replace(/^www\./,'');}catch{return '';}};
const dateFormatter=new Intl.DateTimeFormat('zh-CN',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
const date=v=>{const value=new Date(v);return Number.isNaN(value.getTime())?value.toString():dateFormatter.format(value);};
const size=v=>v<1024*1024?`${Math.max(1,Math.round(v/1024))} KB`:`${(v/1024/1024).toFixed(1)} MB`;
const split=v=>[...new Set(v.split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean))];
const find=id=>[...state.resources,...state.trash].find(x=>x.id===id)||(typeof detailCache!=='undefined'?detailCache.get(id):null);
const visual=r=>VISUALS[r.category]||VISUALS['其他'];
const fileURL=a=>'/api/files/'+encodeURIComponent(typeof a==='string'?a:a.id);
function toast(message,action,callback){clearTimeout(toastTimer);$('#toast-message').textContent=message;$('#toast-action').hidden=!action;$('#toast-action').textContent=action||'';$('#toast-action').onclick=async()=>{try{await callback?.();$('#toast').hidden=true;}catch(e){toast(e.message);}};$('#toast').hidden=false;toastTimer=setTimeout(()=>$('#toast').hidden=true,action?15000:6500);}
async function api(path,method='GET',body,signal){let response;try{response=await fetch(path,{method,signal,...(body!==undefined?{headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});}catch(e){if(e.name==='AbortError')throw e;throw new Error('无法连接资源库，请确认本地应用已启动。');}let data;try{data=await response.json();}catch{throw new Error('服务没有返回有效结果，请重试。');}if(!response.ok){const e=new Error(data.error||'操作失败，请重试。');e.existingId=data.existingId;e.status=response.status;e.current=data.current;e.resource=data.resource;e.conflicts=data.conflicts;throw e;}return data;}
async function rawAPI(path,file,headers={}){let response;try{response=await fetch(path,{method:'POST',headers,body:file});}catch{throw new Error('上传中断，请确认服务仍在运行。');}const result=await response.json();if(!response.ok)throw new Error(result.error||'文件保存失败。');return result;}
async function reload(){await reloadData();libraryReady=true;}
async function reloadData(){if(typeof ShijiQuery!=='undefined'){if(state.remote)return remoteReload();let meta;try{meta=await api('/api/library');}catch(e){if(e.status!==404)throw e;}if(meta?.queryVersion===1){state.remote=meta;return remoteReload();}}const [data,trash]=await Promise.all([api('/api/resources'),api('/api/trash')]);Object.assign(state,{resources:data.resources,collections:data.collections,collectionMeta:data.collectionMeta||data.collections.map(name=>({name,parent:'',autoTags:[],archived:false})),smartCollections:data.smartCollections||[],trash:trash.resources});state.selected=new Set([...state.selected].filter(id=>find(id)));render();if(state.scope==='health')await refreshHealth();}
function nav(label,count,name,action,active){return `<button class="nav-item ${active?'active':''}" ${action} ${active?'aria-current="page"':''}>${icon(name)}<span>${esc(label)}</span>${count?`<span class="count">${count}</span>`:''}</button>`;}
function scoped(){let items=state.scope==='trash'?state.trash:state.resources;if(state.scope==='favorite')items=items.filter(x=>x.favorite);if(state.scope==='inbox')items=items.filter(x=>x.inbox);if(state.scope==='assets')items=items.filter(x=>x.kind==='file'||x.attachments.length);if(state.scope==='snippets')items=items.filter(x=>['code','prompt'].includes(x.kind));return items;}
function shownItems(){if(state.remote)return state.scope==='trash'?state.trash:state.resources;return scoped().filter(r=>ShijiLibrary.matches(r,state.filters,state.collectionMeta)).sort((a,b)=>state.sort==='name'?a.title.localeCompare(b.title,'zh-CN'):new Date(b[state.sort==='updated'?'updatedAt':'createdAt'])-new Date(a[state.sort==='updated'?'updatedAt':'createdAt']));}
function snapshotFilters(){return {...state.filters,tags:[...state.filters.tags],...(state.scope==='favorite'?{favorite:true}:{}),...(state.scope==='inbox'?{inbox:true}:{}),...(state.scope==='assets'?{hasAssets:true}:{}),...(state.scope==='snippets'?{isSnippet:true}:{})};}
function syncFilters(){for(const [id,key] of [['search','search'],['price-filter','price'],['license-filter','license'],['kind-filter','kind'],['status-filter','linkStatus']])$( '#'+id).value=state.filters[key]||'';}
function selectScope(scope,value=''){if(typeof invalidateSelection==='function')invalidateSelection();state.scope=scope;state.scopeValue=value;state.filters=freshFilters();state.selected.clear();if(scope==='category')state.filters.category=value;if(scope==='collection'){state.filters.collection=value;state.view='board';}if(scope==='smart'){const smart=state.smartCollections.find(s=>s.id===value);if(smart)state.filters={...freshFilters(),...smart.filters,tags:[...(smart.filters.tags||[])]};}syncFilters();closeMenu();render();window.scrollTo({top:0,behavior:'instant'});}
function preview(r){
 const pref=typeof ShijiCoverConfig!=='undefined'?ShijiCoverConfig.read(r):null,cover=pref?.imageSource==='poster'?'':r._coverObjectURL||ShijiBoard.cover(r),fallback=typeof ShijiV5!=='undefined'?ShijiV5.coverMarkup(r):ShijiV2.coverMarkup(r),photo=(!pref||pref.imageSource==='auto'&&pref.imageFit==='fill'&&pref.imageX===50&&pref.imageY===50&&!pref.customTitle&&!pref.customSubtitle)?ShijiV2.photoCoverMarkup(r,cover):'';
 if(photo)return photo+fallback;if(!cover)return fallback;
 const crop=pref&&r.coverConfig?` style="object-fit:${pref.imageFit==='fit'?'contain':'cover'};object-position:${pref.imageX}% ${pref.imageY}%"`:'',image=`<img class="cover-image" src="${esc(cover)}" alt="${esc(r.title)} 的预览" loading="lazy" referrerpolicy="no-referrer"${crop}>`;
 if(pref&&(pref.customTitle||pref.customSubtitle)){const color=ShijiCoverConfig.colors(pref);return `<span class="cover-photo cs-image-cover" data-title-position="${pref.titlePosition}" data-density="${pref.density}" style="--cs-bg:${color.background};--cs-ink:${color.foreground}">${image}<span class="cs-image-caption">${pref.customTitle?`<strong>${esc(pref.customTitle)}</strong>`:''}${pref.customSubtitle?`<span>${esc(pref.customSubtitle)}</span>`:''}</span></span>${fallback}`;}
 return image+fallback;
}
function card(r){const ratio=ShijiBoard.cover(r).startsWith('previews/')?({'recent.co':.85,'reactbits.dev':1.15,'motionsites.ai':1.65,'polyhaven.com':1.22,'freesound.org':1.6}[domain(r.url)]||1.6):ShijiBoard.cover(r)?1.6:ShijiV2.coverRatio(r);return `<article data-resource-id="${esc(r.id)}" data-card-type="${ShijiV2.cardType(r)}" data-cover-kind="${ShijiV2.coverKind(r)}" data-gallery-span="${ShijiV2.gallerySpan(r)}" class="resource-card ${state.selected.has(r.id)?'selected':''}" style="--gallery-ratio:${ratio};--tile-bg:${visual(r)[1]};--tile-ink:${visual(r)[2]}"><div class="card-motion-surface"><button class="card-preview" data-action="detail" data-id="${esc(r.id)}" aria-label="查看 ${esc(r.title)}">${preview(r)}</button>${state.selectMode?`<label class="card-select"><input type="checkbox" data-select="${esc(r.id)}" aria-label="选择 ${esc(r.title)}" ${state.selected.has(r.id)?'checked':''}></label>`:''}<div class="card-body"><div class="card-kicker"><span>${esc(r.language||KINDS[r.kind])} / ${esc(r.category)}</span><span aria-hidden="true">↗</span></div><div class="card-title-row"><button class="card-title" data-action="detail" data-id="${esc(r.id)}">${esc(r.title)}</button>${!r.deleted?`<button class="icon-button card-favorite ${r.favorite?'is-favorite':''}" data-action="favorite" data-id="${esc(r.id)}" aria-label="${r.favorite?'取消常用':'设为常用'}：${esc(r.title)}" aria-pressed="${r.favorite}">${icon('star')}</button>`:''}</div><div class="card-domain">${r.favicon?`<img class="site-favicon" src="${esc(r.favicon)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:''}${esc(domain(r.url)||KINDS[r.kind])}${r.attachments.length?`<span class="attachment-count">${r.attachments.length} 个附件</span>`:''}</div><p class="card-description">${esc((state.filters.collection&&r.projectNotes?.[state.filters.collection])||r.description||r.notes||'留下用途，方便下次找到。')}</p><div class="card-tags">${r.tags.slice(0,3).map(t=>`<button data-action="tag" data-value="${esc(t)}">${esc(t)}</button>`).join('')}</div></div><div class="card-footer"><span class="category-label">${esc(r.category)}</span>${ShijiGallery.media(ShijiBoard.galleryResource(r)).length?`<button class="text-button card-quick-preview" data-action="preview" data-id="${esc(r.id)}" aria-label="预览 ${esc(r.title)}" title="预览素材 · 聚焦封面或标题后按空格">${icon('image')}预览</button>`:''}<span class="card-price">${esc(r.price==='待确认'?'':r.price)}</span>${r.linkStatus==='broken'?'<span class="broken-label">疑似失效</span>':''}${r.deleted?`<button class="text-button" data-action="restore" data-id="${esc(r.id)}">恢复</button>`:r.url?`<a class="icon-button card-open" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer" aria-label="打开 ${esc(r.title)}">${icon('arrow-up-right')}</a>`:''}</div></div></article>`;}
function attachImageFallbacks(root){root.querySelectorAll('.cover-image').forEach(img=>{const media=img.closest('.cover-photo')||img,fallback=media.nextElementSibling,failed=img.hidden||(img.complete&&!img.naturalWidth);img.hidden=failed;media.hidden=failed;if(fallback)fallback.hidden=!failed;img.onload=()=>{img.hidden=false;media.hidden=false;if(fallback)fallback.hidden=true;};img.onerror=()=>{img.hidden=true;media.hidden=true;if(fallback)fallback.hidden=false;};});root.querySelectorAll('.site-favicon').forEach(img=>img.onerror=()=>img.hidden=true);}
const resourceBits=ShijiBits.create($('#resource-grid'),$('.topbar-actions [data-action="add"]'));
const motion=ShijiMotion.init({document,window});
const quickCapture=ShijiQuickCapture.create({document,api,lookup:async url=>state.remote?(await api('/api/resources/lookup','POST',{url})).resource:(await api('/api/resources')).resources.find(r=>r.url===url),context:()=>({projects:state.scope==='collection'?[state.scopeValue]:[]}),notice:toast,onFull:value=>{edit(null,{url:value});setKind();},onSaved:async (r,origin)=>{selectScope('all');await reload();motion.captureConfirmed({resourceId:r.id,...origin});toast('已收藏。正在补全网页标题与介绍。');},onEnriched:async()=>{await captureTasks.poll();}});
const captureTasks=typeof ShijiCaptureTasks!=='undefined'?ShijiCaptureTasks.create({document,api,show:manage,notice:toast,refresh:async()=>{if(document.querySelector('dialog[open]')||!$('#drawer').hidden||state.formBusy)return false;await reload();return true;},onResource:async id=>{const {resource}=await api('/api/resources/'+encodeURIComponent(id));$('#manage-dialog').close();detail(resource);}}):{async poll(){},destroy(){}};
captureTasks.poll();
const categoryDock=ShijiBits.createDock($('#browse-categories'));
const spatial=typeof ShijiV5!=='undefined'?ShijiV5.create({document,preview,reconcile:ShijiCards.render}):{render(){},destroy(){}};
const browseWindow=ShijiBrowse.create();
// DOM residency references existing page records; Bits remains layout/motion owner.
const galleryWindow=typeof ShijiGalleryWindow!=='undefined'&&document.documentElement.clientWidth>0?ShijiGalleryWindow.create({grid:$('#resource-grid'),pack:ShijiBits.pack,reconcile:(...args)=>ShijiCards.render(...args),renderCard:r=>card(r),span:ShijiV2.gallerySpan,cover:ShijiBoard.cover,version:r=>JSON.stringify([state.selected.has(r.id),r.coverConfig||null]),onMount(){attachImageFallbacks($('#resource-grid'));if(typeof markSearchResults==='function')markSearchResults();},schedule:()=>resourceBits.renderWindow()}):null;
resourceBits.setWindow?.(galleryWindow);
async function saveCover(resource,body){
 const path='/api/resources/'+encodeURIComponent(resource.id);
 try{return await api(path+'/cover','POST',body);}
 catch(e){
  if(e.status)throw e;
  // Verify persisted outcome before offering an identical, idempotent retry.
  try{const {resource:actual}=await api(path),same=JSON.stringify(ShijiCoverConfig.normalize(actual.coverConfig))===JSON.stringify(ShijiCoverConfig.normalize(body.config));let imageMatches=actual.coverId===body.coverId;
   if(body.upload){const bytes=Uint8Array.from(atob(body.upload.base64),c=>c.charCodeAt(0)),digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');imageMatches=actual.attachments.some(a=>a.id===actual.coverId&&a.sha256===digest);}
   if(same&&imageMatches)return {resource:actual,changed:false,reconciled:true};
  }catch(_){}
  throw new Error('保存结果尚未确认。请检查连接后重试；同一草稿不会重复添加图片。');
 }
}
async function applyCoverResource(resource){
 const previous=find(resource.id),current={...resource,...(previous?._highlights&&previous.title===resource.title?{_highlights:previous._highlights}:{}),...(previous?._related?{_related:previous._related}:{})};
 for(const key of ['resources','trash'])state[key]=state[key].map(r=>r.id===current.id?current:r);
 if(typeof detailCache!=='undefined')detailCache.set(current.id,current);
 if(state.remote?.page?.resources)state.remote.page.resources=state.remote.page.resources.map(r=>r.id===current.id?current:r);
 const patch=()=>{
  if(galleryWindow?.active()){galleryWindow.refresh(current);resourceBits.renderWindow();}
  else{ShijiCards.update($('#resource-grid'),{id:current.id,html:card(current)});attachImageFallbacks($('#resource-grid'));resourceBits.renderWindow();}
  spatial.render({resources:shownItems(),scope:state.scope});attachImageFallbacks($('#scene-stack'));
  if(state.detail===current.id){const node=$('#detail-content .detail-preview');if(node){node.innerHTML=preview(current);attachImageFallbacks(node);}$('#drawer-title').textContent=current.title;}
  if(typeof markSearchResults==='function')markSearchResults();
 };
 if(!galleryWindow?.deferWhilePressed(patch))patch();
 // Preferences alone preserve membership/order and patch only this article.
 // Actual attachment/color changes can alter filters; use canonical server query.
 const sourceChanged=previous&&['title','url','kind','category','tags','projects','projectNotes','description','notes','snippet','favorite','inbox','parentId','language','author','price','license'].some(key=>JSON.stringify(previous[key])!==JSON.stringify(current[key]));
 if(state.remote&&(state.sort==='updated'||sourceChanged||previous&&(previous.attachments.length!==current.attachments.length||state.filters.color&&JSON.stringify(previous.colors)!==JSON.stringify(current.colors))))await remoteReload();
}
const coverStudio=typeof ShijiCoverStudio!=='undefined'?ShijiCoverStudio.create({document,preview,save:saveCover,onSaved:applyCoverResource,notice:toast}):null;

function pageKey(){return JSON.stringify([state.scope,state.scopeValue,state.view,state.sort,ShijiLibrary.canonicalFilters(state.filters)]);}
function render(){
  if(galleryWindow?.deferWhilePressed(render))return;
  if(typeof queryRenderNeeded==='function'&&queryRenderNeeded())return;
  const renderStart=performance.now();
  const focus=ShijiCards.captureFocus($('.app-shell'));
  motion.beforeListUpdate();resourceBits.begin();if(document.documentElement.dataset.shijiVersion!=='v5')ShijiV2.render(document,state);
  // V5 keeps its complete brand scene while exploring, matching the supplied Demo.
  $('#shiji-hero').hidden=['trash','health'].includes(state.scope);$('#shiji-ticker').hidden=$('#shiji-hero').hidden;
  const resources=state.resources,counts=state.remote?.counts;$('#main-nav').innerHTML=nav('全部资源',counts?.all??resources.length,'library','data-action="scope" data-scope="all"',state.scope==='all')+nav('常用收藏',counts?.favorite??resources.filter(x=>x.favorite).length,'star','data-action="scope" data-scope="favorite"',state.scope==='favorite')+nav('待整理',counts?.inbox??resources.filter(x=>x.inbox).length,'inbox','data-action="scope" data-scope="inbox"',state.scope==='inbox')+nav('素材附件',counts?.assets??resources.filter(x=>x.kind==='file'||x.attachments.length).length,'image','data-action="scope" data-scope="assets"',state.scope==='assets')+nav('代码与提示词',counts?.snippets??resources.filter(x=>['code','prompt'].includes(x.kind)).length,'code','data-action="scope" data-scope="snippets"',state.scope==='snippets')+nav('回收站',counts?.trash??state.trash.length,'trash-2','data-action="scope" data-scope="trash"',state.scope==='trash');
  $('#category-nav').innerHTML=CATEGORIES.filter(c=>(state.remote?state.remote.categoryCounts[c]:resources.some(x=>x.category===c))).map(c=>nav(c,(state.remote?.categoryCounts[c]??resources.filter(x=>x.category===c).length),visual({category:c})[0],`data-action="category" data-value="${esc(c)}"`,state.scope==='category'&&state.scopeValue===c)).join('')||'<p class="collection-empty">收藏后按类型显示</p>';
  $('#collection-nav').innerHTML=projectNavigation();
  $('#collections').innerHTML=state.collections.map(n=>`<option value="${esc(n)}" label="${esc(ShijiLibrary.projectPath(state.collectionMeta,n).join(' / '))}"></option>`).join('');
  $('#smart-nav').innerHTML=state.smartCollections.map(s=>nav(s.name,(state.remote?.smartCounts[s.id]??resources.filter(r=>ShijiLibrary.matches(r,s.filters,state.collectionMeta)).length),'sliders-horizontal',`data-action="smart" data-id="${esc(s.id)}"`,state.scope==='smart'&&state.scopeValue===s.id)).join('');
  const isHealth=state.scope==='health';
  $('#library-health').hidden=!isHealth;
  for(const selector of ['.browse-bar','#active-browse-filters','.toolbar','.filter-extension','#tag-filter','#color-filter-state','#bulk-bar','#project-summary','#demo-banner','#resource-grid','#browse-more','#empty-state'])$(selector).hidden=isHealth;
  const healthNav=$('[data-action=health]');healthNav.classList.toggle('active',isHealth);healthNav.setAttribute('aria-current',isHealth?'page':'false');
  if(isHealth){spatial.render({resources:[],scope:'health'});browseWindow.plan([],'health',state.view);$('#page-title').textContent='库检查';$('#page-description').textContent='找到重复附件，检查文件是否完整。';$('#resource-total').textContent='本机附件';$('#result-count').textContent='检查只读；复用操作保留收藏和来源说明';renderHealth();ShijiCards.restoreFocus($('.app-shell'),focus,$('#search'));return;}
  clearTimeout(healthTimer);
  const name={all:'你的灵感宇宙',favorite:'常用收藏',inbox:'待整理',assets:'素材附件',snippets:'代码与提示词',trash:'回收站',category:state.scopeValue,collection:state.scopeValue,smart:state.smartCollections.find(s=>s.id===state.scopeValue)?.name}[state.scope];$('#page-title').textContent=name||'全部资源';
  $('#page-description').textContent=state.scope==='trash'?'删除的收藏与附件都在这里，可以随时恢复。':state.scope==='collection'?'这个项目的参考、素材、代码与提示词，共用一份收藏。':state.scope==='smart'?'自动收集符合筛选条件的资源。':state.scope==='assets'?'图片、音效和视频，连同来源一起留存。':state.scope==='snippets'?'把能复用的代码与提示词留在手边。':'把好用的网站、素材和灵感，留给下一次创作。';
  const categoryButton=(label,count,name,active,attrs)=>`<button class="browse-category ${active?'active':''}" ${attrs} aria-label="${esc(label)}" aria-pressed="${active}"><span class="category-art">${icon(name)}</span><span class="category-caption">${esc(label)}<span class="category-count" aria-hidden="true">${count}</span></span></button>`;
  $('#browse-categories').innerHTML=categoryButton('全部',counts?.all??resources.length,'grid-2x2',!state.filters.category,'data-action="scope" data-scope="all"')+CATEGORIES.filter(c=>(state.remote?state.remote.categoryCounts[c]:resources.some(x=>x.category===c))).map(c=>categoryButton(c,(state.remote?.categoryCounts[c]??resources.filter(x=>x.category===c).length),VISUALS[c][0],state.filters.category===c,`data-action="category" data-value="${esc(c)}"`)).join('');
  const shown=shownItems();
  spatial.render({resources:shown,scope:state.scope});attachImageFallbacks($('#scene-stack'));
  const page=browseWindow.plan(shown,JSON.stringify([state.scope,state.scopeValue,state.sort,ShijiLibrary.canonicalFilters(state.filters)]),state.view);
  const total=state.remote?.page?.total??shown.length;
  $('#resource-total').textContent=`${total} 条资源`;
  $('#result-count').textContent=page.hasMore?`已显示 ${page.visibleCount} 条 · 匹配 ${shown.length} / ${scoped().length} 条资源`:`显示 ${shown.length} / ${scoped().length} 条资源`;
  if(state.remote)$('#result-count').textContent=`已显示 ${shown.length} 条 · 匹配 ${total} 条资源`;
  $('#browse-more').hidden=!(page.hasMore||state.remote?.page?.nextCursor);
  $('#browse-more-button').textContent=`继续浏览（${state.remote?.page?.nextCursor?Math.min(60,total-shown.length):page.nextCount} 条）`;
  const tags=new Map(Object.entries(state.remote?.tagCounts||{}));if(!state.remote)scoped().forEach(r=>r.tags.forEach(t=>tags.set(t,(tags.get(t)||0)+1)));const top=[...tags].sort((a,b)=>b[1]-a[1]).slice(0,12).map(x=>x[0]);state.filters.tags.forEach(t=>{if(!top.includes(t))top.push(t);});
  $('#tag-filter').innerHTML=top.map(t=>`<button class="tag-pill ${state.filters.tags.includes(t)?'active':''}" data-action="tag" data-value="${esc(t)}" aria-pressed="${state.filters.tags.includes(t)}">${esc(t)}</button>`).join('')+(tags.size>12?'<button class="tag-pill" data-action="all-tags">所有标签</button>':'');
  $('#reset-filter').hidden=!Object.keys(ShijiLibrary.canonicalFilters(state.filters)).length;$('#color-filter-state').hidden=!state.filters.color;$('#color-filter-state').innerHTML=state.filters.color?`<button class="tag-pill" data-action="clear-color"><span class="color-dot" style="background:${state.filters.color}"></span>${state.filters.color} 附近的颜色 ${icon('x')}</button>`:'';
  $('#project-summary').innerHTML=state.scope==='smart'?`<button class="text-button" data-action="delete-smart" data-id="${esc(state.scopeValue)}">移除此智能集合</button>`:state.scope==='collection'?`<div class="project-context"><nav aria-label="项目路径">${ShijiLibrary.projectPath(state.collectionMeta,state.scopeValue).map(n=>`<button class="text-button" data-action="collection" data-value="${esc(n)}">${esc(n)}</button>`).join('<span aria-hidden="true">/</span>')}</nav><span>包含下级项目</span><button class="text-button" data-action="manage-projects">项目设置</button></div>`:'';
  smartSummary();
  $('#demo-banner').hidden=true;$('#select-mode').textContent=state.selectMode?'完成选择':'开始选择';$('#bulk-bar').hidden=!state.selectMode;$('#bulk-bar').innerHTML=`<label><input type="checkbox" data-select-all ${(state.remote?state.selected.size>=total&&shown.every(r=>state.selected.has(r.id))&&(shown.length===total||state.selectionAll?.key===remoteKey()&&state.selectionAll?.revision===state.remote.page.revision):shown.length&&shown.every(r=>state.selected.has(r.id)))?'checked':''}> 全选匹配结果（${total} 条）</label><strong>已选 ${state.selected.size} 条</strong>${state.scope==='trash'?'<button class="text-button" data-action="bulk-restore">恢复所选</button>':'<button class="text-button" data-action="bulk-tags">加标签</button><button class="text-button" data-action="bulk-projects">加入项目</button><button class="text-button" data-action="bulk-remove-projects">移出项目</button><button class="text-button" data-action="bulk-organized">标为已整理</button><button class="text-button danger" data-action="bulk-delete">移到回收站</button>'}`;
  for(const v of ['grid','list','board']){$('#'+v+'-view').classList.toggle('active',state.view===v);$('#'+v+'-view').setAttribute('aria-pressed',String(state.view===v));}
  $('#density').value=state.density;$('#preview-mode').value=state.previewMode;$('#gallery-open').disabled=state.remote?!total:!shown.some(r=>ShijiGallery.media(ShijiBoard.galleryResource(r)).length);$('#gallery-open').title=$('#gallery-open').disabled?'添加图片、音频、视频或网页缩略图后可连续预览':'按当前筛选和排序浏览素材';
  $('#resource-grid').className='resource-grid density-'+state.density+(state.previewMode==='fit'?' preview-fit':'')+(state.view==='list'?' list-layout':state.view==='board'?' board-layout':'');
  if(state.view!=='grid')galleryWindow?.setItems([],pageKey());
  if(state.view==='grid'&&galleryWindow)galleryWindow.setItems(page.items,pageKey(),JSON.stringify([state.selectMode,state.filters.collection,state.filters.search]));
  else if(state.view==='board'&&shown.length){$('#resource-grid').innerHTML=page.groups.map(g=>`<section class="board-lane"><h2>${g.label}<span>${g.items.length<g.total?g.items.length+' / ':''}${state.remote?.page?.kindCounts[g.kind]??g.total}</span></h2><div>${g.items.map(card).join('')}</div></section>`).join('');}else ShijiCards.render($('#resource-grid'),page.items.map(r=>({id:r.id,html:card(r)})));
  const conditions=ShijiControls.conditions(state.filters,ShijiLibrary.canonicalFilters);$('#filter-entry').textContent=`筛选 (${conditions.length})`;
  $('#active-browse-filters').hidden=!conditions.length;$('#active-browse-filters').innerHTML=conditions.map(c=>`<button class="filter-chip" data-action="remove-filter" data-key="${esc(c.key)}" data-value="${esc(JSON.stringify(c.value))}" aria-label="移除${esc(c.label)}">${esc(c.label)} ${icon('x')}</button>`).join('');
  if(!galleryWindow?.active()&&typeof markSearchResults==='function')markSearchResults();
  if(!galleryWindow?.active())attachImageFallbacks($('#resource-grid'));resourceBits.render();motion.afterListUpdate([state.scope,state.scopeValue,state.view,state.sort,state.filters.category].join('|'));$('#empty-state').hidden=shown.length>0;
  const hasResources=(state.remote?.counts?.all??resources.length)>0;
  const emptyProject=state.scope==='collection'&&!(state.remote?(state.remote.projectCounts[state.scopeValue]||0):resources.some(r=>ShijiLibrary.matches(r,{collection:state.scopeValue},state.collectionMeta)));
  if(!shown.length)$('#empty-state').innerHTML=`<div class="empty-mark">${icon(state.scope==='trash'?'trash-2':'search')}</div><h2>${state.scope==='trash'?'回收站是空的':emptyProject?'这个项目还没有资源':hasResources?'没有匹配的资源':'从第一个好资源开始'}</h2><p>${state.scope==='trash'?'资源删除后会留在这里，附件也能一起恢复。':emptyProject?'收藏网站或添加素材，默认加入此项目；也可以从全部资源批量加入。':hasResources?'试试其他关键词或标签，也可以清除筛选条件。':'粘贴网址、拖入素材或保存截图，建立自己的开发资源库。'}</p>${state.scope==='trash'?'':`<div class="empty-actions"><button class="primary" data-action="add">收藏资源</button><button class="secondary" data-action="${hasResources?'reset':'import-files'}">${emptyProject?'浏览全部资源':hasResources?'清除筛选':'添加素材'}</button></div>`}`;
  ShijiCards.restoreFocus($('.app-shell'),focus,$('#search'));
  document.dispatchEvent(new CustomEvent('shiji:rendered',{detail:{ms:performance.now()-renderStart,total:shown.length}}));
}
async function browseMore(){
  if(state.remote&&state.remote.page?.nextCursor){await remoteLoad({append:true});return;}
  const ids=new Set(Array.from($('#resource-grid').querySelectorAll('.resource-card'),el=>el.dataset.resourceId));
  browseWindow.more();render();
  const next=Array.from($('#resource-grid').querySelectorAll('.resource-card')).find(el=>!ids.has(el.dataset.resourceId));
  if(next){next.querySelector('.card-preview')?.focus({preventScroll:true});next.scrollIntoView({block:'nearest',behavior:'instant'});}
}
function syncNavigation(){const compact=navMedia.matches,open=$('#sidebar').classList.contains('open');$('#sidebar').inert=compact&&!open;$('#main').inert=compact&&open;$('.mobile-menu').setAttribute('aria-expanded',String(compact&&open));}
function closeMenu(){const focusInside=$('#sidebar').contains(document.activeElement);$('#sidebar').classList.remove('open');$('#sidebar-backdrop').classList.remove('visible');syncNavigation();if(focusInside&&navMedia.matches)$('.mobile-menu').focus();}
function openDrawer(){if($('#drawer').hidden){lastFocus=document.activeElement;const width=document.documentElement.clientWidth;document.body.style.setProperty('--drawer-scrollbar-space',(width?Math.max(0,window.innerWidth-width):0)+'px');}$('#drawer').hidden=false;$('#drawer-backdrop').hidden=false;document.body.classList.add('drawer-open');$('.app-shell').inert=true;}
const formTagEditor=ShijiTags.create($('#tag-editor'),$('#f-tags'),names=>state.formTags=names,message=>{$('#form-error').textContent=message;$('#form-error').hidden=false;});
function closeDrawer(){if(typeof detailLoadRun!=='undefined')detailLoadRun++;if(state.formBusy){toast("正在保存，请稍候。");return false;}if(!quickNoteMayLeave())return false;pausePreviewPlayers($('#drawer'));if(typeof motion!=='undefined')motion.closeDetail();state.metadataRun++;$('#drawer').hidden=true;$('#drawer-backdrop').hidden=true;document.body.classList.remove('drawer-open');document.body.style.removeProperty('--drawer-scrollbar-space');$('.app-shell').inert=false;state.editing=null;state.detail=null;state.pending=[];if(typeof galleryWindow!=='undefined')galleryWindow?.pin('detail');if(lastFocus?.isConnected)lastFocus.focus();else $('#search').focus();}
function setKind(){const kind=$('#f-kind').value;$('#snippet-fields').hidden=!['code','prompt'].includes(kind);$('#f-url').required=kind==='website';$('#metadata-button').disabled=!$('#f-url').value.trim();}
function projectFields(){document.querySelectorAll('[data-project-note]').forEach(el=>state.formProjects[JSON.parse(el.dataset.projectNote)]=el.value);$('#project-notes-fields').innerHTML=split($('#f-projects').value).map(n=>`<label>用于「${esc(n)}」的备注<textarea rows="2" data-project-note="${esc(JSON.stringify(n))}" maxlength="2000" placeholder="在这个项目中怎么使用？">${esc(state.formProjects[n]||'')}</textarea></label>`).join('');}
function renderPending(){$('#pending-files').innerHTML=state.pending.map((p,i)=>`<div class="pending-file"><span>${esc(p.file.name)} <small>${size(p.file.size)}${p.cover?' · 作为封面':''}</small></span><button type="button" class="text-button" data-action="remove-pending" data-index="${i}">移除</button></div>`).join('');}
function queueFiles(files){if(state.formBusy){toast('正在保存，请稍候。');return false;}for(const file of files){if(file.size>64*1024*1024){toast('「'+file.name+'」超过 64 MB。');continue;}state.pending.push({file,cover:file.type.startsWith('image/')});}renderPending();return true;}
function edit(item,prefill={}){
  if(typeof cancelPendingDetail==='function')cancelPendingDetail();
  if(state.remote&&item?._summary){hydratedAction('edit',item);return;}
  if(state.formBusy){toast("正在保存，请稍候。");return;}
  if(!quickNoteMayLeave())return;
  pausePreviewPlayers($('#drawer'));closeMenu();state.detail=null;state.editing=item?.id||null;state.metadataRun++;state.pending=[];state.formBase={...(item||{})};state.formProjects=Object.assign(Object.create(null),item?.projectNotes||{});$('#project-notes-fields').replaceChildren();
  $('#drawer-title').textContent=item?'编辑资源':'收藏资源';$('#drawer-subtitle').textContent='网站、素材和可复用的内容，都可以留在这里。';$('#detail-content').hidden=true;$('#resource-form').hidden=false;$('#resource-form').reset();$('#form-error').hidden=true;
  if(state.remote&&item?.parentId&&!(state.parentOptions||state.resources).some(r=>r.id===item.parentId))state.parentOptions=[{id:item.parentId,title:item._related?.parent?.title||'当前来源资源'},...(state.parentOptions||state.resources)];
  $('#f-category').innerHTML=CATEGORIES.map(c=>`<option>${c}</option>`).join('');$('#f-parentId').innerHTML='<option value="">独立收藏</option>'+(state.parentOptions||state.resources).filter(r=>r.id!==item?.id).map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');
  const defaults={url:'',title:'',kind:'website',category:state.filters.category||'其他',tags:[],projects:state.filters.collection?[state.filters.collection]:[],description:'',notes:'',snippet:'',language:'',author:'',sourceUrl:'',parentId:'',price:'待确认',license:'待确认',thumbnail:'',licenseUrl:'',inbox:true,favorite:false};const values={...defaults,...item,...prefill};
  for(const [key,value] of Object.entries(defaults)){if(key==='tags')continue;const el=$('#f-'+key);if(!el)continue;if(el.type==='checkbox')el.checked=values[key];else el.value=['tags','projects'].includes(key)?values[key].join('，'):values[key];}
  formTagEditor.set(values.tags);
  $('#existing-files').innerHTML=(item?.attachments||[]).map(a=>`<div class="existing-file">${esc(a.name)} <small>${size(a.size)}</small></div>`).join('');$('#metadata-state').textContent='粘贴网址后自动尝试补全。';$('#save-button').textContent=item?'保存修改':'保存资源';renderPending();projectFields();ShijiEdit.start(document,state,split,item);$('#edit-conflict').hidden=true;setKind();openDrawer();$('#f-url').focus();
}
function setEditBusy(busy){state.formBusy=busy;$('.form-body').inert=busy;$('#save-button').disabled=busy;document.querySelectorAll('[data-action^="edit-conflict-"]').forEach(el=>el.disabled=busy);}
function showEditConflict(error){
  state.formConflict={resource:error.resource,conflicts:error.conflicts};
  const panel=$('#edit-conflict');
  $('#edit-conflict-fields').innerHTML=error.conflicts.map(c=>`<section><h4>${esc(c.field==='projectNotes'?'用于「'+c.key+'」的备注':ShijiEdit.labels[c.field]||c.field)}</h4><dl><dt>最新已保存</dt><dd><pre>${esc(ShijiEdit.text(c.current))}</pre></dd><dt>本次提交的修改</dt><dd><pre>${esc(ShijiEdit.text(c.value))}</pre></dd></dl></section>`).join('');
  panel.hidden=false;panel.scrollIntoView({block:'nearest'});panel.focus();
}
async function handleEditConflict(action){
  const conflict=state.formConflict;if(!conflict)return;
  if(action==='edit-conflict-mine'){
    state.formSnapshot=ShijiEdit.rebase(state.formSnapshot,conflict.resource,conflict.conflicts);state.formConflict=null;$('#edit-conflict').hidden=true;$('#resource-form').requestSubmit();return;
  }
  setEditBusy(true);
  try{
    const latest=(await api('/api/resources/'+state.editing)).resource;if(latest.deleted)throw new Error('资源已在回收站，请关闭后恢复资源。');
    const pending=state.pending;setEditBusy(false);edit(latest);state.pending=pending;renderPending();toast('已载入最新资料，待上传附件仍保留。');
  }catch(e){$('#form-error').textContent=e.message;$('#form-error').hidden=false;}
  finally{setEditBusy(false);}
}

async function readMetadata(){const url=$('#f-url').value.trim();if(!url)return;const run=++state.metadataRun;const values={title:$('#f-title').value,description:$('#f-description').value,thumbnail:$('#f-thumbnail').value};$('#metadata-button').disabled=true;$('#metadata-state').textContent='正在读取网页信息…';try{const result=await api('/api/metadata','POST',{url});if(run!==state.metadataRun||$('#drawer').hidden||$('#f-url').value.trim()!==url)return;for(const key of ['title','description','thumbnail']){const el=$('#f-'+key);if(result[key]&&(!el.value||el.value===state.formBase['auto'+key])){el.value=result[key];state.formBase['auto'+key]=result[key];}}if(result.favicon)state.formBase.favicon=result.favicon;$('#metadata-state').textContent=result.message;}catch(e){if(run===state.metadataRun)$('#metadata-state').textContent=e.message+' 也可以直接手动保存。';}finally{if(run===state.metadataRun)$('#metadata-button').disabled=false;}}
async function coloursFromFile(file){if(!file.type.startsWith('image/'))return [];try{const bmp=await createImageBitmap(file);const canvas=document.createElement('canvas');canvas.width=64;canvas.height=64;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(bmp,0,0,64,64);bmp.close();return ShijiLibrary.extractPalette(ctx.getImageData(0,0,64,64).data);}catch{return [];}}
async function upload(rid,file,cover=false,extra={}){if(file.size>64*1024*1024)throw new Error('单个文件最多 64 MB。');const colors=await coloursFromFile(file);const metadata={name:file.name,cover,colors,...extra};const encoded=btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(metadata))));return rawAPI('/api/resources/'+rid+'/attachments',file,{'Content-Type':'application/octet-stream','X-Metadata':encoded});}
async function importAssets(files){await prepareAssets(files);}
function attachmentView(a,r){let media='';if(a.mime.startsWith('image/'))media=`<button class="attachment-image" data-action="image" data-id="${esc(r.id)}" data-file="${esc(a.id)}" aria-label="放大 ${esc(a.name)}"><img src="${fileURL(a)}" alt="${esc(a.name)}" loading="lazy"></button>`;else if(a.mime.startsWith('audio/'))media=`<audio controls preload="metadata" src="${fileURL(a)}">浏览器不支持音频预览。</audio>`;else if(a.mime.startsWith('video/'))media=`<video controls preload="metadata" src="${fileURL(a)}">浏览器不支持视频预览。</video>`;return `<section class="attachment-block">${media}<p class="media-error field-help" role="status" hidden>文件缺失、格式损坏或浏览器不支持预览。可下载原文件打开；缺失文件请从完整备份恢复。</p><div class="attachment-heading"><strong>${esc(a.name)}</strong><span>${size(a.size)}</span></div><p class="attachment-provenance">${esc(a.author||'作者待补充')} · ${esc(a.license||'待确认')}${a.sourceUrl?` · <a href="${esc(a.sourceUrl)}" target="_blank" rel="noopener noreferrer">来源</a>`:''}${a.licenseUrl?` · <a href="${esc(a.licenseUrl)}" target="_blank" rel="noopener noreferrer">许可说明</a>`:''}</p>${!media?'<p class="field-help">此格式暂不支持预览，文件已保存在本机。</p>':''}<div class="attachment-actions">${a.mime.startsWith('audio/')||a.mime.startsWith('video/')?`<button class="text-button" data-action="image" data-id="${esc(r.id)}" data-file="${esc(a.id)}">连续预览</button>`:''}<a class="text-button" href="${fileURL(a)}?download=1" download>${icon('download')}下载原文件</a>${a.mime.startsWith('image/')?`<button class="text-button" data-action="similar" data-id="${esc(r.id)}" data-file="${esc(a.id)}">找相似图片</button>`:''}${!r.deleted?`<button class="text-button" data-action="attachment-info" data-id="${esc(r.id)}" data-file="${esc(a.id)}">来源与授权</button>${a.mime.startsWith('image/')?`<button class="text-button" data-action="cover" data-id="${esc(r.id)}" data-file="${esc(a.id)}">${r.coverId===a.id?'当前封面':'设为封面'}</button><button class="text-button" data-action="extract-colors" data-file="${esc(a.id)}" data-id="${esc(r.id)}">提取颜色</button>`:''}`:''}</div><div class="palette-row">${(a.colors||[]).map(c=>`<button style="background:${c}" data-action="filter-color" data-value="${c}" aria-label="查找 ${c} 附近的颜色" title="${c}"></button>`).join('')}</div></section>`;}
function detail(r){const origin=arguments[1];if(typeof cancelPendingDetail==='function')cancelPendingDetail();if(r&&typeof galleryWindow!=='undefined')galleryWindow?.pin('detail',r.id);if(state.remote&&r?._summary){hydratedAction('detail',r,origin);return;}if(state.formBusy){toast("正在保存，请稍候。");return;}if(!r||!quickNoteMayLeave())return;pausePreviewPlayers($('#drawer'));closeMenu();state.detail=r.id;state.editing=null;$('#drawer-title').textContent=r.title;$('#drawer-subtitle').textContent=`${domain(r.url)||KINDS[r.kind]} · 收藏于 ${date(r.createdAt)}${r.deleted?' · 回收站':''}`;$('#resource-form').hidden=true;$('#detail-content').hidden=false;
  const parent=r._related?.parent||find(r.parentId),children=r._related?.children||state.resources.filter(x=>x.parentId===r.id),history=Object.entries(r.projectNotes||{}).filter(([name,note])=>!r.projects.includes(name)&&note);$('#detail-content').innerHTML=`<div class="detail-body"><div class="detail-preview" style="--tile-bg:${visual(r)[1]};--tile-ink:${visual(r)[2]}">${preview(r)}</div>${r.url?`<a class="detail-domain" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.url)}</a>`:''}<div class="detail-actions">${!r.deleted?`<button class="secondary" data-action="cover-studio" data-id="${esc(r.id)}">封面设计</button>`:''}${r.url?`<a class="secondary" href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">打开资源${icon('external-link')}</a>`:''}${!r.deleted?`<button class="secondary" data-action="favorite" data-id="${esc(r.id)}">${icon('star')}${r.favorite?'已设为常用':'设为常用'}</button><button class="secondary" data-action="assign-project" data-id="${esc(r.id)}">${icon('folder')}加入项目</button><button class="secondary" data-action="assign-tags" data-id="${esc(r.id)}">${icon('tag')}加标签</button>`:''}</div><dl class="detail-grid"><div><dt>资源类型</dt><dd>${esc(r.category)} · ${KINDS[r.kind]}</dd></div><div><dt>链接状态</dt><dd>${r.url?LINK_STATUS[r.linkStatus]:'本地资源'}${r.linkCheckedAt?`<small>${date(r.linkCheckedAt)}</small>`:''}</dd></div><div><dt>价格</dt><dd>${esc(r.price)}</dd></div></dl><section class="detail-block source-license" aria-labelledby="source-license-title"><h3 id="source-license-title">来源与授权</h3><dl><div><dt>作者</dt><dd>${esc(r.author||'待补充')}</dd></div><div><dt>授权</dt><dd><span class="license-label ${r.license==='待确认'?'license-pending':''}">${esc(r.license)}</span></dd></div></dl><div class="source-license-links">${r.sourceUrl||r.url?`<a href="${esc(r.sourceUrl||r.url)}" target="_blank" rel="noopener noreferrer">查看原始来源 ${icon('external-link')}</a>`:'<span class="field-help">来源网址待补充</span>'}${r.licenseUrl?`<a href="${esc(r.licenseUrl)}" target="_blank" rel="noopener noreferrer">查看许可说明 ${icon('external-link')}</a>`:'<span class="field-help">许可说明待补充</span>'}</div></section>${r.linkMessage?`<p class="field-help">${esc(r.linkMessage)}</p>`:''}${r.tags.length?`<div class="detail-block"><h3>标签</h3><div class="detail-tags">${r.tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div></div>`:''}${r.projects.length?`<div class="detail-block"><h3>关联项目</h3>${r.projects.map(n=>`<div class="project-reference"><button class="text-button" data-action="go-project" data-value="${esc(n)}">${icon('folder')}${esc(n)}</button>${!r.deleted?`<button class="text-button project-detach" data-action="remove-project" data-id="${esc(r.id)}" data-value="${esc(JSON.stringify(n))}" aria-label="将此资源移出 ${esc(n)}">移出</button>`:''}${quickNoteSection(r,'project',n,'项目使用备注')}</div>`).join('')}</div>`:''}${history.length?`<details class="detail-block project-note-history"><summary>移出项目的使用备注 · ${history.length}</summary><p class="field-help">备注随资源保留；重新加入原项目后会恢复到关联项目中。</p>${history.map(([name,note])=>`<div class="project-reference"><strong>${esc(ShijiLibrary.projectPath(state.collectionMeta,name).join(' / '))}</strong>${quickNoteSection(r,'project',name,'保留的项目备注')}${!r.deleted&&state.collectionMeta.some(p=>p.name===name)&&!ShijiLibrary.isProjectArchived(state.collectionMeta,name)?`<button class="text-button" data-action="rejoin-project" data-id="${esc(r.id)}" data-value="${esc(JSON.stringify(name))}" aria-label="重新加入 ${esc(name)}">重新加入</button>`:''}</div>`).join('')}</details>`:''}${r.description?`<div class="detail-block"><h3>资源介绍</h3><p>${esc(r.description)}</p></div>`:''}${quickNoteSection(r,'notes','', '收藏理由 / 使用备注')}${r.snippet?`<div class="detail-block"><div class="section-title"><h3>${r.kind==='prompt'?'提示词':'代码片段'}${r.language?' · '+esc(r.language):''}</h3><button class="text-button" data-action="copy-snippet" data-id="${esc(r.id)}">复制内容</button></div><pre class="code-content"><code>${esc(r.snippet)}</code></pre></div>`:''}${parent?`<div class="detail-block"><h3>来源资源</h3><button class="text-button" data-action="detail" data-id="${esc(parent.id)}">${esc(parent.title)}</button></div>`:''}${children.length?`<div class="detail-block"><h3>关联素材与内容</h3>${children.map(c=>`<button class="text-button" data-action="detail" data-id="${esc(c.id)}">${esc(c.title)}</button>`).join('')}</div>`:''}<div class="detail-block"><div class="section-title"><h3>截图与附件 · ${r.attachments.length}</h3>${!r.deleted?`<button class="text-button" data-action="detail-add-files" data-id="${esc(r.id)}">添加附件</button>`:''}</div>${r.attachments.map(a=>attachmentView(a,r)).join('')||'<p class="field-help">可以添加截图、音效、视频或其他文件。</p>'}</div></div><footer class="drawer-footer detail-footer">${r.deleted?`<button class="secondary" data-action="restore" data-id="${esc(r.id)}">恢复资源与附件</button>`:`<button class="text-button danger" data-action="delete" data-id="${esc(r.id)}">${icon('trash-2')}移到回收站</button><div><button class="secondary" data-action="derive" data-id="${esc(r.id)}">收藏具体内容</button><button class="primary" data-action="edit" data-id="${esc(r.id)}">${icon('pencil')}编辑</button></div>`}</footer>`;attachImageFallbacks($('#detail-content'));$('#detail-content').querySelectorAll('.attachment-block img,.attachment-block audio,.attachment-block video').forEach(media=>{const error=()=>{media.closest('.attachment-block').querySelector('.media-error').hidden=false;};media.addEventListener('error',error);if(media.error||(media.tagName==='IMG'&&media.complete&&!media.naturalWidth))error();});openDrawer();$('#drawer').focus();if(state.remote&&state.filters.search)markSearchDetail();if(typeof motion!=='undefined')motion.openDetail({resourceId:r.id,sourceElement:origin?.closest('.space-pane')?.querySelector('.space-pane-preview')||[...$('#resource-grid').querySelectorAll('.resource-card')].find(el=>el.dataset.resourceId===r.id)?.querySelector('.card-preview'),detailElement:$('#detail-content .detail-preview')});}
function manage(title,html){closeMenu();$('#manage-title').textContent=title;$('#manage-content').innerHTML=html;$('#manage-error').hidden=true;if(!$('#manage-dialog').open)$('#manage-dialog').showModal();}
async function copyText(value,message='已复制'){try{await navigator.clipboard.writeText(value);toast(message);}catch{manage('复制内容',`<p>浏览器未允许自动复制，请选择下方内容后复制。</p><textarea class="copy-fallback" readonly>${esc(value)}</textarea>`);$('.copy-fallback').select();}}
async function backups(){const info=await api('/api/backups');manage('备份与恢复',`<p>自动快照只保存数据库和新增附件；完整 ZIP 可手动制作，也会每天制作一次。保留近 24 小时逐时、7 天逐日、4 周逐周的版本。</p><div class="management-actions"><button class="primary" data-action="download-backup">${icon('download')}下载完整备份</button><button class="secondary" data-action="make-backup">立即完整备份</button><button class="text-button" data-action="import">选择 JSON / ZIP 备份</button><a class="text-button" href="/api/export" download>导出条目 JSON</a></div><p class="field-help">恢复按网址合并，保留已有收藏；确认前会显示摘要，恢复前会保存一份完整备份。</p><p class="field-help">完整 ZIP 和展开后的内容各限 16 GB，单个附件最多 64 MB。</p><p id="backup-work-message" role="status" class="field-help">${esc(backupMessage)}</p>${info.warning?`<p class="form-error">${esc(info.warning)}</p>`:''}${info.pending?'<p class="field-help">新修改等待自动快照。</p>':''}<h3>本机备份记录</h3><div class="backup-list">${[...(info.snapshots||[]),...info.backups].sort((a,b)=>b.createdAt.localeCompare(a.createdAt)).map(b=>`<div class="backup-row"><span>${date(b.createdAt)}<small>${b.kind==='snapshot'?'自动快照':'完整 ZIP'} · ${size(b.size)}</small></span><button class="text-button" data-action="restore-backup" data-name="${esc(b.name)}">从此备份恢复</button>${b.kind==='zip'?`<a href="/api/backups/${encodeURIComponent(b.name)}" download aria-label="下载此备份">${icon('download')}</a>`:''}</div>`).join('')||'<p>还没有备份。</p>'}</div>`);setBackupBusy(backupBusy,backupMessage);}
function offerUndo(message,result){ShijiRecovery.undoNotice($('#undo-list'),message,result,async token=>{await api('/api/undo','POST',{token});await reload();toast('已撤销。');},toast);}
async function approveRecovery(preview){
 const n=preview.summary;
 const accepted=await ShijiRecovery.confirm($('#confirm-dialog'),{title:'确认恢复备份',message:`包含 ${n.active} 条收藏、${n.trash} 条回收站资源、${n.attachments} 个附件（${size(n.bytes)}）、${n.collections} 个项目和 ${n.smartCollections} 个智能集合。按网址合并，已有收藏保留；回收站资源按备份状态恢复。`,confirmLabel:'确认恢复'});
 if(!accepted){await api('/api/restore/cancel','POST',{ticket:preview.ticket});backupMessage='已取消恢复，数据未更改。';return false;}
 setBackupBusy(true,'正在恢复已校验的备份，请保持应用运行…');
 const result=await api('/api/restore/confirm','POST',{ticket:preview.ticket,confirm:true});await reload();backupMessage=`已恢复 ${result.restored} 条收藏，保留 ${result.skipped} 条已有记录${result.repairedFiles?`，修复 ${result.repairedFiles} 个附件`:''}。`;toast(backupMessage);return true;
}
async function restoreNamedBackup(name){if(backupBusy)return;setBackupBusy(true,'正在校验本机备份…');try{await approveRecovery(await api('/api/backups/preflight','POST',{name}));}catch(e){backupMessage=e.message;toast(e.message);}finally{setBackupBusy(false,backupMessage);if($('#manage-dialog').open)await backups();}}

function capturePanel(){const origin=location.origin;const code=`javascript:(()=>{const p=new URLSearchParams({url:location.href,title:document.title,selection:getSelection().toString().slice(0,10000)});window.open('${origin}/?'+p,'shiji-save','width=620,height=850')})()`;manage('浏览器采集',`<p>看到好网站时，直接存到拾集的待整理中。</p><h3>收藏小书签</h3><p>把下面按钮拖到浏览器书签栏。在任何网页点击它，即可打开预填网址、标题和选中文字的收藏表单。</p><a class="secondary bookmarklet" id="bookmarklet" href="${esc(code)}">${icon('bookmark')}收藏到拾集</a><h3>Chrome / Edge 扩展</h3><p>支持一键保存页面、选中文字、右键链接 / 图片和当前页截图。资源库需要在本机运行。</p><div class="management-actions"><a class="secondary" href="browser-extension.zip" download>${icon('download')}下载采集扩展</a><button class="primary" data-action="copy-pair">复制配对码</button></div><p class="field-help">解压扩展 → 浏览器扩展管理 → 开启开发者模式 → 加载解压的文件夹。打开扩展，填写本地地址 <code>${esc(origin)}</code>，粘贴配对码后保存设置。</p>`);}
function batchDialog(action){if(!state.selected.size){toast('先选择需要整理的资源。');return;}const isTags=action==='tags';manage(isTags?'批量加标签':'批量加入项目',`<form data-manage-form="batch" data-batch-action="${action}"><p>为所选 ${state.selected.size} 条资源添加${isTags?'标签':'项目'}，已有内容会保留。</p><label>${isTags?'标签':'项目名称'}<input name="values" required maxlength="2500" placeholder="多个名称用逗号分隔"></label><button class="primary">应用到所选资源</button></form>`);}
async function runBatch(action,extra={}){if(!state.selected.size){toast('先选择资源。');return;}if(action==='delete'&&state.selected.size>=20&&!await ShijiRecovery.confirm($('#confirm-dialog'),{title:'移入回收站',message:`将 ${state.selected.size} 条资源移入回收站，附件仍会保留。`,confirmLabel:'移入回收站'}))return;const result=await (state.remote?selectedOperation('batch',{ids:[...state.selected],action,...extra}):api('/api/batch','POST',{ids:[...state.selected],action,...extra}));state.selected.clear();await reload();if(action==='delete')offerUndo(`已将 ${result.changed} 条资源移入回收站`,result);else toast('批量整理已保存。');}
function tagManager(){const tags=(state.remote?[...state.remote.allTags]:[...new Set([...state.resources,...state.trash].flatMap(r=>r.tags))]).sort((a,b)=>a.localeCompare(b,'zh-CN'));manage('标签管理',tags.length?`<p>重命名标签，或合并到已有标签。资源和智能集合会一起更新。</p><form data-manage-form="tags"><label>原标签<select name="from">${tags.map(t=>`<option>${esc(t)}</option>`).join('')}</select></label><label>新名称 / 合并到<input name="to" required maxlength="50" list="all-tags"><datalist id="all-tags">${tags.map(t=>`<option value="${esc(t)}"></option>`).join('')}</datalist></label><button class="primary">保存标签修改</button></form><div class="detail-tags">${tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div>`:'<p>还没有标签。收藏或编辑资源时添加标签，就可以在这里统一管理。</p>');}
function attachmentInfo(a,r){manage('附件来源与授权',`<form data-manage-form="attachment" data-file="${esc(a.id)}" data-id="${esc(r.id)}"><p>${esc(a.name)}</p><label>作者<input name="author" value="${esc(a.author)}" maxlength="200"></label><label>具体来源网址<input name="sourceUrl" value="${esc(a.sourceUrl)}" maxlength="4000"></label><label>授权<select name="license">${['待确认','允许商用','需署名','仅个人使用'].map(l=>`<option ${a.license===l?'selected':''}>${l}</option>`).join('')}</select></label><label>许可说明网址<input name="licenseUrl" value="${esc(a.licenseUrl)}" maxlength="4000"></label><button class="primary">保存附件信息</button></form>`);}
async function extractAttachment(a,r){const response=await fetch(fileURL(a));if(!response.ok)throw new Error('图片文件无法读取。');const blob=await response.blob();const colors=await coloursFromFile(blob);if(!colors.length)throw new Error('浏览器无法解析这张图片。');await api('/api/attachments/'+a.id,'PUT',{colors});await reload();detail(find(r.id));toast('已提取图片主色，点击色块可查找相近素材。');}
async function checkLinks(button){const ids=state.remote?(await api('/api/query/ids','POST',{...(state.selected.size?{scope:'all'}:remoteBody()),linksOnly:true})).ids.filter(id=>!state.selected.size||state.selected.has(id)):(state.selected.size?[...state.selected].map(find):shownItems()).filter(r=>r&&r.url&&!r.deleted).map(r=>r.id);if(!ids.length){toast('当前没有可检查的网址。');return;}const label=button.textContent;button.disabled=true;try{let done=0;for(let i=0;i<ids.length;i+=12){button.textContent=`检查中 ${done} / ${ids.length}`;await api('/api/check-links','POST',{ids:ids.slice(i,i+12)});done+=Math.min(12,ids.length-i);}await reload();toast(`已检查 ${ids.length} 个链接。访问受限或超时会标为暂时无法判断。`);}finally{button.disabled=false;button.textContent=label;}}
document.addEventListener('click',async event=>{
  const el=event.target.closest('[data-action]');if(!el)return;const action=el.dataset.action;const r=el.dataset.id?find(el.dataset.id):null;
  try{
    if(state.formBusy){toast('正在保存，请稍候。');return;}
    if(!action.startsWith('note-')&&['close','detail','edit','derive','delete','restore','go-project','remove-project','rejoin-project','assign-project','assign-tags','detail-add-files','attachment-info','cover','extract-colors','favorite','cover-studio'].includes(action)&&!quickNoteMayLeave())return;
    if(action.startsWith('note-'))await handleQuickNoteAction(action,el);
    else if(action==='close-manage'&&(projectPickerBusy()||tagPickerBusy())){toast('正在保存，请稍候。');return;}
    if(action==='bookmark-intake'||action==='bookmark-page')handleBookmarkAction(action,el);
    else if(action==='preview'&&r)openGallery(r);
    else if(action==='gallery'||action.startsWith('image-'))await galleryAction(action);
    else if(action==='health'||action.startsWith('health-'))await handleHealth(action,el);
    else if(['manage-projects','toggle-project','bulk-links','edit-link-intake'].includes(action))await handleOrganizingAction(action,el);
    else if(action==='edit-conflict-mine'||action==='edit-conflict-latest')await handleEditConflict(action);
    else if(action==='add'){closeMenu();quickCapture.open();}
    else if(action==='scope')selectScope(el.dataset.scope);
    else if(action==='category'||action==='collection')selectScope(action,el.dataset.value);
    else if(action==='smart')selectScope('smart',el.dataset.id);
    else if(action==='advanced-filter')filterPanel();
    else if(action==='edit-smart')filterPanel('edit',el.dataset.id);
    else if(action==='smart-reset')selectScope('smart',state.scopeValue);
    else if(action==='tag'){const t=el.dataset.value;state.filters.tags=state.filters.tags.includes(t)?state.filters.tags.filter(x=>x!==t):[...state.filters.tags,t];render();}
    else if(['grid','list','board'].includes(action)){state.view=action;localStorage.setItem('shiji-view',action);render();}
    else if(action==='detail')detail(r,el);
    else if(action==='discover'){const rows=shownItems();if(rows.length)detail(rows[Math.floor(Math.random()*rows.length)]);else toast('收藏一些资源后再来发现灵感。');}
    else if(action==='search-focus')$('#search').focus();
    else if(action==='cover-studio'&&r){const resource=r._summary?await fullResource(r.id):r;coverStudio?.open(resource);}
    else if(action==='edit')edit(r);
    else if(action==='derive'&&r)edit(null,{parentId:r.id,sourceUrl:r.url,category:r.category,projects:r.projects});
    else if(action==='favorite'&&r){const sourceRect=el.getBoundingClientRect(),adding=!r.favorite;el.disabled=true;await api('/api/resources/'+r.id+'/edit','POST',{changes:{favorite:adding},expected:{favorite:r.favorite}});await reload();if(state.detail===r.id)detail(find(r.id));if(adding)motion.favoriteConfirmed({sourceRect});}
    else if(action==='close')closeDrawer();
    else if(action==='remove-filter'){state.filters=ShijiControls.remove(state.filters,el.dataset.key,JSON.parse(el.dataset.value));syncFilters();render();}
    else if(action==='reset')selectScope('all');
    else if(action==='delete'&&r){await api('/api/resources/'+r.id,'DELETE');closeDrawer();await reload();toast('已移到回收站','撤销',async()=>{await api('/api/resources/'+r.id+'/restore','POST',{});await reload();});}
    else if(action==='restore'&&r){await api('/api/resources/'+r.id+'/restore','POST',{});closeDrawer();await reload();toast('资源与附件已恢复。');}
    else if(action==='browse-more')await browseMore();
    else if(action==='select-mode'){if(typeof invalidateSelection==='function')invalidateSelection();state.selectMode=!state.selectMode;if(!state.selectMode)state.selected.clear();render();}
    else if(action==='bulk-tags')await openTagPicker([...state.selected]);
    else if(action==='assign-tags'&&r)await openTagPicker([r.id]);
    else if(action.startsWith('tag-picker-'))handleTagPickerAction(action,el);
    else if(action==='bulk-projects')await openProjectPicker([...state.selected]);
    else if(action==='bulk-remove-projects')await openProjectPicker([...state.selected],'remove');
    else if(action==='remove-project'&&r)await openProjectPicker([r.id],'remove',JSON.parse(el.dataset.value));
    else if(action==='rejoin-project'&&r)await openProjectPicker([r.id],'add',JSON.parse(el.dataset.value));
    else if(action==='assign-project'&&r)await openProjectPicker([r.id]);
    else if(action.startsWith('project-picker-'))handleProjectPickerAction(action,el);
    else if(action==='bulk-delete')await runBatch('delete');
    else if(action==='bulk-restore')await runBatch('restore');
    else if(action==='bulk-organized')await runBatch('organized');
    else if(action==='tags')tagManager();
    else if(action==='all-tags'){const tags=(state.remote?Object.keys(state.remote.tagCounts):[...new Set(scoped().flatMap(r=>r.tags))]).sort((a,b)=>a.localeCompare(b,'zh-CN'));manage('组合筛选标签',`<form data-manage-form="filter-tags"><p>${state.filters.tagMode==='any'?'资源需要包含至少一个选中的标签。':'资源需要同时包含所有选中的标签。'}</p><div class="all-tag-options">${tags.map(t=>`<label><input type="checkbox" value="${esc(t)}" ${state.filters.tags.includes(t)?'checked':''}>${esc(t)}</label>`).join('')}</div><button class="primary">应用标签筛选</button></form>`);}
    else if(action==='save-smart')filterPanel('create');
    else if(action==='delete-smart'){const result=await api('/api/smart-collections/'+el.dataset.id,'DELETE');selectScope('all');await reload();offerUndo('智能集合已移除，资源仍然保留',result);}
    else if(action==='restore-backup')await restoreNamedBackup(el.dataset.name);
    else if(action==='new-collection'){if($('#manage-dialog').open)$('#manage-dialog').close();$('#collection-parent').innerHTML=projectOptions(state.scope==='collection'?state.scopeValue:'');$('#collection-autoTags').value='';$('#collection-error').hidden=true;closeMenu();$('#collection-dialog').showModal();$('#collection-name').value='';$('#collection-name').focus();}
    else if(action==='cancel-collection')$('#collection-dialog').close();
    else if(action==='go-project'){closeDrawer();selectScope('collection',el.dataset.value);}
    else if(action==='metadata')await readMetadata();
    else if(action==='import-files')assetIntakePanel();
    else if(action==='pick-attachments')$('#attachment-files').click();
    else if(action==='detail-add-files'){edit(r);$('#attachment-files').click();}
    else if(action==='remove-pending'){state.pending.splice(Number(el.dataset.index),1);renderPending();}
    else if(action==='image')openGallery(r,el.dataset.file);
    else if(action==='similar')similarOpen(r,el.dataset.file);
    else if(action.startsWith('similar-'))await similarAction(action,el);
    else if(action==='close-image')$('#image-dialog').close();
    else if(action==='cover'&&r){el.disabled=true;try{await api('/api/resources/'+r.id+'/edit','POST',{changes:{coverId:el.dataset.file},expected:{coverId:r.coverId}});}catch(e){await reload();detail(find(r.id));throw e;}await reload();detail(find(r.id));toast('封面已更新。');}
    else if(action==='attachment-info'&&r)attachmentInfo(r.attachments.find(a=>a.id===el.dataset.file),r);
    else if(action==='extract-colors'&&r){el.disabled=true;await extractAttachment(r.attachments.find(a=>a.id===el.dataset.file),r);}
    else if(action==='copy-snippet'&&r)await copyText(r.snippet);
    else if(action==='color-filter')manage('按颜色查找',`<form data-manage-form="color"><p>查找截图和素材中与指定颜色相近的主色。上传图片时会自动提取主色。</p><label>选择颜色<input type="color" name="color" value="${state.filters.color||'#268bd2'}"></label><button class="primary">查找相近颜色</button></form>`);
    else if(action==='filter-color'){closeDrawer();state.filters.color=el.dataset.value;render();}
    else if(action==='clear-color'){state.filters.color='';render();}
    else if(action==='check-links')await checkLinks(el);
    else if(action==='backups')await backups();
    else if(action==='website-previews')await previews();
    else if(action==='preview-toggle'){const info=await api('/api/website-previews');await api('/api/website-previews','POST',!info.enabled?{enabled:true,paused:false}:{paused:!info.paused});await previews();}
    else if(action==='preview-off'){await api('/api/website-previews','POST',{enabled:false});await previews();}
    else if(action==='preview-retry'){await api('/api/website-previews','POST',{retry:true});await previews();}
    else if(action==='make-backup'||action==='download-backup')await makeBackup(action==='download-backup');
    else if(action==='import')$('#import-file').click();
    else if(action==='capture')capturePanel();
    else if(action==='copy-pair'){const result=await api('/api/pairing');await copyText(result.token,'配对码已复制，请粘贴到采集扩展。');}
    else if(action==='close-manage')$('#manage-dialog').close();
    else if(action==='help')$('#help-dialog').showModal();
    else if(action==='close-help')$('#help-dialog').close();
    else if(action==='menu'){$('#sidebar').classList.toggle('open');$('#sidebar-backdrop').classList.toggle('visible');syncNavigation();if($('#sidebar').classList.contains('open'))$('.sidebar-close').focus();else $('.mobile-menu').focus();}
    else if(action==='dismiss-toast')$('#toast').hidden=true;
    else if(action==='retry')await reload();
  }catch(e){if($('#manage-dialog').open){$('#manage-error').textContent=e.message;$('#manage-error').hidden=false;}else toast(e.message);}finally{if(el.isConnected&&!action.startsWith('image-'))el.disabled=false;}
});
$('#resource-form').addEventListener('submit',async event=>{
  event.preventDefault();if(state.formBusy)return;if(!formTagEditor.commit())return;
  setEditBusy(true);state.metadataRun++;const button=$('#save-button');button.textContent='保存中…';$('#form-error').hidden=true;projectFields();
  const raw=ShijiEdit.read(document,state,split);let saved=false,closed=false;
  try{
    const rid=state.editing;
    const result=await api(rid?'/api/resources/'+rid+'/edit':'/api/resources','POST',rid?ShijiEdit.diff(raw,state.formInitial,state.formSnapshot):raw);
    saved=true;state.editing=result.resource.id;state.formBase=result.resource;state.formSnapshot=ShijiEdit.clone(result.resource);state.formInitial=ShijiEdit.clone(raw);state.formConflict=null;$('#edit-conflict').hidden=true;
    let reusedAttachments=0;
    for(const pending of [...state.pending]){button.textContent='保存附件…';const current=result.resource;const attached=await upload(current.id,pending.file,pending.cover,{sourceUrl:current.sourceUrl||current.url});if(attached.reused)reusedAttachments++;if(pending.cover&&attached.attachment.mime.startsWith('image/'))state.formBase.coverId=attached.attachment.id;state.pending.splice(state.pending.indexOf(pending),1);renderPending();}
    let coverWarning='';const current=result.resource;
    if(current.thumbnail&&!state.formBase.coverId&&!current.attachments.some(a=>a.mime.startsWith('image/'))){try{await api('/api/remote-cover','POST',{id:current.id,url:current.thumbnail});}catch{coverWarning='；远程封面未缓存，可稍后添加截图。';}}
    setEditBusy(false);closeDrawer();closed=true;
    if(state.scope==='trash'||state.scope==='smart')selectScope('all');else{state.filters.tags=[];state.filters.search='';syncFilters();}
    await reload();if(!rid&&typeof motion!=='undefined')motion.captureConfirmed({resourceId:result.resource.id});toast('收藏与附件已保存'+(reusedAttachments?`，${reusedAttachments} 个相同附件已复用`:'')+coverWarning);
  }catch(e){
    if(closed){toast('内容已保存，但列表刷新失败。请刷新页面查看。');return;}
    await reload().catch(()=>{});
    setEditBusy(false);
    if(e.status===409&&e.resource&&Array.isArray(e.conflicts))showEditConflict(e);
    else{$('#form-error').textContent=e.message+(saved?' 资源资料已保存；未完成的附件仍可重试。':' 草稿已保留，可以继续修改或重试。');$('#form-error').hidden=false;}
  }finally{setEditBusy(false);button.textContent=state.editing?'保存修改':'保存资源';setKind();}
});
window.addEventListener('beforeunload',event=>{if(state.formBusy||(typeof quickCapture!=='undefined'&&quickCapture.isBusy())){event.preventDefault();event.returnValue='';}});

$('#f-url').addEventListener('input',()=>setKind());$('#f-url').addEventListener('blur',()=>{if($('#f-url').value.trim())readMetadata();});$('#f-kind').addEventListener('change',setKind);$('#f-projects').addEventListener('blur',projectFields);
$('#collection-form').addEventListener('submit',async event=>{event.preventDefault();const button=event.submitter;button.disabled=true;try{const name=$('#collection-name').value.trim();await api('/api/collections','POST',{name,parent:$('#collection-parent').value,autoTags:split($('#collection-autoTags').value)});await reload();$('#collection-dialog').close();selectScope('collection',name);toast('项目已创建。');}catch(e){$('#collection-error').textContent=e.message;$('#collection-error').hidden=false;}finally{button.disabled=false;}});
$('#manage-dialog').addEventListener('submit',async event=>{const form=event.target.closest('[data-manage-form]');if(!form)return;event.preventDefault();const button=event.submitter;button.disabled=true;$('#manage-error').hidden=true;try{const data=Object.fromEntries(new FormData(form)),mode=form.dataset.manageForm;
  if(await handleTagPickerForm(form,mode))return;
  if(await handleProjectPickerForm(form,mode))return;
  if(await handleAssetForm(form,mode))return;
  if(await handleFilterForm(form,mode,event.submitter))return;
  if(await handleBookmarkForm(form,mode))return;
  if(await handleOrganizingForm(form,mode))return;
  if(mode==='filter-tags')state.filters.tags=[...form.querySelectorAll('input:checked')].map(el=>el.value);
  else if(mode==='tags')await api('/api/tags','POST',data);
  else if(mode==='batch')await runBatch(form.dataset.batchAction,{[form.dataset.batchAction]:split(data.values)});
  else if(mode==='color')state.filters.color=data.color;
  else if(mode==='attachment')await api('/api/attachments/'+form.dataset.file,'PUT',data);
  $('#manage-dialog').close();await reload();if(mode==='attachment'&&state.detail)detail(find(state.detail));toast(mode==='color'?'已按相近颜色筛选。':'修改已保存。');
}catch(e){$('#manage-error').textContent=e.message;$('#manage-error').hidden=false;}finally{button.disabled=false;}});
$('#asset-files').addEventListener('change',async event=>{const files=[...event.target.files];event.target.value='';await importAssets(files);});$('#attachment-files').addEventListener('change',event=>{queueFiles([...event.target.files]);event.target.value='';});
$('#attachment-drop').addEventListener('click',()=>$('#attachment-files').click());$('#attachment-drop').addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();$('#attachment-files').click();}});
$('#import-file').addEventListener('change',async event=>{
  const file=event.target.files[0];event.target.value='';if(!file)return;
  if(backupBusy){toast('当前备份操作仍在进行，请等完成提示后重试。');return;}
  try{
    if(file.name.toLowerCase().endsWith('.zip')){
      if(file.size>16*1024*1024*1024)throw new Error('完整备份超过 16 GB。');
      setBackupBusy(true,'正在上传并预检完整备份，稍后显示摘要…');
      await approveRecovery(await rawAPI('/api/restore/preflight',file,{'Content-Type':'application/zip'}));
    }else{
      if(file.size>12*1024*1024)throw new Error('JSON 文件超过 12 MB。');
      setBackupBusy(true,'正在校验并合并 JSON 条目…');
      const result=await api('/api/import','POST',JSON.parse(await file.text()));await reload();toast(`已导入 ${result.added} 条，跳过 ${result.skipped} 条重复记录。`);
    }
    if(!file.name.toLowerCase().endsWith('.zip'))backupMessage='恢复已完成。';
  }catch(e){backupMessage=e instanceof SyntaxError?'不是有效的 JSON 备份。':e.message;toast(backupMessage);}
  finally{setBackupBusy(false,backupMessage);if($('#manage-dialog').open&&$('#backup-work-message'))await backups().catch(e=>toast(e.message));}
});
for(const [id,key] of [['search','search'],['price-filter','price'],['license-filter','license'],['kind-filter','kind'],['status-filter','linkStatus']])$('#'+id).addEventListener(id==='search'?'input':'change',e=>{const value=e.target.value;if(id==='search'&&state.scope==='health')selectScope('all');state.filters[key]=value;if(id==='search'){$('#search').value=value;if(state.remote){state.sort=value?'relevance':'new';$('#sort').value=state.sort;}}render();});
$('#preview-mode').addEventListener('change',e=>{state.previewMode=e.target.value==='fit'?'fit':'frame';ShijiBits.savePreviewMode(localStorage,state.previewMode);render();});
$('#density').addEventListener('change',e=>{state.density=e.target.value==='compact'?'compact':'comfortable';localStorage.setItem('shiji-density',state.density);render();});
$('#sort').addEventListener('change',e=>{state.sort=e.target.value;render();});
document.addEventListener('change',event=>{const el=event.target;if(el.dataset.select){if(typeof invalidateSelection==='function')invalidateSelection();if(state.remote&&state.selected.size&&state.selectionRevision!==state.remote.page.revision){el.checked=false;toast('资源已变化，请先结束选择，再重新选择。');return;}state.selectionAll=null;if(el.checked){state.selected.add(el.dataset.select);if(state.remote)state.selectionRevision=state.remote.page.revision;}else state.selected.delete(el.dataset.select);render();}if(el.hasAttribute('data-select-all')){if(state.remote){selectMatching(el.checked).catch(e=>toast(e.message));return;}if(el.checked)shownItems().forEach(r=>state.selected.add(r.id));else shownItems().forEach(r=>state.selected.delete(r.id));render();}});
document.addEventListener('paste',event=>{const files=[...(event.clipboardData?.files||[])].filter(f=>f.type.startsWith('image/'));if(!files.length||document.querySelector('dialog[open]'))return;event.preventDefault();if(state.formBusy){toast('正在保存，请稍候。');return;}if(!quickNoteMayLeave())return;if($('#drawer').hidden||$('#resource-form').hidden)edit(null,{kind:'file',category:'美术素材',title:'截图 '+new Date().toLocaleString('zh-CN')});queueFiles(files);toast('截图已加入，保存收藏后会存到本机。');});
document.addEventListener('dragenter',event=>{if([...event.dataTransfer.types].includes('Files')){event.preventDefault();dragDepth++;$('#page-drop').hidden=false;}});document.addEventListener('dragover',event=>{if([...event.dataTransfer.types].includes('Files'))event.preventDefault();});document.addEventListener('dragleave',()=>{dragDepth--;if(dragDepth<=0){dragDepth=0;$('#page-drop').hidden=true;}});
document.addEventListener('drop',async event=>{const files=[...event.dataTransfer.files];dragDepth=0;$('#page-drop').hidden=true;if(!files.length)return;event.preventDefault();if(state.formBusy){toast('正在保存，请稍候。');return;}if(!quickNoteMayLeave())return;if(document.querySelector('dialog[open]'))return;if($('#drawer').hidden)await importAssets(files);else{if($('#resource-form').hidden)edit(find(state.detail));queueFiles(files);}});
$('#drawer-backdrop').addEventListener('click',closeDrawer);$('#sidebar-backdrop').addEventListener('click',closeMenu);
const browseControls=ShijiControls.bind(document);
document.addEventListener('keydown',event=>{if(event.defaultPrevented)return;if(imageKeys(event)||quickPreviewKeys(event))return;if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){event.preventDefault();if(document.querySelector('dialog[open]'))return;if(state.formBusy){toast('正在保存，请稍候。');return;}if(!quickNoteMayLeave())return;if(!$('#drawer').hidden)closeDrawer();if(!$('#manage-dialog').open)$('#search').focus();}if(event.key==='Escape'){if(!document.querySelector('dialog[open]')){if(!$('#drawer').hidden)closeDrawer();else if(typeof cancelPendingDetail==='function')cancelPendingDetail();}closeMenu();}if(event.key.toLowerCase()==='n'&&!event.metaKey&&!event.ctrlKey&&!event.altKey&&!event.target.closest('input,textarea,select,dialog')&&$('#drawer').hidden){event.preventDefault();quickCapture.open();}if(event.key==='Tab'&&!$('#drawer').hidden&&!document.querySelector('dialog[open]')){const list=[...$('#drawer').querySelectorAll('button,input,select,textarea,a[href],summary,[tabindex="0"]')].filter(el=>!el.disabled&&el.getClientRects().length),first=list[0],last=list[list.length-1];if(event.shiftKey&&(document.activeElement===first||document.activeElement===$('#drawer'))){event.preventDefault();last?.focus();}else if(!event.shiftKey&&(document.activeElement===last||document.activeElement===$('#drawer'))){event.preventDefault();first?.focus();}}});
const navMedia=matchMedia('(max-width:880px)');navMedia.addEventListener('change',()=>closeMenu());syncNavigation();
initGallery();initSimilar();initQuickNotes();
reload().then(()=>{const params=new URLSearchParams(location.search);if(params.get('url')){edit(null,{url:params.get('url'),title:params.get('title')||'',notes:params.get('selection')||''});history.replaceState({},'',location.pathname);readMetadata();}}).catch(e=>{$('#empty-state').hidden=false;$('#empty-state').innerHTML=`<h2>暂时无法打开资源库</h2><p>${esc(e.message)}</p><button class="primary" data-action="retry">重试</button>`;toast(e.message);});

function setBackupBusy(busy,message=''){
  backupBusy=busy;backupMessage=message;
  document.querySelectorAll('[data-action="make-backup"],[data-action="download-backup"],[data-action="import"],[data-action="restore-backup"]').forEach(el=>el.disabled=busy);
  if($('#backup-work-message'))$('#backup-work-message').textContent=message;
}
async function makeBackup(download=false){
  if(backupBusy){toast('当前备份操作仍在进行，请等完成提示后重试。');return;}
  setBackupBusy(true,'正在校验附件并制作完整备份，请保持应用运行…');
  try{
    const result=await api('/api/backups','POST',{});
    if(download){const link=document.createElement('a');link.href='/api/backups/'+encodeURIComponent(result.name);link.download=result.name;document.body.append(link);link.click();link.remove();}
    backupMessage=download?'完整备份已制作，下载已交给浏览器。':'完整备份已保存到本机。';toast(backupMessage);
  }catch(e){backupMessage=e.message;toast(e.message);}
  finally{setBackupBusy(false,backupMessage);if($('#manage-dialog').open&&$('#backup-work-message'))await backups().catch(e=>toast(e.message));}
}

// Desktop commands reuse the same guarded actions as the web UI.
window.ShijiDesktop={command:async({name,value=''})=>{
 if(name==='search'){if(state.formBusy||!$('#drawer').hidden||document.querySelector('dialog[open]'))return;$('#search').value=value;$('#search').dispatchEvent(new Event('input',{bubbles:true}));return;}
 if(name==='refresh'){if(!$('#drawer').hidden||document.querySelector('dialog[open]')||state.formBusy)return;await reload();return;}
 if(['add','import-files'].includes(name))if(state.formBusy||document.querySelector('dialog[open]'))return;document.querySelector('.topbar-actions [data-action="'+name+'"]').click();
}};
if(window.ShijiNative||new URLSearchParams(location.search).get('desktop')==='1')document.documentElement.classList.add('native-app');
const desktopSync=ShijiDesktopSync.create({
 busy:()=>!libraryReady||document.hidden||!$('#drawer').hidden||!!document.querySelector('dialog[open]')||state.formBusy,
 load:async signal=>{const response=await fetch(state.remote?'/api/library':'/api/resources',{signal});if(!response.ok)throw new Error('刷新失败');return response.json();},
 apply:async data=>{if(state.remote){if(data.queryVersion!==1)return;if(data.revision!==state.remote.revision)await remoteReload();else{state.remote.search=data.search;queryBusy(false);}return;}const trash=await api('/api/trash');if(!$('#drawer').hidden||document.querySelector('dialog[open]'))throw new Error('保留当前编辑');Object.assign(state,{resources:data.resources,collections:data.collections,collectionMeta:data.collectionMeta||[],smartCollections:data.smartCollections||[],trash:trash.resources});state.selected=new Set([...state.selected].filter(id=>find(id)));render();}
});
window.addEventListener('pagehide',()=>{coverStudio?.destroy();desktopSync.destroy();galleryWindow?.destroy();resourceBits.destroy();categoryDock.destroy();spatial.destroy();quickCapture.destroy();captureTasks.destroy();},{once:true});

$('#manage-dialog').addEventListener('input',event=>{if(event.target.id==='tag-picker-search')searchTagPicker(event.target.value);});
$('#manage-dialog').addEventListener('change',event=>{if(event.target.matches('[data-tag-choice]'))chooseTagPicker(JSON.parse(event.target.value),event.target.checked);});
$('#manage-dialog').addEventListener('cancel',event=>{if(tagPickerBusy())event.preventDefault();});

$('#manage-dialog').addEventListener('input',event=>{if(event.target.id==='project-picker-search')searchProjectPicker(event.target.value);});
$('#manage-dialog').addEventListener('change',event=>{if(event.target.matches('[data-project-choice]'))chooseProjectPicker(JSON.parse(event.target.value),event.target.checked);});
$('#manage-dialog').addEventListener('cancel',event=>{if(projectPickerBusy())event.preventDefault();});

let previewPoll=null,previewCompleted=null;
function previewStatusText(info){return `${ShijiPreviewUI.status(info)} · 已补全 ${info.completed} · 待处理 ${info.pending} · 失败 ${info.failed}`;}
function watchPreviews(info){
 if(previewPoll){clearInterval(previewPoll);previewPoll=null;}
 if(!info.enabled||info.paused)return;
 previewPoll=setInterval(async()=>{try{const current=await api('/api/website-previews');if($('#preview-job-status'))$('#preview-job-status').textContent=previewStatusText(current);if(previewCompleted!==null&&current.completed!==previewCompleted)await reload();previewCompleted=current.completed;if(!current.enabled||current.paused){clearInterval(previewPoll);previewPoll=null;}}catch{}},5000);
}
async function previews(){const info=await api('/api/website-previews');previewCompleted=info.completed;manage('网站预览补全',`<p>为还没有预览图的网站保存本地封面。优先读取网页的 og:image；读取失败时使用本机 Chrome 截图。失败不会影响收藏。</p><p class="field-help">默认关闭。开启后一次处理一个网站，两次至少间隔 ${info.interval} 秒；截图使用独立的临时浏览器配置，只读取公网地址。</p><p id="preview-job-status" role="status">${esc(previewStatusText(info))}</p><div class="management-actions"><button class="primary" data-action="preview-toggle">${ShijiPreviewUI.button(info)}</button>${info.enabled?'<button class="secondary" data-action="preview-off">关闭自动补全</button>':''}${info.failed?'<button class="text-button" data-action="preview-retry">重试失败项</button>':''}</div><p class="field-help">${info.chromeAvailable?'已找到本机 Chrome。':'未找到本机 Chrome；仍会尝试网页预览图，也可手动上传截图。'} 已有预览网址或本地封面会保留。暂停时，正在读取的结果也不会写入。</p>${info.failures.length?`<details class="preview-failures"><summary>最近失败的 ${info.failures.length} 条</summary>${info.failures.map(f=>`<p><strong>${esc(f.title)}</strong><br>${esc(f.message)}</p>`).join('')}</details>`:''}`);watchPreviews(info);}
api('/api/website-previews').then(info=>{previewCompleted=info.completed;watchPreviews(info);}).catch(()=>{});

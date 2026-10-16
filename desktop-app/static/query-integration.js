/* Progressive migration of the existing V5 state, rendering and business actions. */
let queryClient=null,detailLoadRun=0,detailLoadKey=null,selectionRun=0;
function invalidateSelection(){selectionRun++;state.selectionAll=null;}
const detailCache=new Map();
function remoteBody(){return {scope:state.scope,scopeValue:state.scopeValue,filters:JSON.parse(JSON.stringify(state.filters)),sort:state.sort,limit:60};}
function remoteKey(){return JSON.stringify(remoteBody());}
function queryBusy(value){
 const grid=$('#resource-grid');grid.setAttribute('aria-busy',String(value));grid.inert=Boolean(value&&state.remote?.key!==remoteKey());
 const status=$('#search-status');if(status){const indexing=state.remote?.search?.indexing;status.textContent=value?'正在搜索…':indexing?`正在建立全文索引（${state.remote.search.pending} 条待处理）· 当前仍可完整检索`:'';status.hidden=!value&&!indexing;}
}
function querySetup(){
 if(queryClient)return;
 queryClient=ShijiQuery.create({request:(body,signal)=>api('/api/query','POST',body,signal),busy:queryBusy,apply:(result,body,append)=>{
  const requestKey=JSON.stringify({scope:body.scope,scopeValue:body.scopeValue,filters:body.filters,sort:body.sort,limit:body.limit});
  if(requestKey!==remoteKey()||state.scope==='health')return;
  const old=body.scope==='trash'?state.trash:state.resources,seen=new Set(old.map(r=>r.id));
  const rows=append?[...old,...result.resources.filter(r=>!seen.has(r.id))]:result.resources;
  if(body.scope==='trash')state.trash=rows;else state.resources=rows;
  Object.assign(state.remote,{page:result,key:requestKey,loadingKey:null});detailCache.clear();
  if(body.filters.search)ShijiQuery.remember(localStorage,body.filters.search);
  if(append)browseWindow.more();render();
 }});
}
async function remoteLoad({append=false,delay=0}={}){
 querySetup();const body=remoteBody(),key=remoteKey();
 state.remote.loadingKey=key;
 if(append){if(!state.remote.page?.nextCursor)return null;body.cursor=state.remote.page.nextCursor;}
 try{return await queryClient.load(body,{append,delay});}
 catch(e){
  state.remote.loadingKey=null;
  if(e.status===409&&append){toast('资源库已变化，已从第一页重新加载。');return remoteLoad();}
  // Keep the last usable page, but label it explicitly and never send its selection as new results.
  const status=$('#search-status');if(status){status.hidden=false;status.textContent=e.message+' ';const retry=document.createElement('button');retry.className='text-button';retry.textContent='重试搜索';retry.dataset.action='query-retry';status.append(retry);}throw e;
 }
}
function queryRenderNeeded(){
 if(!state.remote)return false;
 const key=remoteKey();
 if(detailLoadKey!==null&&detailLoadKey!==key)cancelPendingDetail();
 if(state.scope==='health'){queryClient?.cancel();state.remote.loadingKey=null;queryBusy(false);return false;}
 if(state.selectionAll&&state.selectionAll.key!==key){state.selected.clear();invalidateSelection();}
 if(state.remote.loadingKey&&state.remote.loadingKey!==key){queryClient?.cancel();state.remote.loadingKey=null;queryBusy(false);}
 if(state.remote.key===key)return false;
 if(state.remote.loadingKey!==key)remoteLoad({delay:document.activeElement===$('#search')?120:0}).catch(e=>toast(e.message));
 return true;
}
async function remoteReload(){
 const meta=await api('/api/library');
 if(meta.queryVersion!==1)throw new Error('服务查询版本不兼容，请重新启动应用。');
 state.remote={...state.remote,...meta};Object.assign(state,{collections:meta.collections,collectionMeta:meta.collectionMeta,smartCollections:meta.smartCollections});
 if(state.scope==='health'){render();await refreshHealth();return;}
 return remoteLoad();
}
async function fullResource(id,valid=()=>true){
 const {resource,parent,children}=await api('/api/resources/'+encodeURIComponent(id));
 if(!valid())return null;
 resource._related={parent,children};
 detailCache.set(id,resource);while(detailCache.size>200)detailCache.delete(detailCache.keys().next().value);
 for(const ref of [parent,...(children||[])].filter(Boolean))if(!detailCache.has(ref.id))detailCache.set(ref.id,{...ref,_summary:true});
 for(const key of ['resources','trash'])state[key]=state[key].map(r=>r.id===id?resource:r);
 return resource;
}
function cancelPendingDetail(){detailLoadRun++;detailLoadKey=null;if(typeof galleryWindow!=='undefined')galleryWindow?.pin('detail');}
async function hydratedAction(kind,item,origin){
 const run=++detailLoadRun,key=remoteKey(),revision=state.remote?.page?.revision;detailLoadKey=key;
 const valid=()=>run===detailLoadRun&&key===remoteKey()&&revision===state.remote?.page?.revision;
 try{const resource=await fullResource(item.id,valid);if(!resource||!valid()){if(run===detailLoadRun)cancelPendingDetail();return;}
  if(kind==='edit'){await loadParentOptions(resource.parentId);if(!valid()){if(run===detailLoadRun)cancelPendingDetail();return;}edit(resource);}else detail(resource,origin);
 }catch(e){if(valid()){cancelPendingDetail();toast(e.message);}else if(run===detailLoadRun)cancelPendingDetail();}
}
async function selectMatching(checked){
 const run=++selectionRun,snapshot=remoteKey(),result=await api('/api/query/ids','POST',remoteBody());
 if(run!==selectionRun||snapshot!==remoteKey())return;
 if(result.revision!==state.remote.page.revision){await remoteReload();throw new Error('资源已变化，请确认新的匹配范围后再全选。');}
 if(state.selected.size&&state.selectionRevision!==result.revision)throw new Error('资源已变化，请先结束选择，再重新选择。');
 if(checked){state.selectionAll={key:snapshot,revision:result.revision};result.ids.forEach(id=>state.selected.add(id));state.selectionRevision=result.revision;}
 else {result.ids.forEach(id=>state.selected.delete(id));state.selectionAll=null;}
 render();
}
async function selectedOperation(operation,body,revision=state.selectionRevision??state.remote?.page?.revision){
 if(!state.remote)return api(operation==='batch'?'/api/batch':operation==='tags'?'/api/tags/assign':operation==='projects'?'/api/projects/assign':'/api/projects/remove','POST',body);
 return api('/api/query/batch','POST',{operation,body,revision});
}
async function organizationData(ids){
 if(!state.remote)return api('/api/resources');
 return api('/api/query/organization','POST',{ids,revision:state.selectionRevision??state.remote.page.revision});
}
function markSearchResults(){
 if(!state.remote)return;
 const records=new Map(shownItems().map(r=>[r.id,r]));
 for(const card of $('#resource-grid').querySelectorAll('.resource-card')){
  const r=records.get(card.dataset.resourceId);if(!r)continue;
  card.querySelectorAll('.art-copy,.art-code-name,.card-title').forEach(el=>{
   if(state.filters.search)ShijiQuery.mark(el,r._highlights?.title);
   else if(el.querySelector('mark'))ShijiQuery.mark(el,[]);
  });
 }
}
function recentSearches(){
 const root=$('#search-history');if(!root)return;root.replaceChildren();
 if(!state.remote||$('#search').value.trim())return;
 for(const value of ShijiQuery.recent(localStorage)){
  const button=document.createElement('button');button.type='button';button.className='text-button';button.textContent=value;
  button.addEventListener('click',()=>{$('#search').value=value;$('#search').dispatchEvent(new Event('input',{bubbles:true}));$('#search').focus();root.hidden=true;});root.append(button);
 }
 root.hidden=!root.childElementCount;
}
document.addEventListener('click',event=>{
 if(event.target.closest('[data-action="query-retry"]'))remoteLoad().catch(e=>toast(e.message));
 if(!event.target.closest('.search-field,#search-history')){const root=$('#search-history');if(root)root.hidden=true;}
});
document.addEventListener('focusin',event=>{if(event.target.id==='search')recentSearches();});
function firstQueryCard(){
 const first=shownItems()[0];
 const node=first&&typeof galleryWindow!=='undefined'?galleryWindow?.ensure(first.id):null;
 return node?.querySelector('.card-preview')||$('#resource-grid .card-preview');
}
document.addEventListener('keydown',event=>{
 if(event.target.id!=='search'||!state.remote||event.isComposing)return;
 if(event.key==='Enter'){
  event.preventDefault();ShijiQuery.remember(localStorage,event.target.value);
  if(!$('#resource-grid').inert){firstQueryCard()?.click();}
 }else if(event.key==='ArrowDown'){
  event.preventDefault();if(!$('#resource-grid').inert)firstQueryCard()?.focus();
 }else if(event.key==='Escape'){
  event.preventDefault();if(event.target.value){event.target.value='';event.target.dispatchEvent(new Event('input',{bubbles:true}));}else event.target.blur();
  const root=$('#search-history');if(root)root.hidden=true;
 }
});
window.addEventListener('pagehide',()=>{queryClient?.destroy();detailLoadRun++;detailCache.clear();},{once:true});

async function loadParentOptions(selected=''){
 const query=$('#parent-search')?.value||'';
 const page=await api('/api/query','POST',{filters:{search:query},sort:'name',limit:100});
 state.parentOptions=page.resources;
 if(selected&&!state.parentOptions.some(r=>r.id===selected)){
  try{const {resource}=await api('/api/resources/'+encodeURIComponent(selected));state.parentOptions.unshift(resource);}catch{}
 }
}
let parentSearchTimer=null,parentSearchRun=0;
document.addEventListener('input',event=>{
 if(event.target.id!=='parent-search'||!state.remote)return;
 const run=++parentSearchRun;clearTimeout(parentSearchTimer);parentSearchTimer=setTimeout(async()=>{
  try{const selected=$('#f-parentId').value;await loadParentOptions(selected);if(run!==parentSearchRun||!state.editing&&$('#drawer').hidden)return;
   $('#f-parentId').innerHTML='<option value="">独立收藏</option>'+state.parentOptions.filter(r=>r.id!==state.editing).map(r=>`<option value="${esc(r.id)}">${esc(r.title)}</option>`).join('');$('#f-parentId').value=selected;
  }catch(e){toast(e.message);}
 },150);
});

async function remoteGallery(owner,key){
 const body={...remoteBody(),mediaOnly:true,projection:'media'},queryKey=remoteKey();
 if(owner)body.anchor=owner.id;
 const page=await api('/api/query','POST',body);
 if(queryKey!==remoteKey())return;
 const resources=page.resources;
 if(owner)owner=resources.find(r=>r.id===owner.id);
 const snapshot=ShijiGallery.mediaQueue(resources.map(ShijiBoard.galleryResource),owner?ShijiBoard.galleryResource(owner):owner,key);
 snapshot.remoteCursor=page.nextCursor;snapshot.remotePrevious=page.previousCursor;snapshot.remoteQuery=body;
 if(!snapshot.items.length){toast('当前结果没有可预览素材。');return;}
 openGallerySnapshot(snapshot);
}

async function remoteGalleryMore(open=true){
 const run=galleryState.run,cursor=galleryState.remoteCursor,body=galleryState.remoteQuery;if(!cursor)return;
 $('#image-next').disabled=true;
 try{
  let items=[],next=cursor;
  // Skip pages without media; retain the same revision-bound cursor and all filters.
  while(next&&!items.length){const page=await api('/api/query','POST',{...body,cursor:next,projection:'media'});next=page.nextCursor;items=ShijiGallery.mediaQueue(page.resources.map(ShijiBoard.galleryResource)).items;}
  if(open&&(run!==galleryState.run||!$('#image-dialog').open))return;
  const seen=new Set(galleryState.items.map(r=>r.resourceId+'|'+r.key));items=items.filter(r=>!seen.has(r.resourceId+'|'+r.key));
  const first=galleryState.items.length;galleryState.items.push(...items);galleryState.remoteCursor=next;
  if(open&&items.length)moveGallery(first);
  else if(!open&&items.length)openGallerySnapshot({...galleryState,index:first});
  else if(!open)toast('当前结果没有可预览素材。');
 }catch(e){$('#image-action-status').textContent=e.status===409?'资源库已变化，请关闭预览并重新打开。':e.message;}
 finally{if($('#image-dialog').open)$('#image-next').disabled=galleryState.index===galleryState.items.length-1&&!galleryState.remoteCursor;}
}

async function remoteGalleryPrevious(){
 const cursor=galleryState.remotePrevious;if(!cursor)return;
 const run=galleryState.run;$('#image-prev').disabled=true;
 try{
  const page=await api('/api/query','POST',{...galleryState.remoteQuery,cursor,projection:'media'});
  if(run!==galleryState.run||!$('#image-dialog').open)return;
  const seen=new Set(galleryState.items.map(r=>r.resourceId+'|'+r.key));const items=ShijiGallery.mediaQueue(page.resources.map(ShijiBoard.galleryResource)).items.filter(r=>!seen.has(r.resourceId+'|'+r.key));
  galleryState.items.unshift(...items);galleryState.remotePrevious=page.previousCursor;galleryState.index=items.length;moveGallery(Math.max(0,items.length-1));
 }catch(e){$('#image-action-status').textContent=e.message;}
 finally{if($('#image-dialog').open)$('#image-prev').disabled=galleryState.index===0&&!galleryState.remotePrevious;}
}

function markSearchDetail(){
 const terms=state.remote?.page?.terms||[];
 $('#drawer').querySelectorAll('#drawer-title,[data-note-text],.code-content code,.detail-tags span,.detail-block>p').forEach(el=>{if(!el.children.length)ShijiQuery.mark(el,ShijiQuery.ranges(el.textContent,terms));});
}
async function queryImageCandidates(owner,signal){
 const body={scope:owner.deleted?'trash':'all',filters:{mediaType:'image'},projection:'media',limit:100,sort:'new'};let cursor=null,resources=[];
 do{const page=await api('/api/query','POST',{...body,...(cursor?{cursor}:{})},signal);resources.push(...page.resources);cursor=page.nextCursor;}while(cursor&&!signal.aborted);
 if(signal.aborted)throw new DOMException('已取消','AbortError');
 return {resources};
}

async function remoteGalleryEdge(last){
 const run=galleryState.run;const {anchor,...body}=galleryState.remoteQuery;
 const page=await api('/api/query','POST',{...body,edge:last?'last':'first',projection:'media'});
 if(run!==galleryState.run||!$('#image-dialog').open)return;
 const items=ShijiGallery.mediaQueue(page.resources.map(ShijiBoard.galleryResource)).items;
 if(!items.length)return;
 galleryState.items=items;galleryState.index=last?items.length-1:0;galleryState.remoteCursor=page.nextCursor;galleryState.remotePrevious=page.previousCursor;renderGallery();
}

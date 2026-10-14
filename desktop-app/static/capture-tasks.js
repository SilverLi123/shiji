/* Compact real-job controls; resource writes stay in the existing API/Store. */
(function(root){
 'use strict';
 const labels={pending:'等待补全',running:'正在补全',retry:'等待重试',completed:'已完成',failed:'补全失败',cancelled:'已取消',skipped:'已跳过'};
 const types={capture:'网页补全',preview:'网站预览',asset:'网页图片'};
 const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function markup(info,busy=false){
  const button=(action,label,id='',extra='')=>`<button type="button" class="secondary" data-capture-action="${action}" data-task-id="${esc(id)}" ${busy?'disabled':''} ${extra}>${label}</button>`;
  return `<section class="capture-panel" data-capture-panel aria-label="后台补全任务"><p>收藏已保存在本机。网络解析和图片下载在后台进行，失败时仍可使用原收藏和海报。</p><div class="capture-overview"><p role="status">待处理 ${info.counts.pending||0} · 处理中 ${info.counts.running||0} · 待重试 ${info.counts.retry||0}<br>已完成 ${info.counts.completed||0} · 失败 ${info.counts.failed||0}</p>${button(info.paused?'resume':'pause',info.paused?'恢复后台处理':'暂停后台处理')}</div><p data-capture-error role="alert" hidden></p>${info.paused?'<p class="field-help">后台处理已暂停。正在读取的结果不会写入。</p>':''}<div class="capture-job-list">${info.tasks.length?info.tasks.map(task=>`<article class="capture-job" data-task-row="${esc(task.id)}"><header><h3>${esc(task.title||'原收藏')}</h3><span class="capture-state" data-state="${esc(task.status)}">${labels[task.status]||'未知状态'}</span></header><p class="capture-job-meta">${types[task.type]||'后台处理'} · 已尝试 ${task.attempts} 次${task.status==='retry'?` · ${new Date(task.nextAt*1000).toLocaleTimeString('zh-CN',{hour:'2-digit',minute:'2-digit'})} 后重试`:''}</p>${task.error?`<p class="capture-job-error">${esc(task.error)}</p>`:''}<div class="capture-job-actions">${button('resource','查看资源',task.id)}${['pending','running','retry'].includes(task.status)?button('cancel','取消补全',task.id):''}${['failed','cancelled'].includes(task.status)?button('retry','重新尝试',task.id):''}</div>${task.suggestionState==='pending'&&task.suggestions?.category&&!['pending','running','cancelled','skipped'].includes(task.status)?`<div class="capture-suggestions"><p>整理建议：${esc(task.suggestions.category)}${task.suggestions.tags?.length?' · '+esc(task.suggestions.tags.join(' · ')):''}</p><p class="field-help">追加建议标签；分类只填未分类资源。已有整理不会被替换。</p><div class="capture-job-actions">${button('accept','接受建议',task.id)}${button('ignore','忽略',task.id)}</div></div>`:''}</article>`).join(''):'<p class="capture-empty">还没有后台任务。收藏链接后，补全会在这里显示。</p>'}</div><p class="field-help">显示最近 ${info.tasks.length} 条任务。取消补全不会删除收藏。</p></section>`;
 }
 function create({document:doc,api,show,refresh=async()=>true,onResource=()=>{},notice=()=>{},pollMs=5000}){
  const win=doc.defaultView,dialog=doc.getElementById('manage-dialog'),content=doc.getElementById('manage-content');
  let info=null,dead=false,busy=false,inflight=null,timer=null,lastFocus=null,signature='',needsRefresh=false,panelSignature='';
  const ownPanel=()=>dialog?.open&&!!content?.querySelector('[data-capture-panel]');
  function repaint(force=false){
   if(!ownPanel())return;
   const next=JSON.stringify(info)+busy;if(!force&&next===panelSignature)return;panelSignature=next;
   const focus=content.contains(doc.activeElement)?{action:doc.activeElement.dataset.captureAction,id:doc.activeElement.dataset.taskId}:null;
   content.innerHTML=markup(info,busy);
   if(focus?.action){const target=[...content.querySelectorAll('[data-capture-action]')].find(el=>el.dataset.captureAction===focus.action&&el.dataset.taskId===focus.id);(target||content.querySelector('button'))?.focus({preventScroll:true});}
  }
  async function deferredRefresh(){if(needsRefresh&&!dead&&await refresh())needsRefresh=false;}
  function update(value){
   info=value;for(const badge of doc.querySelectorAll('[data-capture-count]')){if(badge.textContent!==String(info.active))badge.textContent=String(info.active);badge.hidden=!info.active;}
   const next=JSON.stringify([info.counts.completed,info.counts.failed,info.tasks.filter(t=>['completed','failed'].includes(t.status)||t.expectedRevision!==t.resourceVersion).map(t=>[t.id,t.expectedRevision,t.suggestionState])]);
   if(signature&&next!==signature)needsRefresh=true;signature=next;repaint();
  }
  function schedule(){win.clearTimeout(timer);if(!dead&&!doc.hidden)timer=win.setTimeout(poll,pollMs);}
  async function poll(){
   if(dead||doc.hidden)return info;if(inflight)return inflight;
   win.clearTimeout(timer);
   inflight=(async()=>{try{const value=await api('/api/capture/tasks');if(!dead){update(value);await deferredRefresh();}}catch{}finally{inflight=null;schedule();}return info;})();return inflight;
  }
  async function open(){
   if(dead)return;lastFocus=doc.activeElement;
   try{const value=await api('/api/capture/tasks');if(dead)return;update(value);show('后台补全',markup(info,busy));panelSignature='';content.querySelector('button')?.focus({preventScroll:true});}catch(e){notice(e.message);}
  }
  async function click(event){
   if(event.target.closest('[data-capture-open]')){await open();return;}
   const button=event.target.closest('[data-capture-action]');if(!button||!ownPanel()||busy)return;
   const action=button.dataset.captureAction,id=button.dataset.taskId,task=info.tasks.find(t=>t.id===id);
   if(action==='resource'){try{await onResource(task?.resourceId);}catch(e){notice(e.message);}return;}
   busy=true;repaint(true);
   try{const body={action,...(id?{id}:{}),...(['accept','ignore'].includes(action)?{updatedAt:task.expectedRevision}:{})};const value=await api('/api/capture/tasks','POST',body);if(!dead){update(value);if(action==='accept')needsRefresh=true;}}
   catch(e){if(!dead&&ownPanel()){busy=false;repaint(true);const error=content.querySelector('[data-capture-error]');error.hidden=false;error.textContent=e.message;return;}}
   finally{busy=false;if(!dead)repaint();}
   await deferredRefresh();
  }
  function visibility(){win.clearTimeout(timer);if(!doc.hidden)poll();}
  function closed(){if(content?.querySelector('[data-capture-panel]')){lastFocus?.isConnected&&lastFocus.focus({preventScroll:true});deferredRefresh().catch(()=>{});}}
  doc.addEventListener('click',click);doc.addEventListener('visibilitychange',visibility);dialog?.addEventListener('close',closed);
  return {open,poll,destroy(){dead=true;win.clearTimeout(timer);doc.removeEventListener('click',click);doc.removeEventListener('visibilitychange',visibility);dialog?.removeEventListener('close',closed);}};
 }
 const api={create,markup};if(typeof module==='object')module.exports=api;else root.ShijiCaptureTasks=api;
})(typeof window==='object'?window:globalThis);

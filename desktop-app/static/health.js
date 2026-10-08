/* Manual library maintenance inside the existing resource workspace. */
let healthTimer=null,healthResult=null;
const healthBytes=n=>n===0?'0 B':size(n);
function healthOwner(a){return `<div class="health-file"><div><strong>${esc(a.name)}</strong><span>${esc(a.resourceTitle)}${a.inTrash?' · 回收站':''}</span></div>${a.unlinked?'':`<button class="secondary" data-action="health-resource" data-id="${esc(a.resourceId)}">查看资源</button>`}</div>`;}
function renderHealth(){
  const root=$('#library-health'),s=healthResult,report=s?.report,sharing=s?.sharing,busy=sharing?.status==='running';
  const focus=ShijiCards.captureFocus(root);
  root.innerHTML=`<div class="health-actions"><button class="primary" data-action="health-scan" ${s?.status==='running'||busy?'disabled':''}>${s?.status==='running'?'正在检查…':report?'重新检查附件':'开始检查附件'}</button>${s?.status==='running'?`<button class="secondary" data-action="health-cancel" ${s.cancelRequested?'disabled':''}>${s.cancelRequested?'正在取消…':'取消检查'}</button>`:''}${report?'<a class="secondary" href="/api/library-health/report" download>下载检查报告</a>':''}<button class="text-button" data-action="backups" ${busy?'disabled':''}>从备份恢复</button></div><p id="health-progress" class="field-help" role="status" tabindex="-1">${healthStatusText(s)}</p><p class="field-help">扫描只读取本地附件；复用相同内容需要在下方单独操作，收藏记录和来源说明保留。</p>${sharingView(sharing)}${report?healthReport(report,sharing,s?.jobId,s?.status==='running'):`<div class="health-empty"><h2>先了解附件的状态</h2><p>检查结果会列出重复内容与需要恢复的文件，并保留它们所属的资源和来源说明。</p></div>`}`;
  ShijiCards.restoreFocus(root,focus,root.querySelector('[data-action=health-scan]'));
  if(focus&&(!root.contains(root.ownerDocument.activeElement)||root.ownerDocument.activeElement.disabled)){
    (root.querySelector('[data-action=health-scan]:not(:disabled)')||root.querySelector('a[href^="/api/backups/"]')||root.querySelector('#health-progress'))?.focus({preventScroll:true});
  }
}
function healthStatusText(s){
  if(!s)return '尚未检查，本次检查只读取本地附件。';
  if(s.status==='running')return `已检查 ${s.progress.done} / ${s.progress.total} 个附件${s.cancelRequested?'，正在取消':''}。`;
  if(s.status==='failed')return esc(s.error||'检查未完成，请重试。');
  if(s.status==='cancelled')return '检查已取消，收藏和文件没有改动。';
  if(s.status==='complete')return '本次附件检查已完成。';
  return '尚未检查，本次检查只读取本地附件。';
}
function sharingStatus(s){
  if(s.status==='running'){
    if(s.cancelRequested)return '正在取消并回退本组改动…';
    if(s.phase==='backup')return '正在保存恢复前快照…';
    if(s.phase==='cleanup')return '文件内容已复用，正在清理临时文件；此阶段已不能取消。';
    const phase={checking:'校验相同附件',preparing:'准备文件复用',publishing:'替换文件路径'}[s.phase]||'处理附件';
    return `${phase}：${s.progress.done} / ${s.progress.total}。`;
  }
  if(s.status==='complete')return `已复用 ${s.changedFiles} 个附件的内容；登记附件的独立内容减少 ${healthBytes(s.sharedBytes)}。重新检查可更新分组和统计。`;
  if(s.status==='cancelled')return '复用已取消，本组改动已回退。可重新检查后再操作。';
  return esc(s.error||'复用未完成，请重新检查后重试。');
}
function sharingView(s){
  if(!s||s.status==='idle')return '';
  return `<section class="health-section" aria-label="文件内容复用"><h2>文件内容复用</h2><p id="sharing-progress" role="status">${sharingStatus(s)}</p><div class="health-actions">${s.status==='running'?`<button class="secondary" data-action="health-share-cancel" ${s.cancelRequested||s.phase==='cleanup'?'disabled':''}>${s.phase==='cleanup'?'正在收尾…':s.cancelRequested?'正在回退…':'取消复用'}</button>`:''}${s.backup?`<a class="secondary" href="/api/backups/${encodeURIComponent(s.backup.name)}" download>下载恢复前快照</a>`:''}</div>${s.backup?'<p class="field-help">快照单独保存在本机，占用额外空间；可在“备份与恢复”中核对或下载。</p>':''}${s.cleanupWarning?`<p class="health-warning" role="status">${esc(s.cleanupWarning)}</p>`:''}${s.recoveryDirectory?`<p class="health-warning">暂存目录：data/files/${esc(s.recoveryDirectory)}。请保留其中剩余的临时文件，并核对恢复前快照。</p>`:''}</section>`;
}
function healthReport(r,sharing,scanJobId,scanBusy=false){
  const reasons={missing:'文件缺失',corrupt:'内容与保存时不一致',unreadable:'无法读取文件',changed:'扫描期间文件发生变化',unlinked:'所属资源不存在'},busy=sharing?.status==='running';
  const groups=r.duplicates.slice().sort((a,b)=>Number(a.storedCopies===1)-Number(b.storedCopies===1));
  const summary=Number.isFinite(r.sharedBytes)?`<p>独立文件内容 ${healthBytes(r.uniqueStoredBytes)}；${r.sharedFiles} 个附件复用内容，减少重复存储 ${healthBytes(r.sharedBytes)}。</p>`:'';
  return `<div class="health-summary"><p>检查时间：${esc(new Date(r.checkedAt).toLocaleString('zh-CN'))}</p><p>${r.attachments} 个附件，其中 ${r.trashAttachments} 个随资源在回收站；已读取文件 ${healthBytes(r.storedBytes)}。</p>${summary}${r.stale?`<p class="health-warning" role="status">${busy?'正在复用文件内容，完成后请重新检查。':r.staleReason==='busy'?'资源库正在处理其他操作，稍后刷新状态或重新检查。':'收藏或附件已变化，请重新检查以更新结果。'}</p>`:''}</div><section class="health-section"><h2>相同内容 <span>${r.duplicates.length} 组</span></h2><p class="field-help">名称、来源和授权分别保留。复用前会保存恢复快照，再处理本组全部附件；仅支持可建立硬链接的文件系统。尚未复用的组先显示。</p>${r.duplicates.length?groups.slice(0,50).map((g,i)=>`<details class="health-group" ${i===0?'open':''}><summary>${esc(g.items[0].name)} · ${g.items.length} 个副本 · ${healthBytes(g.size)}</summary>${g.items.slice(0,100).map(healthOwner).join('')}${g.items.length>100?`<p class="field-help">此组显示前 100 个附件，复用操作处理全部 ${g.items.length} 个；完整列表在下载报告中。</p>`:''}<div class="health-actions"><button class="secondary" data-action="health-share" data-sha256="${esc(g.sha256)}" ${busy||scanBusy||r.stale||!scanJobId||g.storedCopies===1?'disabled':''}>${g.storedCopies===1?'已复用文件内容':'复用这组文件内容'}</button>${Number.isInteger(g.storedCopies)?`<span class="field-help">${g.storedCopies} 份独立文件内容</span>`:''}</div></details>`).join(''):'<p class="health-clear">本次未发现活动资源中的相同附件。</p>'}${r.duplicates.length>50?'<p class="field-help">显示前 50 组，完整结果在下载报告中。</p>':''}</section><section class="health-section"><h2>需要检查的文件 <span>${r.issues.length} 个</span></h2>${r.issues.length?r.issues.slice(0,100).map(a=>`<div class="health-issue"><p class="health-warning">${esc(reasons[a.reason]||'需要检查')}</p>${healthOwner(a)}</div>`).join(''):'<p class="health-clear">本次未发现缺失或内容异常的已登记附件。</p>'}${r.issues.length>100?'<p class="field-help">显示前 100 个文件，完整结果在下载报告中。</p>':''}${r.issues.length?'<p class="field-help">从完整备份恢复缺失文件；来源仍可用时，也可以打开资源重新添加附件。损坏文件请保留原副本，先核对备份。</p>':''}</section>${r.unregisteredFiles.length?`<section class="health-section"><h2>未登记文件 <span>${r.unregisteredFiles.length} 个</span></h2><p class="field-help">附件目录中发现未登记文件。名称已记录在报告中，文件保留在原处。</p></section>`:''}`;
}
async function refreshHealth(){
  clearTimeout(healthTimer);const result=await api('/api/library-health');healthResult=result;
  if(state.scope!=='health')return;
  const scanRunning=result.status==='running',shareRunning=result.sharing?.status==='running';
  if(scanRunning&&$('#library-health [data-action=health-cancel]'))$('#health-progress').textContent=healthStatusText(result);
  else if(shareRunning&&$('#library-health [data-action=health-share-cancel]')){
    $('#sharing-progress').textContent=sharingStatus(result.sharing);
    const cancel=$('#library-health [data-action=health-share-cancel]'),disabled=result.sharing.cancelRequested||result.sharing.phase==='cleanup';
    if(disabled&&cancel===cancel.ownerDocument.activeElement)renderHealth();
    else{cancel.disabled=disabled;cancel.textContent=result.sharing.phase==='cleanup'?'正在收尾…':result.sharing.cancelRequested?'正在回退…':'取消复用';}
    if(result.sharing.backup&&!$('#library-health a[href^="/api/backups/"]'))renderHealth();
  }else renderHealth();
  if(scanRunning||shareRunning)healthTimer=setTimeout(()=>refreshHealth().catch(healthError),1000);
}
function healthError(e){if(state.scope==='health'){const el=$('#health-progress');if(el)el.textContent=e.message+' 可以重新连接查看任务状态。';renderHealthRetry();}}
function renderHealthRetry(){const button=$('#library-health [data-action=health-scan]');if(button){button.disabled=false;button.textContent='重新连接检查';}}
async function handleHealth(action,el){
  if(action==='health'){selectScope('health');await refreshHealth();}
  else if(action==='health-scan'){
    if(el.textContent==='重新连接检查'){await refreshHealth();return;}
    healthResult=await api('/api/library-health','POST',{});renderHealth();await refreshHealth();
  }
  else if(action==='health-cancel'){healthResult=await api('/api/library-health','POST',{cancel:true});renderHealth();await refreshHealth();}
  else if(action==='health-share'){
    healthResult=await api('/api/library-health/share','POST',{scanJobId:healthResult?.jobId,sha256:el.dataset.sha256});renderHealth();$('#library-health [data-action=health-share-cancel]')?.focus();await refreshHealth();
  }
  else if(action==='health-share-cancel'){
    healthResult=await api('/api/library-health/share','POST',{cancel:true,jobId:healthResult.sharing.jobId});renderHealth();await refreshHealth();
  }
  else if(action==='health-resource'){const item=find(el.dataset.id);if(!item)throw new Error('资源已变化，请刷新后重新检查。');detail(item);}
}

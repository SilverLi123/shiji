'use strict';
let similarJob=null,similarSequence=0;
async function readSimilarPixels(attachment,signal){
  const request=new AbortController();let timedOut=false;const abort=()=>request.abort();
  signal.addEventListener('abort',abort,{once:true});if(signal.aborted)request.abort();
  const timer=setTimeout(()=>{timedOut=true;request.abort();},30000);
  let bitmap;
  try{
    const response=await fetch(fileURL(attachment),{signal:request.signal,cache:'no-store'});
    if(!response.ok)throw new Error('文件无法读取（'+response.status+'），请检查附件或从备份恢复。');
    const declared=Number(response.headers?.get('Content-Length'));
    if(declared>64*1024*1024){await response.body?.cancel();throw new Error('文件超过 64 MB，请先检查附件。');}
    const bytes=await response.blob();
    if(!bytes.size||bytes.size>64*1024*1024)throw new Error('文件为空或超过 64 MB。');
    const decoding=createImageBitmap(bytes,{resizeWidth:ShijiSimilar.SIDE,resizeHeight:ShijiSimilar.SIDE,resizeQuality:'high'});
    // Abort does not cancel native decoding; dispose a late bitmap when it arrives.
    decoding.then(value=>{if(request.signal.aborted)value.close();},()=>{});
    let rejectDecode;const cancelDecode=()=>rejectDecode(new DOMException('已取消','AbortError'));
    const cancelled=new Promise((_,reject)=>{rejectDecode=reject;request.signal.addEventListener('abort',cancelDecode,{once:true});if(request.signal.aborted)cancelDecode();});
    try{bitmap=await Promise.race([decoding,cancelled]);}finally{request.signal.removeEventListener('abort',cancelDecode);}
    if(signal.aborted)throw new DOMException('已取消','AbortError');
    const canvas=document.createElement('canvas');canvas.width=canvas.height=ShijiSimilar.SIDE;
    const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(bitmap,0,0);
    return ShijiSimilar.descriptor(context.getImageData(0,0,canvas.width,canvas.height).data);
  }catch(e){if(timedOut)throw new Error('读取超过 30 秒，请检查服务后重试。');if(e.name==='AbortError')throw e;if(e.name==='InvalidStateError'||e.name==='EncodingError')throw new Error('浏览器无法解析这张图片，请检查格式或从备份恢复。');if(e.name==='TypeError')throw new Error('读取失败，请检查本地服务或图片格式后重试。');throw new Error(e.message||'浏览器无法解析这张图片。');}
  finally{bitmap?.close();clearTimeout(timer);signal.removeEventListener('abort',abort);}
}
function similarOpen(owner,key){
  const attachment=owner?.attachments?.find(a=>a.id===key&&a.mime.startsWith('image/'));
  if(!attachment){toast('只支持已收藏的本地图片，请先保存图片附件。');return;}
  if(similarJob?.attachment.id!==key){
    similarStop(false);
    similarJob={owner:structuredClone(owner),attachment:structuredClone(attachment),entries:[],rows:[],failures:[],checked:0,phase:'idle',mode:'strict',page:0,controller:null,run:0};
  }
  const job=similarJob;
  manage('找相似图片',`<section id="similar-panel"><div class="similar-reference"><img src="${fileURL(job.attachment)}" alt="查询图片：${esc(job.attachment.name)}"><div><strong>${esc(job.attachment.name)}</strong><p>${esc(job.owner.title)}</p><p class="field-help">${job.owner.deleted?'只查找回收站中的本地图片':'查找全部活动资源中的本地图片'}，不受主页筛选影响。</p></div></div><p class="field-help">按缩略图颜色与结构找视觉相近图片，结果需人工判断。动画仅比较默认静帧或首帧；网页缩略图不参与。收藏、来源和授权不会改变。结果保留本次查找时的信息，重新查找可更新。</p><div class="similar-controls"><label>匹配范围<select id="similar-mode"><option value="strict">较接近</option><option value="broad">更宽松</option></select></label><button id="similar-start" class="secondary" data-action="similar-start">重新查找</button><button id="similar-cancel" class="text-button" data-action="similar-cancel">取消查找</button></div><p id="similar-status" role="status" aria-live="polite"></p><div id="similar-failures"></div><h3 id="similar-summary">相近结果</h3><div id="similar-results"></div><div class="similar-pagination"><button id="similar-prev" class="secondary" data-action="similar-prev">上一页</button><span id="similar-page"></span><button id="similar-next" class="secondary" data-action="similar-next">下一页</button></div></section>`);
  $('#similar-mode').value=job.mode;
  $('#similar-mode').addEventListener('change',e=>{job.mode=e.target.value;job.page=0;similarRender(job);});
  $('.similar-reference img').addEventListener('error',e=>{e.target.hidden=true;});
  similarRender(job);
  if(job.phase==='idle')void similarStart();
}
function similarStop(render=true){
  const job=similarJob;if(!job||job.phase!=='running')return;
  job.controller.abort();job.phase='cancelled';job.run=++similarSequence;
  if(render)similarRender(job);
}
async function similarStart(){
  const job=similarJob;if(!job||job.phase==='running')return;
  // Every scan refreshes records and reads file bytes without persisting an index.
  job.phase='running';job.rows=[];job.failures=[];job.checked=0;job.entries=[];job.page=0;job.loading=true;job.controller=new AbortController();job.run=++similarSequence;const run=job.run;
  similarRender(job);
  try{
    let library;const controller=job.controller;let timedOut=false;
    const timer=setTimeout(()=>{timedOut=true;controller.abort();},30000);
    try{
      if(state.remote){library=await queryImageCandidates(job.owner,controller.signal);}else{
      const response=await fetch(job.owner.deleted?'/api/trash':'/api/resources',{signal:controller.signal,cache:'no-store'});
      if(!response.ok)throw new Error('无法读取素材库，请检查本地服务后重试。');
      library=await response.json();}
    }catch(e){throw new Error(timedOut?'读取素材库超过 30 秒，请检查服务后重试。':'无法读取素材库，请检查本地服务后重试。');}
    finally{clearTimeout(timer);}
    if(job.run!==run||job.controller.signal.aborted)return;
    const owner=library.resources.find(r=>r.id===job.owner.id),attachment=owner?.attachments.find(a=>a.id===job.attachment.id&&!a.deleted);
    if(!attachment)throw new Error('查询图片已移除或移动了范围，请关闭并重新选择。');
    job.owner=structuredClone(owner);job.attachment=structuredClone(attachment);
    job.loading=false;job.entries=ShijiSimilar.candidates(library.resources,owner,attachment.id);job.rows=[];job.failures=[];job.checked=0;job.page=0;
    similarRender(job);
    let lastUpdate=0;
    const result=await ShijiSimilar.scan(attachment,job.entries,readSimilarPixels,job.controller.signal,outcome=>{
      if(job.run!==run)return;
      Object.assign(job,{rows:outcome.rows,failures:outcome.failures,checked:outcome.checked});
      if(Date.now()-lastUpdate>200){lastUpdate=Date.now();similarRender(job);}
    });
    if(job.run!==run)return;
    Object.assign(job,result,{phase:result.cancelled?'cancelled':'done'});
  }catch(e){if(job.run!==run)return;job.phase='error';job.error=e.message||'查找失败，请重试。';}
  finally{if(job.run===run)similarRender(job);}
}
function similarRender(job){
  if(job!==similarJob||!$('#similar-panel'))return;
  $('.similar-reference strong').textContent=job.attachment.name;
  $('.similar-reference p').textContent=job.owner.title;
  const busy=job.phase==='running';$('#similar-start').disabled=busy;$('#similar-cancel').hidden=!busy;$('#similar-mode').disabled=busy;
  const scanned=`已检查 ${job.checked} / ${job.entries.length} 张图片`;
  $('#similar-status').textContent=busy?(job.loading?'正在读取素材库…':`查找中，${scanned}…`):job.phase==='done'?`查找完成，${scanned}。`:job.phase==='cancelled'?`已取消，${scanned}；下方仅为已检查的结果。`:job.phase==='error'?`查找未完成：${job.error}`:'准备查找…';
  const matches=ShijiSimilar.ranked(job.rows,job.mode),page=ShijiSimilar.page(matches,job.page);job.page=page.index;
  $('#similar-summary').textContent=`相近结果 · ${matches.length} 张${busy||job.phase==='cancelled'?'（部分结果）':''}`;
  $('#similar-results').innerHTML=page.rows.map(row=>{
    const a=row.attachment,r=row.resource;
    return `<article class="similar-row"><button class="similar-thumb" data-action="similar-preview" data-file="${esc(a.id)}" aria-label="预览 ${esc(a.name)}"><img src="${fileURL(a)}" alt="${esc(a.name)}" loading="lazy"></button><div class="similar-row-body"><strong>${esc(a.name)}</strong><p>${esc(r.title)} · ${row.distance<=ShijiSimilar.STRICT?'视觉较接近':'可能相近'}</p><p class="field-help">${esc(a.author||'作者待补充')} · ${esc(a.license||'待确认')}</p><div class="similar-links"><button class="text-button" data-action="similar-resource" data-id="${esc(r.id)}">查看资源</button><a class="text-button" href="${fileURL(a)}?download=1" download>下载原文件</a>${a.sourceUrl?`<a class="text-button" href="${esc(a.sourceUrl)}" target="_blank" rel="noopener noreferrer">来源</a>`:''}${a.licenseUrl?`<a class="text-button" href="${esc(a.licenseUrl)}" target="_blank" rel="noopener noreferrer">许可说明</a>`:''}</div></div></article>`;
  }).join('')||`<p class="field-help">${busy?'正在比较本地图片…':job.phase==='cancelled'?'已检查的图片中没有相近结果，可重新查找。':job.phase==='error'?'请检查查询附件或本地服务，再点击重新查找。':job.entries.length?'未找到相近图片，可将匹配范围改为“更宽松”。':'此范围没有其他本地图片。'}</p>`;
  $('#similar-results').querySelectorAll('img').forEach(img=>img.addEventListener('error',()=>{img.hidden=true;img.parentElement.classList.add('similar-unavailable');img.parentElement.textContent='无法预览';}));
  $('#similar-prev').disabled=page.index===0;$('#similar-next').disabled=page.index===page.count-1;$('#similar-page').textContent=`第 ${page.index+1} / ${page.count} 页 · 共 ${page.total} 张`;
  $('#similar-failures').innerHTML=job.failures.length?`<details><summary>${job.failures.length} 张图片无法读取</summary><ul>${job.failures.slice(0,10).map(f=>`<li>${esc(f.name)}：${esc(f.message)}</li>`).join('')}</ul>${job.failures.length>10?'<p class="field-help">这里只显示前 10 项；下载记录可查看全部。</p>':''}<button class="text-button" data-action="similar-report">下载失败记录</button></details>`:'';
}
async function similarAction(action,element){
  if(action==='similar-start')void similarStart();
  else if(action==='similar-cancel')similarStop();
  else if(action==='similar-prev'||action==='similar-next'){similarJob.page+=action==='similar-next'?1:-1;similarRender(similarJob);}
  else if(action==='similar-resource'){
    const job=similarJob,panel=$('#similar-panel');element.disabled=true;
    await reload();
    if(job!==similarJob||!panel?.isConnected||!$('#manage-dialog').open)return;
    const resource=typeof state!=='undefined'&&state.remote?await fullResource(element.dataset.id):find(element.dataset.id);
    if(!resource||Boolean(resource.deleted)!==Boolean(job.owner.deleted))throw new Error('资源已移除或移动了范围，请重新查找。');
    $('#manage-dialog').close();detail(resource);
  }else if(action==='similar-preview'){
    const rows=ShijiSimilar.ranked(similarJob.rows,similarJob.mode),items=rows.map(row=>ShijiGallery.images({...row.resource,attachments:[row.attachment],thumbnail:''})[0]).filter(Boolean);
    openGallerySnapshot({items,index:Math.max(0,items.findIndex(a=>a.key===element.dataset.file))},true);
  }else if(action==='similar-report'){
    const report={query:similarJob.attachment.name,scope:similarJob.owner.deleted?'trash':'active',checked:similarJob.checked,total:similarJob.entries.length,status:similarJob.phase,failures:similarJob.failures};
    const url=URL.createObjectURL(new Blob([JSON.stringify(report,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='shiji-image-search-errors.json';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
}
function initSimilar(){ $('#manage-dialog').addEventListener('close',()=>similarStop(false)); }

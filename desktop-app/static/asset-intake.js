'use strict';
let assetIntake=null;
function assetIntakePanel(){
  if(assetIntake?.busy&& !$('#manage-dialog').open){toast('当前文件仍在保存，请稍后重新打开。');return;}
  if(!assetIntake)assetIntake={rows:[],files:[],page:0,busy:false,stop:false,closed:false,started:false,options:null};
  assetIntake.closed=false;
  assetRender();
}
function assetRender(){
  const job=assetIntake,c=ShijiAssets.counts(job.rows);
  manage('批量添加素材',`<form data-manage-form="assets" class="asset-intake"><p class="field-help">先预览，再勾选导入。每个文件独立保存；暂停或关闭后，已经完成的素材仍在库中。</p><div class="asset-picker"><button type="button" class="secondary" data-asset="pick" ${job.busy?'disabled':''}>选择文件</button><button type="button" class="secondary" data-asset="folder" ${job.busy?'disabled':''}>选择文件夹</button><span class="field-help">最多 200 个文件 · 每个 64 MB · 合计 2 GB</span></div>${job.rows.length?`<fieldset class="asset-settings" ${job.started||job.busy?'disabled':''}><legend>统一整理信息</legend><div class="form-columns"><label>标签<input name="tags" maxlength="1600" placeholder="用逗号分隔"></label><label>项目<select name="project">${projectOptions(state.filters.collection||'').replace('无上级项目','不放入项目')}</select></label><label>来源网址<input name="sourceUrl" type="url" maxlength="4000" placeholder="可稍后补充"></label><label>作者<input name="author" maxlength="200" placeholder="可稍后补充"></label><label>授权<select name="license"><option>待确认</option><option>允许商用</option><option>需署名</option><option>仅个人使用</option></select></label><label>许可说明网址<input name="licenseUrl" type="url" maxlength="4000"></label></div></fieldset><p class="field-help">相同内容默认不选。勾选重复项会另存副本，已有收藏的名称、备注和授权保持原样。文件夹路径只记录为备注。</p><div class="asset-selection"><button type="button" class="text-button" data-asset="new" ${job.busy||job.started?'disabled':''}>只选新文件</button><button type="button" class="text-button" data-asset="none" ${job.busy||job.started?'disabled':''}>取消全部选择</button><span id="asset-selected">已选 ${c.selected} / ${job.rows.length}</span></div><div id="asset-rows" class="asset-rows">${assetRows(job)}</div><div class="asset-pagination"><button type="button" class="secondary" data-asset="previous" ${job.page===0?'disabled':''}>上一页</button><span>第 ${job.page+1} / ${Math.ceil(job.rows.length/20)} 页</span><button type="button" class="secondary" data-asset="next" ${job.page+1>=Math.ceil(job.rows.length/20)?'disabled':''}>下一页</button></div>`:'<p class="asset-empty">选择图片、音频、视频、字体或其他开发素材，也可以在首页拖入文件。</p>'}<p class="asset-progress" id="asset-progress" role="status">${assetProgress(job)}</p><div class="asset-actions"><button type="button" class="secondary" data-asset="close">${job.busy?'暂停并关闭':'关闭'}</button>${job.busy?'<button type="button" class="primary" data-asset="pause">暂停（当前文件完成后）</button>':job.rows.length?`<button class="primary" ${c.remaining?'':'disabled'}>${job.started?'继续 / 重试剩余项':'导入所选文件'}</button>`:''}</div><p class="field-help">失败项可继续重试，成功项不会重复保存。关闭后再次打开“添加素材”可继续；刷新页面或重启应用后，请重新选择文件。</p></form>`);
  if(job.options)for(const [key,value]of Object.entries(job.options)){const el=$('#manage-content [name="'+key+'"]');if(el)el.value=key==='tags'?value.join('，'):key==='project'?value[0]||'':value;}
  assetBind();
}
function assetRows(job){return ShijiAssets.page(job.rows,job.page).map(row=>{
  const done=ShijiAssets.terminal(row),locked=job.busy||job.started;
  return `<div class="asset-row ${row.status==='invalid'?'asset-invalid':''}"><label class="asset-select"><input type="checkbox" data-asset-select="${row.index}" aria-label="导入 ${esc(row.name)}" ${row.selected?'checked':''} ${locked||row.status==='invalid'||done?'disabled':''}></label><div class="asset-row-content"><label>资源名称<input value="${esc(row.title||row.name)}" maxlength="200" data-asset-title="${row.index}" ${locked||row.status==='invalid'?'disabled':''}></label><p class="asset-path">${esc(row.path||row.name)} · ${row.size?size(row.size):'0 字节'}</p><p class="asset-row-status">${esc(row.result==='saved'?'已保存':row.result==='skipped'?'跳过相同内容':row.result==='failed'?'未完成：'+row.error:row.message)}${row.existingTitle?`：${esc(row.existingTitle)}`:''}</p>${row.existingId?`<button type="button" class="text-button" data-asset-existing="${esc(row.existingId)}">查看已有资源${row.status==='trash'?'（回收站）':''}</button>`:''}</div></div>`;
}).join('');}
function assetProgress(job){const c=ShijiAssets.counts(job.rows);return job.preparing?job.preparing:job.busy?`正在保存 ${job.current||''} · 已保存 ${c.saved}，跳过 ${c.skipped}，未完成 ${c.failed}`:job.started?`已保存 ${c.saved} · 跳过 ${c.skipped} · 未完成 ${c.failed} · 剩余 ${c.remaining}`:job.rows.length?`预览 ${job.rows.length} 个文件，尚未保存。`:'尚未选择文件。';}
function assetUpdateProgress(job){if(job.closed||assetIntake!==job)return;$('#asset-progress').textContent=assetProgress(job);$('#asset-rows').innerHTML=assetRows(job);assetBindRows();}
function assetBindRows(){
  document.querySelectorAll('[data-asset-select]').forEach(el=>el.onchange=()=>{assetIntake.rows[Number(el.dataset.assetSelect)].selected=el.checked;const c=ShijiAssets.counts(assetIntake.rows);$('#asset-selected').textContent=`已选 ${c.selected} / ${assetIntake.rows.length}`;$('#manage-content button[type="submit"], #manage-content button.primary:not([type])').disabled=!c.remaining;});
  document.querySelectorAll('[data-asset-title]').forEach(el=>el.oninput=()=>assetIntake.rows[Number(el.dataset.assetTitle)].title=el.value);
  document.querySelectorAll('[data-asset-existing]').forEach(el=>el.onclick=()=>{const r=find(el.dataset.assetExisting);if(!r){toast('已有资源已变化，请重新预览。');return;}assetRememberOptions();$('#manage-dialog').close();detail(r);});
}
function assetBind(){
  assetBindRows();
  document.querySelectorAll('[data-asset]').forEach(el=>el.onclick=async()=>{
    const job=assetIntake,action=el.dataset.asset;
    if(action==='pick')$('#asset-files').click();
    if(action==='folder')$('#asset-folder').click();
    if(action==='close'){assetRememberOptions();job.stop=true;$('#manage-dialog').close();}
    if(action==='pause'){job.stop=true;el.disabled=true;el.textContent='正在完成当前文件…';}
    if(action==='previous'||action==='next'){assetRememberOptions();job.page+=action==='previous'?-1:1;assetRender();}
    if(action==='new'||action==='none'){assetRememberOptions();job.rows.forEach(r=>r.selected=action==='new'&&r.status==='new');assetRender();}
  });
}
function assetRememberOptions(){
  if(assetIntake.started)return;
  const form=$('[data-manage-form="assets"]');if(!form)return;
  const data=new FormData(form);
  assetIntake.options={tags:split(data.get('tags')||''),project:data.get('project')?[data.get('project')]:[],sourceUrl:data.get('sourceUrl')||'',author:data.get('author')||'',license:data.get('license')||'待确认',licenseUrl:data.get('licenseUrl')||''};
}
async function prepareAssets(files){
  if(!files.length)return;
  if(assetIntake?.busy){toast('当前文件仍在处理，请暂停后再选择。');return;}
  if(files.length>200){toast('一次最多选择 200 个文件，请分批选择。');return;}
  if(files.reduce((n,f)=>n+f.size,0)>2*1024*1024*1024){toast('本批文件超过 2 GB，请分批选择。');return;}
  const job=assetIntake={rows:[],files:[...files],page:0,busy:true,stop:false,closed:false,started:false,options:null,preparing:'正在校验所选文件…'};
  assetRender();
  try{
    const manifest=[];
    for(let i=0;i<files.length;i++){
      if(job.stop)break;
      const file=files[i];let sha256='';
      if(file.size>0&&file.size<=64*1024*1024)try{const digest=await crypto.subtle.digest('SHA-256',await file.arrayBuffer());sha256=Array.from(new Uint8Array(digest),n=>n.toString(16).padStart(2,'0')).join('');}catch{}
      manifest.push({name:file.name,path:file.webkitRelativePath||'',size:file.size,sha256});
      job.preparing=`正在校验 ${i+1} / ${files.length}：${file.name}`;if(!job.closed)$('#asset-progress').textContent=job.preparing;
    }
    if(job.stop){job.preparing='已取消预览，没有保存文件。';return;}
    const plan=await api('/api/assets/preview','POST',{files:manifest});
    job.rows=ShijiAssets.initial(plan.items).map(r=>({...r,requestId:crypto.randomUUID()}));job.preparing='';
  }catch(e){job.preparing=e.message+' 请重新选择文件。';}
  finally{job.busy=false;if(!job.closed)assetRender();}
}
async function handleAssetForm(form,mode){
  if(mode!=='assets')return false;
  const job=assetIntake;if(!job||job.busy)return true;
  if(!ShijiAssets.pending(job.rows).length)return true;
  if(!job.started){
    assetRememberOptions();
    const options={...job.options,projects:job.options.project};delete options.project;
    const validated=(await api('/api/assets/validate','POST',options)).options;
    for(const row of ShijiAssets.pending(job.rows))if(!row.title.trim())throw new Error('请为已勾选的文件填写名称。');
    job.settings=validated;job.started=true;
  }
  job.busy=true;job.stop=false;assetRender();
  try{
    for(const row of ShijiAssets.pending(job.rows)){
      if(job.stop)break;
      job.current=row.name;assetUpdateProgress(job);
      try{
        const file=job.files[row.index],colors=await coloursFromFile(file);
        const metadata={...job.settings,name:file.name,title:row.title,path:row.path,sha256:row.sha256,requestId:row.requestId,duplicatePolicy:row.status==='new'?'skip':'copy',colors};
        const encoded=btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(metadata))));
        const result=await rawAPI('/api/assets/import',file,{'Content-Type':'application/octet-stream','X-Metadata':encoded});
        row.result=result.status;row.error='';
        if(result.existingId)row.existingId=result.existingId;
      }catch(e){row.result='failed';row.error=e.message;}
      assetUpdateProgress(job);
    }
    await reload();
  }finally{job.busy=false;job.current='';if(!job.closed)assetRender();else toast(assetProgress(job));}
  return true;
}
document.addEventListener('DOMContentLoaded',()=>{
  $('#asset-folder').addEventListener('change',e=>{const files=[...e.target.files];e.target.value='';prepareAssets(files);});
  $('#manage-dialog').addEventListener('close',()=>{if(assetIntake){assetRememberOptions();assetIntake.closed=true;assetIntake.stop=true;}});
});

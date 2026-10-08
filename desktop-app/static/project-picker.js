/* Add/remove project membership, shared by resource details and batches. */
let projectPicker=null;
function projectPickerBusy(){return Boolean(projectPicker?.busy&&$('#manage-content [data-manage-form="project-picker"]'));}
function projectPickerRows(job){
  const query=job.search.trim().toLocaleLowerCase();
  return job.meta.filter(p=>job.mode==='remove'||!ShijiLibrary.isProjectArchived(job.meta,p.name)).map(p=>({name:p.name,path:ShijiLibrary.projectPath(job.meta,p.name).join(' / '),included:job.resources.filter(r=>r.projects.includes(p.name)).length})).filter(p=>(job.mode!=='remove'||p.included>0)&&p.path.toLocaleLowerCase().includes(query));
}
async function openProjectPicker(ids,mode='add',preselect=''){
  ids=[...new Set(ids)];if(!ids.length){toast('先选择需要整理的资源。');return;}
  const job=projectPicker={ids,mode:mode==='remove'?'remove':'add',resources:[],meta:[],selected:new Set(),search:'',page:0,busy:false};
  manage(job.mode==='remove'?'移出项目':'加入项目','<div id="project-picker-loading" role="status">正在读取项目和当前归属…</div>');
  const current=()=>projectPicker===job&&$('#manage-dialog').open&&$('#project-picker-loading');
  try{
    const data=await api('/api/resources');if(!current())return;
    job.resources=ids.map(id=>data.resources.find(r=>r.id===id));
    if(job.resources.some(r=>!r))throw new Error('所选资源已变化，请刷新后重新选择。');
    job.meta=data.collectionMeta||[];
    const removing=job.mode==='remove';
    $('#manage-content').innerHTML=`<form data-manage-form="project-picker"><p>${removing?`从所选项目移出 ${ids.length} 条资源，其他归属、标签和使用备注保留。`:`为 ${ids.length} 条资源追加项目，原有归属与使用备注保留。`}</p><fieldset class="project-picker-fields"><label>查找项目<input id="project-picker-search" type="search" placeholder="搜索项目名称或完整路径" maxlength="800"></label><div id="project-picker-selected" class="project-picker-selected"></div><div id="project-picker-results"></div><p class="field-help">${removing?'只移出勾选的项目，不影响上级或下级的独立归属。备注留在资源详情，重新加入时恢复显示。':'新加入时继承项目及上级的自动标签。每条资源最多归属 30 个项目。'}</p></fieldset><div class="project-picker-actions"><button type="button" class="secondary" data-action="close-manage">取消</button><button type="submit" class="primary" id="project-picker-save" disabled>${removing?'移出所选项目':'加入所选项目'}</button></div><p id="project-picker-status" class="field-help" role="status"></p></form>`;
    if(preselect&&projectPickerRows(job).some(p=>p.name===preselect&&(removing||p.included<ids.length)))job.selected.add(preselect);
    renderProjectPicker();$('#project-picker-search').focus();
  }catch(e){if(current()){$('#manage-content').innerHTML='<p>未能读取当前项目。请关闭后重新打开选择器。</p>';$('#manage-error').textContent=e.message;$('#manage-error').hidden=false;}}
}
function renderProjectPicker(){
  const job=projectPicker,root=$('#project-picker-results');if(!job||!root)return;
  const focus=ShijiCards.captureFocus(root),rows=projectPickerRows(job),pages=Math.max(1,Math.ceil(rows.length/100));job.page=Math.min(job.page,pages-1);
  root.innerHTML=rows.length?`<div class="project-picker-list">${rows.slice(job.page*100,job.page*100+100).map(p=>`<label class="project-picker-option"><input type="checkbox" data-project-choice data-value="${esc(JSON.stringify(p.name))}" value="${esc(JSON.stringify(p.name))}" ${job.selected.has(p.name)?'checked':''} ${job.mode!=='remove'&&p.included===job.ids.length?'disabled':''}><span><strong>${esc(p.path)}</strong><small>${job.mode==='remove'?`已包含 ${p.included} / ${job.ids.length} 条`:p.included===job.ids.length?'已全部包含':p.included?`已包含 ${p.included} / ${job.ids.length} 条`:'尚未加入'}</small></span></label>`).join('')}</div>${pages>1?`<div class="project-picker-pages"><button type="button" class="secondary" data-action="project-picker-page" data-value="${job.page-1}" ${job.page===0?'disabled':''}>上一页</button><span>第 ${job.page+1} / ${pages} 页 · ${rows.length} 个项目</span><button type="button" class="secondary" data-action="project-picker-page" data-value="${job.page+1}" ${job.page+1===pages?'disabled':''}>下一页</button></div>`:''}`:`<p class="project-picker-empty">${job.mode==='remove'?(job.resources.some(r=>r.projects.length)?'没有匹配的当前归属，可以调整搜索。':'所选资源没有项目归属。'):job.meta.some(p=>!ShijiLibrary.isProjectArchived(job.meta,p.name))?'没有匹配的项目，可以调整搜索。':'还没有可加入的项目。请先在侧栏新建项目，或取消所需项目的归档。'}</p>`;
  ShijiCards.restoreFocus(root,focus,$('#project-picker-search'));
  const selected=$('#project-picker-selected'),snapshot=ShijiCards.captureFocus(selected);
  selected.innerHTML=`<p role="status">已选 ${job.selected.size} 个项目${job.search&&job.selected.size?'，搜索不会清除选择':''}</p>${job.selected.size?`<ul>${[...job.selected].map(name=>`<li><span>${esc(ShijiLibrary.projectPath(job.meta,name).join(' / '))}</span><button type="button" class="text-button" data-action="project-picker-remove" data-value="${esc(JSON.stringify(name))}" aria-label="取消选择 ${esc(name)}">移除</button></li>`).join('')}</ul>`:''}`;
  ShijiCards.restoreFocus(selected,snapshot,$('#project-picker-search'));
  $('#project-picker-save').disabled=!job.selected.size||job.busy;
}
function searchProjectPicker(value){if(!projectPicker||projectPicker.busy)return;projectPicker.search=value;projectPicker.page=0;renderProjectPicker();}
function chooseProjectPicker(name,checked){
  const job=projectPicker;if(!job||job.busy)return;
  if(!projectPickerRows({...job,search:''}).some(p=>p.name===name&&(job.mode==='remove'||p.included<job.ids.length)))return;
  if(checked&&job.selected.size>=30){toast('一次最多选择 30 个项目。');renderProjectPicker();return;}
  if(checked)job.selected.add(name);else job.selected.delete(name);renderProjectPicker();
}
function handleProjectPickerAction(action,el){
  const job=projectPicker;if(!job||job.busy)return;
  if(action==='project-picker-remove'){job.selected.delete(JSON.parse(el.dataset.value));renderProjectPicker();}
  if(action==='project-picker-page'){const value=Number(el.dataset.value);if(!Number.isInteger(value)||value<0)return;job.page=value;renderProjectPicker();$('#project-picker-results input:not(:disabled)')?.focus();}
}
async function handleProjectPickerForm(form,mode){
  if(mode!=='project-picker')return false;
  const job=projectPicker;if(!job||job.busy||!job.selected.size)throw new Error('请选择项目后再保存。');
  job.busy=true;form.querySelector('fieldset').disabled=true;$('#project-picker-status').textContent='正在保存项目归属…';
  try{
    const result=await api(job.mode==='remove'?'/api/projects/remove':'/api/projects/assign','POST',{ids:job.ids,projects:[...job.selected]});
    $('#manage-dialog').close();
    try{await reload();}catch(e){toast('项目归属已保存，但未能刷新列表。请刷新页面查看。');return true;}
    if(state.detail&&!$('#drawer').hidden){detail(find(state.detail));$('#detail-content [data-action=assign-project]')?.focus();}
    toast(job.mode==='remove'?(result.changed?`已将 ${result.changed} 条资源移出所选项目，使用备注保留。`:'所选资源已不属于这些项目。'):result.changed?`已为 ${result.changed} 条资源追加项目。`:'所选资源已包含这些项目。');
  }finally{
    job.busy=false;if(form.isConnected){form.querySelector('fieldset').disabled=false;$('#project-picker-status').textContent='';}
  }
  return true;
}

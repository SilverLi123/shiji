/* Project navigation and bulk intake extend the existing workspace. */
function projectOptions(selected='',exclude=''){
  const blocked=exclude?ShijiLibrary.projectBranch(state.collectionMeta,exclude):new Set();
  return `<option value="">无上级项目</option>`+state.collectionMeta.filter(p=>!blocked.has(p.name)&&(p.name===selected||!ShijiLibrary.isProjectArchived(state.collectionMeta,p.name))).map(p=>`<option value="${esc(p.name)}" ${p.name===selected?'selected':''}>${esc(ShijiLibrary.projectPath(state.collectionMeta,p.name).join(' / '))}</option>`).join('');
}
function projectNavigation(){
  const meta=state.collectionMeta,counts=new Map(meta.map(p=>[p.name,0]));
  for(const r of state.resources){const found=new Set(r.projects.flatMap(n=>ShijiLibrary.projectPath(meta,n)));for(const n of found)counts.set(n,(counts.get(n)||0)+1);}
  const branch=parent=>meta.filter(p=>p.parent===parent&&!p.archived).map(p=>{
    const children=meta.some(x=>x.parent===p.name&&!x.archived),collapsed=state.collapsedProjects.has(p.name);
    return `<li><div class="project-nav-row">${children?`<button class="project-toggle ${collapsed?'':'expanded'}" data-action="toggle-project" data-value="${esc(p.name)}" aria-label="${collapsed?'展开':'收起'} ${esc(p.name)}" aria-expanded="${!collapsed}">${icon('chevron-down')}</button>`:'<span class="project-toggle-space"></span>'}${nav(p.name,counts.get(p.name),'folder',`data-action="collection" data-value="${esc(p.name)}"`,state.scope==='collection'&&state.scopeValue===p.name)}</div>${children&&!collapsed?`<ul>${branch(p.name)}</ul>`:''}</li>`;
  }).join('');
  return branch('')?`<ul class="project-tree">${branch('')}</ul>`:'<p class="collection-empty">把参考和素材放进项目</p>';
}
function saveCollapsedProjects(){try{localStorage.setItem('shiji-collapsed-projects',JSON.stringify([...state.collapsedProjects]));}catch{}}
function projectManager(selected=''){
  if(!state.collectionMeta.length){manage('管理项目','<p>还没有项目。先新建一个项目，再为它设置层级和自动标签。</p><button class="primary" data-action="new-collection">新建项目</button>');return;}
  const p=state.collectionMeta.find(p=>p.name===selected)||state.collectionMeta[0];
  manage('管理项目',`<label>选择项目<select id="manage-project-choice">${state.collectionMeta.map(q=>`<option value="${esc(q.name)}" ${q.name===p.name?'selected':''}>${esc(ShijiLibrary.projectPath(state.collectionMeta,q.name).join(' / '))}${ShijiLibrary.isProjectArchived(state.collectionMeta,q.name)?'（已归档）':''}</option>`).join('')}</select></label>${p.parent&&ShijiLibrary.isProjectArchived(state.collectionMeta,p.parent)?'<p class="field-help">上级项目已归档，此项目随上级隐藏。请先取消上级归档，或把此项目移到其他上级。</p>':''}<form data-manage-form="project-update"><input type="hidden" name="original" value="${esc(p.name)}"><label>项目名称<input name="name" required maxlength="80" value="${esc(p.name)}"><span class="field-help">全库名称唯一，改名会同步备注、下级项目和智能集合。</span></label><label>上级项目<select name="parent">${projectOptions(p.parent,p.name)}</select></label><label>自动标签<input name="autoTags" maxlength="1500" value="${esc(p.autoTags.join('，'))}" placeholder="例如：游戏，交互"><span class="field-help">资源新加入此项目或下级时，继承这些标签。</span></label><label class="option-check"><input type="checkbox" name="applyExisting">同时应用到此项目及下级已有资源</label><label class="option-check"><input type="checkbox" name="archived" ${p.archived?'checked':''}>归档项目，隐藏此项目和下级导航</label><p class="field-help">收藏和附件仍保留；取消归档即可恢复导航。移动到其他项目不会自动改动原有标签。</p><button class="primary">保存项目设置</button></form>`);
}
function bulkLinks(){
  manage('批量收藏网址',`<form data-manage-form="link-preview"><p>每行一个网址，也支持 Markdown 链接。先预览，再选择要保存的条目。</p><label>网址列表<textarea name="links" rows="9" maxlength="128000" required placeholder="https://polyhaven.com/\n[React Bits](https://reactbits.dev/)">${esc(state.linkIntakeText||'')}</textarea></label><p class="field-help">一次最多 200 条，重复和回收站条目会标明。名称可在下一步修改。</p><button class="primary">预览网址</button></form>`);
}
function intakePreview(result){
  state.linkPreview=result.items;
  manage('确认批量收藏',`<form data-manage-form="link-import"><p>共 ${result.total} 条，其中 ${result.new} 条新网址。已收藏和回收站条目会保留原内容。</p><div class="intake-list">${result.items.map((r,i)=>`<div class="intake-row ${r.status==='new'?'':'intake-disabled'}" data-intake-row="${i}"><input type="checkbox" aria-label="导入第 ${r.line} 条" ${r.status==='new'?'checked':'disabled'}><div>${r.status==='new'?`<input class="intake-title" aria-label="第 ${r.line} 条名称" maxlength="200" required value="${esc(r.title)}">`:`<strong>${esc(r.title||r.input.slice(0,160))}</strong>`}<span class="intake-url">${esc(r.url||r.input.slice(0,160))}</span><small>${esc(r.message)}</small></div></div>`).join('')}</div><div class="form-row"><label>加入项目<select name="project">${projectOptions(state.scope==='collection'?state.scopeValue:'').replace('无上级项目','暂不加入项目')}</select></label><label>统一标签<input name="tags" maxlength="1500" placeholder="用逗号分隔"></label></div><p class="field-help">先存到待整理，标题可在上方修改；此步骤不会逐个访问网页。</p><div class="intake-actions"><button type="button" class="secondary" data-action="edit-link-intake">返回修改</button><span id="intake-selected">已选 ${result.new} 条</span><button class="primary" ${result.new?'':'disabled'}>收藏所选网址</button></div></form>`);
}
async function handleOrganizingAction(action,el){
  if(action==='manage-projects')projectManager(state.scope==='collection'?state.scopeValue:'');
  else if(action==='toggle-project'){const n=el.dataset.value;if(state.collapsedProjects.has(n))state.collapsedProjects.delete(n);else state.collapsedProjects.add(n);saveCollapsedProjects();render();}
  else if(action==='bulk-links'||action==='edit-link-intake')bulkLinks();
}
async function handleOrganizingForm(form,mode){
  const data=Object.fromEntries(new FormData(form));
  if(mode==='project-update'){
    await api('/api/collections/update','POST',{original:data.original,name:data.name,parent:data.parent,autoTags:split(data.autoTags),applyExisting:form.elements.applyExisting.checked,archived:form.elements.archived.checked});
    if(state.filters.collection===data.original)state.filters.collection=data.name;
    if(state.scope==='collection'&&state.scopeValue===data.original)state.scopeValue=data.name;
    if(state.collapsedProjects.delete(data.original))state.collapsedProjects.add(data.name);saveCollapsedProjects();
    $('#manage-dialog').close();if(form.elements.archived.checked)selectScope('all');await reload();toast('项目设置已保存。');return true;
  }
  if(mode==='link-preview'){state.linkIntakeText=data.links;const result=await api('/api/links/preview','POST',{text:data.links});intakePreview(result);return true;}
  if(mode==='link-import'){
    const items=[...form.querySelectorAll('[data-intake-row]')].filter(row=>row.querySelector('input[type=checkbox]').checked).map(row=>({url:state.linkPreview[Number(row.dataset.intakeRow)].url,title:row.querySelector('.intake-title').value}));
    if(!items.length)throw new Error('先选择至少一个新网址。');
    const result=await api('/api/links/import','POST',{items,tags:split(data.tags),projects:data.project?[data.project]:[]});
    $('#manage-dialog').close();state.linkIntakeText='';state.linkPreview=[];await reload();selectScope('inbox');toast(`已收藏 ${result.added} 个网址${result.skipped?`，${result.skipped} 个已存在的条目保持原样`:''}。`);return true;
  }
  return false;
}
document.addEventListener('change',e=>{
  if(e.target.id==='manage-project-choice')projectManager(e.target.value);
  const form=e.target.closest('[data-manage-form="link-import"]');if(form){
    for(const row of form.querySelectorAll('.intake-row')){
      const title=row.querySelector('.intake-title');if(title)title.disabled=!row.querySelector('input[type=checkbox]').checked;
    }
    const count=form.querySelectorAll('.intake-row input[type=checkbox]:checked').length;$('#intake-selected').textContent=`已选 ${count} 条`;form.querySelector('button.primary').disabled=!count;
  }
});

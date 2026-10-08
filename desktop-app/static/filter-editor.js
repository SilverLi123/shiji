/* One protected form for temporary filters and saved smart-collection rules. */
function filterSelect(name,label,choices,value){
  return `<label>${label}<select name="${name}">${choices.map(([v,l])=>`<option value="${esc(v)}" ${String(value??'')===String(v)?'selected':''}>${esc(l)}</option>`).join('')}</select></label>`;
}
function filterInput(name,label,value='',extra=''){
  return `<label>${label}<input name="${name}" value="${esc(value||'')}" ${extra}></label>`;
}
function filterPanel(mode='apply',id=''){
  const smart=mode==='edit'?state.smartCollections.find(s=>s.id===id):null;
  if(mode==='edit'&&!smart)throw new Error('智能集合已不存在，请刷新后重新选择。');
  if(mode==='create'&&state.scope==='trash')throw new Error('智能集合只收集活动资源，请先离开回收站。');
  const f=smart?smart.filters:snapshotFilters(),saved=mode!=='apply';
  const projectNames=[...state.collections];if(f.collection&&!projectNames.includes(f.collection))projectNames.push(f.collection);
  const extra=ShijiLibrary.canonicalFilters(Object.fromEntries(Object.entries(f).filter(([k])=>!['search','tags','tagMode','excludeTags','collection','kind','price','license'].includes(k))));
  const tri=[['','不限'],['true','是'],['false','否']];
  manage(mode==='edit'?'编辑智能集合':saved?'保存为智能集合':'高级筛选',`<form data-manage-form="filter-editor" data-filter-mode="${mode}" data-smart-id="${esc(id)}"><p>不同条件需要同时满足。${saved?'自动收集整个活动库中符合规则的资源。':'应用到当前范围；只改变显示结果。'}</p>${saved?filterInput('smartName','集合名称',smart?.name||'', 'required maxlength="80" placeholder="例如：常用 React 素材"'):''}<section class="filter-editor-section"><h3>常用条件</h3>${filterInput('search','关键词',f.search,'maxlength="200" placeholder="多个词用空格分隔，需全部出现"')}<div class="form-row">${filterInput('tags','包含标签',(f.tags||[]).join(', '),'maxlength="1500" placeholder="用逗号分隔"')}${filterSelect('tagMode','标签匹配',[['all','全部标签'],['any','任一标签']],f.tagMode||'all')}</div>${filterInput('excludeTags','排除标签',(f.excludeTags||[]).join(', '),'maxlength="1500" placeholder="包含其中任一个标签的资源将被排除"')}<div class="form-row">${filterSelect('collection','项目（包含下级）',[['','全部项目'],...projectNames.map(n=>[n,ShijiLibrary.projectPath(state.collectionMeta,n).join(' / ')])],f.collection)}${filterSelect('kind','资源形式',[['','全部形式'],...Object.entries(KINDS)],f.kind)}</div><div class="form-row">${filterSelect('price','价格',[['','全部价格'],...['免费','部分免费','付费','待确认'].map(n=>[n,n])],f.price)}${filterSelect('license','授权',[['','全部授权'],...['允许商用','需署名','仅个人使用','待确认'].map(n=>[n,n])],f.license)}</div></section><details class="filter-editor-extra" ${Object.keys(extra).length?'open':''}><summary>更多条件 · 域名、日期与整理状态</summary><div class="form-row">${filterSelect('category','分类',[['','全部分类'],...CATEGORIES.map(n=>[n,n])],f.category)}${filterSelect('linkStatus','链接状态',[['','全部链接状态'],...Object.entries(LINK_STATUS)],f.linkStatus)}</div>${filterInput('domain','网站域名',f.domain,'maxlength="253" placeholder="例如 reactbits.dev，只填主机名称"')}<label class="option-check"><input name="includeSubdomains" type="checkbox" ${f.includeSubdomains!==false?'checked':''}>同时匹配这个域名的子域</label><div class="form-row">${filterInput('createdFrom','收藏日期从（UTC）',f.createdFrom,'type="date"')}${filterInput('createdTo','收藏日期到（UTC）',f.createdTo,'type="date"')}</div><div class="form-row">${filterSelect('favorite','常用收藏',tri,typeof f.favorite==='boolean'?String(f.favorite):'')}${filterSelect('inbox','待整理',tri,typeof f.inbox==='boolean'?String(f.inbox):'')}</div>${filterSelect('mediaType','本地附件类型',[['','不限附件类型'],['image','图片'],['audio','音频'],['video','视频'],['other','其他文件']],f.mediaType)}<p class="field-help">附件类型只匹配上传的本地文件；网页缩略图不算附件。日期包含首尾两天，按 UTC 判断。</p><div class="filter-editor-checks">${[['noTags','没有标签'],['noProjects','没有项目'],['hasNotes','有使用备注（含项目备注）'],['hasAssets','素材资源或有本地附件'],['isSnippet','代码片段或提示词']].map(([k,l])=>`<label class="option-check"><input name="${k}" type="checkbox" ${f[k]?'checked':''}>${l}</label>`).join('')}</div>${filterInput('color','相近颜色',f.color,'maxlength="7" placeholder="可选，填写 #268bd2"')}</details><section class="filter-rule-preview" aria-label="筛选预览"><p id="filter-preview-status" role="status">正在预览条件…</p><p id="filter-preview-rules" class="field-help"></p><ul id="filter-preview-items"></ul></section><div class="filter-editor-actions"><button type="button" class="secondary" data-action="close-manage">取消</button>${mode==='edit'?'<button class="secondary" type="submit" name="intent" value="copy">另存为新集合</button>':''}<button class="primary" type="submit" name="intent" value="save">${mode==='edit'?'保存集合修改':saved?'创建智能集合':'应用筛选'}</button></div></form>`);
  previewFilterForm($('#manage-content form'));
}
function readFilterForm(form){
  const values=Object.fromEntries(new FormData(form));const f={};
  for(const k of ['search','collection','category','kind','price','license','linkStatus','domain','mediaType','createdFrom','createdTo','color','tagMode'])f[k]=values[k]||'';
  for(const k of ['tags','excludeTags'])f[k]=split(values[k]||'');
  for(const k of ['includeSubdomains','noTags','noProjects','hasNotes','hasAssets','isSnippet'])f[k]=form.elements.namedItem(k).checked;
  for(const k of ['favorite','inbox'])if(values[k])f[k]=values[k]==='true';
  return f;
}
function filterPreviewScope(form){return form.dataset.filterMode==='apply'?scoped():state.resources;}
async function previewFilterForm(form){
  const run=state.filterPreviewRun=(state.filterPreviewRun||0)+1;
  const current=()=>run===state.filterPreviewRun&&form.isConnected&&$('#manage-dialog').open;
  const status=form.querySelector('#filter-preview-status');status.textContent='正在预览条件…';form.querySelector('#filter-preview-items').innerHTML='';form.querySelector('#filter-preview-rules').textContent='';
  try{
    const {filters}=await api('/api/filters/validate','POST',{filters:readFilterForm(form)});if(!current())return;
    const results=filterPreviewScope(form).filter(r=>ShijiLibrary.matches(r,filters,state.collectionMeta));
    status.textContent=`匹配 ${results.length} 条 · ${form.dataset.filterMode==='apply'?'当前范围':'整个活动库'}`;
    form.querySelector('#filter-preview-rules').textContent=ShijiLibrary.filterSummary(filters).join('；')||'不限条件';
    form.querySelector('#filter-preview-items').innerHTML=results.slice(0,5).map(r=>`<li>${esc(r.title)}</li>`).join('')+(results.length>5?'<li>更多结果在应用后查看</li>':'');
  }catch(e){if(current())status.textContent='条件需要调整：'+e.message;}
}
async function handleFilterForm(form,mode,submitter){
  if(mode!=='filter-editor')return false;
  const {filters}=await api('/api/filters/validate','POST',{filters:readFilterForm(form)});
  const kind=form.dataset.filterMode;
  if(kind==='apply'){
    if(state.scope==='health')selectScope('all');state.filters={...freshFilters(),...filters};state.selected.clear();syncFilters();render();$('#manage-dialog').close();toast('筛选已应用，收藏内容保持原样。');
  }else{
    const editing=kind==='edit'&&submitter?.value!=='copy';
    const result=await api('/api/smart-collections'+(editing?'/'+form.dataset.smartId:''),editing?'PUT':'POST',{name:form.elements.smartName.value,filters});
    $('#manage-dialog').close();await reload();selectScope('smart',result.id);toast(editing?'智能集合名称与条件已更新。':'智能集合已创建，会自动收集匹配资源。');
  }
  return true;
}
function smartSummary(){
  const rules=ShijiLibrary.filterSummary(state.filters);
  const active=state.scope==='smart'?state.smartCollections.find(s=>s.id===state.scopeValue):null;
  const modified=active&&!ShijiLibrary.sameFilters(state.filters,active.filters);
  $('#advanced-filter-state').hidden=!rules.length;
  $('#advanced-filter-state').textContent=rules.join('；');
  if(active)$('#project-summary').innerHTML=`<div class="smart-context"><span>${modified?'当前筛选已修改，尚未保存到集合':'显示已保存的集合条件'}</span><button class="text-button" data-action="edit-smart" data-id="${esc(active.id)}">编辑已保存条件</button>${modified?'<button class="text-button" data-action="smart-reset">恢复集合条件</button><button class="text-button" data-action="save-smart">当前条件另存为集合</button>':''}<button class="text-button" data-action="delete-smart" data-id="${esc(active.id)}">移除此智能集合</button></div>`;
}
document.addEventListener('input',event=>{
  const form=event.target.closest('[data-manage-form="filter-editor"]');if(!form)return;
  clearTimeout(state.filterPreviewTimer);state.filterPreviewRun=(state.filterPreviewRun||0)+1;
  form.querySelector('#filter-preview-status').textContent='正在预览条件…';form.querySelector('#filter-preview-items').innerHTML='';form.querySelector('#filter-preview-rules').textContent='';
  state.filterPreviewTimer=setTimeout(()=>{if(form.isConnected&&$('#manage-dialog').open)previewFilterForm(form);},250);
});

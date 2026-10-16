/* Explicit additive tagging shared by detail and batch organization. */
let tagPicker=null;
function tagPickerBusy(){return Boolean(tagPicker?.busy&&$('#manage-content [data-manage-form="tag-picker"]'));}
function tagPickerRows(job){
  const query=job.search.trim().toLocaleLowerCase();
  return job.catalog.filter(t=>t.name.toLocaleLowerCase().includes(query));
}
async function openTagPicker(ids){
  ids=[...new Set(ids)];if(!ids.length){toast('先选择需要整理的资源。');return;}
  const job=tagPicker={ids,resources:[],catalog:[],known:new Set(),selected:new Map(),search:'',page:0,busy:false};
  manage('加标签','<div id="tag-picker-loading" role="status">正在读取已有标签…</div>');
  const current=()=>tagPicker===job&&$('#manage-dialog').open&&$('#tag-picker-loading');
  try{
    const data=await (state.remote?organizationData(ids):api('/api/resources'));if(!current())return;job.revision=data.revision;
    const byId=new Map(data.resources.map(r=>[r.id,r]));job.resources=ids.map(id=>byId.get(id));
    if(job.resources.some(r=>!r))throw new Error('所选资源已变化，请刷新后重新选择。');
    const counts=new Map(Object.entries(data.tagCounts||{}));if(!data.tagCounts)for(const r of data.resources)for(const tag of r.tags)counts.set(tag,(counts.get(tag)||0)+1);
    job.catalog=[...counts].map(([name,count])=>({name,count,included:job.resources.filter(r=>r.tags.includes(name)).length})).sort((a,b)=>b.count-a.count||a.name.localeCompare(b.name,'zh-CN'));
    job.known=new Set(counts.keys());
    $('#manage-content').innerHTML=`<form data-manage-form="tag-picker"><p>为 ${ids.length} 条资源追加标签，已有标签与备注保留。</p><fieldset class="project-picker-fields"><label>搜索标签 / 输入新名称<input id="tag-picker-search" type="search" placeholder="搜索已有标签，或输入一个新标签" maxlength="100" aria-describedby="tag-picker-help"></label><p id="tag-picker-help" class="field-help">新名称需点击“选择新标签”再保存；一次输入一个名称，逗号也是名称的一部分。</p><div id="tag-picker-selected" class="project-picker-selected"></div><div id="tag-picker-create"></div><div id="tag-picker-results"></div><p class="field-help">每条资源最多 30 个标签，每个标签最多 50 个字符。</p></fieldset><div class="project-picker-actions"><button type="button" class="secondary" data-action="close-manage">取消</button><button type="submit" class="primary" id="tag-picker-save" disabled>添加所选标签</button></div><p id="tag-picker-status" class="field-help" role="status"></p></form>`;
    renderTagPicker();$('#tag-picker-search').focus();
  }catch(e){if(current()){$('#manage-content').innerHTML='<p>未能读取当前标签。请关闭后重新打开选择器。</p>';$('#manage-error').textContent=e.message;$('#manage-error').hidden=false;}}
}
function renderTagPicker(){
  const job=tagPicker,root=$('#tag-picker-results');if(!job||!root)return;
  const focus=ShijiCards.captureFocus(root),rows=tagPickerRows(job),pages=Math.max(1,Math.ceil(rows.length/100));job.page=Math.min(job.page,pages-1);
  root.innerHTML=rows.length?`<div class="project-picker-list">${rows.slice(job.page*100,job.page*100+100).map(t=>`<label class="project-picker-option"><input type="checkbox" data-tag-choice data-value="${esc(JSON.stringify(t.name))}" value="${esc(JSON.stringify(t.name))}" aria-label="选择标签 ${esc(t.name)}" ${job.selected.has(t.name)?'checked':''} ${t.included===job.ids.length?'disabled':''}><span><strong>${esc(t.name)}</strong><small>${t.included===job.ids.length?'已全部包含':t.included?`已包含 ${t.included} / ${job.ids.length} 条`:'尚未添加'} · 库中 ${t.count} 条资源</small></span></label>`).join('')}</div>${pages>1?`<div class="project-picker-pages"><button type="button" class="secondary" data-action="tag-picker-page" data-value="${job.page-1}" ${job.page===0?'disabled':''}>上一页</button><span>第 ${job.page+1} / ${pages} 页 · ${rows.length} 个标签</span><button type="button" class="secondary" data-action="tag-picker-page" data-value="${job.page+1}" ${job.page+1===pages?'disabled':''}>下一页</button></div>`:''}`:`<p class="project-picker-empty">${job.catalog.length?'没有匹配的已有标签。':'活动资源还没有标签，可以输入新名称。'}</p>`;
  ShijiCards.restoreFocus(root,focus,$('#tag-picker-search'));
  const selected=$('#tag-picker-selected'),snapshot=ShijiCards.captureFocus(selected);
  selected.innerHTML=`<p role="status">已选 ${job.selected.size} 个标签${job.search&&job.selected.size?'，搜索不会清除选择':''}</p>${job.selected.size?`<ul>${[...job.selected].map(([name,create])=>`<li><span>${esc(name)}${create?'（新标签）':''}</span><button type="button" class="text-button" data-action="tag-picker-remove" data-value="${esc(JSON.stringify(name))}" aria-label="取消选择标签 ${esc(name)}">移除</button></li>`).join('')}</ul>`:''}`;
  ShijiCards.restoreFocus(selected,snapshot,$('#tag-picker-search'));
  const query=job.search.trim(),length=Array.from(query).length;
  $('#tag-picker-create').innerHTML=query&&!job.known.has(query)?length>50?'<p class="field-help" role="status">新标签最多 50 个字符，请缩短名称。</p>':`<button type="button" class="secondary tag-picker-create" data-action="tag-picker-create" ${job.selected.has(query)?'disabled':''}>${job.selected.has(query)?'已选择新标签':'选择新标签'}：${esc(query)}</button>`:'';
  $('#tag-picker-save').disabled=!job.selected.size||job.busy;
}
function searchTagPicker(value){if(!tagPicker||tagPicker.busy)return;tagPicker.search=value;tagPicker.page=0;renderTagPicker();}
function chooseTagPicker(name,checked,create=false){
  const job=tagPicker;if(!job||job.busy)return;
  if(create){if(!name||name!==job.search.trim()||Array.from(name).length>50||job.known.has(name))return;}
  else if(!job.known.has(name)||job.resources.every(r=>r.tags.includes(name)))return;
  if(checked&&job.selected.size>=30&&!job.selected.has(name)){toast('一次最多选择 30 个标签。');renderTagPicker();return;}
  if(checked)job.selected.set(name,create);else job.selected.delete(name);renderTagPicker();
  if(create)$('#tag-picker-search').focus();
}
function handleTagPickerAction(action,el){
  const job=tagPicker;if(!job||job.busy)return;
  if(action==='tag-picker-create')chooseTagPicker(job.search.trim(),true,true);
  if(action==='tag-picker-remove'){job.selected.delete(JSON.parse(el.dataset.value));renderTagPicker();}
  if(action==='tag-picker-page'){const value=Number(el.dataset.value);if(!Number.isInteger(value)||value<0)return;job.page=value;renderTagPicker();$('#tag-picker-results input:not(:disabled)')?.focus();}
}
async function handleTagPickerForm(form,mode){
  if(mode!=='tag-picker')return false;
  const job=tagPicker;if(!job||job.busy||!job.selected.size)throw new Error('请选择标签后再保存。');
  const tags=[],create=[];for(const [name,isNew] of job.selected)(isNew?create:tags).push(name);
  job.busy=true;form.querySelector('fieldset').disabled=true;$('#tag-picker-status').textContent='正在保存标签…';
  try{
    const result=await (state.remote?selectedOperation('tags',{ids:job.ids,tags,create},job.revision):api('/api/tags/assign','POST',{ids:job.ids,tags,create}));
    $('#manage-dialog').close();
    try{await reload();}catch(e){toast('标签已保存，但未能刷新列表。请刷新页面查看。');return true;}
    if(state.detail&&!$('#drawer').hidden){detail(find(state.detail));$('#detail-content [data-action=assign-tags]')?.focus();}
    toast(result.changed?`已为 ${result.changed} 条资源添加标签。`:'所选资源已包含这些标签。');
  }finally{
    job.busy=false;if(form.isConnected){form.querySelector('fieldset').disabled=false;$('#tag-picker-status').textContent='';}
  }
  return true;
}

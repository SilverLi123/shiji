/* Bookmark file text is parsed by the local server, never inserted as HTML. */
function bookmarkIntake(){
  const saved=state.bookmarkSource||{};
  manage('导入浏览器书签',`<form data-manage-form="bookmark-preview"><p>先在 Chrome、Edge、Safari 或 Firefox 导出 HTML 书签文件，再在这里预览和选择。</p><label>书签 HTML 文件<input id="bookmark-file" type="file" accept=".html,.htm,text/html" ${saved.html?'':'required'}></label><p id="bookmark-file-state" class="field-help" role="status">${esc(saved.fileName?'已读取：'+saved.fileName:'支持 UTF-8 标准书签 HTML，最多 5 MB、2000 条。')}</p><label>新根项目名称<input name="rootName" value="${esc(saved.rootName||'浏览器书签')}" maxlength="80" required></label><label class="option-check"><input type="checkbox" name="preserveFolders" ${saved.preserveFolders!==false?'checked':''}>保留原文件夹结构</label><p class="field-help">建立新项目，同名时加数字后缀；不改变已有项目。最多保留九层原文件夹，取消勾选后全部放入根项目。空文件夹不导入。</p><button class="primary">预览书签</button></form>`);
}
function saveBookmarkEdits(){
  const draft=state.bookmarkDraft;if(!draft)return;
  document.querySelectorAll('[data-bookmark-line]').forEach(row=>{
    const line=Number(row.dataset.bookmarkLine),input=row.querySelector('.intake-title');
    if(input)draft.titles.set(line,input.value);
  });
  const tags=$('#bookmark-tags');if(tags)draft.tags=tags.value;
}
function bookmarkSelectedCount(){
  const draft=state.bookmarkDraft;if(!draft)return;
  $('#bookmark-selected').textContent=`已选 ${draft.selected.size} 条`;
  $('#bookmark-import-submit').disabled=!draft.selected.size;
  const all=$('#bookmark-select-all');all.checked=draft.selected.size===draft.result.new&&draft.result.new>0;all.indeterminate=draft.selected.size>0&&draft.selected.size<draft.result.new;
}
function renderBookmarkPreview(){
  const draft=state.bookmarkDraft,result=draft.result,page=draft.page,pages=Math.ceil(result.total/100);
  const counts=result.items.reduce((m,r)=>(m[r.status]=(m[r.status]||0)+1,m),{});
  const rows=result.items.slice(page*100,(page+1)*100);
  manage('确认导入浏览器书签',`<form data-manage-form="bookmark-import"><p>共 ${result.total} 条：${result.new} 条新网址，${counts.existing||0} 条已收藏，${counts.trash||0} 条在回收站，${counts.duplicate||0} 条文件内重复，${counts.invalid||0} 条无效。</p><p class="field-help">所选新书签放入「${esc(result.rootName)}」，已有记录保留原内容。同网址的多个文件夹归属随第一条导入。</p><label class="option-check"><input id="bookmark-select-all" type="checkbox" ${result.new?'':'disabled'}>选择全部新网址（跨页）</label><div class="intake-list bookmark-list">${rows.map(r=>{const selected=draft.selected.has(r.line);return `<div class="intake-row ${r.status==='new'?'':'intake-disabled'}" data-bookmark-line="${r.line}"><input type="checkbox" aria-label="导入书签第 ${r.line} 条" ${r.status==='new'?(selected?'checked':''):'disabled'}><div>${r.status==='new'?`<input class="intake-title" aria-label="书签第 ${r.line} 条名称" maxlength="200" required ${selected?'':'disabled'} value="${esc(draft.titles.get(r.line))}">`:`<strong>${esc(r.title)}</strong>`}<span class="intake-url">${esc(r.url)}</span><small>${esc(r.message)}</small><span class="bookmark-folder">原文件夹：${esc(r.folders.join(' / ')||'无文件夹')}</span>${r.projectPaths.length?`<span class="bookmark-folder">保存到：${r.projectPaths.map(p=>esc(p)).join('；')}</span>`:''}${r.tags.length||r.notes||r.createdAt?`<span class="bookmark-metadata">${r.tags.length?'标签：'+esc(r.tags.join('、'))+'；':''}${r.notes?'含描述；':''}${r.createdAt?'保留原收藏时间':''}</span>`:''}${r.warnings.length?`<span class="bookmark-warnings">${r.warnings.map(w=>esc(w)).join('；')}</span>`:''}</div></div>`;}).join('')}</div><div class="bookmark-pagination"><button type="button" class="secondary" data-action="bookmark-page" data-page="${page-1}" ${page?'':'disabled'}>上一页</button><span>第 ${page+1} / ${pages} 页 · 每页 100 条</span><button type="button" class="secondary" data-action="bookmark-page" data-page="${page+1}" ${page<pages-1?'':'disabled'}>下一页</button></div><label>统一添加标签<input id="bookmark-tags" name="tags" maxlength="1500" value="${esc(draft.tags)}" placeholder="可选，用逗号分隔"></label><p class="field-help">只创建所选书签所需的文件夹，保存到待整理；不会逐个访问网页。书签标签与统一标签合计最多 30 个。</p><div class="intake-actions"><button type="button" class="secondary" data-action="bookmark-intake">返回修改</button><span id="bookmark-selected"></span><button class="primary" id="bookmark-import-submit">导入所选书签</button></div></form>`);
  bookmarkSelectedCount();
}
function handleBookmarkAction(action,el){
  if(action==='bookmark-intake')bookmarkIntake();
  else if(action==='bookmark-page'){saveBookmarkEdits();state.bookmarkDraft.page=Number(el.dataset.page);renderBookmarkPreview();}
}
async function handleBookmarkForm(form,mode){
  if(mode==='bookmark-preview'){
    if(!state.bookmarkSource?.html)throw new Error('先选择并读取 HTML 书签文件。');
    state.bookmarkSource={...state.bookmarkSource,rootName:form.elements.rootName.value,preserveFolders:form.elements.preserveFolders.checked};
    const result=await api('/api/bookmarks/preview','POST',state.bookmarkSource);
    state.bookmarkDraft={result,page:0,selected:new Set(result.items.filter(r=>r.status==='new').map(r=>r.line)),titles:new Map(result.items.map(r=>[r.line,r.title])),tags:''};
    renderBookmarkPreview();return true;
  }
  if(mode==='bookmark-import'){
    saveBookmarkEdits();const draft=state.bookmarkDraft;
    const items=[...draft.selected].map(line=>({line,title:draft.titles.get(line)}));
    if(!items.length)throw new Error('先选择至少一条新书签。');
    const result=await api('/api/bookmarks/import','POST',{...state.bookmarkSource,planToken:draft.result.planToken,items,tags:split(draft.tags)});
    $('#manage-dialog').close();state.bookmarkSource=null;state.bookmarkDraft=null;
    await reload();selectScope('inbox');toast(`已导入 ${result.added} 条书签，建立 ${result.createdProjects} 个项目，进入待整理。`);return true;
  }
  return false;
}
document.addEventListener('change',async event=>{
  const el=event.target;
  if(el.id==='bookmark-file'){
    const file=el.files[0];if(!file)return;
    const form=el.closest('form'),button=form.querySelector('button.primary'),label=$('#bookmark-file-state');
    const readId=state.bookmarkReadId=(state.bookmarkReadId||0)+1;
    const current=()=>readId===state.bookmarkReadId&&form.isConnected&&$('#manage-dialog').open;
    button.disabled=true;label.textContent='正在读取书签文件…';
    state.bookmarkSource=null;
    try{
      if(file.size>5*1024*1024)throw new Error('书签 HTML 文件最多 5 MB。');
      const html=new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer());
      if(!current())return;
      state.bookmarkSource={html,fileName:file.name};label.textContent='已读取：'+file.name;$('#manage-error').hidden=true;
    }catch(e){if(current()){label.textContent='未能读取文件。';$('#manage-error').textContent=e instanceof TypeError?'请选择 UTF-8 HTML 文件，或从浏览器重新导出。':e.message;$('#manage-error').hidden=false;}}
    finally{if(current())button.disabled=false;}
  }
  const row=el.closest('[data-bookmark-line]');
  if(row&&el.type==='checkbox'){
    const line=Number(row.dataset.bookmarkLine);if(el.checked)state.bookmarkDraft.selected.add(line);else state.bookmarkDraft.selected.delete(line);
    const title=row.querySelector('.intake-title');if(title)title.disabled=!el.checked;bookmarkSelectedCount();
  }
  if(el.id==='bookmark-select-all'){
    saveBookmarkEdits();state.bookmarkDraft.selected=el.checked?new Set(state.bookmarkDraft.result.items.filter(r=>r.status==='new').map(r=>r.line)):new Set();renderBookmarkPreview();
  }
});

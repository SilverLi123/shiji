/* Targeted inline notes; never submit a stale full resource. */
let quickNoteEdit=null;
function quickNoteSection(r,kind,project,label){
  const value=kind==='notes'?r.notes:(Object.hasOwn(r.projectNotes||{},project)?r.projectNotes[project]:'');
  return `<section class="detail-block quick-note-section" data-note-section><div class="section-title"><h3>${esc(label)}</h3>${!r.deleted?`<button type="button" class="text-button" data-action="note-edit" data-id="${esc(r.id)}" data-kind="${kind}" data-project="${esc(JSON.stringify(project))}">${value?'编辑备注':'添加备注'}</button>`:''}</div><p data-note-text>${esc(value||'记下这个资源适合怎么使用。')}</p></section>`;
}
function syncQuickNoteResource(resource){
  if(!resource||resource.deleted)return;state.resources=state.resources.map(r=>r.id===resource.id?resource:r);render();
}
function quickNoteDirty(job=quickNoteEdit){return Boolean(job?.loaded&&job.form.isConnected&&job.input.value!==job.initial);}
function quickNoteMayLeave(){
  const job=quickNoteEdit;if(!job)return true;
  if(job.busy||quickNoteDirty(job)){toast(job.busy?'正在保存备注，请稍候。':'备注尚未保存，请先保存或取消编辑。');(job.busy?job.status:job.input).focus();return false;}
  cancelQuickNote(false);return true;
}
function cancelQuickNote(focus=true){
  const job=quickNoteEdit;if(!job||job.busy)return;
  quickNoteEdit=null;job.form.remove();if(job.loaded){job.text.textContent=job.expected||'记下这个资源适合怎么使用。';job.trigger.textContent=job.expected?'编辑备注':'添加备注';}job.text.hidden=false;job.trigger.hidden=false;if(focus&&job.trigger.isConnected)job.trigger.focus();
}
function quickNoteCurrent(job){return quickNoteEdit===job&&job.form.isConnected&&!$('#drawer').hidden&&state.detail===job.id;}
function updateQuickNoteControls(job){
  if(!quickNoteCurrent(job))return;
  const count=Array.from(job.input.value).length;job.count.textContent=`${count.toLocaleString('zh-CN')} / ${job.limit.toLocaleString('zh-CN')} 字符`;
  const invalid=count>job.limit;job.input.setAttribute('aria-invalid',String(invalid));job.count.classList.toggle('form-error',invalid);
  job.save.disabled=job.busy||!job.loaded||invalid||!quickNoteDirty(job);job.save.textContent=job.busy?'保存中…':job.conflict?'保存我的版本':'保存备注';
}
async function loadQuickNote(job){
  job.loading=true;job.status.textContent='正在读取最新备注…';job.retry.hidden=true;
  try{
    const {resource:r}=await api('/api/resources/'+encodeURIComponent(job.id));if(!quickNoteCurrent(job))return;
    if(r.deleted)throw new Error('资源已在回收站，请取消编辑并刷新页面。');
    syncQuickNoteResource(r);
    if(job.kind==='project'&&!r.projects.includes(job.project)&&!Object.hasOwn(r.projectNotes||{},job.project))throw new Error('项目备注已变化，请取消后重新打开资源。');
    job.expected=job.kind==='notes'?r.notes:(Object.hasOwn(r.projectNotes||{},job.project)?r.projectNotes[job.project]:'');
    job.input.value=job.expected;job.initial=job.input.value;job.loaded=true;job.input.disabled=false;job.status.textContent='';updateQuickNoteControls(job);job.input.focus();
  }catch(e){if(quickNoteCurrent(job)){job.status.textContent=e.message;job.retry.hidden=false;}}
  finally{job.loading=false;}
}
async function openQuickNote(trigger){
  if(!quickNoteMayLeave())return;
  const section=trigger.closest('[data-note-section]');if(!section)return;
  const kind=trigger.dataset.kind,project=JSON.parse(trigger.dataset.project),id=trigger.dataset.id;
  const form=document.createElement('form');form.className='quick-note-form';form.dataset.quickNoteForm='';
  form.innerHTML='<label for="quick-note-input" class="quick-note-label"></label><textarea id="quick-note-input" rows="5" aria-describedby="quick-note-count quick-note-status" disabled></textarea><p id="quick-note-count" class="field-help"></p><div class="quick-note-actions"><button type="button" class="secondary" data-action="note-cancel">取消编辑</button><button type="submit" class="primary" disabled>保存备注</button></div><p id="quick-note-status" class="field-help" role="status" tabindex="-1"></p><button type="button" class="text-button" data-action="note-retry" hidden>重试读取</button><details class="quick-note-conflict" hidden><summary>查看最新已保存的备注</summary><p class="field-help">输入内容仍保留。比较后可修改输入并“保存我的版本”，或取消编辑保留最新内容。</p><pre></pre></details>';
  form.querySelector('label').textContent=kind==='notes'?'收藏理由 / 使用备注':`项目备注：${project}`;
  const text=section.querySelector('[data-note-text]');text.hidden=true;trigger.hidden=true;section.append(form);
  const job=quickNoteEdit={id,kind,project,trigger,text,form,input:form.querySelector('textarea'),count:form.querySelector('#quick-note-count'),status:form.querySelector('#quick-note-status'),save:form.querySelector('[type=submit]'),retry:form.querySelector('[data-action=note-retry]'),limit:kind==='notes'?10000:2000,initial:'',expected:'',loaded:false,busy:false,loading:false,conflict:false};
  await loadQuickNote(job);
}
async function handleQuickNoteAction(action,el){
  if(action==='note-edit')return openQuickNote(el);
  const job=quickNoteEdit;if(!job||job.busy)return;
  if(action==='note-cancel')cancelQuickNote();
  if(action==='note-retry'&&!job.loading&&!job.loaded)await loadQuickNote(job);
}
async function saveQuickNote(form){
  const job=quickNoteEdit;if(!job||job.form!==form||job.busy||!job.loaded||!quickNoteDirty(job)||Array.from(job.input.value).length>job.limit)return;
  job.busy=true;job.input.disabled=true;form.querySelector('[data-action=note-cancel]').disabled=true;job.status.textContent='正在保存备注…';updateQuickNoteControls(job);
  try{
    const result=await api('/api/resources/'+encodeURIComponent(job.id)+'/note','POST',{kind:job.kind,project:job.project,expected:job.expected,value:job.input.value});if(!quickNoteCurrent(job))return;
    quickNoteEdit=null;state.resources=state.resources.map(r=>r.id===result.resource.id?result.resource:r);render();detail(result.resource);
    const next=[...$('#detail-content').querySelectorAll('[data-action=note-edit]')].find(el=>el.dataset.kind===job.kind&&JSON.parse(el.dataset.project)===job.project);(next||$('#drawer')).focus();toast(result.changed?'备注已保存。':'备注内容没有变化。');
  }catch(e){
    if(quickNoteCurrent(job)){
      job.status.textContent=e.message;
      if(e.status===409&&typeof e.current==='string'){
        if(e.resource?.id===job.id)syncQuickNoteResource(e.resource);job.expected=e.current;job.initial=e.current.replace(/\r\n?/g,'\n');job.conflict=true;const box=form.querySelector('.quick-note-conflict');box.hidden=false;box.open=true;box.querySelector('pre').textContent=e.current||'（空备注）';
      }
    }
  }finally{
    job.busy=false;if(quickNoteCurrent(job)){job.input.disabled=false;form.querySelector('[data-action=note-cancel]').disabled=false;updateQuickNoteControls(job);job.input.focus();}
  }
}
function initQuickNotes(){
  document.addEventListener('input',event=>{if(event.target===quickNoteEdit?.input)updateQuickNoteControls(quickNoteEdit);});
  document.addEventListener('submit',event=>{const form=event.target.closest('[data-quick-note-form]');if(form){event.preventDefault();saveQuickNote(form);}});
  window.addEventListener('beforeunload',event=>{if(quickNoteEdit?.busy||quickNoteDirty()){event.preventDefault();event.returnValue='';}});
}

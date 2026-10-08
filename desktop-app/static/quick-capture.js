/* Real capture uses the existing resource API; localStorage never stores resources. */
(function(root){
 'use strict';
 function parse(value){const raw=value.trim();if(/\s/.test(raw))throw new Error('网址中不能包含空格或换行。');let url;try{url=new URL(raw.includes('://')?raw:'https://'+raw);}catch{throw new Error('请输入有效的 HTTP 或 HTTPS 网址。');}if(!['https:','http:'].includes(url.protocol)||!url.hostname||url.username||url.password)throw new Error('请输入不含账户密码的 HTTP 或 HTTPS 网址。');url.hash='';return url;}
 function fallbackTitle(value){const url=parse(value),parts=url.pathname.split('/').filter(Boolean);return (/^(www\.)?github\.com$/i.test(url.hostname)&&parts.length>=2?parts.slice(0,2).join('/')+' · GitHub':url.hostname).slice(0,200);}
 function create({document:doc,api,context=()=>({}),onSaved=()=>{},onEnriched=()=>{},notice=()=>{},onFull=()=>{},timeoutMs=15000}){
  const dialog=doc.getElementById('quick-capture-dialog'),form=doc.getElementById('quick-capture-form'),input=doc.getElementById('quick-url'),button=doc.getElementById('quick-save'),error=doc.getElementById('quick-error');
  let busy=false,dead=false,lastFocus=null,capturedContext={};
  // Keep each unresolved write until its own response or reconciliation settles it.
  const pending=new Map(),maxPending=16;
  const clock=doc.defaultView;
  function bounded(promise){let timer;return Promise.race([promise,new Promise((_,reject)=>{timer=clock.setTimeout(()=>{const e=new Error('保存结果尚未确认。可以关闭窗口，稍后核对；请勿假定保存失败。');e.uncertain=true;reject(e);},timeoutMs);})]).finally(()=>clock.clearTimeout(timer));}
  function showError(message){error.textContent=message+' 草稿已保留。';error.hidden=false;}
  function setBusy(value){busy=value;input.readOnly=value;for(const el of dialog.querySelectorAll('button'))el.disabled=value;button.textContent=value?'正在保存…':'收藏链接';}
  function open(){if(dead||busy)return;lastFocus=doc.activeElement;capturedContext=context();error.hidden=true;if([...pending.values()].some(a=>a.uncertain))showError('上次保存结果尚未确认。再次提交会先核对资源库。');dialog.showModal();input.focus();}
  function close(){if(busy)return;dialog.close();}
  async function confirmed(attempt,result,late=false){
   if(dead||attempt.confirmed)return;attempt.confirmed=true;attempt.uncertain=false;if(pending.get(attempt.url)===attempt)pending.delete(attempt.url);
   if(!late){dialog.close();input.value='';}else if(dialog.open&&input.value.trim()===attempt.draft)error.hidden=true;
   try{await onSaved(result.resource,{sourceRect:late?null:attempt.sourceRect});}catch{notice('链接已收藏，但列表刷新失败。请刷新查看。');}
   if(dead)return;if(late)notice('刚才的链接已确认收藏。');
   // Separate bounded work: metadata can never undo a durable capture.
   api('/api/resources/'+result.resource.id+'/enrich','POST',{url:result.resource.url,updatedAt:result.resource.updatedAt}).then(result=>{if(!dead)return onEnriched(result);}).catch(()=>{});
  }
  async function submit(event){event.preventDefault();if(busy||dead)return;error.hidden=true;
   let attempt;
   try{const url=parse(input.value);if(url.href.length>4000)throw new Error('网址不能超过 4000 个字符。');setBusy(true);
    const previous=pending.get(url.href);
    if(previous?.uncertain){
     const latest=await bounded(api('/api/resources'));
     if(dead)return;
     const resource=latest.resources.find(r=>r.url===url.href);
     if(resource){await confirmed(previous,{resource});return;}
     if(previous.confirmed){dialog.close();input.value='';return;}
     if(previous.uncertain)throw new Error('资源库尚未返回这条链接，原请求仍待确认。可以关闭窗口，稍后核对或刷新应用。');
    }
    if(pending.size>=maxPending)throw new Error('已有多条收藏请求等待确认。请稍后核对资源库或刷新应用后再收藏新链接。');
    attempt={url:url.href,draft:input.value,sourceRect:button.getBoundingClientRect(),confirmed:false,uncertain:false};pending.set(url.href,attempt);
    const request=api('/api/resources','POST',{url:url.href,title:fallbackTitle(url.href),kind:'website',category:/^(www\.)?github\.com$/i.test(url.hostname)?'开发工具':'其他',inbox:true,projects:capturedContext.projects||[]});
    try{const result=await bounded(request);if(!dead)await confirmed(attempt,result);}
    catch(e){if(e.uncertain){attempt.uncertain=true;request.then(result=>confirmed(attempt,result,true),failure=>{attempt.uncertain=false;if(pending.get(attempt.url)===attempt)pending.delete(attempt.url);if(!dead&&dialog.open&&input.value.trim()===attempt.draft)showError(failure.message+' 可以修改或重试。');}).catch(()=>{});}else if(pending.get(attempt.url)===attempt)pending.delete(attempt.url);throw e;}
   }catch(e){if(!dead){showError(e.message);input.focus();}}
   finally{if(!dead)setBusy(false);}
  }
  function cancel(e){if(busy){e.preventDefault();notice('正在保存，请稍候。');}}
  function click(e){if(e.target.closest('[data-quick-close]'))close();if(e.target.closest('[data-quick-full]')&&!busy){const value=input.value;close();onFull(value);}}
  function restoreFocus(){if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});}
  form.addEventListener('submit',submit);dialog.addEventListener('cancel',cancel);dialog.addEventListener('click',click);dialog.addEventListener('close',restoreFocus);
  return {open,submit,isBusy:()=>busy,destroy(){dead=true;form.removeEventListener('submit',submit);dialog.removeEventListener('cancel',cancel);dialog.removeEventListener('click',click);dialog.removeEventListener('close',restoreFocus);}};
 }
 const api={create,fallbackTitle};if(typeof module==='object')module.exports=api;else root.ShijiQuickCapture=api;
})(typeof window==='object'?window:globalThis);

/* Real capture uses the existing resource API; localStorage never stores resources. */
(function(root){
 'use strict';
 function parse(value){const raw=value.trim();if(/\s/.test(raw))throw new Error('网址中不能包含空格或换行。');let url;try{url=new URL(raw.includes('://')?raw:'https://'+raw);}catch{throw new Error('请输入有效的 HTTP 或 HTTPS 网址。');}if(!['https:','http:'].includes(url.protocol)||!url.hostname||url.username||url.password)throw new Error('请输入不含账户密码的 HTTP 或 HTTPS 网址。');url.hash='';return url;}
 function fallbackTitle(value){const url=parse(value),parts=url.pathname.split('/').filter(Boolean);return (/^(www\.)?github\.com$/i.test(url.hostname)&&parts.length>=2?parts.slice(0,2).join('/')+' · GitHub':url.hostname).slice(0,200);}
 function create({document:doc,api,context=()=>({}),onSaved=()=>{},onEnriched=()=>{},notice=()=>{},onFull=()=>{}}){
  const dialog=doc.getElementById('quick-capture-dialog'),form=doc.getElementById('quick-capture-form'),input=doc.getElementById('quick-url'),button=doc.getElementById('quick-save'),error=doc.getElementById('quick-error');
  let busy=false,dead=false,lastFocus=null,capturedContext={};
  function setBusy(value){busy=value;input.readOnly=value;for(const el of dialog.querySelectorAll('button'))el.disabled=value;button.textContent=value?'正在保存…':'收藏链接';}
  function open(){if(dead||busy)return;lastFocus=doc.activeElement;capturedContext=context();error.hidden=true;dialog.showModal();input.focus();}
  function close(){if(busy)return;dialog.close();}
  async function submit(event){event.preventDefault();if(busy||dead)return;error.hidden=true;
   try{const url=parse(input.value);if(url.href.length>4000)throw new Error('网址不能超过 4000 个字符。');setBusy(true);
    const sourceRect=button.getBoundingClientRect();
    const result=await api('/api/resources','POST',{url:url.href,title:fallbackTitle(url.href),kind:'website',category:/^(www\.)?github\.com$/i.test(url.hostname)?'开发工具':'其他',inbox:true,projects:capturedContext.projects||[]});
    if(dead)return;setBusy(false);dialog.close();input.value='';
    try{await onSaved(result.resource,{sourceRect});}catch{notice('链接已收藏，但列表刷新失败。请刷新查看。');}
    if(dead)return;
    // This request starts only after durable save. Failure cannot undo the capture.
    api('/api/resources/'+result.resource.id+'/enrich','POST',{url:result.resource.url,updatedAt:result.resource.updatedAt}).then(result=>{if(!dead)return onEnriched(result);}).catch(()=>{});
   }catch(e){if(!dead){error.textContent=e.message+' 草稿已保留，可以修改或重试。';error.hidden=false;input.focus();}}
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

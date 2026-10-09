/* Presentation only. Resource state and mutations remain in app.js. */
(function(root){
 'use strict';
 function cardType(r){
  if(['code','prompt'].includes(r.kind))return 'text';
  if(r.kind==='website'&&r.category==='开发工具')return 'tool';
  return 'visual';
 }
 const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function source(r){try{return new URL(r.url||r.sourceUrl).hostname.replace(/^www\./,'');}catch{return '';}}
 function coverKind(r){
  if(r.kind==='code')return 'code';
  if(r.kind==='prompt')return 'prompt';
  if(r.kind==='file')return 'file';
  return r.category==='开发工具'||source(r)==='github.com'?'tool':'editorial';
 }
 // Derived display only: no guessed stars, tech stacks, authors or remote assets.
 function coverMarkup(r){
  const kind=coverKind(r),host=source(r),title=escape(r.title),category=escape(r.category||''),body=String(r.snippet||r.description||r.notes||'');
  const attachments=Array.isArray(r.attachments)?r.attachments:[];
  const label=kind==='code'?(r.language||'代码片段'):kind==='prompt'?'提示词':kind==='file'?'本地素材':host;
  const top=`<span class="cover-source">${escape(label)}</span><span class="cover-category">${category}</span>`;
  let content='',footer='';
  if(kind==='code'){
   const lines=body.slice(0,6000).split('\n');
   content=`<span class="cover-code-lines snippet-preview"><code>${lines.slice(0,9).map(line=>`<span class="cover-code-line">${escape(line)||' '}</span>`).join('')}</code></span>`;
   footer=`<span>${title}</span><span>${body?body.split('\n').length+' 行':''}</span>`;
  }else{
   content=`<strong class="cover-title">${title}</strong>${body?`<span class="cover-excerpt">${escape(body.slice(0,500))}</span>`:''}`;
   let meta='';
   if(kind==='tool'){
    if(host==='github.com'){try{meta=new URL(r.url).pathname.split('/').filter(Boolean).slice(0,2).join(' / ');}catch{}}
    footer=`<span>${escape(meta||host)}</span>${r.language?`<span>${escape(r.language)}</span>`:''}`;
   }else if(kind==='file')footer=`<span>${escape(attachments[0]?.name||'')}</span><span>${attachments.length?attachments.length+' 个附件':''}</span>`;
   else footer=`<span>${host?escape(host):category}</span>${r.author?`<span>${escape(r.author)}</span>`:''}`;
  }
  return `<span class="domain-mark resource-cover cover-${kind}" aria-hidden="true"><span class="cover-meta">${top}</span><span class="cover-content">${content}</span><span class="cover-bottom">${footer}</span></span>`;
 }
 function render(doc,state){
  const hero=doc.getElementById('shiji-hero');
  if(hero)hero.hidden=state.scope!=='all'||state.view!=='grid'||Object.entries(state.filters||{}).some(([key,v])=>!['tagMode','includeSubdomains'].includes(key)&&(typeof v==='boolean'||(Array.isArray(v)?v.length:!!v)));
  const ticker=doc.getElementById('shiji-ticker');if(ticker)ticker.hidden=!!hero?.hidden;
 }
 const api={cardType,coverKind,coverMarkup,render};if(typeof module==='object')module.exports=api;else root.ShijiV2=api;
})(typeof window==='object'?window:globalThis);

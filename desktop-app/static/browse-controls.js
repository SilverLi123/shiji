(function(root){
 const labels={search:'搜索',category:'分类',price:'价格',license:'授权',kind:'形式',linkStatus:'链接',color:'颜色',collection:'项目',domain:'域名',mediaType:'附件',createdFrom:'开始日期',createdTo:'结束日期',tags:'标签',excludeTags:'排除标签',favorite:'常用',inbox:'待整理',hasAssets:'有素材',isSnippet:'代码或提示词',noTags:'没有标签',noProjects:'没有项目',hasNotes:'有备注'};
 function conditions(filters,canonical){return Object.entries(canonical(filters)).filter(([key])=>!['tagMode','includeSubdomains'].includes(key)).flatMap(([key,value])=>(Array.isArray(value)?value:[value]).map(v=>({key,value:v,label:labels[key]+(typeof v==='boolean'?'：'+(v?'是':'否'):'：'+v)})));}
 function remove(filters,key,value){const next={...filters};if(['tags','excludeTags'].includes(key))next[key]=(next[key]||[]).filter(x=>x!==value);else delete next[key];if(key==='domain')delete next.includeSubdomains;if(key==='tags'&&!next.tags.length)delete next.tagMode;return next;}
 function bind(doc){
  const toggles=[...doc.querySelectorAll('[data-browse-toggle]')];let current=null;
  function close(focus=true){if(!current)return;const last=current;doc.getElementById(last.dataset.browseToggle).hidden=true;last.setAttribute('aria-expanded','false');current=null;if(focus)last.focus();}
  for(const toggle of toggles)toggle.addEventListener('click',()=>{if(current===toggle){close();return;}close(false);current=toggle;doc.getElementById(toggle.dataset.browseToggle).hidden=false;toggle.setAttribute('aria-expanded','true');});
  doc.addEventListener('keydown',e=>{if(e.key==='Escape'&&current&&!doc.querySelector('dialog[open]')){e.preventDefault();close();}},true);
  doc.addEventListener('click',e=>{if(current&&!current.contains(e.target)&&!doc.getElementById(current.dataset.browseToggle).contains(e.target))close();});
  return {close};
 }
 const api={bind,conditions,remove};if(typeof module==='object')module.exports=api;else root.ShijiControls=api;
})(typeof window==='object'?window:globalThis);

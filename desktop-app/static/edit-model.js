/* Changed-field editing: initial displayed values and exact server expectations. */
(function(root){
  'use strict';
  const fields=['url','title','kind','category','description','notes','snippet','language','author','sourceUrl','parentId','price','license','thumbnail','licenseUrl','favicon','tags','projects','favorite','inbox'];
  const labels={url:'资源网址',title:'名称',kind:'资源形式',category:'资源类型',description:'简短介绍',notes:'收藏理由 / 使用备注',snippet:'代码 / 提示词',language:'语言',author:'作者',sourceUrl:'原始来源网址',parentId:'来源资源',price:'价格',license:'授权',thumbnail:'预览图片网址',licenseUrl:'授权说明网址',favicon:'网站图标',tags:'标签',projects:'项目集合',favorite:'常用',inbox:'待整理',coverId:'封面'};
  const clone=v=>JSON.parse(JSON.stringify(v));
  const norm=v=>typeof v==='string'?v.replace(/\r\n?/g,'\n').trim():v;
  const same=(a,b)=>JSON.stringify(norm(a))===JSON.stringify(norm(b));
  function read(doc,state,split){
    const raw={coverId:state.formBase.coverId||'',favicon:state.formBase.favicon||'',demo:false};
    for(const k of fields){if(k==='favicon')continue;const el=doc.querySelector('#f-'+k);raw[k]=k==='tags'?[...(state.formTags||[])]:k==='projects'?split(el.value):['favorite','inbox'].includes(k)?el.checked:el.value;}
    raw.projectNotes=Object.assign(Object.create(null),state.formProjects);
    for(const p of raw.projects)if(!Object.hasOwn(raw.projectNotes,p))raw.projectNotes[p]='';
    return raw;
  }
  function start(doc,state,split,item){state.formSnapshot=clone(item||{});state.formInitial=read(doc,state,split);state.formConflict=null;}
  function diff(draft,initial,resource){
    const changes={},expected={};
    for(const k of fields)if(!same(draft[k],initial[k])){changes[k]=draft[k];expected[k]=resource[k];}
    const notes=Object.create(null),old=Object.create(null);
    for(const [k,v] of Object.entries(draft.projectNotes||{}))if(!Object.hasOwn(initial.projectNotes||{},k)||!same(v,initial.projectNotes[k])){
      notes[k]=v;old[k]=Object.hasOwn(resource.projectNotes||{},k)?resource.projectNotes[k]:null;
    }
    if(Object.keys(notes).length){changes.projectNotes=notes;expected.projectNotes=old;}
    return {changes,expected};
  }
  function rebase(resource,latest,conflicts){
    const base=clone(resource);base.projectNotes=Object.assign(Object.create(null),base.projectNotes);
    for(const c of conflicts)if(c.field==='projectNotes'){
      if(Object.hasOwn(latest.projectNotes||{},c.key))base.projectNotes[c.key]=latest.projectNotes[c.key];else delete base.projectNotes[c.key];
    }else if(fields.includes(c.field))base[c.field]=clone(latest[c.field]);
    return base;
  }
  function text(value){return value===null?'（尚未记录）':value===''?'（空）':typeof value==='boolean'?(value?'是':'否'):Array.isArray(value)?value.join('、'):String(value);}
  const api={fields,labels,read,start,diff,rebase,text,clone};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiEdit=api;
})(typeof window==='object'?window:globalThis);

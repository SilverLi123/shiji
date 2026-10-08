/* Display batches only; search, sorting, selection and galleries keep full results. */
(function(root){
  'use strict';
  const lanes=[['website','网站参考'],['file','素材文件'],['code','代码片段'],['prompt','提示词']];
  function create(step=60){
    let query=null,limit=step;
    return {
      more(){limit+=step;},
      plan(items,key,view){
        if(key!==query){query=key;limit=step;}
        const groups=view==='board'?lanes.map(([kind,label])=>{
          const matches=items.filter(r=>r.kind===kind);
          return {kind,label,total:matches.length,items:matches.slice(0,limit)};
        }).filter(g=>g.total):[];
        const visible=view==='board'?groups.flatMap(g=>g.items):items.slice(0,limit);
        const nextCount=view==='board'?groups.reduce((n,g)=>n+Math.min(step,g.total-g.items.length),0):Math.min(step,items.length-visible.length);
        return {items:visible,groups,total:items.length,visibleCount:visible.length,hasMore:visible.length<items.length,nextCount};
      }
    };
  }
  const api={create};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiBrowse=api;
})(typeof window==='object'?window:globalThis);

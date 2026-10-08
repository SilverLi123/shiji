(function(root){
  'use strict';
  const terminal=row=>['saved','skipped'].includes(row.result);
  const pending=rows=>rows.filter(row=>row.selected&&!terminal(row)&&row.status!=='invalid');
  const counts=rows=>({selected:rows.filter(r=>r.selected).length,saved:rows.filter(r=>r.result==='saved').length,skipped:rows.filter(r=>r.result==='skipped').length,failed:rows.filter(r=>r.result==='failed').length,remaining:pending(rows).length});
  const initial=rows=>rows.map(row=>({...row,selected:row.status==='new',result:'',requestId:''}));
  const page=(rows,index,length=20)=>rows.slice(index*length,(index+1)*length);
  const model={terminal,pending,counts,initial,page};
  if(typeof module==='object'&&module.exports)module.exports=model;else root.ShijiAssets=model;
})(typeof globalThis==='object'?globalThis:this);

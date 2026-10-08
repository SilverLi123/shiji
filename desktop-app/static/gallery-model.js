/* A gallery is a snapshot of the caller's ordered, filtered resources. */
(function(root){
  'use strict';
  function images(resource){
    const entries=(resource.attachments||[]).filter(a=>a.mime?.startsWith('image/')).map(a=>({
      kind:'image',mime:a.mime,key:a.id,resourceId:resource.id,resourceTitle:resource.title,name:a.name,
      src:'/api/files/'+encodeURIComponent(a.id),download:'/api/files/'+encodeURIComponent(a.id)+'?download=1',
      author:a.author||'',license:a.license||'待确认',sourceUrl:a.sourceUrl||'',licenseUrl:a.licenseUrl||'',size:a.size,inTrash:!!resource.deleted
    }));
    if(!entries.length&&resource.thumbnail)entries.push({kind:'image',key:resource.id+'/thumbnail',resourceId:resource.id,resourceTitle:resource.title,name:resource.title+' · 网页缩略图',src:resource.thumbnail,download:'',author:resource.author||'',license:resource.license||'待确认',sourceUrl:resource.sourceUrl||resource.url||'',licenseUrl:resource.licenseUrl||'',inTrash:!!resource.deleted});
    return entries;
  }
  function queue(resources,owner,key){
    const chosen=owner&&!resources.some(r=>r.id===owner.id)?[owner]:resources;
    const items=chosen.flatMap(images);
    return {items,index:Math.max(0,items.findIndex(a=>a.key===key))};
  }
  function media(resource){
    const pictures=images(resource),byKey=new Map(pictures.map(item=>[item.key,item]));
    const entries=(resource.attachments||[]).flatMap(a=>{
      if(byKey.has(a.id))return [byKey.get(a.id)];
      const kind=a.mime?.startsWith('audio/')?'audio':a.mime?.startsWith('video/')?'video':'';
      return kind?[{kind,mime:a.mime,key:a.id,resourceId:resource.id,resourceTitle:resource.title,name:a.name,
        src:'/api/files/'+encodeURIComponent(a.id),download:'/api/files/'+encodeURIComponent(a.id)+'?download=1',
        author:a.author||'',license:a.license||'待确认',sourceUrl:a.sourceUrl||'',licenseUrl:a.licenseUrl||'',size:a.size,inTrash:!!resource.deleted}]:[];
    });
    if(!pictures.some(item=>item.download))entries.push(...pictures);
    return entries;
  }
  function mediaQueue(resources,owner,key){
    const chosen=owner&&!resources.some(r=>r.id===owner.id)?[owner]:resources;
    const items=chosen.flatMap(media);
    const index=key?items.findIndex(item=>item.key===key):owner?items.findIndex(item=>item.resourceId===owner.id):0;
    return {items,index:Math.max(0,index)};
  }
  const api={images,queue,media,mediaQueue};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiGallery=api;
})(typeof window==='object'?window:globalThis);

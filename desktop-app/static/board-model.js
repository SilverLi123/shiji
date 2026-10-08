/* Bundled homepage captures are display fallbacks, never attachment records. */
(function(root){
  'use strict';
  const pages={'recent.co':'recent','motionsites.ai':'motionsites','reactbits.dev':'reactbits','polyhaven.com':'polyhaven','freesound.org':'freesound'};
  function cover(resource){
    if(resource.coverId)return '/api/files/'+encodeURIComponent(resource.coverId);
    if(resource.thumbnail)return resource.thumbnail;
    if(resource.kind!=='website')return '';
    try{const url=new URL(resource.url);if(!['http:','https:'].includes(url.protocol)||url.username||url.password||url.pathname!=='/'||url.search||url.hash)return '';const page=pages[url.hostname.replace(/^www\./,'')];return page?'previews/'+page+'.jpg':'';}catch{return '';}
  }
  function galleryResource(resource){
    return resource.thumbnail?resource:{...resource,thumbnail:cover({...resource,coverId:''})};
  }
  const api={cover,galleryResource};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiBoard=api;
})(typeof window==='object'?window:globalThis);

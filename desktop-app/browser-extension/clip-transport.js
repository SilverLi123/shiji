/* Receipt-first delivery: ambiguous POST results never trigger blind creation. */
(function(root){
 'use strict';
 const problem=(message,flags={})=>Object.assign(new Error(message),flags);
 function create(fetcher=root.fetch.bind(root)){
  async function request(setting,path,body={}){
   let response;
   try{response=await fetcher(setting.base+path,{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+setting.token},body:JSON.stringify(body),signal:AbortSignal.timeout(path==='/api/clip'?12000:4000)});}
   catch{throw problem('电脑暂未连接，内容已留在浏览器，稍后自动重试。',{retryable:true,halt:true});}
   if(response.status===401||response.status===403)throw problem('配对不可用，请检查原资源库的连接设置。',{blocked:true,halt:true});
   if(response.status===404)throw problem('电脑端版本不支持可靠采集，请更新后重试。',{blocked:true,halt:true});
   if(!response.ok)throw problem(response.status>=500||response.status===429?'电脑暂时无法保存，稍后自动重试。':'电脑未接受这条内容，请检查原网页或重新采集。',{retryable:response.status>=500||response.status===429,halt:response.status>=500||response.status===429});
   try{return await response.json();}catch{throw problem('电脑返回的结果尚未确认，会先核对回执再重试。',{retryable:true,halt:true});}
  }
  async function ping(setting){return request(setting,'/api/clip/ping');}
  async function send(row,setting){
   const capability=await ping(setting);
   if(capability.captureReceipts!==1)throw problem('请更新电脑端以支持可靠采集，待发送内容已保留。',{blocked:true,halt:true});
   const receipt=await request(setting,'/api/clip/status',{requestId:row.id});
   if(receipt.requestId!==row.id||!['saved','not_found'].includes(receipt.status))throw problem('收藏回执无效，内容已保留，稍后重新核对。',{retryable:true,halt:true});
   if(receipt.status==='saved')return {receipt};
   return request(setting,'/api/clip',{...row.payload,requestId:row.id});
  }
  return {send,ping};
 }
 const api={create};if(typeof module==='object')module.exports=api;else root.ShijiClipTransport=api;
})(typeof self==='object'?self:globalThis);

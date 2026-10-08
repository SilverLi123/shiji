(function(root){
  'use strict';
  function settings(base,token){const url=new URL(base);if(url.protocol!=='http:'||!['127.0.0.1','localhost'].includes(url.hostname)||url.username||url.password||url.search||url.hash||!['','/'].includes(url.pathname))throw new Error('本地地址须为 http://127.0.0.1:端口 或 http://localhost:端口。');if(typeof token!=='string'||token.trim().length<32||token.trim().length>128)throw new Error('请从资源库的“浏览器采集”复制配对码。');return {base:url.origin,token:token.trim()};}
  function imageURL(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href.slice(0,4000):'';}catch{return '';}}
  function payload(page,selection=''){const url=new URL(page.url);if(!['http:','https:'].includes(url.protocol)||url.username||url.password)throw new Error('请打开普通网站后再收藏。');return {url:url.href,title:String(page.title||url.hostname).slice(0,200),selection:String(selection||page.selection||'').slice(0,10000),description:String(page.description||'').slice(0,1000),thumbnail:imageURL(page.thumbnail),favicon:imageURL(page.favicon)};}
  const api={settings,payload};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiClip=api;
})(typeof self==='object'?self:globalThis);

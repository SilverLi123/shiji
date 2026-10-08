/* Presentation only. Resource state and mutations remain in app.js. */
(function(root){
 'use strict';
 function cardType(r){
  if(['code','prompt'].includes(r.kind))return 'text';
  if(r.kind==='website'&&r.category==='开发工具')return 'tool';
  return 'visual';
 }
 function render(doc,state){
  const hero=doc.getElementById('shiji-hero');
  if(hero)hero.hidden=state.scope!=='all'||state.view!=='grid'||Object.entries(state.filters||{}).some(([key,v])=>!['tagMode','includeSubdomains'].includes(key)&&(typeof v==='boolean'||(Array.isArray(v)?v.length:!!v)));
  const ticker=doc.getElementById('shiji-ticker');if(ticker)ticker.hidden=!!hero?.hidden;
 }
 const api={cardType,render};if(typeof module==='object')module.exports=api;else root.ShijiV2=api;
})(typeof window==='object'?window:globalThis);

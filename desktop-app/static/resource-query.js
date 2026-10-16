/* Query transport only: resource ownership stays in the existing application state. */
(function(root){
 'use strict';
 function create({request,apply,busy=()=>{}}){
  let epoch=0,controller=null,timer=null,settle=null,destroyed=false;
  function cancel(){epoch++;clearTimeout(timer);timer=null;controller?.abort();settle?.(null);settle=null;}
  function load(body,{append=false,delay=0}={}){
   cancel();if(destroyed)return Promise.resolve(null);const run=epoch;controller=new AbortController();const signal=controller.signal;busy(true);
   return new Promise((resolve,reject)=>{settle=resolve;const start=async()=>{timer=null;try{const result=await request(body,signal);if(run!==epoch||destroyed){resolve(null);return;}apply(result,body,append);resolve(result);}catch(e){if(run===epoch&&e.name!=='AbortError')reject(e);else resolve(null);}finally{if(run===epoch){settle=null;busy(false);}}};if(delay)timer=setTimeout(start,delay);else start();});
  }
  return {load,cancel,destroy(){destroyed=true;cancel();busy(false);}};
 }
 function mark(element,ranges){
  const text=Array.from(element.textContent),doc=element.ownerDocument,parts=[];let last=0;
  for(const [a,b] of ranges||[]){if(a<last||a<0||b>text.length||b<=a)continue;parts.push(doc.createTextNode(text.slice(last,a).join('')));const node=doc.createElement('mark');node.className='search-match';node.textContent=text.slice(a,b).join('');parts.push(node);last=b;}
  parts.push(doc.createTextNode(text.slice(last).join('')));element.replaceChildren(...parts);
 }
 function ranges(value,terms){
  const chars=Array.from(value),positions=[],lower=chars.map((ch,i)=>{const text=ch.toLowerCase();positions.push(...Array.from(text,()=>i));return text}).join(''),spans=[];
  for(const term of terms){let start=0;while(term){const index=lower.indexOf(term,start);if(index<0||spans.length>=200)break;const a=Array.from(lower.slice(0,index)).length,b=a+Array.from(term).length;spans.push([positions[a],positions[b-1]+1]);start=index+term.length;}}
  const merged=[];for(const [a,b] of spans.sort((a,b)=>a[0]-b[0])){if(merged.length&&a<=merged.at(-1)[1])merged.at(-1)[1]=Math.max(b,merged.at(-1)[1]);else merged.push([a,b]);}return merged;
 }
 function recent(storage){try{const list=JSON.parse(storage.getItem('shiji-search-history')||'[]');return Array.isArray(list)?list.filter(x=>typeof x==='string'&&x.length<=200).slice(0,8):[];}catch{return [];}}
 function remember(storage,query){query=query.trim();if(!query||query.length>200)return;try{storage.setItem('shiji-search-history',JSON.stringify([query,...recent(storage).filter(x=>x!==query)].slice(0,8)));}catch{}}
 const api={create,mark,ranges,recent,remember};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiQuery=api;
})(typeof window==='object'?window:globalThis);

/* Pixel descriptors are temporary search data; resource records remain untouched. */
(function(root){
  'use strict';
  const SIDE=16,STRICT=.18,BROAD=.32,PAGE=20;
  function descriptor(rgba){
    if(rgba.length!==SIDE*SIDE*4)throw new Error('无法读取图片像素。');
    const pixels=[],gray=[],mean=[0,0,0];
    for(let i=0;i<rgba.length;i+=4){const alpha=rgba[i+3]/255;let luminance=0;
      for(let c=0;c<3;c++){const v=(rgba[i+c]*alpha+255*(1-alpha))/255;pixels.push(v);mean[c]+=v/(SIDE*SIDE);luminance+=v*[.2126,.7152,.0722][c];}gray.push(luminance);
    }
    const center=gray.reduce((a,b)=>a+b,0)/gray.length;
    const spread=Math.sqrt(gray.reduce((sum,v)=>sum+(v-center)**2,0)/gray.length);
    return {pixels,mean,structure:gray.map(v=>(v-center)/Math.max(spread,.04))};
  }
  function distance(a,b){
    const rms=(x,y)=>Math.sqrt(x.reduce((s,v,i)=>s+(v-y[i])**2,0)/x.length);
    return Math.min(1,.55*rms(a.pixels,b.pixels)+.25*Math.min(1,rms(a.structure,b.structure)/2)+.20*rms(a.mean,b.mean));
  }
  function candidates(resources,owner,key){
    const snapshot=resources.filter(r=>!!r.deleted===!!owner.deleted&&(r.attachments||[]).some(a=>!a.deleted&&a.mime?.startsWith('image/')&&a.id!==key)).map(r=>structuredClone(r));
    return snapshot.flatMap(r=>(r.attachments||[]).filter(a=>!a.deleted&&a.mime?.startsWith('image/')&&a.id!==key).map(a=>({resource:r,attachment:a})));
  }
  function ranked(rows,mode='strict'){
    const limit=mode==='broad'?BROAD:STRICT;
    return rows.filter(r=>r.distance<=limit).slice().sort((a,b)=>a.distance-b.distance||a.attachment.id.localeCompare(b.attachment.id));
  }
  function page(rows,number){const count=Math.max(1,Math.ceil(rows.length/PAGE)),index=Math.max(0,Math.min(count-1,number));return {rows:rows.slice(index*PAGE,(index+1)*PAGE),index,count,total:rows.length};}
  async function scan(subject,entries,read,signal,update=()=>{}){
    const outcome={rows:[],failures:[],checked:0,cancelled:false};
    const stopped=()=>{if(signal.aborted){outcome.cancelled=true;return true;}return false;};
    if(stopped())return outcome;
    const reference=await read(subject,signal);if(stopped())return outcome;
    for(const entry of entries){
      if(stopped())break;
      try{const value=await read(entry.attachment,signal);if(stopped())break;outcome.rows.push({...entry,distance:distance(reference,value)});}
      catch(e){if(stopped())break;outcome.failures.push({id:entry.attachment.id,name:entry.attachment.name,resourceId:entry.resource.id,resourceTitle:entry.resource.title,message:e.message||'无法读取'});}
      outcome.checked++;update(outcome);
    }
    return outcome;
  }
  const api={SIDE,STRICT,BROAD,PAGE,descriptor,distance,candidates,ranked,page,scan};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiSimilar=api;
})(typeof window==='object'?window:globalThis);

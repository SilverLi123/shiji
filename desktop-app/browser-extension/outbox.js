/* One durable delivery queue. Parsing/enrichment stays in the desktop engine. */
(function(root){
 'use strict';
 const KEY='captureOutboxV1',DONE='captureDeliveredV1',MAX_BYTES=8*1024*1024,MAX_ITEMS=100;
 const clone=value=>JSON.parse(JSON.stringify(value));
 async function pairKey(config,cryptoAPI=root.crypto){
  const raw=new TextEncoder().encode(config.base+'\0'+config.token);
  return [...new Uint8Array(await cryptoAPI.subtle.digest('SHA-256',raw))].map(v=>v.toString(16).padStart(2,'0')).join('');
 }
 function create({storage,send,config,now=Date.now,id=()=>root.crypto.randomUUID(),pairKey:identify=pairKey}){
  let lane=Promise.resolve(),draining=null;
  const serial=fn=>{const next=lane.then(fn);lane=next.catch(()=>{});return next;};
  async function read(){
   const value=(await storage.get(KEY))[KEY]??[];
   if(!Array.isArray(value)||value.some(r=>!r||typeof r.id!=='string'||!r.payload||typeof r.payload.url!=='string'||!['pending','sending','failed','blocked'].includes(r.state)))throw new Error('待发送记录无法读取，请保留扩展数据并检查版本。');
   return clone(value);
  }
  async function write(rows,{receipts,admitting=false}={}){
   // Reserve room for attempts, timestamps and bounded error text at admission.
   // State recovery/removal must also work for a pre-upgrade near-cap queue.
   if(admitting&&(rows.length>MAX_ITEMS||new TextEncoder().encode(JSON.stringify(rows)).byteLength+rows.length*2048>MAX_BYTES))throw new Error('待发送空间已达上限，请先发送或移除旧记录；这次内容尚未保存。');
   await storage.set({[KEY]:rows,...(receipts?{[DONE]:receipts}:{})});
  }
  const ready=serial(async()=>{const rows=await read();let changed=false;for(const r of rows)if(r.state==='sending'){r.state='pending';r.nextAt=0;changed=true;}if(changed)await write(rows);});
  // Keep initialization rejection observable through every public operation.
  ready.catch(()=>{});
  async function enqueue(payload){
   const frozen=clone(payload),setting=await config(),pair=await identify(setting);
   await ready;
   return serial(async()=>{
    const rows=await read();const entry={id:id(),payload:frozen,pair,base:setting.base,state:'pending',createdAt:now(),attempts:0,nextAt:0,error:''};
    rows.push(entry);await write(rows,{admitting:true});return {id:entry.id,state:entry.state};
   });
  }
  async function list(){await ready;return serial(async()=>(await read()).map(({payload,pair,...r})=>({...r,title:payload.title||payload.url,url:payload.url})));}
  async function confirmed(requestId){await ready;return serial(async()=>((await storage.get(DONE))[DONE]||[]).some(r=>r.requestId===requestId));}
  async function retry(requestId){
   const setting=await config(),pair=await identify(setting);await ready;
   return serial(async()=>{const rows=await read(),r=rows.find(r=>r.id===requestId);if(!r)throw new Error('待发送记录已处理。');if(r.state==='sending'&&draining)throw new Error('正在确认保存结果，请稍后重试。');if(pair!==r.pair)throw new Error('配对已改变，请连接原资源库后重试；旧记录不会自动转发。');r.state='pending';r.nextAt=0;r.error='';await write(rows);});
  }
  async function remove(requestId){await ready;return serial(async()=>{const rows=await read(),r=rows.find(r=>r.id===requestId);if(r?.state==='sending'&&draining)throw new Error('正在确认保存结果，请稍后移除。');await write(rows.filter(r=>r.id!==requestId));});}
  function drain(){
   if(draining)return draining;
   draining=(async()=>{
    await ready;
    // A storage write can fail after a successful network response. With no
    // other drain alive, retrying its receipt is safe even without a restart.
    await serial(async()=>{const rows=await read();let changed=false;for(const r of rows)if(r.state==='sending'){r.state='pending';r.nextAt=0;changed=true;}if(changed)await write(rows);});
    let delivered=0;
    for(let n=0;n<3;n++){
     const row=await serial(async()=>{const rows=await read(),r=rows.find(r=>r.state==='pending'&&r.nextAt<=now());if(!r)return null;r.state='sending';r.attempts++;await write(rows);return clone(r);});
     if(!row)break;
     let failure=null;
     try{
      const setting=await config();
      if(await identify(setting)!==row.pair)throw Object.assign(new Error('配对已改变。请连接原资源库后重试，旧记录不会自动转发。'),{blocked:true});
      const result=await send(row,setting),receipt=result?.receipt;
      if(receipt?.requestId!==row.id||receipt.status!=='saved'||typeof receipt.resourceId!=='string'||!receipt.resourceId)throw Object.assign(new Error('保存结果尚未确认，会先核对回执再重试。'),{retryable:true,halt:true});
      await serial(async()=>{const rows=await read(),recent=(await storage.get(DONE))[DONE]||[];await write(rows.filter(r=>r.id!==row.id),{receipts:[receipt,...recent.filter(r=>r.requestId!==row.id)].slice(0,100)});});
      delivered++;
     }catch(error){
      failure=error;
      await serial(async()=>{const rows=await read(),r=rows.find(r=>r.id===row.id);if(!r)return;r.state=error.blocked?'blocked':error.retryable===false?'failed':'pending';r.error=[...(error.message||'暂时无法发送，内容仍在浏览器中。')].slice(0,160).join('');r.nextAt=now()+Math.min(300000,30000*2**Math.min(r.attempts-1,4));await write(rows);});
     }
     if(failure?.halt)break;
    }
    return {delivered};
   })().finally(()=>{draining=null;});
   return draining;
  }
  return {enqueue,list,confirmed,retry,remove,drain};
 }
 const api={create,pairKey};if(typeof module==='object')module.exports=api;else root.ShijiOutbox=api;
})(typeof self==='object'?self:globalThis);

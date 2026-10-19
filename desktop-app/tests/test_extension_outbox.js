const assert=require('node:assert/strict');
const {randomUUID,webcrypto}=require('node:crypto');
const {create,pairKey}=require('../browser-extension/outbox.js');

function harness(){
 let data={},quota=false,config={base:'http://127.0.0.1:9876',token:'a'.repeat(40)},clock=1000;
 const storage={get:async key=>structuredClone({[key]:data[key]}),set:async value=>{if(quota)throw new Error('QUOTA');Object.assign(data,structuredClone(value));}};
 const options={storage,config:async()=>config,now:()=>clock,id:randomUUID,pairKey:c=>pairKey(c,webcrypto)};
 return {options,read:()=>structuredClone(data),quota:v=>{quota=v;},config:v=>{config=v;},tick:()=>{clock+=3600000;},restart:send=>create({...options,send})};
}
const body=()=>({url:'https://example.com/original',title:'Frozen title',selection:'New, exact',screenshot:'data:image/png;base64,ORIGINAL'});
const success=row=>({receipt:{requestId:row.id,status:'saved',resourceId:'resource-one'}});
const offline=()=>Object.assign(new Error('电脑未连接，已保留待发送。'),{retryable:true,halt:true});
(async()=>{
 // Durable before network: mutation of the caller's object cannot alter retry content.
 const h=harness();let frozen;
 let q=h.restart(async()=>{throw offline();});const payload=body(),entry=await q.enqueue(payload);payload.title='Changed';
 assert.equal((await q.list()).length,1);
 await q.drain();assert.equal((await q.list())[0].state,'pending');
 q=h.restart(async row=>{frozen=row;return success(row);});h.tick();await q.drain();
 assert.equal((await q.list()).length,0);assert.equal(frozen.id,entry.id);
 assert.equal(frozen.payload.title,'Frozen title');assert.equal(frozen.payload.screenshot,'data:image/png;base64,ORIGINAL');
 assert.ok(!JSON.stringify(h.read()).includes('a'.repeat(40)),'Outbox never duplicates credentials');

 // Concurrent enqueues and drains cannot lose items or dispatch one item twice.
 const concurrent=harness();const identify=concurrent.options.pairKey;let pairCalls=0,releaseFirstPair;const firstPair=new Promise(r=>releaseFirstPair=r);concurrent.options.pairKey=async c=>{const call=++pairCalls,pair=await identify(c);if(call===1)await firstPair;return pair;};let release,entered;const gate=new Promise(r=>release=r),start=new Promise(r=>entered=r);let sent=[];
 q=concurrent.restart(async row=>{sent.push(row.id);entered();await gate;return success(row);});
 const firstEnqueue=q.enqueue(body()),secondEnqueue=q.enqueue({...body(),url:'https://example.com/other'});const secondEntry=await secondEnqueue;releaseFirstPair();const entries=[await firstEnqueue,secondEntry];
 const drain=q.drain();await start;const second=q.drain();
 assert.equal(sent[0],entries[1].id,"pair-key hashing may finish in a different order from calls");
 await assert.rejects(q.remove(sent[0]),/正在/);
 const third=await q.enqueue({...body(),url:'https://example.com/third'});release();await Promise.all([drain,second]);
 assert.equal(new Set(sent).size,3);assert.equal(sent.length,3);assert.equal((await q.list()).length,0);

 // Re-pairing must not silently send an old queue into another library.
 const paired=harness();let contacted=false;q=paired.restart(async row=>{contacted=true;return success(row);});
 const old=await q.enqueue(body());paired.config({base:'http://127.0.0.1:9876',token:'b'.repeat(40)});
 await q.drain();assert.equal(contacted,false);assert.equal((await q.list())[0].state,'blocked');
 await assert.rejects(q.retry(old.id),/配对/);
 paired.config({base:'http://127.0.0.1:9876',token:'a'.repeat(40)});await q.retry(old.id);await q.drain();assert.equal((await q.list()).length,0);

 // A failed disk write cannot be reported as queued or dispatched.
 const disk=harness();q=disk.restart(async()=>{throw new Error('must not send');});disk.quota(true);
 await assert.rejects(q.enqueue(body()),/QUOTA/);disk.quota(false);assert.equal((await q.list()).length,0);

 // Removal persists across workers; oversized queues refuse new captures, not old ones.
 q=disk.restart(async row=>success(row));const removed=await q.enqueue(body());await q.remove(removed.id);
 assert.equal((await disk.restart(async row=>success(row)).list()).length,0);
 await assert.rejects(q.enqueue({...body(),selection:'x'.repeat(8*1024*1024)}),/空间|上限/);
 assert.equal((await q.list()).length,0);

 // Recover a terminated worker's sending marker; confirmation must match the exact request.
 const interrupted=harness();q=interrupted.restart(async()=>({receipt:{requestId:'wrong',status:'saved',resourceId:'x'}}));
 const waiting=await q.enqueue(body());await q.drain();assert.equal((await q.list()).length,1);
 const saved=interrupted.read();saved.captureOutboxV1[0].state='sending';await interrupted.options.storage.set(saved);
 q=interrupted.restart(async row=>success(row));interrupted.tick();await q.drain();assert.equal((await q.list()).length,0);

 // Accepted near-cap content must remain removable offline, even when error
 // state needs more bytes. Rejecting admission up front is also safe.
 const near=harness();q=near.restart(async()=>{throw offline();});
 const probe=await q.enqueue({...body(),screenshot:''});
 const overhead=new TextEncoder().encode(JSON.stringify(near.read().captureOutboxV1)).byteLength;
 await q.remove(probe.id);
 let accepted;
 try{accepted=await q.enqueue({...body(),screenshot:'a'.repeat(8*1024*1024-overhead-30)});}
 catch(error){assert.match(error.message,/空间|上限/);}
 if(accepted){await q.drain();await q.remove(accepted.id);}
 assert.equal((await q.list()).length,0);
 const large=await q.enqueue({...body(),screenshot:'a'.repeat(8*1024*1024-overhead-4096)});
 await q.drain();await q.remove(large.id);assert.equal((await q.list()).length,0);
 console.log('PASS: extension durable outbox, frozen payload, restart, serial delivery, pairing fence, storage failure and cancellation');
})().catch(e=>{console.error(e);process.exit(1)});

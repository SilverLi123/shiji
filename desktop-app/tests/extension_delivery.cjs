/* Process-level QA runner, production outbox and transport, real HTTP backend. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {webcrypto,randomUUID}=require('node:crypto');
const {create,pairKey}=require('../browser-extension/outbox');
const transport=require('../browser-extension/clip-transport');
const folder=process.argv[2],mode=process.argv[3],settings=JSON.parse(fs.readFileSync(path.join(folder,'config.json'))),file=path.join(folder,'outbox.json');
const read=()=>fs.existsSync(file)?JSON.parse(fs.readFileSync(file)):{};
const storage={get:async key=>({[key]:read()[key]}),set:async value=>{const tmp=file+'.tmp';fs.writeFileSync(tmp,JSON.stringify({...read(),...value}),{mode:0o600});fs.renameSync(tmp,file);}};
const fetcher=async(url,options)=>{
 const response=await fetch(url,{...options,headers:{...options.headers,Origin:'chrome-extension://'+'a'.repeat(32)}});
 if(mode==='deliver-lost'&&url.endsWith('/api/clip')){await response.text();throw new TypeError('test-only: response lost after server committed');}
 return response;
};
(async()=>{
 const q=create({storage,config:async()=>settings,send:transport.create(fetcher).send,id:randomUUID,pairKey:c=>pairKey(c,webcrypto)});
 if(mode==='offline')await q.enqueue(JSON.parse(fs.readFileSync(path.join(folder,'payload.json'))));
 else for(const row of await q.list())await q.retry(row.id);
 await q.drain();const rows=await q.list();
 assert.equal(rows.length,mode==='confirm'?0:1);
 if(mode!=='confirm'){assert.equal(rows[0].state,'pending');assert.ok(rows[0].attempts>0);}
 console.log('PASS: '+mode+' persisted delivery state');
})().catch(error=>{console.error(error);process.exit(1)});

const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('fs'),path=require('path');
const {webcrypto}=require('node:crypto');
(async()=>{
 let handler,requests=[],badges=[],offline=false;const data={base:'http://127.0.0.1:8782',token:'x'.repeat(40)};
 const receipts=new Map(),alarms=new Map();
 const chrome={runtime:{id:'a'.repeat(32),onInstalled:{addListener(){}},onStartup:{addListener(){}},onMessage:{addListener(fn){handler=fn}}},contextMenus:{onClicked:{addListener(){}}},
 storage:{local:{get:async keys=>Object.fromEntries((Array.isArray(keys)?keys:[keys]).map(k=>[k,structuredClone(data[k])])),set:async value=>Object.assign(data,structuredClone(value)),setAccessLevel:async()=>{}},onChanged:{addListener(){}}},
 action:{setBadgeText:async v=>badges.push(v.text),setBadgeBackgroundColor:async()=>{}},alarms:{get:async k=>alarms.get(k),create:async(k,v)=>alarms.set(k,v),clear:async k=>alarms.delete(k),onAlarm:{addListener(){}}},
 tabs:{query:async()=>[{id:5,windowId:1}],captureVisibleTab:async()=> 'data:image/png;base64,PNG'},scripting:{executeScript:async()=>[{result:{url:'https://example.com/',title:'Example',selection:'Selection'}}]}};
 const context=vm.createContext({chrome,crypto:webcrypto,TextEncoder,AbortSignal,URL,console,fetch:async(url,options)=>{
  requests.push({url,options});if(offline)throw new TypeError('offline');const body=JSON.parse(options.body);
  let result;if(url.endsWith('/ping'))result={captureReceipts:1};
  else if(url.endsWith('/status'))result=receipts.get(body.requestId)||{requestId:body.requestId,status:'not_found'};
  else{const receipt={requestId:body.requestId,status:'saved',resourceId:'resource'};receipts.set(body.requestId,receipt);result={receipt};}
  return {ok:true,status:200,json:async()=>result};
 }});
 context.importScripts=(...files)=>files.forEach(file=>vm.runInContext(fs.readFileSync(path.join(__dirname,'../browser-extension',file),'utf8'),context));
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../browser-extension/background.js'),'utf8'),context);
 function send(message,sender={id:chrome.runtime.id}){return new Promise(resolve=>{const keep=handler(message,sender,resolve);if(!keep)resolve(null);});}
 assert.equal(await send({type:'capture'},{id:'foreign'}),null);
 assert.ok((await send({type:'ping'})).ok);
 const captured=await send({type:'capture',screenshot:true});assert.ok(captured.saved);assert.equal(captured.queued,false);
 const post=requests.find(r=>r.url.endsWith('/api/clip')),body=JSON.parse(post.options.body);
 assert.equal(body.selection,'Selection');assert.ok(body.screenshot);assert.equal(body.requestId,captured.requestId);assert.equal(post.options.headers.Authorization,'Bearer '+data.token);
 assert.ok(badges.includes('✓'));
 offline=true;const queued=await send({type:'capture'});assert.ok(queued.ok);assert.ok(queued.queued);assert.equal(queued.saved,false);
 assert.equal((await send({type:'outbox'})).rows.length,1);assert.ok(alarms.has('shiji-capture-outbox'));
 offline=false;assert.ok((await send({type:'retry',id:queued.requestId})).ok);
 for(let i=0;i<30 && (await send({type:'outbox'})).rows.length;i++)await new Promise(r=>setTimeout(r,5));
 assert.equal((await send({type:'outbox'})).rows.length,0);
 console.log('PASS: actual extension background sender guard, frozen screenshot, queued vs saved, alarm and receipt retry');
})().catch(e=>{console.error(e);process.exit(1)});

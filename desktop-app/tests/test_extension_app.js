const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('fs');
(async()=>{
 let handler,requests=[],badges=[];const config={base:'http://127.0.0.1:8782',token:'x'.repeat(40)};
 const chrome={runtime:{id:'a'.repeat(32),onInstalled:{addListener(){}},onMessage:{addListener(fn){handler=fn}}},contextMenus:{onClicked:{addListener(){}}},storage:{local:{get:async()=>config,set:async()=>{}}},action:{setBadgeText:async v=>badges.push(v.text),setBadgeBackgroundColor:async()=>{}},tabs:{query:async()=>[{id:5,windowId:1}],captureVisibleTab:async()=> 'data:image/png;base64,PNG'},scripting:{executeScript:async()=>[{result:{url:'https://example.com/',title:'Example',selection:'Selection'}}]}};
 const context=vm.createContext({chrome,ShijiClip:require('../browser-extension/utils'),importScripts(){},fetch:async(url,options)=>{requests.push({url,options});return {ok:true,json:async()=>({alreadySaved:false})}},AbortSignal});
 vm.runInContext(fs.readFileSync(require('path').join(__dirname,'../browser-extension/background.js'),'utf8'),context);
 function send(message,sender={id:chrome.runtime.id}){return new Promise(resolve=>{const keep=handler(message,sender,resolve);if(!keep)resolve(null);});}
 assert.equal(await send({type:'capture'},{id:'foreign'}),null);
 assert.ok((await send({type:'ping'})).ok);assert.equal(requests[0].url,config.base+'/api/clip/ping');assert.equal(requests[0].options.headers.Authorization,'Bearer '+config.token);
 assert.ok((await send({type:'capture',screenshot:true})).ok);const body=JSON.parse(requests[1].options.body);assert.equal(body.selection,'Selection');assert.ok(body.screenshot);assert.deepEqual(badges,['✓']);
 console.log('Extension authenticated ping, sender guard and screenshot payload passed');
})().catch(e=>{console.error(e);process.exit(1)});

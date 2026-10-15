const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom');
const root=path.join(__dirname,'../browser-extension');
const tick=()=>new Promise(r=>setTimeout(r,10));
(async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(root,'popup.html'),'utf8'),{runScripts:'outside-only',url:'https://extension.invalid/'}),w=dom.window,d=w.document;
 let rows=[{id:'one',title:'<img src=x onerror=alert(1)>',url:'https://example.com',state:'pending',error:'电脑未连接',attempts:1}],failRetry=true,listener;
 w.chrome={storage:{local:{get:async()=>({base:'http://127.0.0.1:8782',token:'x'.repeat(40)}),set:async()=>{}},onChanged:{addListener:fn=>listener=fn}},runtime:{sendMessage:async msg=>{
  if(msg.type==='ping')return {ok:false,message:'未连接'};
  if(msg.type==='outbox')return {ok:true,rows:structuredClone(rows)};
  if(msg.type==='capture')return {ok:true,queued:true,saved:false,message:'已保存在浏览器，等待发送到 App。'};
  if(msg.type==='retry')return failRetry?{ok:false,message:'配对已改变'}:{ok:true,message:'已安排重试'};
  if(msg.type==='remove'){rows=[];return {ok:true,message:'已移除待发送记录'};}
 }}};
 w.confirm=()=>true;w.ShijiClip=require('../browser-extension/utils.js');
 w.eval(fs.readFileSync(path.join(root,'popup.js'),'utf8'));await tick();
 assert.equal(d.querySelectorAll('[data-outbox-row]').length,1);
 assert.equal(d.querySelector('[data-outbox-row] h3').textContent,'<img src=x onerror=alert(1)>');
 assert.equal(d.querySelector('[data-outbox-row] img'),null);
 d.querySelector('#save').click();await tick();assert.notEqual(d.querySelector('#connection').dataset.connected,'true','Queued does not mean saved or connected');
 const retry=d.querySelector('[data-queue-action="retry"]');retry.focus();retry.click();await tick();
 assert.match(d.querySelector('#status').textContent,/配对/);assert.equal(d.activeElement.dataset.queueAction,'retry');assert.equal(d.activeElement.disabled,false);
 failRetry=false;d.activeElement.click();await tick();assert.match(d.querySelector('#status').textContent,/重试/);
 rows[0].state='sending';listener({captureOutboxV1:{}},'local');await tick();
 assert.ok([...d.querySelectorAll('[data-queue-action]')].every(el=>el.disabled));
 rows[0].state='pending';listener({captureOutboxV1:{}},'local');await tick();
 d.querySelector('[data-queue-action="remove"]').click();await tick();assert.equal(d.querySelectorAll('[data-outbox-row]').length,0);
 assert.match(d.querySelector('#outbox-list').textContent,/没有待发送/);
 dom.window.close();console.log('PASS: popup escaped pending content, queued vs saved, retry failure focus, sending guard and removal');
})().catch(e=>{console.error(e);process.exit(1)});

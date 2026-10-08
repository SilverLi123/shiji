'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{JSDOM}=require('jsdom'),recovery=require('../static/recovery');
const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8')),doc=dom.window.document,$=s=>doc.querySelector(s),dialog=$('#confirm-dialog');
dialog.showModal=()=>dialog.open=true;dialog.close=()=>dialog.open=false;
(async()=>{
 let p=recovery.confirm(dialog,{title:'Restore',message:'1 resource'});assert.equal(doc.activeElement,$('[data-confirm-no]'));dialog.dispatchEvent(new dom.window.Event('cancel',{cancelable:true}));assert.equal(await p,false);
 p=recovery.confirm(dialog,{title:'Restore',message:'1 resource'});$('[data-confirm-yes]').click();assert.equal(await p,true);
 const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');let accepted=false,calls=[];
 const c={$,ShijiRecovery:{confirm:async()=>accepted},state:{selected:new Set(Array.from({length:20},(_,i)=>String(i)))},api:async(u,m,b)=>{calls.push({u,m,b});return {changed:20};},reload:async()=>{},toast(){},offerUndo(){},size:n=>String(n),setBackupBusy(){},backupMessage:''};vm.createContext(c);
 vm.runInContext(source.slice(source.indexOf('async function runBatch('),source.indexOf('\n',source.indexOf('async function runBatch('))),c);
 await c.runBatch('delete');assert.equal(calls.length,0);assert.equal(c.state.selected.size,20);accepted=true;await c.runBatch('delete');assert.equal(calls[0].b.action,'delete');assert.equal(c.state.selected.size,0);
 vm.runInContext(source.slice(source.indexOf('async function approveRecovery('),source.indexOf('\nasync function restoreNamedBackup')),c);
 accepted=false;calls=[];await c.approveRecovery({ticket:'t',summary:{active:1,trash:0,attachments:0,bytes:0,collections:0,smartCollections:0}});assert.equal(calls[0].u,'/api/restore/cancel');assert.equal(calls.length,1);
 accepted=true;calls=[];c.api=async(u,m,b)=>{calls.push({u,m,b});return {restored:1,skipped:0};};await c.approveRecovery({ticket:'t',summary:{active:1,trash:0,attachments:0,bytes:0,collections:0,smartCollections:0}});assert.equal(calls[0].u,'/api/restore/confirm');assert.equal(calls[0].b.confirm,true);
 dom.window.close();console.log('Recovery confirmation, cancel and batch threshold passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

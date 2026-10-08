'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const model=require('../static/similar-model.js'),gallery=require('../static/gallery-model.js');
function pattern({color=[30,90,150],delta=0,invert=false,transparent=false}={}){
  const data=new Uint8ClampedArray(16*16*4);
  for(let y=0;y<16;y++)for(let x=0;x<16;x++){const dark=(x<8)!==invert,c=dark?color:[245,240,220],i=(y*16+x)*4;for(let k=0;k<3;k++)data[i+k]=c[k]+delta;data[i+3]=transparent?0:255;}return data;
}
const base=model.descriptor(pattern()),near=model.descriptor(pattern({delta:8})),different=model.descriptor(pattern({color:[10,170,30],invert:true}));
assert.equal(model.distance(base,base),0);assert(model.distance(base,near)<model.STRICT);assert(model.distance(base,different)>model.BROAD);
const white=new Uint8ClampedArray(1024).fill(255);assert.equal(model.distance(model.descriptor(pattern({transparent:true})),model.descriptor(white)),0);
assert.throws(()=>model.descriptor(new Uint8Array(4)));
const file=(id,more={})=>({id,name:id+'.png',mime:'image/png',size:40,author:'A',license:'需署名',sourceUrl:'https://example.com/source',licenseUrl:'https://example.com/license',...more});
const a={id:'r1',title:'A',attachments:[file('query'),file('same-owner'),file('deleted',{deleted:true}),file('audio',{mime:'audio/wav'})]},b={id:'r2',title:'B',thumbnail:'https://example.com/remote',attachments:[file('peer')]},trash={id:'r3',deleted:true,title:'Trash',attachments:[file('trash')]};
const library=[a,b,trash],original=JSON.stringify(library);const candidates=model.candidates(library,a,'query');assert.deepEqual(candidates.map(e=>e.attachment.id),['same-owner','peer']);candidates[0].attachment.name='changed';assert.equal(JSON.stringify(library),original);assert.deepEqual(model.candidates(library,trash,'trash'),[]);
const large={id:'large',attachments:Array.from({length:5000},(_,i)=>file('large-'+i))};const largeCandidates=model.candidates([large],large,'large-0');assert.equal(largeCandidates.length,4999);assert.equal(largeCandidates[0].resource,largeCandidates[4998].resource);
const rows=Array.from({length:45},(_,i)=>({attachment:file(String(i).padStart(2,'0')),resource:b,distance:i/100}));assert.equal(model.ranked(rows).length,19);assert.equal(model.ranked(rows,'broad').length,33);assert.equal(model.page(rows,99).rows.length,5);assert.equal(model.page(rows,99).index,2);assert.equal(model.page([],2).count,1);
const queue=model.ranked([{attachment:a.attachments[1],resource:a,distance:.01},{attachment:b.attachments[0],resource:b,distance:.02}]).map(e=>gallery.images(e.resource).find(i=>i.key===e.attachment.id));assert.deepEqual(queue.map(i=>i.key),['same-owner','peer']);assert.equal(queue[0].license,'需署名');assert.equal(queue[0].sourceUrl,'https://example.com/source');
(async()=>{
 let calls=[],updates=0;let control=new AbortController();
 const outcome=await model.scan(file('query'),[{attachment:file('bad'),resource:a},{attachment:file('near'),resource:b},{attachment:file('different'),resource:b}],async item=>{calls.push(item.id);if(item.id==='bad')throw Error('broken');return item.id==='different'?different:base;},control.signal,()=>updates++);
 assert.equal(outcome.checked,3);assert.equal(outcome.failures.length,1);assert.equal(model.ranked(outcome.rows).length,1);assert.equal(updates,3);assert.equal(JSON.stringify(library),original);
 calls=[];control=new AbortController();const stopped=await model.scan(file('query'),rows,async item=>{calls.push(item.id);return base;},control.signal,()=>control.abort());assert.equal(stopped.checked,1);assert.equal(stopped.cancelled,true);assert.equal(calls.length,2);
 control=new AbortController();let finish;const pending=model.scan(file('query'),rows,()=>new Promise(r=>{finish=r;}),control.signal);await Promise.resolve();control.abort();finish(base);assert.equal((await pending).rows.length,0);
 await assert.rejects(model.scan(file('query'),rows,async()=>{throw Error('query missing');},new AbortController().signal),/query missing/);
 // Actual controller source: close stops a request, and a late library response cannot overwrite a newer scan.
 const elements=new Map(),listeners=new Map();let requestResolve,fetches=0;
 const jobOwner={id:'owner',title:'Source',attachments:[file('subject')]};
 const context=vm.createContext({ShijiSimilar:model,ShijiGallery:gallery,structuredClone,AbortController,DOMException,Date,Blob,URL,setTimeout,clearTimeout,console,
  fetch:()=>{fetches++;return new Promise(r=>{requestResolve=r;});},state:{resources:[jobOwner],trash:[]},
  $:selector=>selector==='#manage-dialog'?{addEventListener:(name,cb)=>listeners.set(name,cb)}:elements.get(selector)||null,
  fileURL:attachment=>'/api/files/'+attachment.id,toast:()=>{},esc:v=>String(v),document:{},manage:()=>{}
 });
 vm.runInContext(fs.readFileSync(require.resolve('../static/similar.js'),'utf8'),context);
 vm.runInContext(`similarRender=()=>{};similarJob={owner:${JSON.stringify(jobOwner)},attachment:${JSON.stringify(jobOwner.attachments[0])},phase:'idle'};initSimilar();`,context);
 const first=vm.runInContext('similarStart()',context);assert.equal(fetches,1);listeners.get('close')();assert.equal(vm.runInContext('similarJob.phase',context),'cancelled');requestResolve({ok:true,json:async()=>({resources:[jobOwner]})});await first;assert.equal(vm.runInContext('similarJob.phase',context),'cancelled');
 const second=vm.runInContext('similarStart()',context);assert.equal(vm.runInContext('similarJob.checked',context),0);requestResolve({ok:true,json:async()=>({resources:[]})});await second;assert.equal(vm.runInContext('similarJob.phase',context),'error');assert.match(vm.runInContext('similarJob.error',context),/已移除/);
 // Actual reader closes decoded bitmaps when cancellation arrives during native decoding.
 let decodeResolve,closed=0;const controller=new AbortController();context.fetch=async(url,options)=>{assert.equal(url,'/api/files/subject');assert.equal(options.cache,'no-store');return {ok:true,blob:async()=>({size:40})};};context.createImageBitmap=()=>new Promise(r=>{decodeResolve=r;});context.testSignal=controller.signal;
 const reading=vm.runInContext(`readSimilarPixels({id:'subject'},testSignal)`,context);while(!decodeResolve)await Promise.resolve();controller.abort();await assert.rejects(reading,/已取消/);decodeResolve({close:()=>closed++});await Promise.resolve();await Promise.resolve();assert.equal(closed,1);
 let blobRead=false,bodyCancelled=false;context.fetch=async()=>({ok:true,headers:{get:()=>String(65*1024*1024)},body:{cancel:async()=>{bodyCancelled=true;}},blob:async()=>{blobRead=true;}});context.testSignal=new AbortController().signal;await assert.rejects(vm.runInContext(`readSimilarPixels({id:'subject'},testSignal)`,context),/超过 64 MB/);assert.equal(blobRead,false);assert.equal(bodyCancelled,true);
 // Resolve fresh scan results through authoritative records, including late attachments.
 let current=null,finishReload,opened=[];const panel={isConnected:true},modal={open:true,close(){this.open=false;}},imageModal={open:true,close(){this.open=false;}},ui=new Map();
 const nav=vm.createContext({ShijiSimilar:model,ShijiGallery:gallery,structuredClone,AbortController,DOMException,Date,Blob,URL,setTimeout,clearTimeout,console,
  $:selector=>selector==='#similar-panel'?panel:selector==='#manage-dialog'?modal:selector==='#image-dialog'?imageModal:ui.get(selector)||(()=>{const node={disabled:false,textContent:''};ui.set(selector,node);return node;})(),
  find:id=>current?.id===id?current:null,reload:()=>new Promise(resolve=>{finishReload=resolve;}),detail:r=>opened.push(r.id),document:{},toast:()=>{},esc:String
 });
 vm.runInContext(fs.readFileSync(require.resolve('../static/similar.js'),'utf8'),nav);
 vm.runInContext(fs.readFileSync(require.resolve('../static/gallery.js'),'utf8'),nav);
 vm.runInContext(`similarJob={owner:{id:'query-owner',deleted:false}}`,nav);
 nav.button={dataset:{id:'late-resource'}};let navigating=vm.runInContext(`similarAction('similar-resource',button)`,nav);
 assert.equal(nav.button.disabled,true);current={id:'late-resource',attachments:[file('late-file')]};finishReload();await navigating;assert.deepEqual(opened,['late-resource']);assert.equal(modal.open,false);
 modal.open=true;current={id:'late-resource',deleted:true};navigating=vm.runInContext(`similarAction('similar-resource',button)`,nav);finishReload();await assert.rejects(navigating,/移动了范围/);assert.equal(modal.open,true);
 current={id:'late-resource'};navigating=vm.runInContext(`similarAction('similar-resource',button)`,nav);panel.isConnected=false;finishReload();await navigating;assert.equal(opened.length,1);panel.isConnected=true;
 nav.recordQuery=(owner,key)=>opened.push(owner.id+':'+key);
 vm.runInContext(`similarOpen=(owner,key)=>recordQuery(owner,key);galleryState.items=[{resourceId:'existing',key:'late-file',inTrash:false}];galleryState.index=0;galleryState.run=10;galleryState.fromSimilar=true;`,nav);
 current={id:'existing',attachments:[]};imageModal.open=true;navigating=vm.runInContext(`galleryAction('image-similar')`,nav);current={id:'existing',attachments:[file('late-file')]};finishReload();await navigating;assert.equal(opened.at(-1),'existing:late-file');assert.equal(imageModal.open,false);
 imageModal.open=true;modal.open=true;current={id:'late-resource',attachments:[]};vm.runInContext(`galleryState.items[0].resourceId='late-resource'`,nav);
 navigating=vm.runInContext(`galleryAction('image-resource')`,nav);finishReload();await navigating;assert.equal(opened.at(-1),'late-resource');assert.equal(modal.open,false);
 imageModal.open=true;current=null;navigating=vm.runInContext(`galleryAction('image-resource')`,nav);finishReload();await navigating;assert.match(ui.get('#image-action-status').textContent,/已移除/);assert.equal(imageModal.open,true);assert.equal(ui.get('#image-similar').disabled,false);
 current={id:'late-resource'};navigating=vm.runInContext(`galleryAction('image-resource')`,nav);vm.runInContext(`galleryState.run++`,nav);const count=opened.length;finishReload();await navigating;assert.equal(opened.length,count);
 console.log('PASS: similarity pixels, rank/page/scope/provenance, partial scans, decoder cancellation; fresh resource/attachment navigation, removed scope and late navigation guards.');
})().catch(e=>{console.error(e);process.exitCode=1;});

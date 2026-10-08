'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{JSDOM}=require('jsdom');
const source=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8'),model=require('../static/edit-model');
const clone=v=>JSON.parse(JSON.stringify(v));
function resource(extra={}){return {id:'r',url:'https://example.test/',title:'Original',kind:'website',category:'其他',description:'Description',notes:'Line one\r\nLine two',snippet:'',language:'',author:'Author',sourceUrl:'',parentId:'',price:'待确认',license:'待确认',thumbnail:'',licenseUrl:'',favicon:'',tags:['a,b'],projects:['P,Q'],projectNotes:JSON.parse('{"P,Q":"Original project","__proto__":"Historical note"}'),favorite:false,inbox:true,coverId:'',attachments:[],...extra};}
function setup(item=resource()){
 const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8'),{url:'http://localhost/'}),doc=dom.window.document,$=s=>doc.querySelector(s),handlers={},calls=[],toasts=[];
 doc.addEventListener=(type,fn)=>{handlers[type]=fn;};
 let submit;$('#resource-form').addEventListener=(type,fn)=>{assert.equal(type,'submit');submit=fn;};
 dom.window.HTMLElement.prototype.scrollIntoView=function(){};
 const state={resources:[item],filters:{},formBase:{},formProjects:Object.create(null),pending:[],metadataRun:0,editing:null,detail:null,scope:'all',formBusy:false};
 const c={document:doc,window:dom.window,$,state,ShijiEdit:model,CATEGORIES:['其他'],split:v=>v.split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean),esc:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'),size:n=>n+' B',toast:v=>toasts.push(v),quickNoteMayLeave:()=>true,pausePreviewPlayers(){},closeMenu(){},openDrawer(){ $('#drawer').hidden=false;},lastFocus:null,syncFilters(){},selectScope(){},setKind(){},reload:async()=>{},find:id=>state.resources.find(r=>r.id===id),dragDepth:0,importAssets:async()=>{},TextEncoder,api:async(url,method,body)=>{calls.push({url,method,body:clone(body)});return {resource:item};},upload:async()=>({attachment:{id:'a',mime:'text/plain'}})};
 c.formTagEditor=require('../static/tag-editor').create(doc.querySelector('#tag-editor'),doc.querySelector('#f-tags'),v=>c.state.formTags=v,()=>{});vm.createContext(c);
 vm.runInContext(source.slice(source.indexOf('function closeDrawer()'),source.indexOf('\nasync function coloursFromFile')),c);
 const click=source.indexOf("document.addEventListener('click',async event=>"),save=source.indexOf("$('#resource-form').addEventListener('submit'");
 vm.runInContext(source.slice(click,save),c);vm.runInContext(source.slice(save,source.indexOf("\n$('#f-url').addEventListener",save)),c);
 const paste=source.indexOf("document.addEventListener('paste',event=>");vm.runInContext(source.slice(paste,source.indexOf("\n$('#drawer-backdrop')",paste)),c);
 $('#resource-form').requestSubmit=()=>{c.lastSubmit=submit({preventDefault(){}});};
 c.edit(item);
 const action=async(name,attrs={})=>{const el=doc.createElement('button');el.dataset.action=name;Object.assign(el.dataset,attrs);doc.body.append(el);await handlers.click({target:el});el.remove();};
 return {dom,doc,$,c,state,calls,toasts,handlers,save:()=>submit({preventDefault(){}}),action,close:()=>dom.window.close()};
}
async function busy(){
 const h=setup();let resolve;h.c.api=()=>new Promise(r=>resolve=r);h.$('#f-title').value='Draft';const p=h.save();
 assert.equal(h.state.formBusy,true);assert.equal(h.$('.form-body').inert,true,'saving must stop edits made after the captured draft');
 const before=h.state.pending.length;h.c.queueFiles([{name:'late.png',type:'image/png',size:1}]);assert.equal(h.state.pending.length,before,'late chooser result must not enter a saving draft');
 h.handlers.paste({clipboardData:{files:[{name:'paste.png',type:'image/png',size:1}]},preventDefault(){}});await h.handlers.drop({dataTransfer:{files:[{name:'drop.png',type:'image/png',size:1}]},preventDefault(){}});assert.equal(h.state.pending.length,before);
 assert.equal(h.toasts.some(t=>t.includes('截图已加入')),false);assert.equal(h.c.closeDrawer(),false);h.c.edit(resource({id:'other'}));assert.equal(h.state.editing,'r');
 const event=new h.dom.window.Event('beforeunload',{cancelable:true});h.dom.window.dispatchEvent(event);assert.equal(event.defaultPrevented,true);
 resolve({resource:resource({title:'Draft'})});await p;assert.equal(h.$('.form-body').inert,false);assert.equal(h.state.formBusy,false);h.close();
}
async function deltas(){
 const exact=setup();exact.c.formTagEditor.set(['a,b','New, exact']);await exact.save();assert.deepEqual(exact.calls[0].body,{changes:{tags:['a,b','New, exact']},expected:{tags:['a,b']}});exact.close();
 const h=setup();h.$('#f-title').value='Edited';await h.save();assert.deepEqual(h.calls[0].body,{changes:{title:'Edited'},expected:{title:'Original'}},'untouched delimiter-containing tags/projects and CRLF notes must not be replayed');h.close();
 const m=setup();m.state.formBase.favicon='https://example.test/new.png';m.$('#f-author').value='New author';await m.save();assert.deepEqual(m.calls[0].body,{changes:{author:'New author',favicon:'https://example.test/new.png'},expected:{author:'Author',favicon:''}},'metadata must compare to immutable original');m.close();
 const original=resource(),latest=resource({title:'Latest',notes:'Unseen note',projectNotes:JSON.parse('{"__proto__":"Latest historical","New":"new note"}')});
 const rebased=model.rebase(original,latest,[{field:'title'},{field:'projectNotes',key:'__proto__'}]);assert.equal(rebased.notes,original.notes);assert.equal(rebased.title,'Latest');assert.equal(rebased.projectNotes.__proto__,'Latest historical');assert.equal(Object.hasOwn(rebased.projectNotes,'New'),false);
 const initial={...original,projectNotes:{}};const d=model.diff({...original,projectNotes:JSON.parse('{"__proto__":"Draft","New\\u0000key":""}')},initial,original);assert.equal(d.expected.projectNotes.__proto__,'Historical note');assert.equal(d.expected.projectNotes['New\0key'],null);
}
function conflict(resourceValue=resource({title:'<img src=x onerror=boom>'}),field='title',value='Draft'){
 return Object.assign(new Error('资料已变更'),{status:409,resource:resourceValue,conflicts:[{field,current:resourceValue[field],value}]});
}
async function recovery(){
 const h=setup();h.$('#f-title').value='Draft';const pending={file:{name:'draft.txt',size:1,type:'text/plain'},cover:false};h.state.pending=[pending];h.c.api=async()=>{throw conflict();};await h.save();
 assert.equal(h.$('#f-title').value,'Draft');assert.equal(h.state.pending[0],pending);assert.equal(h.$('#edit-conflict').hidden,false);assert.equal(h.doc.activeElement,h.$('#edit-conflict'));assert.equal(h.$('#edit-conflict').querySelector('img'),null);assert.match(h.$('#edit-conflict-fields').textContent,/<img src=x/);assert.equal(h.$('.form-body').inert,false);
 const calls=[];h.c.api=async(url,method,body)=>{calls.push(clone(body));return {resource:resource({title:'Draft'})};};await h.action('edit-conflict-mine');await h.c.lastSubmit;assert.deepEqual(calls[0],{changes:{title:'Draft'},expected:{title:'<img src=x onerror=boom>'}});assert.equal(h.state.pending.length,0);h.close();
 const l=setup();l.$('#f-title').value='Draft';l.state.pending=[pending];l.c.api=async()=>{throw conflict();};await l.save();let finish;l.c.api=()=>new Promise(r=>finish=r);const load=l.action('edit-conflict-latest');assert.equal(l.$('.form-body').inert,true);assert.equal(l.$('[data-action="edit-conflict-mine"]').disabled,true);finish({resource:resource({title:'Even newer',notes:'Fresh note'})});await load;assert.equal(l.$('#f-title').value,'Even newer');assert.equal(l.$('#f-notes').value,'Fresh note');assert.equal(l.state.pending[0],pending);assert.equal(l.$('#edit-conflict').hidden,true);assert.equal(l.state.formBusy,false);l.close();
 for(const deleted of [false,true]){const x=setup();x.$('#f-title').value='Draft';x.c.api=async()=>{throw conflict();};await x.save();x.c.api=async()=>{if(!deleted)throw new Error('Offline');return {resource:resource({deleted:true})};};await x.action('edit-conflict-latest');assert.equal(x.$('#f-title').value,'Draft');assert.equal(x.$('#edit-conflict').hidden,false);assert.equal(x.$('#form-error').hidden,false);assert.equal(x.state.formBusy,false);x.close();}
}
async function uploads(){
 const h=setup();h.$('#f-title').value='Draft';const first={file:{name:'first.txt',type:'text/plain',size:1},cover:false},second={file:{name:'second.txt',type:'text/plain',size:1},cover:false};h.state.pending=[first,second];let count=0;
 h.c.api=async(url,method,body)=>{h.calls.push(clone(body));return {resource:resource({title:'Draft',notes:'Latest note',sourceUrl:'https://latest.test/'})};};
 h.c.upload=async(id,file,cover,extra)=>{assert.equal(extra.sourceUrl,'https://latest.test/');if(++count===2)throw new Error('Upload unavailable');return {attachment:{id:'a',mime:'text/plain'}};};await h.save();assert.equal(h.state.pending.length,1);assert.equal(h.state.pending[0],second);assert.equal(h.$('#drawer').hidden,false);assert.match(h.$('#form-error').textContent,/资料已保存/);assert.equal(h.state.formBusy,false);
 h.c.upload=async()=>({attachment:{id:'b',mime:'text/plain'}});await h.save();assert.deepEqual(h.calls[1],{changes:{},expected:{}},'retry must not replay the original metadata or create a second record');assert.equal(h.state.pending.length,0);assert.equal(h.$('#drawer').hidden,true);h.close();
 const n=setup();n.c.edit(null,{title:'New',url:'https://new.test/'});n.state.pending=[second];n.c.api=async(url,method,body)=>{n.calls.push({url,body:clone(body)});return {resource:resource({id:'new',title:'New',url:'https://new.test/'})};};n.c.upload=async()=>{throw new Error('Failed file');};await n.save();assert.equal(n.calls[0].url,'/api/resources');n.c.upload=async()=>({attachment:{id:'a',mime:'text/plain'}});await n.save();assert.equal(n.calls[1].url,'/api/resources/new/edit');assert.equal(n.calls.length,2);n.close();
 const r=setup();r.$('#f-title').value='Draft';r.c.reload=async()=>{throw new Error('Network unavailable');};await r.save();assert.equal(r.$('#drawer').hidden,true);assert.match(r.toasts.at(-1),/已保存.*刷新失败/);assert.equal(r.$('#form-error').hidden,true);r.close();
}
async function metadata(){
 const h=setup();let finish;h.c.api=(url)=>url==='/api/metadata'?new Promise(r=>finish=r):Promise.resolve({resource:resource({title:'Draft'})});const reading=h.c.readMetadata();h.$('#f-title').value='Draft';await h.save();finish({title:'Late title',description:'Late description',favicon:'https://late.test/icon.png'});await reading;assert.equal(h.$('#f-title').value,'Draft');assert.equal(h.state.formBase.favicon,'');h.close();
}
async function quickActions(){
 const h=setup();h.state.editing=null;h.state.detail=null;await h.action('favorite',{id:'r'});assert.deepEqual(h.calls[0],{url:'/api/resources/r/edit',method:'POST',body:{changes:{favorite:true},expected:{favorite:false}}});
 h.c.detail=()=>{};await h.action('cover',{id:'r',file:'image'});assert.deepEqual(h.calls[1].body,{changes:{coverId:'image'},expected:{coverId:''}});assert.equal(Object.hasOwn(h.calls[1].body.changes,'colors'),false);
 let reloads=0,details=0;h.c.api=async()=>{throw conflict(resource({coverId:'latest'}),'coverId','image');};h.c.reload=async()=>{reloads++;};h.c.detail=()=>details++;await h.action('cover',{id:'r',file:'image'});assert.equal(reloads,1);assert.equal(details,1);assert.match(h.toasts.at(-1),/资料已变更/);h.close();
}
(async()=>{for(const test of [busy,deltas,recovery,uploads,metadata,quickActions])await test();console.log('Guarded editor: actual submit/actions, deltas, exact keys, busy races, conflict recovery, upload retries and late metadata passed.');})().catch(e=>{console.error(e);process.exitCode=1;});

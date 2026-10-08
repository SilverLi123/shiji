'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{JSDOM}=require('jsdom');
const root=path.join(__dirname,'../static'),app=fs.readFileSync(path.join(root,'app.js'),'utf8');
const cases=['Normal','__proto__','constructor','toString','hasOwnProperty','普通项目✨','HTML <"&>','Exact\u0000name'];
async function exercise(name,existing,remove=false,note='Typed note'){
 const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8')),doc=dom.window.document;let submit,payload;
 doc.querySelector('#resource-form').addEventListener=(type,fn)=>{assert.equal(type,'submit');submit=fn;};
 const projectNotes=JSON.parse('{"Historical":"Earlier note"}');if(existing)Object.defineProperty(projectNotes,name,{value:'Saved note',enumerable:true,writable:true});
 const item={id:'resource',kind:'file',title:'Resource',category:'其他',projects:existing?[name]:[],projectNotes,attachments:[],tags:[],notes:'Resource note',author:'Author',sourceUrl:'https://example.com/source',price:'待确认',license:'待确认'};
 const context={document:doc,$:s=>doc.querySelector(s),CATEGORIES:['其他'],state:{resources:[item],filters:{},scope:'all',metadataRun:0},esc:v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),split:v=>[...new Set(v.split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean))],pausePreviewPlayers(){},quickNoteMayLeave(){return true;},quickNoteSection(){return "";},closeMenu(){},renderPending(){},setKind(){},openDrawer(){},closeDrawer(){},syncFilters(){},reload:async()=>{},toast(){},api:async(url,method,raw)=>{assert.equal(url,'/api/resources/resource/edit');assert.equal(method,'POST');const patch=JSON.parse(JSON.stringify(raw));payload={...item,...patch.changes,projectNotes:{...item.projectNotes,...patch.changes.projectNotes}};return {resource:payload};}};
 context.window=dom.window;context.ShijiEdit=require('../static/edit-model');context.formTagEditor=require('../static/tag-editor').create(doc.querySelector('#tag-editor'),doc.querySelector('#f-tags'),v=>context.state.formTags=v,()=>{});vm.createContext(context);
 let start=app.indexOf('function projectFields()');vm.runInContext(app.slice(start,app.indexOf('\nfunction renderPending',start)),context);
 start=app.indexOf('function edit(item');vm.runInContext(app.slice(start,app.indexOf('\nasync function readMetadata',start)),context);context.edit(item);
 if(!existing){doc.querySelector('#f-projects').value=name;context.projectFields();}
 let textarea=doc.querySelector('[data-project-note]');assert.equal(textarea.value,existing?'Saved note':'','new project notes start empty even for prototype-like names');
 textarea.value=note;
 if(remove)doc.querySelector('#f-projects').value='';
 context.projectFields();
 start=app.indexOf("$('#resource-form').addEventListener('submit'");vm.runInContext(app.slice(start,app.indexOf("\n$('#f-url').addEventListener",start)),context);await submit({preventDefault(){}});
 assert.deepEqual(payload.projects,remove?[]:[name]);
 assert.equal(payload.projectNotes[name],note,'exact project name must receive its own typed note');
 assert.equal(payload.projectNotes.Historical,'Earlier note');
 assert.deepEqual(Object.keys(payload.projectNotes).sort(),['Historical',name].sort(),'no normalized or extra project-note keys');
 assert.equal(doc.querySelector('#form-error').hidden,true);
 context.edit({...item,...payload});
 if(!remove)assert.equal(doc.querySelector('[data-project-note]').value,note,'saved exact key displays on reopening');
 const otherNotes=JSON.parse('{"Other history":"Other earlier note"}');Object.defineProperty(otherNotes,name,{value:'Other resource note',enumerable:true});
 context.edit({...item,id:'other-resource',projects:[name],projectNotes:otherNotes});
 assert.equal(doc.querySelector('[data-project-note]').value,'Other resource note','switching resources loads the second resource note');
 assert.deepEqual(Object.keys(context.state.formProjects).sort(),['Other history',name].sort(),'old editor fields do not enter another resource');
 context.edit(null);assert.deepEqual(Object.keys(context.state.formProjects),[],'new resource starts without previous project notes');
 dom.window.close();
}
(async()=>{
 const failures=[];
 for(const name of cases)for(const existing of [false,true])for(const remove of [false,true]){
  try{await exercise(name,existing,remove);await exercise(name,existing,remove,'');}
  catch(e){failures.push(`${JSON.stringify(name)} existing=${existing} remove=${remove}: ${e.message}`);}
 }
 assert.deepEqual(failures,[]);
 console.log('Actual edit/capture/submit/reopen: prototype-like, Unicode, HTML and NUL project names preserve distinct changed/blank/historical notes.');
})().catch(e=>{console.error(e);process.exitCode=1;});

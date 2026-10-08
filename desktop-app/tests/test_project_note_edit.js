'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),{JSDOM}=require('jsdom');
const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const keys=['url','title','kind','category','description','notes','snippet','language','author','sourceUrl','parentId','price','license','thumbnail','licenseUrl','tags','projects'];
async function saveAfterRemoval(note,initial={P:'Original note',Historical:'Earlier note'}){
 const dom=new JSDOM('<form id="resource-form"><div class="form-body"><ul id="tag-editor-list"></ul>'+keys.map(k=>`<input id="f-${k}">`).join('')+'<input id="f-inbox" type="checkbox"><input id="f-favorite" type="checkbox"><div id="project-notes-fields"></div><button id="save-button"></button><section id="edit-conflict" hidden></section><p id="form-error" hidden></p></div></form>');
 const doc=dom.window.document,form=doc.querySelector('form');let submit,payload;
 form.addEventListener=(name,fn)=>{assert.equal(name,'submit');submit=fn;};
 const context={document:doc,$:s=>doc.querySelector(s),state:{formBase:{},formProjects:{...initial},editing:'resource',pending:[],scope:'all',filters:{}},split:v=>v.split(/[,，、\n]/).map(x=>x.trim()).filter(Boolean),esc:v=>String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'),api:async(url,method,raw)=>{assert.equal(url,'/api/resources/resource/edit');assert.equal(method,'POST');payload={projects:JSON.parse(JSON.stringify(raw)).changes.projects,projectNotes:{...initial,...JSON.parse(JSON.stringify(raw)).changes.projectNotes}};return {resource:{id:'resource',attachments:[]}};},closeDrawer(){},syncFilters(){},reload:async()=>{},toast(){}};
 context.window=dom.window;context.setKind=()=>{};context.ShijiEdit=require('../static/edit-model');context.state.formSnapshot={projects:['P'],projectNotes:{...initial}};context.state.formInitial={projects:['P'],projectNotes:{...initial}};context.formTagEditor=require('../static/tag-editor').create(doc.body,doc.querySelector('#f-tags'),v=>context.state.formTags=v,()=>{});vm.createContext(context);
 const start=app.indexOf('function projectFields()');vm.runInContext(app.slice(start,app.indexOf('\nfunction renderPending',start)),context);
 doc.querySelector('#f-projects').value='P';context.projectFields();context.state.formInitial=context.ShijiEdit.read(doc,context.state,context.split);context.state.formSnapshot={...context.state.formInitial,projects:['P'],projectNotes:{...initial}};
 doc.querySelector('[data-project-note]').value=note;
 doc.querySelector('#f-projects').value='';context.projectFields();
 assert.equal(context.state.formProjects.P,note,'blur captures the removed project’s pending edit');
 vm.runInContext(app.slice(app.indexOf('function setEditBusy('),app.indexOf('function showEditConflict(')),context);
 const handler=app.indexOf("$('#resource-form').addEventListener('submit'");vm.runInContext(app.slice(handler,app.indexOf("\n$('#f-url').addEventListener",handler)),context);
 await submit({preventDefault(){}});
 assert.deepEqual(payload.projects,[]);
 assert.equal(payload.projectNotes.P,note,'submit retains a changed or explicitly cleared former project note');
 assert.equal(payload.projectNotes.Historical,initial.Historical,'earlier retained notes survive the same edit');
 assert.equal(doc.querySelector('#form-error').hidden,true);
 dom.window.close();return payload;
}
(async()=>{
 await saveAfterRemoval('Newly edited note');
 await saveAfterRemoval('');
 await saveAfterRemoval('New temporary project note',{Historical:'Earlier note'});
 console.log('Actual full editor capture/submit preserves edited, blank and newly removed project notes.');
})().catch(e=>{console.error(e);process.exitCode=1;});

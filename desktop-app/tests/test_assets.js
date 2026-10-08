'use strict';
const assert=require('node:assert/strict'),model=require('../static/asset-model.js');
const input=[{status:'new',index:0},{status:'existing',index:1},{status:'trash',index:2},{status:'duplicate',index:3},{status:'invalid',index:4}];
const rows=model.initial(input);assert.deepEqual(rows.map(r=>r.selected),[true,false,false,false,false]);assert.equal(input[0].selected,undefined);
rows[0].result='saved';rows[1].selected=true;rows[1].result='failed';rows[2].selected=true;rows[2].result='skipped';rows[3].selected=true;
assert.deepEqual(model.pending(rows).map(r=>r.index),[1,3]);assert.deepEqual(model.counts(rows),{selected:4,saved:1,skipped:1,failed:1,remaining:2});
assert.equal(model.page(Array.from({length:45},(_,index)=>index),2).length,5);assert.deepEqual(model.page(rows,0,2),rows.slice(0,2));
rows[1].result='saved';rows[3].result='skipped';assert.equal(model.pending(rows).length,0);
console.log('Asset selection, duplicate defaults, retry boundaries, counts and pagination passed.');

// Exercise the actual intake close listener, including the header/Escape route.
const vm=require('node:vm'),fs=require('node:fs');
let ready,closeListener,activeForm=null;
const formDefaults=()=>({tags:'',project:'',sourceUrl:'',author:'',license:'待确认',licenseUrl:''});
const ctx={ShijiAssets:model,state:{filters:{},collectionMeta:[]},esc:String,size:String,projectOptions:()=>'',split:v=>v.split(/[，,]/).filter(Boolean),
  FormData:class {constructor(form){this.values=form.values;}get(k){return this.values[k];}},
  document:{addEventListener:(name,fn)=>{if(name==='DOMContentLoaded')ready=fn;},querySelectorAll:()=>[]},
  manage:()=>{activeForm={values:formDefaults()};},toast:()=>{},
  $:selector=>{
    if(selector==='[data-manage-form="assets"]')return activeForm;
    if(selector==='#asset-folder')return {addEventListener:()=>{}};
    if(selector==='#manage-dialog')return {open:false,addEventListener:(name,fn)=>{if(name==='close')closeListener=fn;}};
    const match=selector.match(/\[name="(.*?)"\]/);
    if(match&&activeForm)return {set value(v){activeForm.values[match[1]]=v;},get value(){return activeForm.values[match[1]];}};
  }
};
vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../static/asset-intake.js'),'utf8'),ctx);ready();
vm.runInContext('assetIntakePanel()',ctx);
const entered={tags:'设计，游戏',project:'项目 A',sourceUrl:'https://source.example/',author:'作者',license:'需署名',licenseUrl:'https://source.example/license'};
Object.assign(activeForm.values,entered);closeListener();vm.runInContext('assetIntakePanel()',ctx);
assert.deepEqual(activeForm.values,entered);
// Closing a different management form must not overwrite saved intake options.
activeForm=null;closeListener();vm.runInContext('assetIntakePanel()',ctx);assert.deepEqual(activeForm.values,entered);
console.log('Intake common metadata persists through close/reopen; unrelated forms do not overwrite it.');

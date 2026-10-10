'use strict';
// This integration is invoked by Python against a real temporary HTTP/SQLite store.
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{JSDOM}=require('jsdom');
let runtimeDom;
(async()=>{
 const {base}=JSON.parse(fs.readFileSync(0,'utf8')),html=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
 const dom=runtimeDom=new JSDOM(html,{url:base,runScripts:'outside-only',pretendToBeVisual:true}),w=dom.window,d=w.document;
 w.fetch=(url,options)=>fetch(new URL(url,base),options);w.matchMedia=q=>({matches:q.includes('pointer')||q.includes('hover'),addEventListener(){},removeEventListener(){}});w.scrollTo=()=>{};w.ResizeObserver=class {observe(){} unobserve(){} disconnect(){}};w.IntersectionObserver=undefined;
 w.Element.prototype.getBoundingClientRect=()=>({x:0,y:80,left:0,top:80,width:300,height:240,right:300,bottom:320});Object.defineProperty(d.querySelector('#resource-grid'),'clientWidth',{value:900});
 for(const dialog of d.querySelectorAll('dialog')){dialog.showModal=function(){this.open=true;};dialog.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'));};}
 let rendered=0;d.addEventListener('shiji:rendered',()=>rendered++);
 const wait=async check=>{const end=Date.now()+8000;while(!check()){assert.ok(Date.now()<end,'real application condition timed out');await new Promise(r=>setTimeout(r,10));}};
 w.eval([...d.querySelectorAll('script[src]')].map(script=>process.env.SHIJI_QA_BASELINE&&script.getAttribute('src')==='stable-cards.js'?execFileSync('git',['show','d7a6749:desktop-app/static/stable-cards.js'],{cwd:path.join(__dirname,'../..'),encoding:'utf8'}):fs.readFileSync(path.join(__dirname,'../static',script.getAttribute('src')),'utf8')).join('\n')); 
 await wait(()=>rendered>0);
 d.querySelector('.topbar [data-action="add"]').click();d.querySelector('#quick-url').value='https://github.com/SilverLi123/shiji';d.querySelector('#quick-capture-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));
 await wait(()=>!!d.querySelector('#resource-grid .card-preview'));
 const before=await(await fetch(base+'/api/resources')).json();assert.equal(before.resources.length,1);const id=before.resources[0].id;
 const preview=d.querySelector('#resource-grid .card-preview'),card=preview.closest('.resource-card'),count=rendered;
 const pointer=name=>{const e=new w.MouseEvent(name,{bubbles:true,cancelable:true,clientX:110,clientY:130,button:0});Object.defineProperties(e,{pointerType:{value:'mouse'},pointerId:{value:1}});preview.dispatchEvent(e);};
 pointer('pointerdown');await fetch(base+'/qa-release',{method:'POST'});await wait(()=>rendered>count&&d.querySelector('#resource-grid .card-preview').textContent.includes('已补全的真实资源'));
 assert.equal(d.querySelector('#resource-grid .card-preview'),preview);assert.equal(d.querySelector('#resource-grid .resource-card'),card);assert.equal(preview.dataset.id,id);
 pointer('pointerup');preview.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true,detail:1}));
 assert.equal(d.querySelector('#drawer').hidden,false,'the single original click opens the real detail drawer');assert.equal(d.querySelector('#drawer-title').textContent,'已补全的真实资源');
 const saved=await(await fetch(base+'/api/resources')).json();assert.equal(saved.resources[0].id,id);assert.equal(saved.resources[0].title,'已补全的真实资源');
 dom.window.close();console.log('PASS: real Quick Capture -> durable SQLite -> delayed enrich -> actual app render during press -> one original detail click');
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>runtimeDom?.window.close());

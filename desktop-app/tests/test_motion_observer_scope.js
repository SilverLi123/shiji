'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{JSDOM}=require('jsdom');
const {init}=require('../static/shiji-v2-motion');
(async()=>{
 const dom=new JSDOM(fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8'),{url:'http://localhost',pretendToBeVisual:true}),w=dom.window,d=w.document;
 w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
 w.Element.prototype.animate=()=>({finished:new Promise(()=>{}),cancel(){},play(){},pause(){}});
 let scans=0;const query=d.querySelectorAll.bind(d);d.querySelectorAll=s=>{if(s==='.art-v3')scans++;return query(s);};
 const ui=init({document:d,window:w});await new Promise(r=>setImmediate(r));scans=0;
 const status=d.createElement('span');d.body.append(status);status.textContent='Saved';await new Promise(r=>setImmediate(r));
 assert.equal(scans,0,'status, particles and QA metrics must not rescan every poster');
 const art=d.createElement('div');art.className='art-v3';d.body.append(art);await new Promise(r=>setImmediate(r));
 assert.ok(art.classList.contains('art-in-view'),'new artwork still participates');
 art.remove();await new Promise(r=>setImmediate(r));assert.ok(scans>=2,'removed artwork releases observers');
 ui.destroy();dom.window.close();console.log('PASS: mutation work limited to artwork and overlay state');
})().catch(e=>{console.error(e);process.exitCode=1;});

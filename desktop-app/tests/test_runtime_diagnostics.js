'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{JSDOM}=require('jsdom');
const source=fs.readFileSync(path.join(__dirname,'../static/runtime-diagnostics.js'),'utf8'),shell=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');
assert.ok(!shell.includes('runtime-diagnostics.js'),'normal libraries never load the QA probe');
const dom=new JSDOM(shell,{url:'http://localhost',runScripts:'outside-only'}),w=dom.window,d=w.document;let t=0,id=0;const pending=new Map();
Object.defineProperty(w,'performance',{value:{now:()=>t}});Object.defineProperty(d,'hidden',{value:false,configurable:true});
w.requestAnimationFrame=fn=>{pending.set(++id,fn);return id;};w.cancelAnimationFrame=id=>pending.delete(id);
d.getAnimations=()=>[{constructor:{name:'CSSAnimation'},playState:'running'},{constructor:{name:'CSSTransition'},playState:'running'}];
const modalProxy=d.createElement('div');modalProxy.className='shiji-dialog-exit';d.body.append(modalProxy);
w.eval(source);d.dispatchEvent(new w.Event('DOMContentLoaded'));
const search=d.querySelector('#search');search.value='PRIVATE RESOURCE CONTENT';
for(let i=0;i<300;i++)search.dispatchEvent(new w.Event('input',{bubbles:true}));
const rows=()=>JSON.parse(d.querySelector('#qa-runtime-metrics').textContent);
assert.ok(rows().length<=240);assert.ok(!JSON.stringify(rows()).includes(search.value));assert.equal(rows().at(-1).cssRunning,1);assert.equal(rows().at(-1).transitionRunning,1);assert.equal(rows().at(-1).ghosts,1,'count the actual modal proxy class');
for(let i=0;i<220;i++){t+=17;const batch=[...pending.values()];pending.clear();batch.forEach(fn=>fn(t));}
const frames=rows().filter(r=>r.event==='frames').length;assert.ok(frames>0);
w.dispatchEvent(new w.Event('pagehide'));assert.equal(rows().filter(r=>r.event==='frames').length,frames,'completed frame bins must not be reported twice');
assert.equal(pending.size,0);dom.window.close();console.log('PASS: opt-in metadata-only bounded diagnostics, animation classification and one report per frame window');

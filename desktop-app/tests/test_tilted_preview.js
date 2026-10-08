const assert=require('node:assert/strict');
const fs=require('node:fs');const {JSDOM}=require('jsdom');
const {tiltPoint}=require('../static/resource-bits');
assert.deepEqual(tiltPoint(200,150,{left:100,top:50,width:200,height:200}),{x:-0,y:0});
assert.deepEqual(tiltPoint(300,50,{left:100,top:50,width:200,height:200}),{x:3,y:3});
assert.deepEqual(tiltPoint(-999,999,{left:100,top:50,width:200,height:200}),{x:-3,y:-3});
assert.deepEqual(tiltPoint(1,1,{width:0,height:2}),{x:0,y:0});
const dom=new JSDOM('<div id="grid"><article class="resource-card" data-resource-id="one"><button class="card-preview"><img class="cover-image"></button></article></div><button id="save"></button>',{runScripts:'outside-only'});
const w=dom.window;const grid=w.document.getElementById('grid'),preview=grid.querySelector('button'),img=grid.querySelector('img');
const queries=new Map();w.matchMedia=q=>{if(!queries.has(q)){const a=new w.EventTarget();a.matches=!q.includes('reduced');queries.set(q,a);}return queries.get(q);};
w.ResizeObserver=class{observe(){}disconnect(){}};w.requestAnimationFrame=()=>1;w.cancelAnimationFrame=()=>{};
Object.defineProperty(grid,'clientWidth',{value:600});preview.getBoundingClientRect=()=>({left:100,top:50,width:200,height:200});
Object.defineProperty(img,'complete',{value:true,configurable:true});Object.defineProperty(img,'naturalWidth',{value:800,configurable:true});
w.eval(fs.readFileSync(require.resolve('../static/resource-bits'),'utf8'));
const ui=w.ShijiBits.create(grid,w.document.getElementById('save'));ui.render();
function move(type='mouse',target=img){const e=new w.MouseEvent('pointermove',{bubbles:true,clientX:300,clientY:50});Object.defineProperty(e,'pointerType',{value:type});target.dispatchEvent(e);}
function active(){return preview.classList.contains('bits-tilt-active');}
move();assert.ok(active());assert.equal(preview.style.getPropertyValue('--tilt-x'),'3deg');assert.equal(preview.style.getPropertyValue('--tilt-y'),'3deg');
img.dispatchEvent(new w.MouseEvent('pointerout',{bubbles:true,relatedTarget:preview}));assert.ok(active(),'moving within preview retains pose');
preview.dispatchEvent(new w.MouseEvent('pointerout',{bubbles:true}));assert.ok(!active());assert.equal(preview.style.getPropertyValue('--tilt-x'),'');
for(const kind of ['touch','pen']){move(kind);assert.ok(!active(),kind+' is static');}
move();grid.classList.add('preview-fit');move();assert.ok(!active(),'fit mode is static');grid.classList.remove('preview-fit');
Object.defineProperty(img,'naturalWidth',{value:0,configurable:true});move();assert.ok(!active(),'broken image is static');Object.defineProperty(img,'naturalWidth',{value:800,configurable:true});
preview.disabled=true;move();assert.ok(!active());preview.disabled=false;
for(const name of ['focusin','scroll','blur']){move();assert.ok(active());(name==='focusin'?preview:w).dispatchEvent(new w.Event(name,{bubbles:true}));assert.ok(!active(),name+' resets');}
move();ui.begin();assert.ok(!active(),'render/layout resets');
for(const [q,on] of [['(prefers-reduced-motion: reduce)',true],['(hover: hover) and (pointer: fine)',false]]){
  move();assert.ok(active());const mq=queries.get(q),prior=mq.matches;mq.matches=on;mq.dispatchEvent(new w.Event('change'));assert.ok(!active());move();assert.ok(!active());mq.matches=prior;mq.dispatchEvent(new w.Event('change'));
}
move();ui.destroy();assert.ok(!active());move();assert.ok(!active(),'destroy removes listeners');
dom.window.close();console.log('TiltedCard native DOM: bounded mapping, stable image-only pose, guards, reset and lifecycle passed.');

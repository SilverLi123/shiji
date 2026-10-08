// Developer-only DOM verification; jsdom does not ship as an application dependency.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom'),bits=require('../static/resource-bits');
assert.equal(bits.imageRatio(1280,720),1280/720);
assert.equal(bits.imageRatio(400,1200),1/3);
assert.equal(bits.imageRatio(10000,1),16);
assert.equal(bits.imageRatio(1,10000),.125);
for(const [w,h] of [[0,720],[1280,0],[NaN,2],[2,Infinity]])assert.equal(bits.imageRatio(w,h),1.6);
const dom=new JSDOM('<section id="grid" class="preview-fit"><article class="resource-card" data-resource-id="a"><button class="card-preview"><img class="cover-image"></button></article></section>',{url:'http://localhost'});
const win=dom.window,grid=win.document.querySelector('#grid'),image=grid.querySelector('img'),preview=grid.querySelector('button');
assert.equal(bits.readPreviewMode(win.localStorage),'frame');bits.savePreviewMode(win.localStorage,'fit');assert.equal(bits.readPreviewMode(win.localStorage),'fit');
bits.savePreviewMode(win.localStorage,'invalid');assert.equal(bits.readPreviewMode(win.localStorage),'frame');
const unavailable={getItem(){throw Error('blocked');},setItem(){throw Error('quota');}};assert.equal(bits.readPreviewMode(unavailable),'frame');assert.doesNotThrow(()=>bits.savePreviewMode(unavailable,'fit'));
let width=0,height=0,pending=null,measurements=0;
Object.defineProperties(image,{naturalWidth:{get:()=>width},naturalHeight:{get:()=>height}});
Object.defineProperty(grid,'clientWidth',{value:600});
Object.defineProperty(grid.children[0],'offsetHeight',{get(){measurements++;return 200;}});
const keys=['innerWidth','matchMedia','addEventListener','removeEventListener','requestAnimationFrame','cancelAnimationFrame','ResizeObserver'],saved=keys.map(k=>[k,global[k]]);
try{
 global.innerWidth=1280;global.matchMedia=()=>({matches:true,addEventListener(){},removeEventListener(){}});
 global.addEventListener=()=>{};global.removeEventListener=()=>{};global.ResizeObserver=undefined;
 global.requestAnimationFrame=fn=>{pending=fn;return 1;};global.cancelAnimationFrame=()=>{pending=null;};
 const ui=bits.create(grid,null);ui.render();assert.equal(preview.style.getPropertyValue('--image-ratio'),'1.6');
 width=400;height=1200;image.dispatchEvent(new win.Event('load'));assert.equal(typeof pending,'function','late image arrival schedules measured reflow');
 pending();pending=null;assert.equal(preview.style.getPropertyValue('--image-ratio'),String(1/3));assert.ok(measurements>=2);
 width=0;height=0;image.dispatchEvent(new win.Event('error'));pending();pending=null;assert.equal(preview.style.getPropertyValue('--image-ratio'),'1.6','failed image uses a usable fallback frame');
 grid.classList.add('board-layout');width=1200;height=400;ui.render();assert.equal(preview.style.getPropertyValue('--image-ratio'),'3','board previews also use the decoded ratio');assert.equal(grid.style.height,'');
 grid.classList.remove('preview-fit');image.dispatchEvent(new win.Event('load'));assert.equal(pending,null,'composition mode avoids image reflow');
 grid.classList.add('preview-fit');ui.destroy();image.dispatchEvent(new win.Event('load'));assert.equal(pending,null,'destroy removes captured image listeners');
}finally{for(const [k,v] of saved){if(v===undefined)delete global[k];else global[k]=v;}dom.window.close();}
// Exercise the app's actual native change handler, including storage failure.
const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8'),vm=require('node:vm');
const handler=app.split('\n').find(line=>line.startsWith("$('#preview-mode').addEventListener"));let change,rendered=0;
const state={previewMode:'frame'};vm.runInNewContext(handler,{state,ShijiBits:bits,localStorage:unavailable,$:()=>({addEventListener(_,fn){change=fn;}}),render(){rendered++;}});
change({target:{value:'fit'}});assert.equal(state.previewMode,'fit');assert.equal(rendered,1);
change({target:{value:'invalid'}});assert.equal(state.previewMode,'frame');assert.equal(rendered,2);
console.log('full preview ratios, bounds, late-load/error reflow, board reuse, preference persistence/failure and lifecycle passed');

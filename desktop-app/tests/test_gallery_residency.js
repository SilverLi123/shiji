/* Unit residency/cache contract; real CSS/layout is covered separately in gallery_browser.cjs. */
'use strict';
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),{pack}=require('../static/resource-bits'),Cards=require('../static/stable-cards'),Window=require('../static/gallery-window');
(async()=>{
const dom=new JSDOM('<html data-shiji-version="v5"><body><section id="grid" class="resource-grid bits-masonry"></section></body></html>',{pretendToBeVisual:true}),w=dom.window,d=w.document,grid=d.getElementById('grid');
Object.defineProperty(grid,'clientWidth',{get:()=>900});grid.getBoundingClientRect=()=>({top:0,bottom:5000,left:0,width:900,height:5000});
Object.defineProperty(w.HTMLElement.prototype,'offsetHeight',{get(){return this.dataset.galleryWide==='true'?300:230}});
w.scrollBy=()=>{};let renders=0,reconciles=0,packs=0,coverReads=0;const selected=new Set();
const rows=Array.from({length:1000},(_,i)=>({id:String(i),title:'Title'+i,span:i%13===0?2:1}));
const ui=Window.create({grid,pack(...args){packs++;return pack(...args)},reconcile(...args){reconciles++;Cards.render(...args)},renderCard(r){renders++;return `<article class="resource-card ${selected.has(r.id)?'selected':''}" data-resource-id="${r.id}"><div class="card-motion-surface"><button class="card-preview">${r.title}</button></div></article>`},version:r=>String(selected.has(r.id)),span:r=>r.span,cover:()=>{coverReads++;return '';},schedule(){}});
const config={width:900,columns:3,gap:18,rowGap:33,feature:true};ui.setItems(rows,'all','normal');ui.layout(config);const first=grid.firstElementChild,initialRenders=renders,initialReconciles=reconciles,initialPacks=packs;
assert.ok(grid.children.length<30);assert.ok(coverReads<200,'frame geometry must not resolve cover preferences for every unmeasured offscreen row: '+coverReads);ui.layout(config);assert.equal(reconciles,initialReconciles,'same viewport does not repeatedly reconcile/repaint unchanged DOM');assert.equal(renders,initialRenders);
selected.add('0');ui.setItems(rows.slice(),'all','normal');ui.layout(config);assert.equal(packs,initialPacks,'selection-only display updates do not repack1000rows');assert.equal(renders,initialRenders+1,'only changed mounted selection regenerates markup');assert.equal(grid.firstElementChild,first);assert.ok(first.classList.contains('selected'));
rows[0]={...rows[0],title:'Updated'};ui.setItems(rows,'all','normal');ui.layout(config);assert.equal(grid.firstElementChild.textContent,'Updated');
grid.querySelector('button').dispatchEvent(new w.Event('pointerdown',{bubbles:true}));let flushed=0;
assert.equal(ui.deferWhilePressed(()=>flushed++),true,'hold global rendering until pointer-up/click dispatch completes');
assert.equal(flushed,0);w.dispatchEvent(new w.Event('pointerup'));assert.equal(flushed,0,'do not flush before the ensuing click');
await new Promise(r=>w.setTimeout(r,10));assert.equal(flushed,1,'release flushes the latest render once');
assert.equal(ui.deferWhilePressed(()=>flushed++),false,'ordinary rendering remains synchronous');
grid.querySelector('button').dispatchEvent(new w.Event('pointerdown',{bubbles:true}));ui.deferWhilePressed(()=>flushed++);w.dispatchEvent(new w.Event('blur'));await new Promise(r=>w.setTimeout(r,10));assert.equal(flushed,2,'blur cannot leave a pending render permanently blocked');
const beforePatch=renders,kept=grid.firstElementChild;assert.equal(ui.refresh({...rows[0],title:'Cover changed'}),true);ui.layout(config);assert.equal(grid.firstElementChild,kept);assert.equal(kept.textContent,'Cover changed');assert.equal(renders,beforePatch+1,'one cover refresh does not regenerate siblings');
const visibleRenders=renders;assert.equal(ui.refresh({...rows[999],title:'Offscreen cover'}),true);ui.layout(config);assert.equal(renders,visibleRenders,'offscreen cover refresh creates no visible art');assert.equal(ui.refresh({id:'outside-query'}),false);
ui.setItems([],'all','normal');ui.layout(config);assert.equal(grid.children.length,0);ui.destroy();dom.window.close();
console.log('residency no-op scroll, per-card display invalidation, bounded HTML and empty cleanup passed');
})().catch(e=>{console.error(e);process.exitCode=1});

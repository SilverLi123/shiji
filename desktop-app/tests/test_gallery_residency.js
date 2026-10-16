/* Unit residency/cache contract; real CSS/layout is covered separately in gallery_browser.cjs. */
'use strict';
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),{pack}=require('../static/resource-bits'),Cards=require('../static/stable-cards'),Window=require('../static/gallery-window');
const dom=new JSDOM('<html data-shiji-version="v5"><body><section id="grid" class="resource-grid bits-masonry"></section></body></html>',{pretendToBeVisual:true}),w=dom.window,d=w.document,grid=d.getElementById('grid');
Object.defineProperty(grid,'clientWidth',{get:()=>900});grid.getBoundingClientRect=()=>({top:0,bottom:5000,left:0,width:900,height:5000});
Object.defineProperty(w.HTMLElement.prototype,'offsetHeight',{get(){return this.dataset.galleryWide==='true'?300:230}});
w.scrollBy=()=>{};let renders=0,reconciles=0,packs=0;const selected=new Set();
const rows=Array.from({length:1000},(_,i)=>({id:String(i),title:'Title'+i,span:i%13===0?2:1}));
const ui=Window.create({grid,pack(...args){packs++;return pack(...args)},reconcile(...args){reconciles++;Cards.render(...args)},renderCard(r){renders++;return `<article class="resource-card ${selected.has(r.id)?'selected':''}" data-resource-id="${r.id}"><div class="card-motion-surface"><button class="card-preview">${r.title}</button></div></article>`},version:r=>String(selected.has(r.id)),span:r=>r.span,cover:()=>'',schedule(){}});
const config={width:900,columns:3,gap:18,rowGap:33,feature:true};ui.setItems(rows,'all','normal');ui.layout(config);const first=grid.firstElementChild,initialRenders=renders,initialReconciles=reconciles,initialPacks=packs;
assert.ok(grid.children.length<30);ui.layout(config);assert.equal(reconciles,initialReconciles,'same viewport does not repeatedly reconcile/repaint unchanged DOM');assert.equal(renders,initialRenders);
selected.add('0');ui.setItems(rows.slice(),'all','normal');ui.layout(config);assert.equal(packs,initialPacks,'selection-only display updates do not repack1000rows');assert.equal(renders,initialRenders+1,'only changed mounted selection regenerates markup');assert.equal(grid.firstElementChild,first);assert.ok(first.classList.contains('selected'));
rows[0]={...rows[0],title:'Updated'};ui.setItems(rows,'all','normal');ui.layout(config);assert.equal(grid.firstElementChild.textContent,'Updated');
ui.setItems([],'all','normal');ui.layout(config);assert.equal(grid.children.length,0);ui.destroy();dom.window.close();
console.log('residency no-op scroll, per-card display invalidation, bounded HTML and empty cleanup passed');

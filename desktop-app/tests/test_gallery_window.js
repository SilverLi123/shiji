'use strict';
const assert=require('node:assert/strict'),{pack}=require('../static/resource-bits');
const {createGeometry}=require('../static/gallery-window');
const rows=Array.from({length:5000},(_,i)=>({id:String(i),span:i%13===0?2:1,height:150+i%7*53}));
const original=JSON.stringify(rows),g=createGeometry(pack);
for(const columns of [1,2,3]){
 const config={width:columns*310,columns,gap:18,rowGap:33};
 const expected=pack(rows.map(r=>r.height),config.width,columns,18,rows.map(r=>r.span),33);
 g.rebuild(rows,config,r=>r.height);
 assert.equal(g.height,expected.height);assert.deepEqual(g.position('7'),expected.items[7]);
 for(const top of [0,1000,10000,g.height-900]){
  const indices=g.visible(top,top+900,450,new Set(['4999']));
  const expectedIndices=expected.items.flatMap((p,i)=>p.y+p.h>=top-450&&p.y<=top+1350?[i]:[]);
  assert.deepEqual(indices,[...new Set([...expectedIndices,4999])].sort((a,b)=>a-b));
  assert.ok(indices.length<60,'DOM working set bounded independently of5000rows');
 }
}
const before=g.position('120'),anchor=g.anchor(before.y+10,before.y+600);assert.ok(anchor);
const old=g.position(anchor.id).y;rows[0]={...rows[0],height:rows[0].height+200};g.rebuild(rows,{width:930,columns:3,gap:18,rowGap:33},r=>r.height);
assert.equal(g.anchorDelta(anchor),g.position(anchor.id).y-old);
const keep=g.position('120');g.rebuild([...rows,{id:'new',span:2,height:567}],{width:930,columns:3,gap:18,rowGap:33},r=>r.height);assert.deepEqual(g.position('120'),keep,'append preserves prior geometry');
g.rebuild(rows.slice().reverse(),{width:930,columns:3,gap:18,rowGap:33},r=>r.height);assert.equal(g.position('4999').y,0,'reorder respects source order');
g.rebuild([],{width:930,columns:3,gap:18,rowGap:33},()=>0);assert.equal(g.height,0);assert.deepEqual(g.visible(0,900,450,new Set(['missing'])),[]);assert.equal(g.anchorDelta(anchor),0);
assert.equal(JSON.stringify(rows.slice(1)),JSON.stringify(JSON.parse(original).slice(1)),'geometry never mutates source data');
console.log('variable masonry heights/spans, indexed viewport/overscan, pins, anchors, append/reorder and empty geometry passed');

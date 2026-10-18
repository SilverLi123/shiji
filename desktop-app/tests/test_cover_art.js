const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),V5=require('../static/shiji-v5');
const d=new JSDOM('<div></div>').window.document,root=d.querySelector('div');
const r={id:'real',title:'长中文标题与代码 <script>alert(1)</script>',kind:'code',url:'https://github.com/silver/shiji',language:'JavaScript',snippet:'const title = "<img onerror=alert(1)>";\n  return title;',description:'实际说明',tags:['真实标签'],category:'开发工具'};
const layouts=new Set();
for(const style of ['editorial','spatial','developer','kinetic','minimal'])for(const template of ['a','b','c']){
 const item={...r,coverConfig:{style,template,customTitle:'独立封面标题',customSubtitle:'真实副标题',primary:'#777777'}};
 const markup=V5.coverMarkup(item);root.innerHTML=markup;
 assert.equal(root.querySelector('.cs3-title')?.textContent,'独立封面标题');
 assert.equal(root.querySelector('.cs3-subtitle')?.textContent,'真实副标题');
 assert.equal(root.querySelector('.cs3-cover')?.dataset.coverCustomTitle,'true');
 assert.equal(root.querySelector('script,img,[onerror],iframe'),null);
 assert.equal(root.querySelector('.cs3-cover')?.dataset.coverStyle,style);
 assert.equal(root.querySelector('.cs3-cover')?.dataset.coverTemplate,template);
 layouts.add(root.querySelector('.cs3-composition')?.dataset.composition);
 assert.equal(V5.coverMarkup(item),markup,'no randomness on remount');
}
assert.equal(layouts.size,15,'materially named authored compositions');
root.innerHTML=V5.coverMarkup({...r,coverConfig:{style:'developer',template:'a'}});
assert.ok(root.querySelector('pre').textContent.includes('  return title;'));
assert.ok(!root.querySelector('img'));
assert.equal(r.title,'长中文标题与代码 <script>alert(1)</script>');
root.innerHTML=V5.coverMarkup({...r,coverConfig:{version:5,style:'future'}});assert.equal(root.querySelector('.cs3-cover'),null);assert.ok(root.querySelector('.art-code'));
root.innerHTML=V5.coverMarkup({...r,coverConfig:{style:'v5'}});assert.equal(root.querySelector('.cs3-cover'),null);
root.innerHTML=V5.coverMarkup({...r,kind:'prompt',snippet:'Exact <prompt>',description:'Other description',notes:'Other notes',coverConfig:null});assert.ok(root.textContent.includes('Exact <prompt>'));assert.equal(root.querySelector('prompt'),null);
console.log('PASS: 15 authored cover compositions, safe real text/code, custom title separation and original V5 fallback');

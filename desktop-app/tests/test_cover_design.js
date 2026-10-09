'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{JSDOM}=require('jsdom');
const ui=require('../static/shiji-v2'),board=require('../static/board-model'),{pack}=require('../static/resource-bits');
const records=[
 {id:'tool',kind:'website',title:'My real project',url:'https://github.com/owner/project',category:'开发工具',language:'Swift',tags:['SQLite'],favorite:true},
 {id:'design',kind:'website',title:'设计系统与构图',url:'https://design.example/',category:'UI / 设计',tags:[]},
 {id:'motion',kind:'website',title:'Motion reference',url:'https://motionsites.ai/',category:'灵感',tags:[]},
 {id:'code',kind:'code',title:'Actual source',language:'JavaScript',snippet:'const label = "<script>alert(1)</script>";\nreturn label;',tags:[]},
 {id:'prompt',kind:'prompt',title:'自己的提示词',snippet:'从材料、光线与构图分析参考。',tags:[]},
 {id:'article',kind:'website',title:'从收集到创作：关于界面节奏、内容层次与长期灵感管理的一份长标题笔记',url:'https://reading.example/',category:'灵感',tags:[]},
 {id:'audio',kind:'file',title:'Saved audio',category:'音频',tags:[]},
 {id:'file',kind:'file',title:'Saved document',category:'其他',tags:[]}
];
assert.deepEqual(records.map(ui.coverKind),['tool','design','motion','code','prompt','article','audio','file']);
for(const record of records){
 const original=JSON.stringify(record),html=ui.coverMarkup(Object.freeze(record));
 const dom=new JSDOM(html),el=dom.window.document.querySelector('.cover-art');
 assert.equal(el.classList.contains('cover-'+ui.coverKind(record)),true);
 assert.equal(el.getAttribute('aria-hidden'),'true');
 assert.ok(el.textContent.includes(record.title));assert.equal(JSON.stringify(record),original);
 assert.equal(ui.coverMarkup(record),html,'no random or time-dependent composition');
 assert.ok(Number.isFinite(ui.coverRatio(record)));assert.equal(dom.window.document.querySelectorAll('script,img,button,a,input').length,0);
 dom.window.close();
}
const code=new JSDOM(ui.coverMarkup(records[3]));
assert.equal(code.window.document.querySelector('code').textContent,records[3].snippet.split('\n')[0]);
assert.equal(code.window.document.querySelectorAll('script').length,0);code.window.close();
const hostile={...records[0],title:'"><img src=x onerror=alert(1)>',language:'<svg onload=alert(1)>',tags:['<script>bad</script>']};
const escaped=new JSDOM(ui.coverMarkup(hostile));assert.equal(escaped.window.document.querySelectorAll('img,script,[onload],[onerror]').length,0);escaped.window.close();
assert.deepEqual(records.map(ui.gallerySpan),[2,1,1,1,1,1,1,1]);
const roles=new Map(records.map(r=>[r.id,ui.gallerySpan(r)]));for(const r of [...records].reverse())assert.equal(ui.gallerySpan(r),roles.get(r.id));
assert.equal(ui.gallerySpan({...records[0],favorite:false}),2,'favourite toggles never change the feature footprint');
// Execute actual preview and image handlers, including the existing adjacent
// fallback contract used by keyed image reuse after an edit.
const app=fs.readFileSync(require.resolve('../static/app.js'),'utf8');
const context={ShijiBoard:board,ShijiV2:ui,esc:v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))};
vm.createContext(context);vm.runInContext(app.slice(app.indexOf('function preview(r)'),app.indexOf('\nfunction card(r)')),context);
vm.runInContext(app.slice(app.indexOf('function attachImageFallbacks(root)'),app.indexOf('\nconst resourceBits=')),context);
for(const image of [{coverId:'local'}, {thumbnail:'https://images.example/actual.jpg'}, {url:'https://polyhaven.com/'}]){
 const r={...records[0],...image},dom=new JSDOM(context.preview(r)),doc=dom.window.document,img=doc.querySelector('img.cover-image');
 assert.ok(img);assert.equal(img.getAttribute('src'),board.cover(r));assert.ok(img.nextElementSibling.matches('.cover-art'));
 context.attachImageFallbacks(doc);img.onerror();assert.equal(img.hidden,true);assert.equal(img.nextElementSibling.hidden,false);
 img.onload();assert.equal(img.hidden,false);assert.equal(img.nextElementSibling.hidden,true);dom.window.close();
}
assert.equal(new JSDOM(context.preview(records[3])).window.document.querySelector('img'),null);
// The actual card renderer puts every visual/control inside the same surface,
// while preserving the resource ID and the existing delegated actions.
Object.assign(context,{state:{selected:new Set(),selectMode:true,filters:{}},domain:url=>{try{return new URL(url).hostname;}catch{return '';}},KINDS:{website:'网站',snippet:'代码'},visual:()=>['','#fff','#000'],icon:()=>'<svg></svg>',ShijiGallery:{media:()=>[]}});
vm.runInContext(app.slice(app.indexOf('function card(r)'),app.indexOf('\n',app.indexOf('function card(r)'))),context);
for(const record of records){
 const r={...record,attachments:[],favorite:false,price:'待确认',projects:[]},doc=new JSDOM(context.card(r)).window.document,el=doc.querySelector('.resource-card'),surface=el.querySelector('.card-motion-surface');
 assert.equal(el.dataset.resourceId,r.id);assert.equal(el.children.length,1);assert.ok(surface.querySelector('.card-preview'));assert.ok(surface.querySelector('.card-title'));assert.ok(surface.querySelector('.card-footer'));assert.ok(surface.querySelector('[data-select]'));assert.ok(surface.querySelector('[data-action="favorite"]'));
 doc.defaultView.close();
}
// Span packing uses contiguous columns and must stay deterministic, bounded,
// and free of overlap across long lists, responsive widths and mixed heights.
for(const n of [1,2,3]){
 const heights=Array.from({length:1000},(_,i)=>120+(i*97)%410),spans=heights.map((_,i)=>i%7===0?2:1);
 const p=pack(heights,1100,n,22,spans);assert.deepEqual(pack(heights,1100,n,22,spans),p);
 for(let i=0;i<p.items.length;i++){
  const a=p.items[i];assert.ok(a.x>=0&&a.x+a.w<=1100.001&&a.y+a.h<=p.height+.001);
  for(let j=0;j<i;j++){const b=p.items[j];assert.ok(a.x+a.w<=b.x+.001||b.x+b.w<=a.x+.001||a.y+a.h<=b.y+.001||b.y+b.h<=a.y+.001,`overlap ${n}:${i}/${j}`);}
 }
}
console.log('Cover art: eight true-field templates, escaping, code content, image precedence/error recovery, deterministic features and 1000 mixed-span non-overlap passed');

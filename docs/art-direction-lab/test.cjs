const assert=require('node:assert/strict');const {JSDOM}=require('jsdom');const lab=require('./lab.js');
const r={id:'actual-id',title:'Name <script>unsafe</script>',url:'https://github.com/test/repo',kind:'website',category:'开发工具',language:'Swift',tags:['SQLite','<b>']};
const masters=['shiji','vscode','godot','react','olla','motion','polyhaven','hugging','pytorch','article','code','prompt'];
for(const master of masters){const item={master,group:'Test',resource:{...r,kind:master==='code'?'code':master==='prompt'?'prompt':'website',snippet:'  const x = "<tag>";\n    return x;'}};
 const markup=lab.art(item);assert.equal(markup,lab.art(item));const doc=new JSDOM(markup).window.document;
 assert.equal(doc.querySelectorAll('script,b>script').length,0);assert.equal(doc.querySelector('.art').dataset.resourceId,r.id);assert.ok(doc.querySelector('h2').textContent.replace(/\s/g,'').includes('Name<script>unsafe</script>'));
 if(master==='code')assert.deepEqual([...doc.querySelectorAll('pre code')].map(e=>e.textContent),item.resource.snippet.split('\n'));
 if(master==='prompt')assert.equal(doc.querySelector('.prompt-page p').textContent,item.resource.snippet);
 if(master==='polyhaven')assert.equal(doc.querySelector('img').getAttribute('src'),'/polyhaven.jpg');
}
for(const master of ['shiji','godot','hugging']){const item={master,group:'Test',resource:r};const doc=new JSDOM(lab.art(item,'board')+lab.art(item,'compare')).window.document;const ids=[...doc.querySelectorAll('[id]')].map(e=>e.id);assert.equal(new Set(ids).size,ids.length);}
assert.throws(()=>lab.art({master:'unknown',resource:r}));assert.equal(lab.domain({url:'invalid',kind:'prompt'}),'本地 Prompt');
console.log('12 masters + HTML escaping, actual code/Prompt, real image, stable IDs and unique SVG paint servers: passed');
(async()=>{
 const fs=require('node:fs');const url=process.argv[2];if(!url)return;
 const items=await(await fetch(url+'lab-data')).json();const dom=new JSDOM(fs.readFileSync(__dirname+'/index.html','utf8'),{runScripts:'outside-only',url});const w=dom.window;
 let preferenceChange;const preference={matches:false,addEventListener:(_,fn)=>preferenceChange=fn};w.matchMedia=()=>preference;
 let hidden=false;Object.defineProperty(w.document,'hidden',{get:()=>hidden});
 let next=1,frames=new Map();w.requestAnimationFrame=fn=>{const id=next++;frames.set(id,fn);return id};w.cancelAnimationFrame=id=>frames.delete(id);
 w.fetch=async path=>({ok:true,json:async()=>items,text:async()=>fs.readFileSync(__dirname+(path==='/compare2.css'?'/../../desktop-app/static/shiji-v2.css':'/../cover-studio-2/qa/baseline.css'),'utf8')});
 w.ShijiV2=require('../../desktop-app/static/shiji-v2.js');w.ShijiBaseline=require('../cover-studio-2/qa/baseline.js');w.eval(fs.readFileSync(__dirname+'/lab.js','utf8'));
 for(let i=0;i<10&&!w.document.querySelector('#board .art');i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(w.document.querySelectorAll('#board>article').length,12);assert.equal(w.document.querySelectorAll('#pairs>article').length,12);
 const ids=[...w.document.querySelectorAll('[id]')].map(e=>e.id);assert.equal(new Set(ids).size,ids.length);
 const button=w.document.querySelector('#spatial');button.click();assert.equal(button.getAttribute('aria-pressed'),'true');
 const art=w.document.querySelector('.art');art.getBoundingClientRect=()=>({left:0,top:0,width:400,height:300});
 for(let i=0;i<40;i++)art.dispatchEvent(new w.MouseEvent('pointermove',{bubbles:true,clientX:100+i,clientY:140}));assert.equal(frames.size,1,'coalesce pointer samples');
 const [id,fn]=[...frames.entries()][0];frames.delete(id);fn();assert.ok(Number.isFinite(Number(art.style.getPropertyValue('--px'))));
 hidden=true;w.document.dispatchEvent(new w.Event('visibilitychange'));assert.equal(w.document.body.classList.contains('spatial'),false);assert.equal(frames.size,0);assert.equal(art.style.getPropertyValue('--px'),'');
 hidden=false;w.document.dispatchEvent(new w.Event('visibilitychange'));preference.matches=true;preferenceChange();assert.equal(button.disabled,true);assert.equal(button.getAttribute('aria-pressed'),'false');assert.equal(w.document.body.classList.contains('spatial'),false);
 w.document.querySelector('[data-view="compare"]').click();assert.equal(w.document.querySelector('#board').hidden,true);assert.equal(w.document.querySelector('#compare').hidden,false);
 console.log('Actual persisted 12-resource DOM, comparison controls, SVG identity, coalesced pointer, background cleanup and system reduced-motion precedence: passed');w.close();
})().catch(e=>{console.error(e);process.exitCode=1;});

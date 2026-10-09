'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {JSDOM}=require('jsdom'),ui=require('../static/shiji-v2'),board=require('../static/board-model');
const base={id:'kept-id',kind:'website',title:'A <project> & "name"',url:'https://github.com/owner/repo',category:'其他',tags:[],attachments:[],description:'Real description',language:'Swift'};
const before=JSON.stringify(base),dom=new JSDOM('<main></main>'),doc=dom.window.document;
function cover(r){const node=doc.createElement('div');node.innerHTML=ui.coverMarkup(r);return node;}
assert.equal(ui.coverKind(base),'tool');assert.equal(cover(base).querySelector('.cover-title').textContent,base.title);
assert.ok(cover(base).textContent.includes('owner / repo'));assert.ok(cover(base).textContent.includes('Swift'));assert.equal(JSON.stringify(base),before);
assert.equal(ui.coverKind({...base,url:'https://github.com.evil.test/owner/repo'}),'editorial');
const code={...base,kind:'code',language:'JavaScript',snippet:'const safe = "<img onerror=alert(1)>";\n  return safe;\n'};
const codeNode=cover(code);assert.equal(codeNode.querySelector('.cover-code-line').textContent,code.snippet.split('\n')[0]);assert.equal(codeNode.querySelectorAll('.cover-code-line')[1].textContent,'  return safe;');assert.equal(codeNode.querySelector('img'),null);assert.ok(codeNode.textContent.includes('3 行'));
assert.equal(cover({...code,snippet:Array(50).fill('line').join('\n')}).querySelectorAll('.cover-code-line').length,9);
const prompt=cover({...base,kind:'prompt',snippet:'Actual prompt',notes:'Other note'});assert.equal(prompt.querySelector('.cover-excerpt').textContent,'Actual prompt');assert.ok(prompt.querySelector('.cover-prompt'));
assert.equal(cover({...base,kind:'prompt',snippet:'',notes:'Actual note',description:''}).querySelector('.cover-excerpt').textContent,'Actual note');
assert.ok(cover({...base,kind:'file',url:'',attachments:[{name:'real.png'}]}).textContent.includes('real.png'));
assert.equal(cover({...base,language:'',description:'',url:'https://example.com/'}).querySelector('.cover-excerpt'),null);
for(const r of [base,code,{...base,title:'长'.repeat(200)}]){const el=cover(r);assert.equal(el.querySelector('[data-action]'),null);assert.equal(el.querySelector('.resource-cover').getAttribute('aria-hidden'),'true');assert.equal(el.querySelector('script'),null);}
const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const codePreview=app.slice(app.indexOf('function mark(r)'),app.indexOf('function card(r)'));
const preview=vm.runInNewContext(codePreview+'\npreview',{ShijiV2:ui,ShijiBoard:board,esc:s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))});
const displayed=doc.createElement('div');displayed.innerHTML=preview({...base,coverId:'real-cover'});
assert.equal(displayed.querySelector('.cover-image').getAttribute('src'),'/api/files/real-cover');assert.ok(displayed.querySelector('.cover-image').nextElementSibling.matches('.resource-cover'),'real image retains a safe failure fallback');
assert.equal(displayed.querySelector('.cover-title').textContent,base.title);
const index=fs.readFileSync(path.join(__dirname,'../static/index.html'),'utf8');assert.ok(index.includes('href="shiji-v21.css"'));
dom.window.close();console.log('PASS: derived real-field covers, exact code whitespace, bounded previews, escaping, no mutation, image precedence/failure fallback and retained IDs.');

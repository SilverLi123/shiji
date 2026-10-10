'use strict';
// Records arrive from a real ephemeral HTTP/SQLite library, never Demo seeds.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{JSDOM}=require('jsdom');
const V5=require('../static/shiji-v5'),V2=require('../static/shiji-v2'),Board=require('../static/board-model'),Cards=require('../static/stable-cards'),Library=require('../static/library');
const {resources,id,attachmentId}=JSON.parse(fs.readFileSync(0,'utf8')),row=resources.find(r=>r.id===id),before=JSON.stringify(resources);
assert.ok(Library.matches(row,{search:'V3 精确',tags:['New, exact'],favorite:true}));
const code=fs.readFileSync(require.resolve('../static/app.js'),'utf8'),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const preview=vm.runInNewContext(code.slice(code.indexOf('function preview(r)'),code.indexOf('function card(r)'))+'\npreview',{ShijiV5:V5,ShijiV2:V2,ShijiBoard:Board,esc});
const dom=new JSDOM('<div id="space-showcase"><div id="scene-stack"></div></div>',{url:'http://localhost'}),d=dom.window.document;
const deck=V5.create({document:d,preview,reconcile:Cards.render});deck.render({resources});
assert.ok([...d.querySelectorAll('.space-pane')].some(el=>el.dataset.id===id));
assert.equal(d.querySelector('img.cover-image').getAttribute('src'),'/api/files/'+attachmentId);
const old=d.querySelector('.space-pane');deck.render({resources});assert.equal(d.querySelector('.space-pane'),old);
const poster=d.createElement('div');poster.innerHTML=V5.coverMarkup(row);assert.equal(poster.querySelector('.art-copy').textContent,row.title);assert.ok(poster.querySelector('.art-terminal').textContent.includes('Swift'));
const prompt=resources.find(r=>r.kind==='prompt');poster.innerHTML=V5.coverMarkup(prompt);assert.ok(poster.textContent.includes('Exact <prompt>'));assert.equal(poster.querySelector('prompt,script'),null);
// Actual preview fallback is the generated V5 poster behind the hidden image.
assert.ok(d.querySelector('.cover-image + .art-v3'));
deck.render({resources:[]});assert.equal(d.querySelectorAll('.space-pane').length,0);assert.ok(d.querySelector('#space-showcase').hidden);
assert.equal(JSON.stringify(resources),before);deck.destroy();dom.window.close();
console.log('PASS: persisted HTTP fields -> V5 real image priority, poster fallback, exact text, stable IDs, search and empty deck');

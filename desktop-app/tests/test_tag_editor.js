'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{JSDOM}=require('jsdom');
const tags=require('../static/tag-editor'),model=require('../static/edit-model');
const dom=new JSDOM('<div id="editor"><ul id="tag-editor-list"></ul><input id="f-tags"></div>'),doc=dom.window.document,input=doc.querySelector('input');let values=[],error='';
const editor=tags.create(doc.querySelector('#editor'),input,v=>values=v,v=>error=v);
editor.set(['New, exact','已有，标签']);assert.deepEqual(values,['New, exact','已有，标签']);assert.equal(doc.querySelectorAll('li').length,2);
input.value='One, more';input.dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));assert.deepEqual(editor.read(),['New, exact','已有，标签','One, more']);assert.equal(input.value,'');
input.value='New, exact';editor.commit();assert.equal(editor.read().length,3);
input.value='X'.repeat(51);assert.equal(editor.commit(),false);assert.match(error,/50/);assert.equal(editor.read().length,3);input.value='';
const remove=doc.querySelector('button');assert.match(remove.getAttribute('aria-label'),/New, exact/);remove.click();assert.deepEqual(editor.read(),['已有，标签','One, more']);
editor.set(Array.from({length:30},(_,i)=>'tag'+i));input.value='31st';assert.equal(editor.commit(),false);assert.match(error,/30/);
editor.set(['😀'.repeat(50)]);assert.equal(editor.read()[0].length,100);input.value='Draft, exact';assert.equal(editor.commit(),true);
const resource={tags:['New, exact'],projectNotes:{}},initial={tags:['New, exact'],projectNotes:{}},draft={tags:['New, exact','Another, exact'],projectNotes:{}};
assert.deepEqual(JSON.parse(JSON.stringify(model.diff(draft,initial,resource))),{changes:{tags:['New, exact','Another, exact']},expected:{tags:['New, exact']}});
const state={formBase:{},formProjects:{},formTags:['New, exact']};for(const key of model.fields){if(['tags','favicon'].includes(key))continue;const el=doc.createElement('input');el.id='f-'+key;doc.body.append(el);}
assert.deepEqual(model.read(doc,state,()=>[]).tags,['New, exact']);dom.window.close();console.log('Exact tag arrays, literal commas, Enter, remove, duplicates, limits and guarded delta passed.');

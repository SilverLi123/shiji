const assert=require('node:assert/strict');
const {images,queue}=require('../static/gallery-model.js');
const first={id:'first',title:'Buttons',thumbnail:'https://example.com/preview.jpg',attachments:[
  {id:'f1',name:'button.png',mime:'image/png',size:100,author:'Designer',license:'需署名',sourceUrl:'https://example.com/source',licenseUrl:'https://example.com/license'},
  {id:'sound',name:'tap.wav',mime:'audio/wav'},
  {id:'f2',name:'layout.jpg',mime:'image/jpeg'}
]};
const second={id:'second',title:'Motion',attachments:[{id:'f3',name:'motion.gif',mime:'image/gif'}]};
const empty={id:'empty',title:'Code',attachments:[]};
const original=JSON.stringify([first,second,empty]);
// The caller has already applied search/project/tags/sort. Never widen that result.
assert.deepEqual(queue([second,first,empty]).items.map(i=>i.key),['f3','f1','f2']);
assert.deepEqual(queue([second]).items.map(i=>i.key),['f3']);
assert.equal(queue([second,first],first,'f2').index,2);
// Detail reached through a health issue or related resource stays within that owner.
assert.deepEqual(queue([second],first,'f2').items.map(i=>i.key),['f1','f2']);
assert.equal(queue([second],first,'f2').index,1);
// All image attachments remain in the sequence, even identical copies with different provenance.
assert.equal(images(first).length,2);assert.equal(images(first)[0].author,'Designer');
assert.equal(images(first)[0].licenseUrl,'https://example.com/license');
assert.equal(images(first)[0].download,'/api/files/f1?download=1');
const web={id:'web',title:'Reference',thumbnail:'https://example.com/preview.jpg',url:'https://example.com/',license:'待确认'};
assert.equal(images(web)[0].sourceUrl,web.url);assert.equal(images(web)[0].download,'');
assert.equal(images({...web,thumbnail:''}).length,0);assert.equal(queue([empty]).items.length,0);
const trash={...first,id:'trash',deleted:true};
assert(queue([trash]).items.every(i=>i.resourceId==='trash'&&i.inTrash));
assert(queue([first,second]).items.every(i=>!i.inTrash));
assert.equal(JSON.stringify([first,second,empty]),original);
console.log('PASS: filtered/sorted gallery snapshots, owner fallback, image/provenance retention, thumbnail boundaries, trash isolation and no data mutation.');

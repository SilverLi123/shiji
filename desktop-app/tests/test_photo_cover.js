'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const {JSDOM}=require('jsdom'),ShijiV2=require('../static/shiji-v2'),ShijiBoard=require('../static/board-model');
const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const preview=vm.runInNewContext(app.slice(app.indexOf('function preview(r)'),app.indexOf('function card(r)'))+'\npreview',{ShijiV2,ShijiBoard,esc});
const attach=vm.runInNewContext(app.slice(app.indexOf('function attachImageFallbacks(root)'),app.indexOf('const resourceBits='))+'\nattachImageFallbacks');
const dom=new JSDOM('<div id="card"></div><div id="detail"></div>'),d=dom.window.document;
const row={id:'actual-kept-id',kind:'website',title:'Poly Haven',url:'https://polyhaven.com/',category:'3D',tags:[],attachments:[]};
const before=JSON.stringify(row),card=d.querySelector('#card');card.innerHTML=preview(row);
assert.ok(card.querySelector('.cover-photo'),'the approved photographic print must reach the product card, not only the Lab');
assert.equal(card.querySelector('.cover-photo-image').getAttribute('src'),'previews/polyhaven.jpg');
assert.equal(card.querySelector('.cover-photo-title').textContent,'Poly Haven');
assert.equal(card.querySelector('.cover-photo-category').textContent,'3D');
assert.ok(card.querySelector('.cover-photo-caption').textContent.includes('局部'));
assert.equal(card.querySelector('.cover-photo-domain').textContent,'polyhaven.com');
assert.equal(JSON.stringify(row),before,'display never rewrites saved data');
attach(card);
const image=card.querySelector('.cover-image'),poster=card.querySelector('.cover-photo'),fallback=poster.nextElementSibling;
assert.equal(fallback.hidden,true);
image.dispatchEvent(new dom.window.Event('error'));assert.equal(poster.hidden,true);assert.equal(fallback.hidden,false);
image.dispatchEvent(new dom.window.Event('load'));assert.equal(poster.hidden,false);assert.equal(fallback.hidden,true);
// User images and arbitrary website screenshots are never fed through a snapshot-specific crop.
for(const resource of [{...row,coverId:'user-photo'},{...row,thumbnail:'https://example.com/actual.jpg'},{...row,url:'https://polyhaven.com/textures'},{...row,url:'https://polyhaven.com.evil.test/'}]){
 const node=d.createElement('div');node.innerHTML=preview(resource);assert.equal(node.querySelector('.cover-photo'),null);
 if(resource.coverId)assert.equal(node.querySelector('.cover-image').getAttribute('src'),'/api/files/user-photo');
 if(resource.thumbnail)assert.equal(node.querySelector('.cover-image').getAttribute('src'),resource.thumbnail);
}
const edited={...row,title:'建筑 <script>不是代码</script> & 长标题',category:'素材 <3D>'};
const detail=d.querySelector('#detail');detail.innerHTML=preview(edited);
assert.equal(detail.querySelector('.cover-photo-title').textContent,edited.title);
assert.equal(detail.querySelector('.cover-photo-category').textContent,edited.category);
assert.equal(detail.querySelector('script,[onerror],[onload]'),null);
// Stable reconciler must preserve a failed nested source rather than retrying on every sort.
const stable=require('../static/stable-cards');
const grid=d.createElement('div');
const item=r=>({id:r.id,html:'<article class="resource-card" data-resource-id="'+r.id+'">'+preview(r)+'</article>'});
stable.render(grid,[item(row)]);attach(grid);
const failed=grid.querySelector('.cover-image');failed.dispatchEvent(new dom.window.Event('error'));
stable.render(grid,[item({...row,title:'手动编辑后的标题'})]);attach(grid);
assert.equal(grid.querySelector('.cover-image'),failed);
assert.equal(grid.querySelector('.cover-photo').hidden,true);assert.equal(grid.querySelector('.cover-art').hidden,false);
dom.window.close();console.log('PASS: approved photographic cover in real product preview, true fields, user-image precedence, error/reload fallback, stable identity and escaping');

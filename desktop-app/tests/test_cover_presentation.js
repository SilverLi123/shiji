const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),Board=require('../static/board-model'),Cards=require('../static/stable-cards');
const r={id:'real',kind:'website',url:'https://example.test',coverId:'chosen',thumbnail:'https://example.test/real.png',attachments:[]};
assert.equal(Board.cover({...r,coverConfig:{imageSource:'poster'}}),'');
assert.equal(Board.cover({...r,coverConfig:{imageSource:'website'}}),'https://example.test/real.png');
assert.equal(Board.cover({...r,coverConfig:{imageSource:'image'}}),'/api/files/chosen');
assert.equal(Board.cover({...r,coverId:'',coverConfig:{imageSource:'image'}}),'');
assert.equal(Board.galleryResource({...r,thumbnail:'',coverConfig:{imageSource:'poster'}}).thumbnail,'','poster preference does not invent an attachment');
const d=new JSDOM('<div id="grid"></div>').window.document,grid=d.querySelector('div');
Cards.render(grid,['a','b','c'].map(id=>({id,html:`<article class="resource-card" data-resource-id="${id}"><button data-action="detail" data-id="${id}">${id}</button></article>`})));
const before=[...grid.children],focused=before[1].querySelector('button');focused.focus();
Cards.update(grid,{id:'b',html:'<article class="resource-card" data-resource-id="b"><button data-action="detail" data-id="b">updated</button></article>'});
assert.deepEqual([...grid.children],before);assert.equal(d.activeElement,focused);assert.equal(focused.textContent,'updated');assert.equal(before[0].textContent,'a');assert.equal(before[2].textContent,'c');
assert.equal(Cards.update(grid,{id:'absent',html:'<article></article>'}),false,'offscreen resources are not injected into current query');
console.log('PASS: real image source authority, poster fallback and focused single-card patch without sibling churn');

const box=d.createElement('div');Cards.render(box,[{id:'image',html:'<article class=resource-card data-resource-id=image><img class=cover-image src=/same style="object-position:50% 25%"></article>'}]);const image=box.querySelector('img');Cards.update(box,{id:'image',html:'<article class=resource-card data-resource-id=image><img class=cover-image src=/same style="object-position:12% 80%;object-fit:contain"></article>'});assert.equal(box.querySelector('img'),image);assert.equal(image.style.objectPosition,'12% 80%');assert.equal(image.style.objectFit,'contain');

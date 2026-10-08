const assert=require('node:assert/strict');
const {pack,magnetPoint,columns}=require('../static/resource-bits');
const p=pack([350,160,240,190,200],622,2,18);
assert.equal(p.items[0].w,302);assert.deepEqual(p.items.map(({x,y})=>[x,y]),[[0,0],[320,0],[320,178],[0,368],[320,436]]);assert.equal(p.height,636);
for(let i=0;i<p.items.length;i++)for(let j=i+1;j<p.items.length;j++){const a=p.items[i],b=p.items[j];assert.ok(a.x+a.w<=b.x||b.x+b.w<=a.x||a.y+a.h<=b.y||b.y+b.h<=a.y,'cards cannot overlap');}
assert.equal(pack([],600,3).height,0);assert.equal(pack([50],300,1).height,50);
assert.deepEqual([390,665,1000,1280].map(columns),[1,2,3,3]);
const rect={left:100,top:10,width:120,height:40};assert.deepEqual(magnetPoint(160,30,rect),{x:0,y:0});assert.deepEqual(magnetPoint(800,100,rect),{x:0,y:0});assert.equal(magnetPoint(235,30,rect).x,8);assert.equal(magnetPoint(220,30,rect).x,60/9);
console.log('resource bits geometry, ordering, non-overlap and bounded pointer feedback passed');
const saved=new Map(),events=new Map(),queries=new Map();let animateCalls=0,cancelCalls=0,disconnected=false;
for(const k of ['matchMedia','innerWidth','addEventListener','removeEventListener','ResizeObserver','requestAnimationFrame','cancelAnimationFrame'])saved.set(k,global[k]);
try{
 global.innerWidth=665;
 global.matchMedia=q=>{if(!queries.has(q))queries.set(q,{matches:true,addEventListener(_,fn){this.handler=fn;},removeEventListener(){this.handler=null;}});return queries.get(q);};
 global.addEventListener=(name,fn)=>events.set(name,fn);global.removeEventListener=name=>events.delete(name);
 global.ResizeObserver=class{observe(){}disconnect(){disconnected=true;}};global.requestAnimationFrame=()=>1;global.cancelAnimationFrame=()=>{};
 const makeCard=id=>({dataset:{resourceId:id},style:{},offsetHeight:120,getBoundingClientRect:()=>({left:0,top:0}),animate(){animateCalls++;return {finished:new Promise(()=>{}),cancel(){cancelCalls++;}};}});
 const cards=[makeCard('one')],classes=new Set();
 const grid={hidden:false,clientWidth:622,style:{},children:cards,classList:{contains:c=>classes.has(c),toggle(c,on){on?classes.add(c):classes.delete(c);}},querySelectorAll:()=>cards,addEventListener(){},removeEventListener(){}};
 const button={style:{},disabled:false,matches:()=>false,getBoundingClientRect:()=>rect,addEventListener(){},removeEventListener(){}};
 const ui=require('../static/resource-bits').create(grid,button);ui.begin();ui.render();
 assert.equal(animateCalls,0,'reduced motion does not animate');assert.equal(grid.style.height,'120px');
 events.get('pointermove')({clientX:220,clientY:30,pointerType:'mouse'});assert.equal(button.style.transform,'');
 const reduced=queries.get('(prefers-reduced-motion: reduce)');reduced.matches=false;reduced.handler();
 events.get('pointermove')({clientX:220,clientY:30,pointerType:'touch'});assert.equal(button.style.transform,'');
 events.get('pointermove')({clientX:220,clientY:30,pointerType:'mouse'});assert.ok(button.style.transform.startsWith('translate3d'));
 cards.push(makeCard('two'));ui.begin();ui.render();assert.equal(animateCalls,1,'only newly visible card enters');
 reduced.matches=true;reduced.handler();assert.equal(cancelCalls,1,'preference change cancels active animation');
 classes.add('list-layout');ui.begin();ui.render();assert.equal(grid.style.height,'');assert.ok(!classes.has('bits-masonry'));
 classes.delete('list-layout');grid.dataset={galleryColumns:'2'};global.innerWidth=1280;ui.render();assert.equal(cards[0].style.width,'300px','Recent gallery explicitly keeps two large columns');
 ui.destroy();assert.ok(disconnected);assert.equal(events.size,0);assert.equal(reduced.handler,null);
}finally{for(const [k,v] of saved){if(v===undefined)delete global[k];else global[k]=v;}}
console.log('reduced motion, touch fallback, new-card reveal and lifecycle cleanup passed');
// Execute the app's real detail renderer: gallery-only framing must not leak into it.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const app=fs.readFileSync(path.join(__dirname,'../static/app.js'),'utf8');
const detailCode=app.slice(app.indexOf('function detail(r)'),app.indexOf('\nfunction manage(',app.indexOf('function detail(r)')));
const nodes=new Map(),resource={id:'detail-test',title:'Example',kind:'website',url:'https://example.com/',createdAt:'2026-01-01',category:'灵感',linkStatus:'unchecked',price:'待确认',license:'待确认',attachments:[],projects:[],tags:[],projectNotes:{}};
const context={state:{resources:[resource]},$:s=>{if(!nodes.has(s))nodes.set(s,{querySelectorAll:()=>[],focus(){}});return nodes.get(s);},pausePreviewPlayers(){},quickNoteMayLeave(){return true;},quickNoteSection(){return "";},closeMenu(){},date:()=>'',find:()=>null,visual:()=>['image','#eee','#000'],preview:()=>'<img alt="Example">',esc:v=>String(v??''),icon:()=>'',domain:url=>{try{return new URL(url).hostname;}catch{return '';}},KINDS:{website:'网站'},LINK_STATUS:{unchecked:'未检查'},attachImageFallbacks(){},openDrawer(){}};
vm.runInNewContext(detailCode+'\ndetail(resource);',{...context,resource});
assert.ok(nodes.get('#detail-content').innerHTML.includes('https://example.com/'));assert.ok(nodes.get('#detail-content').innerHTML.includes('待确认'));assert.equal(context.state.detail,'detail-test');
console.log('real detail renderer retains source and metadata independently of masonry framing');

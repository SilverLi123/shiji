'use strict';
const assert=require('node:assert/strict'),Q=require('../static/resource-query');
const wait=()=>new Promise(r=>setImmediate(r));
(async()=>{
 let pending=[],applied=[],busy=[];
 const c=Q.create({request:(body,signal)=>new Promise(resolve=>pending.push({body,signal,resolve})),apply:(value,body,append)=>applied.push({value,body,append}),busy:v=>busy.push(v)});
 const first=c.load({filters:{search:'old'}});await wait();const second=c.load({filters:{search:'new'}});await wait();
 assert.equal(pending[0].signal.aborted,true);pending[1].resolve({resources:[{id:'new'}]});await second;pending[0].resolve({resources:[{id:'old'}]});await first;
 assert.equal(applied.length,1);assert.equal(applied[0].value.resources[0].id,'new');assert.equal(busy.at(-1),false);
 const a=c.load({filters:{search:'cancelled'}},{delay:20});const b=c.load({filters:{search:'latest'}},{delay:20});await a;await new Promise(r=>setTimeout(r,30));pending.at(-1).resolve({resources:[]});await b;assert.equal(applied.length,2);
 const dom=new (require('jsdom').JSDOM)('<p id="text">🙂动效 &lt;script&gt;React&lt;/script&gt;</p>');const p=dom.window.document.querySelector('p');Q.mark(p,[[1,3],[12,17]]);assert.equal(p.querySelectorAll('mark').length,2);assert.equal(p.querySelector('script'),null);assert.equal(p.textContent,'🙂动效 <script>React</script>');
 const storage={value:'',getItem(){return this.value},setItem(k,v){this.value=v}};Q.remember(storage,'中文');Q.remember(storage,'React');Q.remember(storage,'中文');assert.deepEqual(Q.recent(storage),['中文','React']);
 c.destroy();dom.window.close();console.log('PASS: latest-only queries, cancellation, debounce, safe Unicode highlights and local history');
})().catch(e=>{console.error(e);process.exitCode=1});

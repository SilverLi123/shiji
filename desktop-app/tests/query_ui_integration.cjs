/* Actual page scripts + actual temporary HTTP API. Geometry is stubbed: no FPS claim. */
const assert=require('node:assert/strict'),{JSDOM,VirtualConsole}=require('jsdom');
const base=process.argv[2],errors=[],requests=[];let diagnostic=()=>'',firstLibrary=true,releaseCapability=null,heartbeat=null,capabilityHeld=false;
const wait=async fn=>{const end=Date.now()+6000;while(!fn()){if(Date.now()>end)throw new Error('DOM condition timed out; '+errors.join('\n')+' '+diagnostic());await new Promise(r=>setTimeout(r,10));}};
(async()=>{
 const console=new VirtualConsole();console.on('jsdomError',e=>{if(e.type!=='css-parsing'&&!e.message.includes('Could not parse CSS'))errors.push(e.message)});
 const dom=await JSDOM.fromURL(base,{resources:'usable',runScripts:'dangerously',pretendToBeVisual:true,virtualConsole:console,beforeParse(w){
  w.AbortController=AbortController;w.AbortSignal=AbortSignal;
  const interval=w.setInterval.bind(w);w.setInterval=(fn,ms,...args)=>{if(ms===3000)heartbeat=()=>fn(...args);return interval(fn,ms,...args)};
  w.fetch=async(p,options)=>{requests.push({path:p,body:options?.body});if(p==='/api/library'&&firstLibrary&&process.argv[3]==='slow'){firstLibrary=false;capabilityHeld=true;await new Promise(resolve=>{releaseCapability=resolve});if(w.closed)throw new DOMException('Test window closed','AbortError');}return fetch(new URL(p,base),options)};
  w.matchMedia=()=>({matches:true,addEventListener(){},removeEventListener(){}});w.ResizeObserver=class{observe(){}disconnect(){}};w.IntersectionObserver=class{observe(){}unobserve(){}disconnect(){}};
  w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.HTMLMediaElement.prototype.pause=function(){};w.HTMLMediaElement.prototype.load=function(){};
  w.HTMLDialogElement.prototype.showModal=function(){this.open=true};w.HTMLDialogElement.prototype.close=function(){this.open=false;this.dispatchEvent(new w.Event('close'))};w.CSS={escape:v=>v};w.TextEncoder=TextEncoder;w.structuredClone=structuredClone;
 }});
 try{
 const w=dom.window,d=w.document,$=s=>d.querySelector(s),click=selector=>$(selector).click();diagnostic=()=>d.querySelector('#empty-state').textContent+' '+d.querySelector('#toast').textContent+' '+JSON.stringify(requests);
 // JSDOM.fromURL returns before external scripts execute. Asset delivery and
 // deliberate capability blocking are separate lifecycle phases, not one clock.
 if(d.readyState==='loading')await new Promise(resolve=>d.addEventListener('DOMContentLoaded',resolve,{once:true}));
 if(process.argv[3]==='slow'){
  await wait(()=>capabilityHeld&&heartbeat);
  await heartbeat(); // Execute the actual desktop refresh while capability is held.
  assert.equal(requests.some(r=>r.path==='/api/resources'||r.path==='/api/trash'),false,'A refresh before capability release must not load the full library');
  releaseCapability();
 }
 await wait(()=>$('#result-count')?.textContent.includes('130'));
 assert.equal(d.querySelectorAll('#resource-grid .resource-card').length,60);
 assert.equal(requests.some(r=>r.path==='/api/resources'||r.path==='/api/trash'),false,'Startup must not load full library');
 click('#browse-more-button');await wait(()=>d.querySelectorAll('#resource-grid .resource-card').length===120);
 const search=$('#search');search.value='missing-query-zzzx';search.dispatchEvent(new w.Event('input',{bubbles:true}));await wait(()=>$('#result-count').textContent.includes('匹配 0 条'));
 assert.equal($('#empty-state h2').textContent,'没有匹配的资源','An empty result page is not an empty library');assert.ok($('#empty-state').textContent.includes('清除筛选'));
 search.value='needle';search.dispatchEvent(new w.Event('input',{bubbles:true}));await wait(()=>$('#result-count').textContent.includes('匹配 1 条'));
 assert.equal(d.querySelectorAll('#resource-grid .resource-card').length,1);assert.equal(d.querySelector('#resource-grid mark').textContent,'needle');
 search.focus();search.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Enter',bubbles:true,cancelable:true}));await wait(()=>!$('#drawer').hidden);
 click('#drawer [data-action=close]');await wait(()=>$('#drawer').hidden);
 click('#resource-grid .card-preview');await wait(()=>!$('#drawer').hidden);
 assert.ok($('#detail-content').textContent.includes('END-OF-FULL-CODE'),'Detail hydrates beyond the bounded summary');
 click('#detail-content [data-action="edit"]');await wait(()=>!$('#resource-form').hidden);
 assert.ok($('#f-snippet').value.endsWith('END-OF-FULL-CODE'));
 $('#f-title').value='Changed title';$('#resource-form').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await wait(()=>$('#drawer').hidden);
 const save=requests.filter(r=>r.path.endsWith('/edit')).at(-1);assert.deepEqual(JSON.parse(save.body).changes,{title:'Changed title'},'Editor must not submit truncated notes/code');
 search.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));await wait(()=>$('#result-count').textContent.includes('130'));assert.equal(search.value,'');
 click('#select-mode');const all=$('[data-select-all]');all.checked=true;all.dispatchEvent(new w.Event('change',{bubbles:true}));await wait(()=>$('#bulk-bar').textContent.includes('已选 130 条'));
 click('[data-action="bulk-organized"]');await wait(()=>$('#bulk-bar').textContent.includes('已选 0 条'));
 const batch=requests.find(r=>r.path==='/api/query/batch');assert.equal(JSON.parse(batch.body).body.ids.length,130,'Full-match action must include resources beyond both displayed pages');
 assert.deepEqual(errors,[]);process.stdout.write(JSON.stringify({passed:true,requests:requests.map(r=>({path:r.path})),cards:d.querySelectorAll('#resource-grid .resource-card').length}));
 }finally{dom.window.close();releaseCapability?.();}
})().catch(e=>{console.error(e);process.exitCode=1});

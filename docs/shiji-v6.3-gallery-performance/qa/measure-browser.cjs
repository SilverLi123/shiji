/* Explicitly requested isolated real-browser QA. Never attaches a user browser profile. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'../../..'),{chromium}=require(path.join(root,'desktop-app/node_modules/playwright'));
const [url,out,roundsArg='3',mode='studio',maximum='2000']=process.argv.slice(2);if(!url||!out)throw Error('URL output-prefix [rounds] [studio|calm] [max-loaded]');
const rounds=Number(roundsArg),maxLoaded=Number(maximum),headless=process.env.SHIJI_QA_HEADFUL!=='1';
const executable=process.env.SHIJI_CHROME_PATH||(process.platform==='darwin'?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined);
const raf=page=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
const read=page=>page.locator('#qa-v63-results').textContent().then(JSON.parse);
const percentile=(xs,p)=>xs.length?[...xs].sort((a,b)=>a-b)[Math.min(xs.length-1,Math.floor(xs.length*p))]:null;
async function traceStart(cdp){await cdp.send('Tracing.start',{categories:'devtools.timeline,blink.user_timing,v8',transferMode:'ReturnAsStream'})}
async function traceEnd(cdp,file){const complete=new Promise(resolve=>cdp.once('Tracing.tracingComplete',resolve));await cdp.send('Tracing.end');const {stream}=await complete;const fd=fs.openSync(file,'w');try{for(;;){const r=await cdp.send('IO.read',{handle:stream});fs.writeSync(fd,r.base64Encoded?Buffer.from(r.data,'base64'):r.data);if(r.eof)break}}finally{fs.closeSync(fd);await cdp.send('IO.close',{handle:stream})}}
async function metrics(page,cdp){const usage=await cdp.qaBrowser.send('SystemInfo.getProcessInfo');let physical=[];
 if(process.env.SHIJI_QA_PROCESS_SAMPLER){physical=execFileSync(process.env.SHIJI_QA_PROCESS_SAMPLER,['0',...usage.processInfo.map(p=>String(p.id))],{encoding:'utf8'}).trim().split('\n').filter(Boolean).map(JSON.parse)}
 const m=await cdp.send('Performance.getMetrics');const values=Object.fromEntries(m.metrics.map(v=>[v.name,v.value]));return {...await page.evaluate(()=>({cards:document.querySelectorAll('#resource-grid .resource-card').length,nodes:document.getElementsByTagName('*').length,scrollY,viewport:innerHeight,hidden:document.hidden,focused:document.hasFocus(),gridHeight:document.getElementById('resource-grid').getBoundingClientRect().height,count:document.getElementById('result-count').textContent})),processes:usage.processInfo,physical,layerCount:cdp.qaLayers?.length,heapBytes:values.JSHeapUsedSize,layoutSeconds:values.LayoutDuration,styleSeconds:values.RecalcStyleDuration,scriptSeconds:values.ScriptDuration}}
async function sampling(page,action){await page.getByRole('button',{name:'QA · 开始采样',exact:true}).click();await action();await page.getByRole('button',{name:'QA · 停止采样',exact:true}).click();await raf(page);const q=await read(page),s=q.samples.at(-1);return {durationMs:s.end-s.start,frames:s.frames.length,p50:percentile(s.frames,.5),p95:percentile(s.frames,.95),max:s.frames.length?Math.max(...s.frames):null,scrolls:s.scrolls,hidden:s.hidden,hiddenEnd:s.hiddenEnd,peakCards:s.peakCards}}
(async()=>{
 fs.mkdirSync(path.dirname(out),{recursive:true});const browser=await chromium.launch({headless,executablePath:executable});const file=out+'-'+mode+'.json',prior=process.env.SHIJI_QA_FRESH!=='1'&&fs.existsSync(file)?JSON.parse(fs.readFileSync(file,'utf8')):null;
 const result={url,mode,headless,version:browser.version(),rounds:prior?.rounds.filter(r=>r.completed&&!r.interference).map(r=>({...r,browserVersion:r.browserVersion||prior.version}))||[]},browserCDP=await browser.newBrowserCDPSession();
 try{for(let round=result.rounds.length;round<rounds;round++){
  const context=await browser.newContext({viewport:{width:1280,height:900},deviceScaleFactor:1});const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));await context.route('**/*',route=>{const u=new URL(route.request().url());return u.origin===new URL(url).origin||u.protocol==='data:'?route.continue():route.abort()});
  const cdp=await context.newCDPSession(page);cdp.qaBrowser=browserCDP;await cdp.send('Performance.enable');
  if(process.env.SHIJI_QA_LAYERS==='1'){cdp.on('LayerTree.layerTreeDidChange',e=>cdp.qaLayers=e.layers||[]);await cdp.send('LayerTree.enable');}const recording=process.env.SHIJI_QA_TRACE==='1'&&round===0;if(recording)await traceStart(cdp);
  await page.goto(url,{waitUntil:'domcontentloaded'});await page.waitForFunction(()=>document.getElementById('result-count').textContent.includes('已显示 60 条'),{},{timeout:30000});await raf(page);const initial=await read(page);
  await page.locator('#motion-skip').waitFor({state:'hidden'});
  if(mode==='calm')await page.getByRole('button',{name:'动效模式：Motion Studio，切换为 Calm',exact:true}).click();
  const row={round,browserVersion:browser.version(),url,traced:recording,completed:false,firstRendered:initial.firstRendered,firstPostRaf:initial.firstPostRaf,initial:await metrics(page,cdp),stages:[],searches:[]};result.rounds.push(row);let loaded=60;
  for(const target of [60,300,600,1020,2000].filter(n=>n<=maxLoaded)){
   let unavailable=false;
   const sample=await sampling(page,async()=>{while(loaded<target){const button=page.getByRole('button',{name:/^继续浏览/});if(!await button.isVisible()){unavailable=true;break}await button.click();await page.waitForFunction(previous=>{const text=document.getElementById('result-count').textContent;return Number(text.match(/已显示 (\d+)/)?.[1]||0)>previous},loaded);loaded=await page.locator('#result-count').textContent().then(t=>Number(t.match(/已显示 (\d+)/)[1]));await raf(page)}});
   if(unavailable){row.stages.push({target,unavailable:true,actualLoaded:loaded});break}
   const q=await read(page),stage={target,actualLoaded:loaded,...await metrics(page,cdp),appendFrames:sample,lastRender:q.renders.at(-1)};
   stage.scrollFrames=await sampling(page,async()=>{await page.getByRole('link',{name:'探索我的收藏',exact:true}).click();await raf(page);await page.mouse.move(1000,450);for(let i=0;i<12;i++){await page.mouse.wheel(0,i<6?1000:-1000);await raf(page)}});
   row.stages.push(stage);fs.writeFileSync(out+'-'+mode+'.json',JSON.stringify(result,null,2));console.log(JSON.stringify({phase:'stage',round,mode,target,loaded,cards:stage.cards,render:stage.lastRender?.renderMs,scrollMax:stage.scrollFrames?.max}));if(round===0&&target>=1020)await page.screenshot({path:out+'-'+mode+'-'+target+'.png'});
  }
  for(const query of ['动效 React','','React','']){
   const before=(await read(page)).inputs.length;await page.getByRole('searchbox',{name:'搜索资源',exact:true}).fill(query);
   await page.waitForFunction(index=>{const el=document.getElementById('qa-v63-results');return el&&JSON.parse(el.textContent).inputs[index]?.postRaf!=null},before);const q=await read(page);row.searches.push({query,input:q.inputs[before],request:q.requests.filter(r=>r.path==='/api/query').at(-1),lastRender:q.renders.at(-1),...await metrics(page,cdp)});
  }
  await page.getByRole('button',{name:'UI / 设计',exact:true}).click();await page.waitForFunction(()=>document.getElementById('resource-grid').getAttribute('aria-busy')==='false');await raf(page);row.category={...await metrics(page,cdp),lastRender:(await read(page)).renders.at(-1)};
  const card=page.locator('#resource-grid .card-preview').first();await card.scrollIntoViewIfNeeded();await raf(page);const origin={id:await card.getAttribute('data-id'),box:await card.boundingBox(),scrollY:await page.evaluate(()=>scrollY)};
  row.detailFrames=await sampling(page,async()=>{await card.click();await page.getByRole('button',{name:'关闭详情',exact:true}).waitFor({state:'visible'});await page.locator('.shiji-detail-ghost').waitFor({state:'detached'});await page.getByRole('button',{name:'关闭详情',exact:true}).click();await raf(page)});row.detailReturn={origin,afterScrollY:await page.evaluate(()=>scrollY),ghosts:await page.locator('.shiji-detail-ghost').count()};
  const q=await read(page);row.peakCards=q.peakCards;row.longTasks=q.longTasks;row.raw=q;row.errors=errors;assert.deepEqual(errors,[]);
  if(recording)await traceEnd(cdp,out+'-'+mode+'.trace.json');row.completed=true;fs.writeFileSync(out+'-'+mode+'.json',JSON.stringify(result,null,2));console.log(JSON.stringify({round,mode,stages:row.stages.map(s=>({target:s.target,loaded:s.actualLoaded,cards:s.cards,render:s.lastRender?.renderMs,scroll:s.scrollFrames})),searches:row.searches.map(s=>({query:s.query,ms:s.input.inputToPostRafMs,render:s.lastRender.renderMs})),errors}));await context.close();
 }}finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

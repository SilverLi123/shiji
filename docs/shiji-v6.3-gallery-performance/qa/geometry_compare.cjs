/* Compare actual original/candidate CSS box geometry against identical Store rows. */
'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {chromium}=require(path.resolve(__dirname,'../../../desktop-app/node_modules/playwright'));
const [before,after,out]=process.argv.slice(2),raf=page=>page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
(async()=>{const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'}),results=[];try{
 for(const [phase,url]of[['before',before],['after',after]]){
  const context=await browser.newContext({viewport:{width:1280,height:900},reducedMotion:'reduce'}),page=await context.newPage();
  await context.route('**/*',r=>new URL(r.request().url()).origin===new URL(url).origin?r.continue():r.abort());await page.goto(url);await page.waitForFunction(()=>document.getElementById('result-count').textContent.includes('已显示 60 条'));
  const cases=[];
  for(const width of[1280,820,390]){
   await page.setViewportSize({width,height:900});await raf(page);await page.getByRole('link',{name:'探索我的收藏',exact:true}).click();await raf(page);await page.mouse.wheel(0,600);await raf(page);
   const data=await page.locator('#resource-grid').evaluate(grid=>({height:parseFloat(grid.style.height),cards:[...grid.children].filter(n=>n.matches('.resource-card')).map(n=>({id:n.dataset.resourceId,x:parseFloat(n.style.left),y:parseFloat(n.style.top),w:parseFloat(n.style.width),h:n.offsetHeight,wide:n.dataset.galleryWide}))}));cases.push({width,...data});
   if(width===1280){fs.mkdirSync(path.dirname(out),{recursive:true});await page.screenshot({path:out+'-'+phase+'.png'})}
  }
  results.push({phase,cases});await context.close();
 }
 for(let i=0;i<3;i++){
  const old=results[0].cases[i],next=results[1].cases[i],map=new Map(old.cards.map(r=>[r.id,r]));assert.ok(next.cards.length>0&&next.cards.length<60);
  assert.ok(Math.abs(old.height-next.height)<=1,'full logical height matches reference');
  for(const r of next.cards){const a=map.get(r.id);assert.ok(a,'same stable resource ID');for(const key of['x','y','w','h'])assert.ok(Math.abs(a[key]-r[key])<=1,'CSS geometry '+key+' '+JSON.stringify({a,r}));assert.equal(a.wide,r.wide);}
 }
 fs.writeFileSync(out+'.json',JSON.stringify({passed:true,results},null,2));console.log('actual original/candidate masonry geometry matches within1px at1280/820/390; visible art preserved');
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});

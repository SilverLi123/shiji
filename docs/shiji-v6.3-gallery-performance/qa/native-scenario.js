/* Disposable QA shell only. Automated DOM inputs are explicitly labelled. */
(()=>{
 if(!window.webkit)return;
 let running=false,journal=null;
 const $=s=>document.querySelector(s),raf=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const loaded=()=>Number($('#result-count').textContent.match(/已显示 (\d+)/)?.[1]||0);
 const percentile=(xs,p)=>[...xs].sort((a,b)=>a-b)[Math.min(xs.length-1,Math.floor(xs.length*p))]??null;
 function publish(){window.webkit.messageHandlers.libraryDiagnostics.postMessage({event:'v63-scenario',phase:JSON.stringify(journal)});}
 async function until(condition){const end=performance.now()+120000;while(!condition()){if(document.hidden)throw Error('QA page became hidden; discard foreground timing');if(performance.now()>end)throw Error('QA condition timed out');await new Promise(r=>setTimeout(r,20));}}
 async function measured(name,operation){
  if(document.hidden)throw Error('Not a foreground sample');const qa=window.ShijiV63QA;qa.sample();const start=performance.now();journal.runningStep={name,started:Date.now()};publish();
  try{await operation();await raf();}finally{qa.stop();}
  const data=qa.read(),sample=data.samples.at(-1),frames=sample.frames;
  const result={name,ms:performance.now()-start,loaded:loaded(),cards:document.querySelectorAll('#resource-grid>.resource-card').length,peakCards:sample.peakCards,frames:frames.length,p50:percentile(frames,.5),p95:percentile(frames,.95),max:frames.length?Math.max(...frames):null,scrolls:sample.scrolls,hidden:sample.hidden,hiddenEnd:sample.hiddenEnd};journal.steps.push(result);delete journal.runningStep;publish();if(sample.hidden||sample.hiddenEnd)throw Error('Hidden sample is invalid');return result;
 }
 async function reset(){
  $('[data-action="scope"][data-scope="favorite"]').click();await until(()=>$('#resource-grid').getAttribute('aria-busy')==='false');
  $('[data-action="scope"][data-scope="all"]').click();await until(()=>loaded()===60&&$('#resource-grid').getAttribute('aria-busy')==='false');await raf();
 }
 async function scroll(){
  $('#resource-grid').scrollIntoView({block:'start',behavior:'instant'});await raf();for(let i=0;i<12;i++){window.scrollBy(0,i<6?700:-700);await raf();}
 }
 async function run(){
  if(running)return;if(document.hidden){$('#qa-native-status').textContent='页面被遮挡，不能采样';return;}
  running=true;journal={version:1,input:'QA automated DOM clicks/programmatic scroll; physical coordinate sample is separate',started:Date.now(),viewport:{width:innerWidth,height:innerHeight},steps:[],completed:false};publish();
  try{
   for(const mode of['studio','calm']){
    if(document.documentElement.dataset.shijiMotion!==mode)$('#motion-mode').click();
    if(mode==='studio'&&document.documentElement.dataset.shijiSpace!=='depth')$('#space-mode').click();
    for(let round=0;round<3;round++){
     await reset();journal.mode=mode;journal.round=round;
     for(const target of[60,300,600,1020,2000]){
      const name=mode+'-'+round+'-'+target;
      await measured(name+'-append',async()=>{while(loaded()<target){if($('#browse-more').hidden)break;const old=loaded();$('#browse-more-button').click();await until(()=>loaded()>old&&$('#resource-grid').getAttribute('aria-busy')==='false');await raf();}});
      if(loaded()<target){journal.steps.push({name,unavailable:true,loaded:loaded()});break;}
      await measured(name+'-scroll',scroll);
     }
     const preview=$('#resource-grid .card-preview');if(preview){preview.scrollIntoView({block:'center',behavior:'instant'});await raf();const y=scrollY;
      await measured(mode+'-'+round+'-detail',async()=>{preview.click();await until(()=>!$('#drawer').hidden);await until(()=>!document.querySelector('.shiji-detail-ghost'));$('#drawer [data-action="close"]').click();await raf();});journal.steps.at(-1).returnDelta=scrollY-y;journal.steps.at(-1).ghosts=document.querySelectorAll('.shiji-detail-ghost').length;publish();
     }
    }
    await measured(mode+'-idle30',async()=>{await new Promise(resolve=>setTimeout(resolve,30000));});
   }
   journal.completed=true;
  }catch(e){journal.error=String(e.message||e);}finally{running=false;journal.ended=Date.now();publish();$('#qa-native-status').textContent=journal.completed?'原生对照完成':'原生对照未完成：'+journal.error;}
 }
 document.addEventListener('DOMContentLoaded',()=>{const panel=document.createElement('div');panel.style.cssText='position:fixed;bottom:44px;right:10px;z-index:2000;background:#14151a;color:#c5ff63;font:11px monospace;padding:6px';const button=document.createElement('button');button.textContent='QA · 原生对照运行';button.addEventListener('click',run);const status=document.createElement('span');status.id='qa-native-status';panel.append(button,status);document.body.append(panel);});
})();

/* QA-only passive observation. No synthetic input or second animation system. */
(function(){
 const metrics={userAgent:navigator.userAgent,systemReduce:matchMedia('(prefers-reduced-motion: reduce)').matches,firstInteractive:null,interactions:[],frames:[],visibility:[]};
 const output=document.createElement('script');output.type='application/json';output.id='qa-capture-metrics';document.head.append(output);
 const publish=()=>{output.textContent=JSON.stringify(metrics);};publish();
 window.ShijiCaptureQA=metrics;let pending=null,previous=null,started=performance.now();
 document.addEventListener('input',event=>{if(event.target.id==='search')pending={kind:'search',at:performance.now()};},true);
 document.addEventListener('click',event=>{if(event.target.closest('[data-action="category"],[data-action="scope"][data-scope="category"]'))pending={kind:'category',at:performance.now()};},true);
 document.addEventListener('shiji:rendered',()=>{const item=pending;pending=null;requestAnimationFrame(()=>requestAnimationFrame(()=>{if(metrics.firstInteractive===null)metrics.firstInteractive=performance.now();if(item)metrics.interactions.push({kind:item.kind,ms:performance.now()-item.at});publish();}));});
 document.addEventListener('visibilitychange',()=>{metrics.visibility.push({hidden:document.hidden,at:performance.now()});previous=null;});
 function frame(now){if(!document.hidden&&previous!==null)metrics.frames.push(now-previous);previous=document.hidden?null:now;if(now-started<20000)requestAnimationFrame(frame);else publish();}
 requestAnimationFrame(frame);
})();

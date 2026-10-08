(function(root){
 'use strict';
 function create({load,apply,busy,clock=root,interval=3000}){
  let stopped=false,running=false,last=null,controller=null;
  async function tick(){
   if(stopped||running||busy())return;
   running=true;controller=new AbortController();
   const timeout=clock.setTimeout(()=>controller?.abort(),10000);
   try{const data=await load(controller.signal);if(stopped||busy())return;const fingerprint=JSON.stringify(data);if(last!==fingerprint){await apply(data);if(!stopped)last=fingerprint;}}
   catch(error){if(error.name!=='AbortError'&&root.console)root.console.debug('后台刷新稍后重试');}
   finally{clock.clearTimeout(timeout);running=false;controller=null;}
  }
  const timer=clock.setInterval(tick,interval);
  return {tick,destroy(){stopped=true;clock.clearInterval(timer);controller?.abort();}};
 }
 const api={create};if(typeof module==='object')module.exports=api;else root.ShijiDesktopSync=api;
})(typeof window==='object'?window:globalThis);

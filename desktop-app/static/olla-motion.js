/* Original geometric score inspired by Recent's Olla case study.
 * Native WAAPI; no reference artwork, videos or animation data are bundled. */
(function(root){
  'use strict';
  const duration=7200,easing='cubic-bezier(.65,0,.35,1)';
  function score(){return [
    ['.motion-fold',[{transform:'rotate(0deg) scale(.84)',borderRadius:'50%'},{transform:'rotate(-18deg) scale(1)',borderRadius:'28%',offset:.19},{transform:'rotate(90deg) scale(.78)',borderRadius:'18%',offset:.48},{transform:'rotate(180deg) scale(1)',borderRadius:'34%',offset:.76},{transform:'rotate(360deg) scale(.84)',borderRadius:'50%'}]],
    ['.motion-fold i:first-child',[{transform:'translateX(-12%) rotate(0deg)'},{transform:'translateX(15%) rotate(90deg)',offset:.38},{transform:'translateX(-12%) rotate(360deg)'}]],
    ['.motion-fold i:last-child',[{transform:'translateX(12%) rotate(0deg)'},{transform:'translateX(-15%) rotate(-90deg)',offset:.38},{transform:'translateX(12%) rotate(-360deg)'}]],
    ['.motion-word-track',[{transform:'translateY(0)'},{transform:'translateY(0)',offset:.18},{transform:'translateY(-25%)',offset:.28},{transform:'translateY(-25%)',offset:.47},{transform:'translateY(-50%)',offset:.57},{transform:'translateY(-50%)',offset:.76},{transform:'translateY(-75%)',offset:.87},{transform:'translateY(-75%)'}]],
    ['.motion-slices',[{transform:'rotate(0deg)'},{transform:'rotate(0deg)',offset:.17},{transform:'rotate(180deg)',offset:.44},{transform:'rotate(180deg)',offset:.68},{transform:'rotate(360deg)'}]],
    ...[0,1,2,3].map((i)=>['.motion-slice:nth-child('+(i+1)+')',[{transform:'translateX(0) scaleX(1)'},{transform:`translateX(${(i-1.5)*7}px) scaleX(.65)`,offset:.25},{transform:'translateX(0) scaleX(1)',offset:.48},{transform:`translateX(${(1.5-i)*6}px) scaleX(.78)`,offset:.75},{transform:'translateX(0) scaleX(1)'}]])
  ];}
  function create(stage,{doc=root.document,win=root,storage=root.localStorage}={}){
    if(!stage)return null;
    const reduce=win.matchMedia('(prefers-reduced-motion: reduce)'),button=stage.querySelector('.motion-toggle');
    let paused=false,visible=typeof win.IntersectionObserver!=='function',destroyed=false,animations=[];
    try{paused=storage.getItem('shiji-olla-paused')==='true';}catch{}
    function sync(){
      const allowed=!destroyed&&!reduce.matches&&!paused&&!doc.hidden&&!stage.hidden&&stage.dataset.quiet!=='true'&&visible;
      stage.dataset.motion=reduce.matches?'reduced':allowed?'playing':'paused';
      button.disabled=reduce.matches;
      button.setAttribute('aria-pressed',String(paused||reduce.matches));
      button.setAttribute('aria-label',reduce.matches?'已按系统偏好减少动态效果':paused?'播放视觉动效':'暂停视觉动效');
      button.querySelector('span').textContent=reduce.matches?'静态模式':paused?'播放动效':'暂停动效';
      for(const animation of animations)allowed?animation.play():animation.pause();
    }
    function build(){
      for(const animation of animations)animation.cancel();animations=[];
      if(!reduce.matches&&!destroyed)for(const [selector,frames] of score()){
        const el=stage.querySelector(selector);
        if(el?.animate){const animation=el.animate(frames,{duration,iterations:Infinity,easing});animation.pause();animations.push(animation);}
      }
      sync();
    }
    function toggle(){paused=!paused;try{storage.setItem('shiji-olla-paused',String(paused));}catch{}sync();}
    function preference(){build();}
    function navigation(e){
      if(!e.target.closest?.('[data-action="category"],[data-action="scope"]'))return;
      // Reuse the current score instead of accumulating concurrent timelines.
      for(const animation of animations)animation.currentTime=0;
      sync();
    }
    function context(){
      const title=doc.getElementById('page-title')?.textContent;
      stage.dataset.quiet=String(title==='回收站'||title==='库检查');sync();
    }
    const observer=typeof win.IntersectionObserver==='function'?new win.IntersectionObserver(entries=>{visible=entries.some(e=>e.isIntersecting);sync();},{threshold:0}):null;
    const mutations=typeof win.MutationObserver==='function'?new win.MutationObserver(context):null;
    observer?.observe(stage);const title=doc.getElementById('page-title');if(title)mutations?.observe(title,{childList:true,characterData:true,subtree:true});
    button.addEventListener('click',toggle);doc.addEventListener('visibilitychange',sync);doc.addEventListener('click',navigation);reduce.addEventListener('change',preference);
    build();context();
    return {destroy(){destroyed=true;for(const animation of animations)animation.cancel();animations=[];observer?.disconnect();mutations?.disconnect();button.removeEventListener('click',toggle);doc.removeEventListener('visibilitychange',sync);doc.removeEventListener('click',navigation);reduce.removeEventListener('change',preference);},sync};
  }
  const api={score,create,duration};
  if(typeof module==='object'&&module.exports)module.exports=api;
  else{root.ShijiOlla=api;root.document.addEventListener('DOMContentLoaded',()=>{const ui=create(root.document.getElementById('motion-stage'));root.addEventListener('pagehide',e=>{if(!e.persisted)ui?.destroy();});});}
})(typeof window==='object'?window:globalThis);

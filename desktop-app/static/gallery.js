'use strict';
const galleryState={items:[],index:0,native:false,focus:null,resourceFocus:false,speed:1,loop:false,run:0};
function openGallery(owner,key){
  if(state.remote)return remoteGallery(owner,key).catch(e=>toast(e.message));
  const resources=state.scope==='health'&&owner?[owner]:shownItems();
  const snapshot=ShijiGallery.mediaQueue(resources.map(ShijiBoard.galleryResource),owner?ShijiBoard.galleryResource(owner):owner,key);
  if(!snapshot.items.length){toast('当前结果没有可预览素材，请添加图片、音频、视频或网页缩略图。');return;}
  openGallerySnapshot(snapshot);
}
function openGallerySnapshot(snapshot,fromSimilar=false){
  if(!snapshot.items.length)return;
  Object.assign(galleryState,{remoteCursor:null,remotePrevious:null,remoteQuery:null},snapshot,{native:false,focus:document.activeElement,resourceFocus:false,speed:1,loop:false,fromSimilar});
  pausePreviewPlayers($('#drawer'));renderGallery();$('#image-dialog').showModal();$('#image-close').focus();
}
function pausePreviewPlayers(root){
  root.querySelectorAll('audio,video').forEach(player=>player.pause());
}
function clearPreviewStage(){
  const stage=$('#image-stage');
  stage.querySelectorAll('audio,video').forEach(player=>{player.pause();player.removeAttribute('src');player.load();});
  stage.replaceChildren();
}
function mediaDuration(value){
  if(!Number.isFinite(value)||value<0)return '时长待确认';
  const seconds=Math.floor(value),hours=Math.floor(seconds/3600),minutes=Math.floor(seconds%3600/60);
  return (hours?hours+':'+String(minutes).padStart(2,'0'):String(minutes))+':'+String(seconds%60).padStart(2,'0');
}
function setPlaybackOptions(){
  const player=$('#image-stage').querySelector('audio,video');
  if(player){player.playbackRate=galleryState.speed;player.loop=galleryState.loop;}
  $('#preview-speed').value=String(galleryState.speed);$('#preview-loop').checked=galleryState.loop;
}
function renderGallery(){
  const item=galleryState.items[galleryState.index];if(!item)return;
  const run=++galleryState.run,kind=item.kind||'image',picture=kind==='image';
  galleryState.navigationRun=null;clearPreviewStage();
  $('#image-action-status').textContent='';
  $('#image-similar').disabled=false;$('[data-action="image-resource"]').disabled=false;
  $('#image-title').textContent=item.name;
  $('#image-position').textContent=`${galleryState.index+1} / ${galleryState.items.length}`;
  $('#image-resource').textContent=item.resourceTitle+(item.inTrash?' · 回收站':'');
  $('#image-details').innerHTML=`<span>${esc(item.author||'作者待补充')} · ${esc(item.license)}</span>${item.sourceUrl?`<a href="${esc(item.sourceUrl)}" target="_blank" rel="noopener noreferrer">原始来源</a>`:''}${item.licenseUrl?`<a href="${esc(item.licenseUrl)}" target="_blank" rel="noopener noreferrer">许可说明</a>`:''}`;
  $('#image-download').hidden=!item.download;$('#image-similar').hidden=!picture||!item.download;
  $('.image-size-controls').hidden=!picture;$('#preview-playback').hidden=picture;
  if(item.download)$('#image-download').href=item.download;else $('#image-download').removeAttribute('href');
  $('#image-prev').disabled=galleryState.index===0&&!galleryState.remotePrevious;$('#image-next').disabled=galleryState.index===galleryState.items.length-1&&!galleryState.remoteCursor;
  $('#image-dimensions').textContent=picture?'读取图片中…':'读取媒体信息中…';$('#image-error').hidden=true;
  $('#image-stage').hidden=false;$('#image-stage').classList.toggle('audio-stage',kind==='audio');
  const player=document.createElement(picture?'img':kind);player.id=picture?'large-image':'preview-player';
  const fail=()=>{if(run!==galleryState.run)return;player.hidden=true;if(!picture){player.pause();$('#preview-playback').hidden=true;$('#image-stage').hidden=true;}$('#image-dimensions').textContent='无法预览';$('#image-error').hidden=false;};
  player.addEventListener('error',fail);
  if(picture){
    player.alt=item.name;player.referrerPolicy='no-referrer';
    player.addEventListener('load',()=>{if(run!==galleryState.run)return;$('#image-dimensions').textContent=`${player.naturalWidth} × ${player.naturalHeight} px${item.size?' · '+size(item.size):''}`;});
  }else{
    player.controls=true;player.preload='metadata';player.setAttribute('aria-label',item.name);if(kind==='video')player.playsInline=true;
    player.addEventListener('loadedmetadata',()=>{if(run!==galleryState.run)return;setPlaybackOptions();$('#image-dimensions').textContent=(kind==='video'?`${player.videoWidth} × ${player.videoHeight} px · `:'音频 · ')+mediaDuration(player.duration)+(item.size?' · '+size(item.size):'');});
    player.addEventListener('durationchange',()=>{if(run!==galleryState.run||!Number.isFinite(player.duration))return;$('#image-dimensions').textContent=(kind==='video'?`${player.videoWidth} × ${player.videoHeight} px · `:'音频 · ')+mediaDuration(player.duration)+(item.size?' · '+size(item.size):'');});
    if(kind==='audio'){
      const label=document.createElement('div');label.className='audio-preview-label';label.innerHTML=icon('music')+'<span>音频预览</span><p>点击播放试听，可拖动进度比较不同片段。</p>';$('#image-stage').append(label);
    }
  }
  $('#image-stage').append(player);player.src=item.src;
  setPlaybackOptions();setImageSize(picture&&galleryState.native);
}
function quickPreviewKeys(event){
  if(event.key!==' '||event.repeat||event.metaKey||event.ctrlKey||event.altKey||event.shiftKey||!$('#drawer').hidden||document.querySelector('dialog[open]'))return false;
  const entry=event.target.closest('#resource-grid .card-preview,#resource-grid .card-title');
  if(!entry)return false;const owner=find(entry.closest('[data-resource-id]').dataset.resourceId);
  if(!owner||!ShijiGallery.media(ShijiBoard.galleryResource(owner)).length)return false;
  event.preventDefault();openGallery(owner);return true;
}
function moveGallery(index){
  const next=Math.max(0,Math.min(galleryState.items.length-1,index));
  if(next!==galleryState.index){galleryState.index=next;renderGallery();}
}
function setImageSize(native){
  galleryState.native=Boolean(native&&(!galleryState.items[galleryState.index]?.kind||galleryState.items[galleryState.index].kind==='image'));native=galleryState.native;$('#image-stage').classList.toggle('native-size',native);
  $('#image-fit').setAttribute('aria-pressed',String(!native));$('#image-native').setAttribute('aria-pressed',String(native));
  $('#image-stage').scrollTop=0;$('#image-stage').scrollLeft=0;
}
async function galleryAction(action){
  if(action==='gallery')openGallery();
  else if(action==='image-prev'){if(galleryState.remotePrevious&&galleryState.index===0)await remoteGalleryPrevious();else moveGallery(galleryState.index-1);}
  else if(action==='image-next'){if(galleryState.remoteCursor&&galleryState.index===galleryState.items.length-1)await remoteGalleryMore();else moveGallery(galleryState.index+1);}
  else if(action==='image-fit')setImageSize(false);
  else if(action==='image-native')setImageSize(true);
  else if(action==='image-similar'||action==='image-resource')await galleryNavigate(action);
}
async function galleryNavigate(action){
  const item=galleryState.items[galleryState.index],run=galleryState.run;
  if(!item||galleryState.navigationRun===run)return;
  galleryState.navigationRun=run;
  $('#image-action-status').textContent='正在读取资源…';
  $('#image-similar').disabled=true;$('[data-action="image-resource"]').disabled=true;
  try{
    await reload();
    if(run!==galleryState.run||!$('#image-dialog').open)return;
    const owner=typeof state!=='undefined'&&state.remote?await fullResource(item.resourceId):find(item.resourceId);
    if(!owner||Boolean(owner.deleted)!==Boolean(item.inTrash))throw new Error('资源已移除或移动了范围，请关闭预览并重新查找。');
    if(action==='image-similar'){
      if(!owner.attachments?.some(a=>a.id===item.key&&!a.deleted&&a.mime.startsWith('image/')))throw new Error('图片已移除，请关闭预览并重新选择。');
      $('#image-dialog').close();similarOpen(owner,item.key);
    }else{
      galleryState.resourceFocus=true;$('#image-dialog').close();
      if(galleryState.fromSimilar)$('#manage-dialog').close();detail(owner);
    }
  }catch(e){if(run===galleryState.run&&$('#image-dialog').open)$('#image-action-status').textContent=e.message||'资源读取失败，请重试。';}
  finally{
    if(galleryState.navigationRun===run){galleryState.navigationRun=null;$('#image-similar').disabled=false;$('[data-action="image-resource"]').disabled=false;}
  }
}
function imageKeys(event){
  if(!$('#image-dialog').open)return false;
  if(event.key==='Escape')return true; // Native dialog cancellation closes only this layer.
  if(event.metaKey||event.ctrlKey||event.altKey)return true;
  if(event.target.closest('input,textarea,select,audio,video,[contenteditable]'))return true;
  if(event.key==='ArrowRight'&&galleryState.index===galleryState.items.length-1&&galleryState.remoteCursor){event.preventDefault();void galleryAction('image-next').catch(e=>toast(e.message));return true;}
  if(event.key==='ArrowLeft'&&galleryState.index===0&&galleryState.remotePrevious){event.preventDefault();void galleryAction('image-prev').catch(e=>toast(e.message));return true;}
  if((event.key==='Home'||event.key==='End')&&galleryState.remoteQuery){event.preventDefault();void remoteGalleryEdge(event.key==='End').catch(e=>toast(e.message));return true;}
  const next={ArrowLeft:galleryState.index-1,ArrowRight:galleryState.index+1,Home:0,End:galleryState.items.length-1}[event.key];
  if(next!==undefined){event.preventDefault();moveGallery(next);return true;}
  return false;
}
function initGallery(){
  $('#preview-speed').addEventListener('change',event=>{const value=Number(event.target.value);galleryState.speed=[.5,1,1.5,2].includes(value)?value:1;setPlaybackOptions();});
  $('#preview-loop').addEventListener('change',event=>{galleryState.loop=event.target.checked;setPlaybackOptions();});
  $('#image-dialog').addEventListener('close',()=>{
    galleryState.run++;clearPreviewStage();
    if(galleryState.resourceFocus){galleryState.resourceFocus=false;$('#drawer').focus();}
    else if(galleryState.focus?.isConnected)galleryState.focus.focus();
    else if(!$('#drawer').hidden)$('#drawer').focus();else $('#gallery-open').focus();
  });
}

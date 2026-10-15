'use strict';
importScripts('utils.js','outbox.js','clip-transport.js');
const ALARM='shiji-capture-outbox';
const transport=ShijiClipTransport.create();
async function configuration(){
 const value=await chrome.storage.local.get(['base','token']);
 try{return ShijiClip.settings(value.base||'http://127.0.0.1:8782',value.token||'');}
 catch{throw Object.assign(new Error('请先连接原资源库，待发送内容会保留。'),{blocked:true,halt:true});}
}
const outbox=ShijiOutbox.create({storage:chrome.storage.local,config:configuration,send:transport.send});
async function remember(message,error=false){await chrome.storage.local.set({lastCapture:message});await chrome.action.setBadgeText({text:error?'!':'✓'});await chrome.action.setBadgeBackgroundColor({color:error?'#a23c12':'#176b9a'});}
async function updateQueue(){
 const rows=await outbox.list();
 if(rows.length){await chrome.action.setBadgeText({text:String(rows.length)});await chrome.action.setBadgeBackgroundColor({color:'#8e651d'});}
 if(rows.some(r=>r.state==='pending'||r.state==='sending')){
  if(!await chrome.alarms.get(ALARM))await chrome.alarms.create(ALARM,{periodInMinutes:1});
 }else await chrome.alarms.clear(ALARM);
 return rows;
}
async function flush(){
 try{const result=await outbox.drain();if(result.delivered)await remember(`已发送 ${result.delivered} 条收藏到 App。`);return result;}
 finally{await updateQueue();}
}
async function capture(tab,options={}){
 // Verify a pairing exists before reading a page; offline delivery needs no live App.
 await configuration();
 const [{result:page}]=await chrome.scripting.executeScript({target:{tabId:tab.id},func:()=>{const meta=k=>document.querySelector(`meta[property="${k}"],meta[name="${k}"]`)?.content||'';const absolute=v=>{try{return v?new URL(v,location.href).href:'';}catch{return '';}};return {url:location.href,title:document.title,selection:getSelection().toString(),description:meta('og:description')||meta('description'),thumbnail:absolute(meta('og:image')),favicon:absolute(document.querySelector('link[rel~="icon"]')?.getAttribute('href'))};}});
 if(options.linkUrl){page.url=options.linkUrl;page.title=options.selection||options.linkUrl;page.description='';page.thumbnail='';page.favicon='';}
 const body=ShijiClip.payload(page,options.selection);if(options.imageUrl)body.imageUrl=options.imageUrl;
 if(options.screenshot)body.screenshot=await chrome.tabs.captureVisibleTab(tab.windowId,{format:'png'});
 const entry=await outbox.enqueue(body); // Freeze before the first network operation.
 await updateQueue();
 try{await flush();}catch{/* Durable record remains; the popup can retry receipt reconciliation. */}
 const pending=(await outbox.list()).find(r=>r.id===entry.id);
 const saved=await outbox.confirmed(entry.id);
 const message=saved?'已保存到拾集，网页信息将在后台补全。':pending?'已保存在浏览器，等待发送到 App。':'待发送记录已移除，请在 App 中核对是否已保存。';
 await chrome.storage.local.set({lastCapture:message});
 return {message,queued:!!pending,saved,requestId:entry.id};
}
chrome.runtime.onInstalled.addListener(()=>{chrome.contextMenus.removeAll(()=>{for(const [id,title,contexts] of [['shiji-page','收藏页面到拾集',['page']],['shiji-selection','收藏选中文字到拾集',['selection']],['shiji-link','收藏链接到拾集',['link']],['shiji-image','收藏图片到拾集',['image']]])chrome.contextMenus.create({id,title,contexts});});void flush().catch(()=>{});});
chrome.contextMenus.onClicked.addListener((info,tab)=>{
 const options={selection:info.selectionText||'',linkUrl:info.menuItemId==='shiji-link'?info.linkUrl:'',imageUrl:info.menuItemId==='shiji-image'?info.srcUrl:''};
 capture(tab,options).catch(e=>remember(e.message,true));
});
chrome.runtime.onMessage.addListener((message,sender,reply)=>{
 if(sender.id!==chrome.runtime.id||!['capture','ping','outbox','retry','remove'].includes(message.type))return false;
 (async()=>{try{
  if(message.type==='ping'){await transport.ping(await configuration());reply({ok:true,message:'已连接 App。'});void flush().catch(()=>{});return;}
  if(message.type==='outbox'){reply({ok:true,rows:await updateQueue()});return;}
  if(message.type==='retry'){await outbox.retry(message.id);await updateQueue();reply({ok:true,message:'已安排重新发送。'});void flush().catch(()=>{});return;}
  if(message.type==='remove'){await outbox.remove(message.id);const rows=await updateQueue();if(!rows.length)await chrome.action.setBadgeText({text:''});reply({ok:true,message:'已移除待发送记录；App 中可能已经保存的收藏会保留。'});return;}
  const [tab]=await chrome.tabs.query({active:true,currentWindow:true});if(!tab?.id)throw new Error('请先打开一个网页。');
  reply({ok:true,...await capture(tab,{screenshot:!!message.screenshot})});
 }catch(e){await remember(e.message,true);reply({ok:false,message:e.message});}})();return true;
});
chrome.alarms.onAlarm.addListener(alarm=>{if(alarm.name===ALARM)void flush().catch(()=>{});});
chrome.runtime.onStartup.addListener(()=>{void flush().catch(()=>{});});
chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local'&&(changes.base||changes.token))void flush().catch(()=>{});});
// Recreate a lost alarm and reconcile a terminated worker on every startup.
void chrome.storage.local.setAccessLevel({accessLevel:'TRUSTED_CONTEXTS'}).catch(()=>{});
void flush().catch(()=>{});

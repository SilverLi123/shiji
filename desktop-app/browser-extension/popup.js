'use strict';
const status=document.querySelector('#status'),connection=document.querySelector('#connection');
let queueVersion=0;
function feedback(message,error=false){status.textContent=message;status.dataset.error=String(error);}
async function ping(){connection.textContent='连接中…';try{const result=await chrome.runtime.sendMessage({type:'ping'});connection.textContent=result.ok?'已连接':'未连接';connection.dataset.connected=String(!!result.ok);if(!result.ok)feedback('App 未连接，收藏可先保存在浏览器待发送。',false);}catch{connection.textContent='未连接';connection.dataset.connected='false';feedback('无法检查连接，请重新打开扩展。',true);}}
function element(tag,text,className){const el=document.createElement(tag);if(text)el.textContent=text;if(className)el.className=className;return el;}
async function refreshQueue(anchor){
 const version=++queueVersion;
 const focused=document.activeElement;
 anchor=anchor||(focused?.dataset.queueAction?{id:focused.dataset.id,action:focused.dataset.queueAction}:null);
 try{
  const result=await chrome.runtime.sendMessage({type:'outbox'});if(version!==queueVersion)return;
  if(!result.ok)throw new Error(result.message);
  const list=document.querySelector('#outbox-list'),scroll=list.scrollTop,fragment=document.createDocumentFragment();
  document.querySelector('#outbox-count').textContent=String(result.rows.length);
  const labels={pending:'等待发送',sending:'正在确认',failed:'需要处理',blocked:'检查连接'};
  for(const row of result.rows){
   const article=element('article');article.dataset.outboxRow=row.id;
   article.append(element('h3',row.title),element('p',labels[row.state]||'等待发送','queue-state'));
   if(row.error)article.append(element('p',row.error,'queue-error'));
   const actions=element('div',null,'queue-actions');
   for(const [action,label] of [['retry','重试'],['remove','移除']]){
    const button=element('button',label,'secondary');button.type='button';button.dataset.queueAction=action;button.dataset.id=row.id;button.disabled=row.state==='sending';button.setAttribute('aria-label',label+'：'+row.title);actions.append(button);
   }
   article.append(actions);fragment.append(article);
  }
  if(!result.rows.length)fragment.append(element('p','没有待发送的收藏。','hint'));
  list.replaceChildren(fragment);list.scrollTop=scroll;
  if(anchor&&(document.activeElement===focused||document.activeElement===document.body)){
   const target=[...list.querySelectorAll('[data-queue-action]')].find(el=>el.dataset.id===anchor.id&&el.dataset.queueAction===anchor.action&&!el.disabled);
   (target||document.querySelector('#outbox-heading')).focus();
  }
 }catch(e){if(version===queueVersion)feedback(e.message||'无法读取待发送记录。',true);}
}
document.querySelector('#outbox-list').addEventListener('click',async event=>{
 const button=event.target.closest('[data-queue-action]');if(!button||button.disabled)return;
 const anchor={id:button.dataset.id,action:button.dataset.queueAction};
 if(anchor.action==='remove'&&!confirm('移除浏览器中的待发送记录？App 中可能已经保存的收藏不会删除。'))return;
 button.disabled=true;
 try{const result=await chrome.runtime.sendMessage({type:anchor.action,id:anchor.id});feedback(result.message,!result.ok);}
 catch{feedback('操作未确认，请重新检查待发送列表。',true);}
 finally{await refreshQueue(anchor);}
});
chrome.storage.onChanged.addListener((changes,area)=>{if(area==='local'&&changes.captureOutboxV1)void refreshQueue();});
chrome.storage.local.get(['base','token','lastCapture']).then(async s=>{
 document.querySelector('#base').value=s.base||'http://127.0.0.1:8782';document.querySelector('#token').value=s.token||'';document.querySelector('#open').href=(s.base||'http://127.0.0.1:8782')+'/';feedback(s.lastCapture||'');
 if(!s.token)document.querySelector('#settings').open=true;else await ping();await refreshQueue();
}).catch(()=>feedback('无法读取连接设置，请重新打开扩展。',true));
document.querySelector('#settings-form').addEventListener('submit',async e=>{e.preventDefault();try{const setting=ShijiClip.settings(document.querySelector('#base').value,document.querySelector('#token').value);await chrome.storage.local.set(setting);document.querySelector('#open').href=setting.base+'/';feedback('配对设置已保存。');await ping();await refreshQueue();if(connection.dataset.connected==='true')document.querySelector('#settings').open=false;}catch(e){feedback(e.message,true);}});
for(const id of ['save','screenshot'])document.querySelector('#'+id).addEventListener('click',async()=>{
 const buttons=[document.querySelector('#save'),document.querySelector('#screenshot')];buttons.forEach(b=>b.disabled=true);feedback('正在保存收藏…');
 try{const result=await chrome.runtime.sendMessage({type:'capture',screenshot:id==='screenshot'});feedback(result.message,!result.ok);if(result.saved){connection.textContent='已连接';connection.dataset.connected='true';}}
 catch{feedback('采集结果尚未确认，请先检查待发送列表和 App。',true);}
 finally{buttons.forEach(b=>b.disabled=false);await refreshQueue();}
});

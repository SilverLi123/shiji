(function(root){
 function confirm(dialog,{title,message,confirmLabel='确认'}){
  dialog.querySelector('[data-confirm-title]').textContent=title;
  dialog.querySelector('[data-confirm-message]').textContent=message;
  dialog.querySelector('[data-confirm-yes]').textContent=confirmLabel;
  return new Promise(resolve=>{
   const finish=value=>{dialog.removeEventListener('close',closed);dialog.removeEventListener('cancel',cancel);dialog.querySelector('[data-confirm-yes]').onclick=null;dialog.querySelector('[data-confirm-no]').onclick=null;dialog.close();resolve(value);};
   const closed=()=>finish(false),cancel=event=>{event.preventDefault();finish(false);};
   dialog.addEventListener('close',closed);dialog.addEventListener('cancel',cancel);
   dialog.querySelector('[data-confirm-yes]').onclick=()=>finish(true);dialog.querySelector('[data-confirm-no]').onclick=()=>finish(false);dialog.showModal();dialog.querySelector('[data-confirm-no]').focus();
  });
 }
 function undoNotice(container,message,receipt,undo,onError){
  if(!receipt.undoToken)return;
  const doc=container.ownerDocument,row=doc.createElement('div'),label=doc.createElement('span'),button=doc.createElement('button');
  row.className='undo-notice';label.textContent=message+' · 15 秒内可撤销';button.textContent='撤销';button.className='text-button';row.append(label,button);container.append(row);
  const timer=setTimeout(()=>row.remove(),15000);
  button.onclick=async()=>{button.disabled=true;try{await undo(receipt.undoToken);clearTimeout(timer);row.remove();}catch(e){button.disabled=false;onError(e.message);}};
 }
 const api={confirm,undoNotice};if(typeof module==='object')module.exports=api;else root.ShijiRecovery=api;
})(typeof window==='object'?window:globalThis);

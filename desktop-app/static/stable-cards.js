/* Keyed rendering for the application's native, escaped card markup. */
(function(root){
  'use strict';
  const htmlByNode=new WeakMap();
  function render(container,items){
    const old=new Map(Array.from(container.children).filter(el=>el.matches('.resource-card')).map(el=>[el.dataset.resourceId,el]));
    const keep=new Set();
    items.forEach((item,index)=>{
      let node=old.get(item.id);
      if(!node||htmlByNode.get(node)!==item.html){
        const template=container.ownerDocument.createElement('template');template.innerHTML=item.html;
        const next=template.content.firstElementChild;
        if(node){
          // Preserve decoded media, including a failed cover's fallback state.
          for(const selector of ['.cover-image','.site-favicon']){
            const image=node.querySelector(selector),replacement=next.querySelector(selector);
            if(image&&replacement&&image.getAttribute('src')===replacement.getAttribute('src')){
              image.alt=replacement.alt;replacement.replaceWith(image);
            }
          }
        }
        node=next;htmlByNode.set(node,item.html);
      }
      keep.add(node);
      // Avoid moving nodes which already occupy their sorted position.
      if(container.children[index]!==node)container.insertBefore(node,container.children[index]||null);
    });
    for(const node of Array.from(container.children))if(!keep.has(node))node.remove();
  }
  function captureFocus(container){
    const node=container.ownerDocument.activeElement;
    if(!node||!container.contains(node))return null;
    const attributes=['data-action','data-id','data-scope','data-value','data-select','data-select-all','href'];
    const attrs=attributes.filter(a=>node.hasAttribute(a)).map(a=>[a,node.getAttribute(a)]);
    if(!attrs.length)return null;
    return {node,tag:node.tagName,attrs,classes:Array.from(node.classList).filter(c=>!['active','selected','is-favorite'].includes(c))};
  }
  function restoreFocus(container,snapshot,fallback){
    if(!snapshot||snapshot.node===container.ownerDocument.activeElement)return;
    const candidates=container.querySelectorAll('button,a,input,select,textarea,summary');
    const match=Array.from(candidates).find(el=>el.tagName===snapshot.tag&&snapshot.attrs.every(([name,value])=>el.getAttribute(name)===value)&&snapshot.classes.every(c=>el.classList.contains(c)));
    (snapshot.node.isConnected&&container.contains(snapshot.node)?snapshot.node:match||fallback)?.focus({preventScroll:true});
  }
  const api={render,captureFocus,restoreFocus};
  if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiCards=api;
})(typeof window==='object'?window:globalThis);

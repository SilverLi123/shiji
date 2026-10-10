/* Keyed rendering for the application's native, escaped card markup. */
(function(root){
  'use strict';
  const htmlByNode=new WeakMap();
  // Keep the pressed/focused action and its ancestry alive during metadata updates.
  // Moving a decoded image into a replacement article is insufficient: WebKit
  // cancels a click when its pointer-down target is detached before pointer-up.
  function patch(node,next){
    if(node.nodeType!==next.nodeType||node.nodeName!==next.nodeName)return next;
    if(node.nodeType!==1){if(node.nodeValue!==next.nodeValue)node.nodeValue=next.nodeValue;return node;}
    if(node.matches('.cover-image,.site-favicon')){
      if(node.getAttribute('src')!==next.getAttribute('src'))return next;
      node.alt=next.alt;return node; // Preserve decoding/error/fallback state.
    }
    const artworkVisible=node.matches('.art-v3.art-in-view')&&next.matches('.art-v3');
    for(const attr of [...node.attributes])if(!next.hasAttribute(attr.name))node.removeAttribute(attr.name);
    for(const attr of next.attributes)if(node.getAttribute(attr.name)!==attr.value)node.setAttribute(attr.name,attr.value);
    // IntersectionObserver will not re-emit just because the same target changed text.
    if(artworkVisible)node.classList.add('art-in-view');
    if(node.matches('input[type=checkbox]'))node.checked=next.checked;
    const old=[...node.childNodes],children=[...next.childNodes],used=new Set();
    const key=el=>el.nodeType!==1?'':el.getAttribute('data-action')
      ?[el.getAttribute('data-action'),el.getAttribute('data-id'),el.getAttribute('data-value')].join('|')
      :el.classList[0]||'';
    children.forEach((child,index)=>{
      const compatible=el=>!used.has(el)&&el.nodeName===child.nodeName&&key(el)===key(child);
      const current=old[index]&&compatible(old[index])?old[index]:old.find(compatible);
      if(current)used.add(current);
      const updated=current?patch(current,child):child;
      if(node.childNodes[index]!==updated)node.insertBefore(updated,node.childNodes[index]||null);
    });
    for(const child of old)if(!used.has(child))child.remove();
    return node;
  }
  function render(container,items,selector='.resource-card'){
    const old=new Map(Array.from(container.children).filter(el=>el.matches(selector)).map(el=>[el.dataset.resourceId,el]));
    const keep=new Set();
    items.forEach((item,index)=>{
      let node=old.get(item.id);
      if(!node||htmlByNode.get(node)!==item.html){
        const template=container.ownerDocument.createElement('template');template.innerHTML=item.html;
        const next=template.content.firstElementChild;
        node=node?patch(node,next):next;htmlByNode.set(node,item.html);
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

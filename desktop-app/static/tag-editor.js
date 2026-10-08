/* One exact tag name per Enter. Commas are ordinary characters. */
(function(root){
 'use strict';
 function create(container,input,onChange,onError){
  const doc=container.ownerDocument,list=container.querySelector('#tag-editor-list');let values=[];
  function render(){
   list.replaceChildren();for(const [index,name] of values.entries()){
    const item=doc.createElement('li'),text=doc.createElement('span'),remove=doc.createElement('button');text.textContent=name;remove.type='button';remove.textContent='×';remove.setAttribute('aria-label','移除标签 '+name);remove.addEventListener('click',()=>{values.splice(index,1);render();input.focus();});item.append(text,remove);list.append(item);
   }
   onChange([...values]);
  }
  function commit(){
   const name=input.value.trim();if(!name)return true;
   if([...name].length>50){onError('每个标签最多50个字符。');return false;}
   if(!values.includes(name)&&values.length>=30){onError('每条资源最多30个标签。');return false;}
   if(!values.includes(name))values.push(name);input.value='';render();return true;
  }
  input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.isComposing){event.preventDefault();commit();}});
  return {commit,read:()=>[...values],set(names){values=[...names];input.value='';render();}};
 }
 const api={create};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiTags=api;
})(typeof window==='object'?window:globalThis);

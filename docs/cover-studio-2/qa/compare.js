(async()=>{
 'use strict';const $=s=>document.querySelector(s);let records=[],mode='all',before=false,baselineCSS='';
 function poster(host,r,old=false){
  const cover=ShijiBoard.cover(r),markup=(old?ShijiBaseline:ShijiV2).coverMarkup(r);
  if(old){const shadow=host.attachShadow({mode:'open'});shadow.innerHTML='<style>'+baselineCSS+'</style><div class="card-preview" style="position:absolute;inset:0;container-type:inline-size;border-radius:12px"></div>';const el=shadow.querySelector('.card-preview');el.innerHTML=markup;if(cover){const img=document.createElement('img');img.src=cover;img.alt=r.title+' · 真实封面';img.style.cssText='position:absolute;inset:0;width:100%;height:100%;object-fit:cover;z-index:4';img.onerror=()=>img.remove();el.prepend(img);}return;}
  host.innerHTML=markup;
  if(cover){const img=document.createElement('img');img.src=cover;img.alt=r.title+' · 真实封面';img.loading='lazy';img.onerror=()=>{img.hidden=true;};host.prepend(img);}
 }
 function render(){
  const shown=records.filter(r=>mode==='github'?ShijiV2.coverProfile(r).semantic==='github':mode==='stress'?r.title.length>24||r.title.length<4||r.thumbnail||r.coverId||r.title.includes('未命名'):true),grid=$('#studio-grid');grid.replaceChildren();
  $('#gallery-heading').textContent=shown.length+' 份实际保存的 QA 输入';
  for(const r of shown){const article=document.createElement('article'),cover=document.createElement('div');cover.className='poster';const heading=document.createElement('h3');heading.textContent=r.title;const meta=document.createElement('p'),profile=ShijiV2.coverProfile(r);meta.textContent=profile.kind+' · 构图 '+(Number(profile.variant)+1)+' · '+profile.theme;article.append(cover,heading,meta);poster(cover,r,before);grid.append(article);}
  if(mode!=='github'){
  // Empty title is a renderer defence case: the real Store forbids empty names.
  const missing=records.find(r=>r.title.includes('未命名'));if(missing){const article=document.createElement('article'),cover=document.createElement('div');cover.className='poster';const note=document.createElement('p');note.className='edge-note';note.textContent='仅呈现边界：名称为空时用来源兜底；真实 API 不接受空名称。';article.append(cover,note);poster(cover,{...missing,title:''},before);grid.append(article);}
  }
  for(const name of ['all','github','stress'])$('#'+name).setAttribute('aria-pressed',String(mode===name));$('#toggle-before').setAttribute('aria-pressed',String(before));
 }
 try{const result=await fetch('/api/resources');if(!result.ok)throw new Error('资源库读取失败');records=(await result.json()).resources.sort((a,b)=>b.createdAt.localeCompare(a.createdAt));baselineCSS=await(await fetch('/qa/baseline.css')).text();const r=records.find(r=>r.title==='SHIJI')||records[0];if(r){poster($('#before-focus'),r,true);poster($('#after-focus'),r);}render();
 }catch(e){$('#review-error').hidden=false;$('#review-error').textContent=e.message;}
 for(const name of ['all','github','stress'])$('#'+name).addEventListener('click',()=>{mode=name;render();});$('#toggle-before').addEventListener('click',()=>{before=!before;render();});
})();

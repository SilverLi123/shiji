(function(root,factory){const api=factory(root,root.ShijiCoverConfig||(typeof module==='object'?require('./cover-config'):null),root.ShijiCoverDirection||(typeof module==='object'?require('./cover-direction'):null));if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiCoverStudio=api;})(typeof window==='object'?window:globalThis,function(root,Config,Direction){
 'use strict';
 const labels={auto:'自动推荐',editorial:'Editorial',spatial:'Spatial',developer:'Developer',kinetic:'Kinetic',minimal:'Minimal',v5:'原版 V5'};
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const clone=v=>v==null?null:JSON.parse(JSON.stringify(v));
 function create({document:doc,preview,save,onSaved=()=>{},notice=()=>{}}){
  const win=doc.defaultView,dialog=doc.createElement('dialog');dialog.id='cover-studio';dialog.className='cover-studio';dialog.setAttribute('aria-labelledby','cs-title');
  doc.body.append(dialog);
  let resource=null,draft=null,coverId='',upload=null,objectURL='',busy=false,reading=false,run=0,origin=null,dead=false,gallery=false;
  const invalid=new Set(),q=s=>dialog.querySelector(s),qa=s=>[...dialog.querySelectorAll(s)];
  function error(message=''){const el=q('.cs-error');if(el){el.textContent=message;el.hidden=!message;}}
  function release(){if(objectURL){win.URL.revokeObjectURL(objectURL);objectURL='';}}
  function config(){return Config.read({coverConfig:draft});}
  function readonly(){return Boolean(config().unsupported);}
  function lock(){q('.cs-controls').disabled=busy||readonly();q('[data-cs-action=save]').disabled=busy||reading||readonly()||invalid.size>0;for(const name of ['cancel','reset'])q(`[data-cs-action=${name}]`).disabled=busy;for(const el of qa('[data-cs-template],[data-cs-action=regenerate]'))el.disabled=busy||readonly()||config().style==='v5';dialog.setAttribute('aria-busy',String(busy));q('[data-cs-action=save]').textContent=busy?'正在保存…':'保存封面';}
  function record(){return {...resource,coverId,coverConfig:draft};}
  function paint(thumbnails=false){
   if(!resource||dead)return;
   const r=record(),c=config(),direction=Direction.recommend(r,c)[0],colors=Config.colors(c,direction);
   q('.cs-main-preview').innerHTML=preview(r,objectURL||undefined);
   const status=q('.cs-direction'),images=qa('.cs-main-preview .cover-image');
   status.textContent=readonly()?'此封面来自更新版本。可以保留，或恢复自动后重新设计。':images.length?'正在加载图片预览…':direction.reasons.filter(x=>x!=='已有真实图片').join(' · ')||'程序化海报';
   for(const image of images){const media=image.closest('.cover-photo')||image,fallback=media.nextElementSibling;const current=()=>image.isConnected&&q('.cs-main-preview').contains(image);const fail=()=>{media.hidden=true;if(fallback)fallback.hidden=false;if(current()&&!readonly())status.textContent='图片不可用，已显示海报。可在“封面来源”更换图片。';};const loaded=()=>{media.hidden=false;if(fallback)fallback.hidden=true;if(current()&&!readonly())status.textContent='正在预览真实图片';};image.onerror=fail;image.onload=loaded;if(image.complete){if(image.naturalWidth)loaded();else fail();}else if(fallback)fallback.hidden=true;}
   q('.cs-contrast').textContent=`文字颜色自动匹配 ${colors.foreground.toUpperCase()}`;
   q('.cs-preview-stage').classList.toggle('cs-gallery-preview',gallery);
   q('[data-cs-action=gallery]').setAttribute('aria-pressed',String(gallery));
   for(const button of qa('[data-cs-style]')){button.setAttribute('aria-pressed',String(button.dataset.csStyle===c.style));if(thumbnails)button.querySelector('.cs3-thumbnail').innerHTML=preview({...resource,coverId:'',thumbnail:'',coverConfig:{...c,style:button.dataset.csStyle,imageSource:'poster'}});}
   for(const button of qa('[data-cs-template]')){button.setAttribute('aria-pressed',String(button.dataset.csTemplate===c.template));if(thumbnails&&button.querySelector('.cs3-thumbnail'))button.querySelector('.cs3-thumbnail').innerHTML=preview({...resource,coverId:'',thumbnail:'',coverConfig:{...c,template:button.dataset.csTemplate,imageSource:'poster'}});}
   for(const button of qa('[data-cs-palette]'))button.setAttribute('aria-pressed',String(button.dataset.csPalette===c.palette));
   lock();
  }
  function sync(){const c=config();for(const el of qa('[name]'))if(el.name!=='upload'&&el.name!=='attachment')el.value=el.name==='primary'?(c.primary||Config.colors(c,Direction.recommend(resource,c)[0]).background):c[el.name];q('[name=attachment]').value=coverId;paint(true);}
  function edit(key,value,control){
   if(busy||readonly())return;
   try{draft=Config.normalize({...Config.defaults,...draft,[key]:value});invalid.delete(key);control?.removeAttribute('aria-invalid');error();paint(['style','template','palette','primary'].includes(key));}
   catch(e){invalid.add(key);control?.setAttribute('aria-invalid','true');error(e.message);lock();}
  }
  function close(){if(busy)return false;++run;reading=false;release();dialog.close();return true;}
  async function submit(){
   if(busy||reading||readonly()||invalid.size)return;
   busy=true;error();lock();const token=run;
   const body={config:clone(draft),coverId,expected:{coverConfig:clone(resource.coverConfig),coverId:resource.coverId||''},...(upload?{upload:{...upload}}:{})};
   let result;
   try{result=await save(resource,body);}catch(e){if(dead||token!==run)return;busy=false;error(e.message+(e.status===409?' 请载入最新封面后重新选择。':''));if(e.resource){q('[data-cs-action=latest]').hidden=false;q('[data-cs-action=latest]').onclick=()=>open(e.resource);}lock();return;}
   if(dead||token!==run)return;
   try{await onSaved(result.resource,result);}catch(_){notice('封面已保存；预览暂未更新，请刷新资源库。');}
   if(dead||token!==run)return;
   busy=false;close();notice(result.changed===false?'封面已是最新状态。':'封面已保存。');
  }
  async function fileSelected(file){
   if(!file||busy||readonly())return;
   if(file.size>5*1024*1024||!['image/png','image/jpeg','image/gif','image/webp'].includes(file.type)){error('请选择 5 MB 以内的 PNG、JPEG、GIF 或 WebP 图片。');return;}
   const token=++run;reading=true;error();lock();
   try{
    const encoded=await new Promise((resolve,reject)=>{const reader=new win.FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('图片读取失败，请重新选择。'));reader.readAsDataURL(file);});
    if(dead||token!==run||!dialog.open)return;
    release();objectURL=win.URL.createObjectURL(file);upload={name:file.name,mime:file.type,base64:encoded};coverId='';draft=Config.normalize({...Config.defaults,...draft,imageSource:'image'});reading=false;sync();
   }catch(e){if(token===run){reading=false;error(e.message);lock();}}
  }
  function open(item){
   if(dead||busy)return false;
   ++run;reading=false;release();resource=item;draft=clone(item.coverConfig);coverId=item.coverId||'';upload=null;invalid.clear();gallery=false;if(!dialog.open)origin=doc.activeElement;
   const option=(value,label)=>`<option value="${value}">${label}</option>`;
   const field=(name,label,options)=>`<label>${label}<select name="${name}">${options.map(([v,l])=>option(v,l)).join('')}</select></label>`;
   const images=(item.attachments||[]).filter(a=>String(a.mime||'').startsWith('image/'));
   dialog.innerHTML=`<header class="cs-header"><div><h2 id="cs-title">封面设计</h2><p>${esc(item.title)}</p></div><button type="button" class="secondary" data-cs-action="cancel">取消</button></header><div class="cs-workspace"><fieldset class="cs-controls"><legend class="sr-only">封面设置</legend><aside class="cs-styles"><h3>风格</h3><div class="cs-style-list">${Object.entries(labels).map(([key,label])=>`<button type="button" data-cs-style="${key}" aria-pressed="false"><span class="cs3-thumbnail" aria-hidden="true"></span><span>${label}</span></button>`).join('')}</div><h3>构图</h3><div class="cs-template-list"><button type="button" class="secondary" data-cs-template="auto">自动</button>${['a','b','c'].map((key,i)=>`<button type="button" data-cs-template="${key}" aria-label="构图 ${i+1}"><span class="cs3-thumbnail" aria-hidden="true"></span><span>${i+1}</span></button>`).join('')}</div></aside><section class="cs-properties" aria-label="调整封面"><h3>颜色</h3><div class="cs-palettes">${[['auto','推荐'],['acid','荧光绿'],['paper','纸白'],['violet','紫色'],['cyan','青色'],['coral','珊瑚'],['ink','墨黑']].map(([v,l])=>`<button type="button" data-cs-palette="${v}" aria-label="${l}" title="${l}" style="--swatch:${Config.palettes[v]||'#c5ff43'}">${v==='auto'?'自动':''}</button>`).join('')}</div><label>自定义主色<input type="color" name="primary"></label><button class="text-button" type="button" data-cs-action="color-auto">恢复推荐主色</button><p class="cs-contrast"></p><h3>封面文字</h3><label>封面标题<input name="customTitle" maxlength="400" placeholder="沿用资源名称"></label><label>副标题<textarea name="customSubtitle" maxlength="480" rows="2" placeholder="使用资源内容摘要"></textarea></label><p class="field-help">只调整封面，不修改资源原标题和备注。</p>${field('titlePosition','标题位置',[['auto','跟随构图'],['top','顶部'],['center','居中'],['bottom','底部']])}${field('density','排版密度',[['balanced','均衡'],['compact','紧凑'],['bold','醒目']])}<h3>图片</h3>${field('imageSource','封面来源',[['auto','自动 · 真实封面优先'],['image','本地图片'],['website','网站预览'],['poster','程序化海报']])}<label>图片附件<select name="attachment"><option value="">未选择</option>${images.map(a=>option(esc(a.id),esc(a.name))).join('')}</select></label><label class="cs-upload">上传图片<input type="file" name="upload" accept="image/png,image/jpeg,image/gif,image/webp"></label><p class="field-help">保存时才上传；取消不会添加附件。</p>${field('imageFit','图片适配',[['fill','填充裁剪'],['fit','完整显示']])}<label>横向焦点<input type="range" name="imageX" min="0" max="100" step="1"></label><label>纵向焦点<input type="range" name="imageY" min="0" max="100" step="1"></label></section></fieldset><section class="cs-preview-stage" aria-label="封面预览"><div class="cs-main-preview card-preview"></div><p class="cs-direction"></p><div class="cs-preview-actions"><button class="secondary" type="button" data-cs-action="regenerate">换一版构图</button><button class="secondary" type="button" data-cs-action="gallery" aria-pressed="false">画廊尺寸预览</button></div></section></div><footer class="cs-footer"><div><p class="cs-error" role="alert" hidden></p><button type="button" class="text-button" data-cs-action="latest" hidden>载入最新封面</button><button type="button" class="text-button" data-cs-action="reset">恢复自动封面</button></div><button type="button" class="primary" data-cs-action="save">保存封面</button></footer>`;
   sync();if(!dialog.open)dialog.showModal();q('[data-cs-action=cancel]').focus();dialog.scrollTop=0;return true;
  }
  dialog.addEventListener('click',e=>{
   const button=e.target.closest('button');if(!button||busy)return;
   if(button.dataset.csStyle){edit('style',button.dataset.csStyle);return;}
   if(button.dataset.csTemplate){edit('template',button.dataset.csTemplate);return;}
   if(button.dataset.csPalette){edit('palette',button.dataset.csPalette);edit('primary','');sync();return;}
   switch(button.dataset.csAction){case 'cancel':close();break;case 'save':submit();break;case 'reset':++run;reading=false;release();upload=null;coverId=resource.coverId||'';draft=null;invalid.clear();error();sync();break;case 'regenerate':if(!readonly()){draft=Config.normalize({...Config.defaults,...draft,template:'auto',seed:(config().seed+1)>>>0});sync();}break;case 'gallery':gallery=!gallery;paint();break;case 'color-auto':edit('primary','');sync();break;}
  });
  dialog.addEventListener('input',e=>{const el=e.target;if(!el.name||['upload','attachment'].includes(el.name))return;edit(el.name,['imageX','imageY'].includes(el.name)?Number(el.value):el.value,el);});
  dialog.addEventListener('change',e=>{if(e.target.name==='upload')fileSelected(e.target.files[0]);if(e.target.name==='attachment'&&!busy&&!readonly()){++run;reading=false;release();upload=null;coverId=e.target.value;edit('imageSource','image');sync();}});
  dialog.addEventListener('cancel',e=>{e.preventDefault();close();});
  dialog.addEventListener('close',()=>{++run;reading=false;release();if(origin?.isConnected)origin.focus({preventScroll:true});});
  return{open,busy:()=>busy,destroy(){dead=true;++run;release();dialog.remove();}};
 }
 return{create};
});

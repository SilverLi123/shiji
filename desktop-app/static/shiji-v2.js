/* Presentation only. Resource state and mutations remain in app.js. */
(function(root){
 'use strict';
 function cardType(r){
  if(['code','prompt'].includes(r.kind))return 'text';
  if(r.kind==='website'&&r.category==='开发工具')return 'tool';
  return 'visual';
 }
 function render(doc,state){
  const hero=doc.getElementById('shiji-hero');
  if(hero)hero.hidden=state.scope!=='all'||state.view!=='grid'||Object.entries(state.filters||{}).some(([key,v])=>!['tagMode','includeSubdomains'].includes(key)&&(typeof v==='boolean'||(Array.isArray(v)?v.length:!!v)));
  const ticker=doc.getElementById('shiji-ticker');if(ticker)ticker.hidden=!!hero?.hidden;
 }
 // Templates only read saved fields. They never enrich or mutate a record.
 const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function host(r){try{return new URL(r.url).hostname.replace(/^www\./,'');}catch{return '';}}
 function coverKind(r){
  if(r.kind==='code'||r.kind==='prompt')return r.kind;
  const site=host(r);
  if(site==='github.com'||site==='gitlab.com'||r.category==='开发工具')return 'tool';
  if(/motion|animat|gsap/i.test(site)||r.category==='视频')return 'motion';
  if(r.category==='音频')return 'audio';
  if(['UI / 设计','3D','美术素材','字体'].includes(r.category))return 'design';
  return r.kind==='file'?'file':'article';
 }
 // Tools with saved technical information have room for a larger composition.
 // The role never depends on index, sort, pagination or a favourite toggle.
 function gallerySpan(r){return coverKind(r)==='tool'&&String(r.language||'').trim()?2:1;}
 function coverRatio(r){return {tool:1.35,design:1.1,motion:1.2,code:1.1,prompt:1.16,article:1.04,audio:1.2,file:1.2}[coverKind(r)];}
 const ring='<svg class="cover-geometry cover-rings" viewBox="0 0 240 240" aria-hidden="true"><circle cx="120" cy="120" r="94" fill="none" stroke="currentColor" stroke-width="38"/><circle cx="120" cy="120" r="61" fill="none" stroke="var(--cover-paper)" stroke-width="13"/></svg>';
 const star='<svg class="cover-geometry cover-star" viewBox="0 0 200 200" aria-hidden="true"><path d="M100 0 118 57 159 19 143 77 200 82 151 113 181 163 125 144 114 200 88 149 37 181 57 125 0 114 51 88 19 37 77 57Z" fill="currentColor"/></svg>';
 function codeLine(line){
  // Tokenize the original text before escaping; content never becomes markup.
  return (line.match(/(?:\/\/.*|#[^\n]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:const|let|var|function|return|if|else|for|import|from|def|class|async|await|true|false|null|func|struct|guard)\b|\b\d+(?:\.\d+)?\b|[^"'\w#]+|\w+|.)/g)||[]).map(token=>{
   const type=/^(\/\/|#)/.test(token)?'comment':/^["']/.test(token)?'string':/^(const|let|var|function|return|if|else|for|import|from|def|class|async|await|true|false|null|func|struct|guard)$/.test(token)?'keyword':/^\d/.test(token)?'number':'';
   return type?`<span class="code-${type}">${escape(token)}</span>`:escape(token);
  }).join('');
 }
 // Cover Studio is a pure presentation layer. Identity and art never depend
 // on list order, favourites, mutable tags, timestamps or device dimensions.
 function canonicalURL(value){try{const u=new URL(value);u.hash='';for(const key of [...u.searchParams.keys()])if(/^utm_|^(fbclid|gclid)$/i.test(key))u.searchParams.delete(key);u.searchParams.sort();return u.href;}catch{return '';}}
 function hash(value){let h=2166136261;for(const c of String(value)){h=Math.imul(h^c.codePointAt(0),16777619);}h=Math.imul(h^(h>>>16),2246822507);h=Math.imul(h^(h>>>13),3266489909);return (h^(h>>>16))>>>0;}
 function coverSemantic(r){
  const site=host(r),kind=coverKind(r);
  if(kind==='tool'&&['github.com','gitlab.com'].includes(site))return 'github';
  if(/reactbits|component|ui8|figma/.test(site))return 'ui';
  if(kind!=='motion'&&(/(^|\.)huggingface\.co$|(^|\.)openai\.com$|(^|\.)anthropic\.com$/.test(site)||site.endsWith('.ai')))return 'ai';
  return kind;
 }
 const themes={tool:['cream','lime','violet','mono','chrome'],design:['cyan','cream','coral','violet','chrome'],motion:['lime','violet','cyan','yellow'],code:['navy','cream','mono'],prompt:['coral','cream','violet','lime'],article:['cream','yellow','mono','coral'],audio:['violet','cyan','navy'],file:['mono','cream','chrome','cyan']};
 function coverProfile(r){
  const kind=coverKind(r),identity=String(r.id||'').trim()||canonicalURL(r.url)||String(r.kind||'resource');
  const seed=hash('shiji-cover-2:'+identity),palette=themes[kind];
  return {seed,kind,semantic:coverSemantic(r),variant:String(seed%3),theme:palette[hash('palette:'+identity)%palette.length]};
 }
 const fontContexts=new Map();
 const widths=new Map();
 function glyphMeasure(text,family='system'){
  const key=family+'\0'+text;if(widths.has(key))return widths.get(key);
  let fontContext=fontContexts.get(family);
  if(!fontContexts.has(family)){
   fontContext=null;
   if(root.document&&typeof root.CanvasRenderingContext2D==='function')try{fontContext=root.document.createElement('canvas').getContext('2d');if(fontContext){fontContext.font=family==='serif'?'700 100px Georgia, "Songti SC", serif':family==='mono'?'850 100px ui-monospace, SFMono-Regular, Menlo, monospace':'850 100px -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';if('letterSpacing' in fontContext)fontContext.letterSpacing='-3px';}}catch{}
   fontContexts.set(family,fontContext);
  }
  const value=fontContext?fontContext.measureText(text).width/100:[...text].reduce((n,c)=>n+(/\s/u.test(c)?.28:/[ilI1.,:;'!|]/.test(c)?.28:/[MW@%]/.test(c)?.92:/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}\p{Extended_Pictographic}]/u.test(c)?1:/[A-Z0-9]/.test(c)?.65:.54),0);
  if(widths.size>=512)widths.clear();widths.set(key,value);return value;
 }
 function titleMetrics(value,measure=glyphMeasure){
  const text=String(value||''),units=Math.max(.5,measure(text));
  const segments=text.split(/(?<=[a-z0-9])(?=[A-Z])|(?<=[/_.\-])(?=\S)|(?<=[\p{Script=Han}])|(?=[\p{Script=Han}])|(?<=\s)|(?=\s)/u).filter(Boolean);
  const pieces=segments.map(t=>({space:/^\s+$/u.test(t),width:measure(t)}));
  const longest=Math.max(.5,...pieces.filter(p=>!p.space).map(p=>p.width));
  const lines=units<=5?1:units<=11?2:units<=22?3:units<=36?4:5;
  // Word packing bounds the real number of rows, including CamelCase break
  // opportunities and individual CJK glyphs. Width/line count alone cannot
  // predict wrapping for differently sized words.
  function rowCount(limit){let rows=1,width=0;for(const p of pieces){if(p.space){if(width)width+=p.width;continue;}if(width&&width+p.width>limit){rows++;width=p.width;}else width+=p.width;}return rows;}
  let low=longest,high=Math.max(longest,pieces.reduce((n,p)=>n+p.width,0));
  for(let i=0;i<14;i++){const mid=(low+high)/2;if(rowCount(mid)>lines)low=mid;else high=mid;}
  return {units,lines,emLine:Math.max(longest,high*1.08),height:54/(lines*1.18)};
 }
 function titleHTML(value){return String(value||'').split(/(?<=[a-z0-9])(?=[A-Z])|(?<=[/_.\-])(?=\S)/u).map(escape).join('<wbr>');}
 function coverMarkup(r){
  const profile=coverProfile(r),{kind,variant,theme}=profile,site=host(r),title=String(r.title||site||r.attachments?.[0]?.name||({code:'代码片段',prompt:'提示词',file:'本地素材'}[r.kind]||'资源'));
  const fontFamily=variant==='1'&&['prompt','article'].includes(kind)?'serif':kind==='tool'&&variant==='2'?'mono':'system';
  const metrics=titleMetrics(title,t=>glyphMeasure(t,fontFamily)),tags=(Array.isArray(r.tags)?r.tags:[]).slice(0,3),text=String(r.snippet||r.description||r.notes||'');
  const source=site||({code:'代码片段',prompt:'提示词',file:'本地素材'}[r.kind]||r.category||'资源');
  const name=`<span class="cover-title" style="--cs-em-line:${metrics.emLine.toFixed(3)};--cs-font-h:${metrics.height.toFixed(3)};--cs-lines:${metrics.lines}">${titleHTML(title)}</span>`;
  const top=`<span class="cover-source">${escape(source)}</span>`;
  const foot=`<span class="cover-caption">${escape(kind==='code'?r.language||'代码片段':kind==='prompt'?'提示词':r.category||'资源')}</span>`;
  let art='',body=name;
  if(kind==='tool'){
   const stack=r.language?[String(r.language)]:tags;
   art=variant==='0'?'<span class="cs-type-slab"></span><span class="cs-print-dots"></span>':variant==='1'?'<span class="cs-signal-columns"><i></i><i></i><i></i></span>':'<span class="cs-terminal-frame"><i></i><i></i><i></i></span><span class="cs-orbit-grid"></span>';
   body+=stack.length?`<span class="cover-stack">${stack.map(t=>`<span>${escape(t)}</span>`).join('')}</span>`:'';
  }else if(kind==='code'){
   const lines=String(r.snippet||'').split('\n',9);
   art=variant==='1'?'<span class="cs-margin-rule"></span>':variant==='2'?'<span class="cs-editor-window"><i></i><i></i><i></i></span>':'';
   body=`<span class="cover-code-title">${titleHTML(title)}</span><pre class="cover-code">${lines.map((line,i)=>`<span class="cover-code-line"><span class="cover-line-number" aria-hidden="true">${i+1}</span><code>${codeLine(line.slice(0,160))||' '}</code></span>`).join('')}</pre>`;
  }else if(kind==='prompt'){
   art=variant==='0'?star.replace('cover-geometry cover-star','cs-geometry cs-star'):variant==='1'?'<span class="cs-quote-orbit"></span>':'<span class="cs-paper-sheet"></span><span class="cs-fold-corner"></span>';
   body+=text?`<span class="cover-excerpt">${escape(text.slice(0,200))}</span>`:'';
  }else if(kind==='design'){
   art=variant==='0'?ring.replace('cover-geometry cover-rings','cs-geometry cs-rings'):variant==='1'?'<span class="cs-swiss-cross"></span><span class="cs-color-square"></span>':'<span class="cs-print-disc"></span><span class="cs-registration"></span>';
  }else if(kind==='motion'){
   art=variant==='0'?ring.replace('cover-geometry cover-rings','cs-geometry cs-disc'):variant==='1'?'<svg class="cs-geometry cs-ribbon" viewBox="0 0 200 400"><path d="M180 -40C-80 40 280 130 40 200S230 370 20 440" fill="none" stroke="currentColor" stroke-width="52"/></svg>':'<span class="cs-motion-frames"><i></i><i></i><i></i></span>';
  }else if(kind==='article'){
   art=variant==='0'?'<span class="cs-editorial-rule"></span>':variant==='1'?'<span class="cs-magazine-column"></span>':'<span class="cs-spine"></span><span class="cs-editorial-rule"></span>';
  }else if(kind==='audio'){
   art=variant==='0'?'<svg class="cs-geometry cs-wave" viewBox="0 0 320 100"><path d="M0 50H25L35 42 45 58 55 20 65 80 75 5 85 95 95 25 105 75 115 40 125 60 135 15 145 85 155 35 165 65 175 0 185 100 195 30 205 70 215 45 225 55 235 20 245 80 255 35 265 65 275 40 285 60 295 50H320" fill="none" stroke="currentColor" stroke-width="4"/></svg>':variant==='1'?'<span class="cs-record-disc"></span>':'<span class="cs-signal-columns"><i></i><i></i><i></i></span>';
  }else art=variant==='0'?'<span class="cs-fold-corner"></span>':variant==='1'?'<span class="cs-file-stack"><i></i><i></i><i></i></span>':'<span class="cs-print-disc"></span><span class="cs-margin-rule"></span>';
  return `<span class="cover-art cs-cover cover-${kind} cs-v${variant} cs-theme-${theme}" data-cover-variant="${variant}" data-cover-theme="${theme}" data-cover-semantic="${profile.semantic}" aria-hidden="true">${art}${top}${body}${foot}</span>`;
 }
 // The approved print composition crops only this bundled 1280×720 snapshot.
 // Arbitrary thumbnails and user attachments retain their own uncropped image.
 function photoCoverMarkup(r,source){
  if(source!=='previews/polyhaven.jpg')return '';
  const title=String(r.title||host(r)),longest=Math.max(1,...title.split(/\s+/u).map(word=>glyphMeasure(word)));
  const font=Math.min(20,Math.max(9,68/longest));
  return `<span class="cover-photo" data-preview-art="photographic-print"><span class="cover-photo-domain">${escape(host(r))}</span><span class="cover-photo-sheet"><span class="cover-photo-window"><img class="cover-image cover-photo-image" src="${escape(source)}" alt="${escape(title)} 实际网站预览的建筑局部" loading="lazy" referrerpolicy="no-referrer"></span><span class="cover-photo-caption">网站预览 · 局部</span></span><span class="cover-photo-title" style="--photo-title-size:${font.toFixed(2)}cqw">${escape(title)}</span><span class="cover-photo-category">${escape(r.category||'')}</span></span>`;
 }
 const api={cardType,render,coverKind,coverMarkup,photoCoverMarkup,gallerySpan,coverRatio,coverProfile,titleMetrics,canonicalURL};if(typeof module==='object')module.exports=api;else root.ShijiV2=api;
})(typeof window==='object'?window:globalThis);

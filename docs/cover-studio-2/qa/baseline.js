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
  const site=host(r),tags=Array.isArray(r.tags)?r.tags.join(' '):'';
  if(site==='github.com'||site==='gitlab.com'||r.category==='开发工具')return 'tool';
  if(/motion|animat|gsap/i.test(site+' '+tags)||r.category==='视频')return 'motion';
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
 function coverMarkup(r){
  const kind=coverKind(r),title=String(r.title||''),site=host(r),tags=(Array.isArray(r.tags)?r.tags:[]).slice(0,3),text=String(r.snippet||r.description||r.notes||'');
  const source=site||({code:'代码片段',prompt:'提示词',file:'本地素材'}[r.kind]||r.category||'资源');
  const name=`<span class="cover-title${title.length>28?' cover-title-long':title.length>16?' cover-title-medium':''}">${escape(title)}</span>`;
  const top=`<span class="cover-source">${escape(source)}</span>`;
  const foot=`<span class="cover-caption">${escape(kind==='code'?r.language||'代码片段':kind==='prompt'?'提示词':r.category||'资源')}</span>`;
  let art='',body=name;
  if(kind==='tool'){
   const stack=r.language?[String(r.language)]:tags;
   art='<span class="cover-dot-field" aria-hidden="true"></span><span class="cover-bracket" aria-hidden="true"></span>';
   body+=stack.length?`<span class="cover-stack">${stack.map(t=>`<span>${escape(t)}</span>`).join('')}</span>`:'';
  }else if(kind==='code'){
   const lines=String(r.snippet||'').split('\n',9);
   body=`<span class="cover-code-title">${escape(title)}</span><pre class="cover-code">${lines.map((line,i)=>`<span class="cover-code-line"><span class="cover-line-number" aria-hidden="true">${i+1}</span><code>${codeLine(line.slice(0,160))||' '}</code></span>`).join('')}</pre>`;
  }else if(kind==='prompt'){
   art=star;body+=text?`<span class="cover-excerpt">${escape(text.slice(0,240))}</span>`:'';
  }else if(kind==='design')art=ring+'<span class="cover-cutout" aria-hidden="true"></span>';
  else if(kind==='motion')art=ring+'<svg class="cover-path" viewBox="0 0 400 300" preserveAspectRatio="none" aria-hidden="true"><path d="M-80 260 390 -40M-30 300 440 0M20 340 490 40M70 380 540 80M-30 80 330 380M0 40 360 340M30 0 390 300M60 -40 420 260" fill="none" stroke="currentColor"/></svg>';
  else if(kind==='article')art='<span class="cover-editorial-rule" aria-hidden="true"></span>'+star;
  else if(kind==='audio')art='<svg class="cover-wave" viewBox="0 0 320 100" aria-hidden="true"><path d="M0 50H25L35 42 45 58 55 20 65 80 75 5 85 95 95 25 105 75 115 40 125 60 135 15 145 85 155 35 165 65 175 0 185 100 195 30 205 70 215 45 225 55 235 20 245 80 255 35 265 65 275 40 285 60 295 50H320" fill="none" stroke="currentColor" stroke-width="4"/></svg>';
  else art='<span class="cover-fold" aria-hidden="true"></span>';
  return `<span class="cover-art cover-${kind}" aria-hidden="true">${art}${top}${body}${foot}</span>`;
 }
 const api={cardType,render,coverKind,coverMarkup,gallerySpan,coverRatio};if(typeof module==='object')module.exports=api;else root.ShijiBaseline=api;
})(typeof window==='object'?window:globalThis);

/* Shared pure filtering and colour functions, also usable in Node tests. */
(function(root){
  'use strict';
  const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  function lab(hex){const a=rgb(hex).map(v=>{v/=255;return v>.04045?Math.pow((v+.055)/1.055,2.4):v/12.92});const xyz=[(a[0]*.4124+a[1]*.3576+a[2]*.1805)/.95047,a[0]*.2126+a[1]*.7152+a[2]*.0722,(a[0]*.0193+a[1]*.1192+a[2]*.9505)/1.08883].map(v=>v>.008856?Math.cbrt(v):7.787*v+16/116);return [116*xyz[1]-16,500*(xyz[0]-xyz[1]),200*(xyz[1]-xyz[2])];}
  function distance(a,b){const x=lab(a),y=lab(b);return Math.hypot(...x.map((v,i)=>v-y[i]));}
  const branchCache=new WeakMap();
  function projectBranch(meta,name){let cache=branchCache.get(meta);if(!cache){cache=new Map();branchCache.set(meta,cache);}if(cache.has(name))return cache.get(name);const result=new Set([name]);let changed=true;while(changed){changed=false;for(const p of meta)if(result.has(p.parent)&&!result.has(p.name)){result.add(p.name);changed=true;}}cache.set(name,result);return result;}
  function projectPath(meta,name){const map=new Map(meta.map(p=>[p.name,p]));const result=[],seen=new Set();while(name&&!seen.has(name)){seen.add(name);result.unshift(name);name=map.get(name)?.parent||'';}return result;}
  function isProjectArchived(meta,name){const map=new Map(meta.map(p=>[p.name,p]));return projectPath(meta,name).some(n=>map.get(n)?.archived);}
  function matches(item,f,meta=[]){
    for(const key of ['category','kind','price','license','linkStatus'])if(f[key]&&(item[key]||(key==='linkStatus'?'unchecked':''))!==f[key])return false;
    for(const key of ['favorite','inbox'])if(typeof f[key]==='boolean'&&Boolean(item[key])!==f[key])return false;
    if(f.hasAssets&&item.kind!=='file'&&!(item.attachments||[]).length)return false;
    if(f.isSnippet&&!['code','prompt'].includes(item.kind))return false;
    if(f.collection&&!(item.projects||[]).some(name=>projectBranch(meta,f.collection).has(name)))return false;
    const tags=f.tags||[],ownTags=item.tags||[];
    if(tags.length&&(f.tagMode==='any'?!tags.some(t=>ownTags.includes(t)):tags.some(t=>!ownTags.includes(t))))return false;
    if((f.excludeTags||[]).some(t=>ownTags.includes(t)))return false;
    if(f.noTags&&ownTags.length)return false;
    if(f.noProjects&&(item.projects||[]).length)return false;
    if(f.hasNotes&&![item.notes,...Object.values(item.projectNotes||{})].some(t=>String(t||'').trim()))return false;
    if(f.mediaType&&!(item.attachments||[]).some(a=>f.mediaType==='other'?!/^(image|audio|video)\//.test(a.mime||''):(a.mime||'').startsWith(f.mediaType+'/')))return false;
    if(f.domain){let host;try{host=new URL(item.url).hostname.toLowerCase().replace(/\.$/,'');}catch{return false;}const wanted=f.domain.toLowerCase();if(host!==wanted&&!(f.includeSubdomains!==false&&host.endsWith('.'+wanted)))return false;}
    if(f.createdFrom||f.createdTo){const time=new Date(item.createdAt).getTime();if(!Number.isFinite(time))return false;const day=new Date(time).toISOString().slice(0,10);if(f.createdFrom&&day<f.createdFrom||f.createdTo&&day>f.createdTo)return false;}
    if(f.color&&!([...(item.colors||[]),...(item.attachments||[]).flatMap(a=>a.colors||[])].some(c=>distance(c,f.color)<32)))return false;
    const haystack=[item.title,item.url,item.description,item.notes,item.snippet,item.author,item.sourceUrl,item.category,...(item.tags||[]),...(item.projects||[]),...Object.values(item.projectNotes||{}),...(item.attachments||[]).flatMap(a=>[a.name,a.author,a.sourceUrl])].join(' ').toLocaleLowerCase();
    return (f.search||'').trim().toLocaleLowerCase().split(/\s+/).filter(Boolean).every(word=>haystack.includes(word));
  }
  function extractPalette(pixels){const bins=new Map();for(let i=0;i<pixels.length;i+=4){if(pixels[i+3]<128)continue;const channels=[pixels[i],pixels[i+1],pixels[i+2]],key=channels.map(v=>v>>4).join(',');const b=bins.get(key)||{n:0,total:[0,0,0]};b.n++;channels.forEach((v,j)=>b.total[j]+=v);bins.set(key,b);}const result=[];for(const b of [...bins.values()].sort((a,b)=>b.n-a.n)){const c='#'+b.total.map(v=>Math.round(v/b.n).toString(16).padStart(2,'0')).join('');if(result.every(r=>distance(r,c)>18))result.push(c);if(result.length===5)break;}return result;}
  function canonicalFilters(f){const out={};for(const k of ['search','category','price','license','kind','linkStatus','color','collection','domain','mediaType','createdFrom','createdTo'])if(f[k])out[k]=String(f[k]).trim();for(const k of ['tags','excludeTags'])if(f[k]?.length)out[k]=[...new Set(f[k])].sort();for(const k of ['favorite','inbox'])if(typeof f[k]==='boolean')out[k]=f[k];for(const k of ['hasAssets','isSnippet','noTags','noProjects','hasNotes'])if(f[k])out[k]=true;if(f.tags?.length&&f.tagMode==='any')out.tagMode='any';if(f.domain&&f.includeSubdomains===false)out.includeSubdomains=false;return out;}
  function sameFilters(a,b){return JSON.stringify(canonicalFilters(a))===JSON.stringify(canonicalFilters(b));}
  function filterSummary(f){const out=[];if(f.search)out.push('关键词：'+f.search);if(f.tags?.length)out.push((f.tagMode==='any'?'任一标签：':'全部标签：')+f.tags.join('、'));if(f.excludeTags?.length)out.push('排除标签：'+f.excludeTags.join('、'));for(const [key,label] of [['collection','项目及下级'],['category','分类'],['price','价格'],['license','授权'],['kind','形式'],['linkStatus','链接状态'],['color','相近颜色']])if(f[key])out.push(label+'：'+f[key]);if(f.domain)out.push('域名：'+f.domain+(f.includeSubdomains===false?'（仅此主机）':'（含子域）'));if(f.createdFrom||f.createdTo)out.push('收藏日期 UTC：'+(f.createdFrom||'不限')+' 至 '+(f.createdTo||'不限'));for(const [key,label] of [['favorite','常用'],['inbox','待整理']])if(typeof f[key]==='boolean')out.push(label+'：'+(f[key]?'是':'否'));for(const [key,label] of [['hasAssets','素材或有附件'],['isSnippet','代码或提示词'],['noTags','没有标签'],['noProjects','没有项目'],['hasNotes','有使用备注']])if(f[key])out.push(label);if(f.mediaType)out.push('本地附件：'+({image:'图片',audio:'音频',video:'视频',other:'其他文件'}[f.mediaType]||f.mediaType));return out;}
  const api={matches,distance,extractPalette,projectBranch,projectPath,isProjectArchived,canonicalFilters,sameFilters,filterSummary};if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiLibrary=api;
})(typeof window==='object'?window:globalThis);

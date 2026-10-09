const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),ui=require('../static/shiji-v2');
const base={id:'stable-one',kind:'website',title:'SHIJI',url:'https://github.com/SilverLi123/shiji',category:'开发工具',tags:['SwiftUI'],language:'',description:''};
const profile=ui.coverProfile(base);
assert.deepEqual(ui.coverProfile({...base,tags:['动效','React'],favorite:true}),profile,'tags/favorite never reshuffle artwork');
assert.deepEqual(ui.coverProfile({...base,title:'另一个保存的名称',description:'Changed copy'}),profile,'content edits retain composition');
assert.equal(ui.coverProfile({...base,url:'https://github.com/renamed/project'}).seed,profile.seed,'ID remains primary identity');
assert.deepEqual(ui.coverProfile({kind:'website',url:'https://example.com/path?b=2&utm_source=x&a=1#part'}),ui.coverProfile({kind:'website',url:'https://EXAMPLE.com/path?a=1&b=2'}),'fallback canonical URL');
for(const kind of ['tool','design','motion','code','prompt','article','audio','file']){
 const r={...base,kind:kind==='tool'?'website':['code','prompt','file'].includes(kind)?kind:'website',url:'https://example.com/',category:{tool:'开发工具',design:'UI / 设计',motion:'视频',audio:'音频',article:'灵感',file:'其他'}[kind]||'其他',snippet:'const x = "<script>";\n  return x;'};
 const variants=new Set(),themes=new Set();for(let i=0;i<60;i++){const p=ui.coverProfile({...r,id:kind+'-'+i});variants.add(p.variant);themes.add(p.theme);}
 assert.equal(variants.size,3,kind+' has three structural compositions');assert.ok(themes.size>=3,kind+' has independent palettes');
 const before=JSON.stringify(r),doc=new JSDOM(ui.coverMarkup(r)).window.document,el=doc.querySelector('.cover-art');assert.ok(el.dataset.coverVariant);assert.equal(el.dataset.coverTheme,ui.coverProfile(r).theme);assert.ok(el.textContent.includes(r.title));assert.equal(JSON.stringify(r),before);assert.equal(doc.querySelectorAll('script,img,a,button,input').length,0);doc.defaultView.close();
}
for(const title of ['', 'UI','WWWWWWWW','iiiiiiii','拾集 SHIJI Motion Studio','长中文标题'.repeat(14),'a'.repeat(300),'SuperLongRepositoryNameWithoutSpaces','emoji 👩‍💻 创作']){const m=ui.titleMetrics(title);assert.ok(Number.isFinite(m.units)&&Number.isFinite(m.emLine));assert.ok(m.lines>=1&&m.lines<=5);assert.ok(m.emLine>0);}
assert.ok(ui.titleMetrics('WWWWWW').units>ui.titleMetrics('iiiiii').units,'glyph widths matter, not length');
assert.ok(ui.titleMetrics('中中中中中中').units>ui.titleMetrics('iiiiii').units);
assert.ok(ui.titleMetrics('AAAAA BBBBB CCCCC DD',s=>s.length).emLine>=8,'word packing fits four uneven words into three rows; average character width alone would clip');
let measurements=0;const measured=ui.titleMetrics('Wide title',s=>{measurements++;return s.length*.9;});assert.ok(measurements>1&&measured.units>0,'actual font measure hook is used');
const hostile={...base,title:'"><svg onload=alert(1)>😃',description:'<script>bad</script>',language:'x" style="color:red',tags:['<img src=x onerror=alert(1)>']};const doc=new JSDOM(ui.coverMarkup(hostile)).window.document;assert.equal(doc.querySelectorAll('script,[onload],[onerror]').length,0);for(const e of doc.querySelectorAll('[style]'))assert.ok(!e.getAttribute('style').includes('alert'));assert.ok(doc.querySelector('.cover-title').textContent.includes(hostile.title));doc.defaultView.close();
assert.equal(ui.coverKind({...base,url:'https://example.com/',category:'灵感',tags:['motion']}),'article','mutable tags are copy, not composition identity');
console.log('Cover Studio: stable identity, canonical URL, 3 structures/type, themes, glyph-aware typography, real fields and injection safety passed');

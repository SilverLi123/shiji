const assert=require('node:assert/strict');
const {matches,sameFilters,canonicalFilters,filterSummary}=require('../static/library.js');
const item={title:'React UI',url:'https://components.example.com/item',sourceUrl:'https://elsewhere.example/',tags:['React','动效'],projects:['按钮'],notes:'',projectNotes:{按钮:'参考用法'},attachments:[{mime:'image/png'},{mime:'audio/wav'}],favorite:false,inbox:false,kind:'website',createdAt:'2026-10-02T00:15:00+08:00'};
const tree=[{name:'界面',parent:''},{name:'按钮',parent:'界面'}];
assert(matches(item,{tags:['React','音频'],tagMode:'any',collection:'界面',hasNotes:true,favorite:false,inbox:false,domain:'example.com',mediaType:'audio',createdFrom:'2026-10-01',createdTo:'2026-10-01'},tree));
for(const filters of [{tags:['React','音频']},{excludeTags:['React']},{noTags:true},{noProjects:true},{favorite:true},{inbox:true},{domain:'example.com',includeSubdomains:false},{domain:'elsewhere.example'},{domain:'ample.com'},{mediaType:'video'},{mediaType:'other'},{createdFrom:'2026-10-02'},{createdTo:'2026-09-30'}])assert(!matches(item,filters,tree),JSON.stringify(filters));
assert(!matches({...item,url:'https://evil-example.com/'},{domain:'example.com'}));
assert(matches({...item,url:'https://example.com./'},{domain:'example.com',includeSubdomains:false}));
assert(matches({...item,url:'https://xn--fsqu00a.xn--0zwm56d/'},{domain:'xn--fsqu00a.xn--0zwm56d'}));
for(const [unicode,ascii,unrelated] of [['faß.de','xn--fa-hia.de','fass.de'],['straße.de','xn--strae-oqa.de','strasse.de']]){
  assert(matches({...item,url:'https://'+unicode+'/'},{domain:ascii}));
  assert(matches({...item,url:'https://'+ascii+'/'},{domain:ascii}));
  assert(!matches({...item,url:'https://'+unrelated+'/'},{domain:ascii}));
  assert(!matches({...item,url:'https://'+unicode+'/'},{domain:unrelated}));
}
assert(!matches({...item,url:'',createdAt:'invalid'},{createdFrom:'2026-01-01'}));
assert(matches({...item,tags:[],projects:[],notes:'独立备注',projectNotes:{},attachments:[{mime:'application/pdf'}]},{noTags:true,noProjects:true,hasNotes:true,mediaType:'other'}));
assert(!matches({...item,notes:'',projectNotes:{按钮:'   '}},{hasNotes:true}));
assert(!matches({...item,attachments:[],thumbnail:'image.png'},{mediaType:'image'}));
assert(matches(item,{tags:[],tagMode:'any'}));
assert(sameFilters({tags:['B','A'],favorite:false},{tags:['A','B'],tagMode:'all',excludeTags:[],noTags:false,includeSubdomains:true,domain:'',favorite:false}));
assert(!sameFilters({favorite:false},{}));assert(!sameFilters({tags:['A'],tagMode:'all'},{tags:['A'],tagMode:'any'}));
assert.deepEqual(canonicalFilters({tags:[],excludeTags:[],includeSubdomains:true,hasAssets:false}),{});
assert(filterSummary({favorite:false,inbox:false,excludeTags:['弃用'],tagMode:'any',tags:['A','B']}).includes('常用：否'));
assert(filterSummary({tags:['A'],tagMode:'any'}).includes('任一标签：A'));
const untouched=JSON.stringify(item);matches(item,{noTags:true});assert.equal(JSON.stringify(item),untouched);
console.log('PASS: advanced tag and exclusion semantics, false states, host boundaries/IDNA, UTC inclusive dates, local media, legacy defaults and no filter mutations.');

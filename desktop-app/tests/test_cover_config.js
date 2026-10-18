const assert=require('node:assert/strict');
const vectors=require('./fixtures/cover-config.json');
const Config=require('../static/cover-config.js');
for(const c of vectors.valid){
 const before=JSON.stringify(c.input),actual=Config.normalize(c.input);
 assert.equal(JSON.stringify(c.input),before,c.name);
 if('want' in c)assert.deepEqual(actual,c.want,c.name);
 else for(const[k,v]of Object.entries(c.subset))assert.deepEqual(actual[k],v,c.name);
 assert.deepEqual(Config.normalize(actual),actual);
}
for(const v of [...vectors.invalid,{customTitle:'中'.repeat(201)},{customSubtitle:'s'.repeat(241)},{extra:'中'.repeat(3000)},{imageX:NaN},{extra:Infinity},{version:2,extra:NaN},{extra:undefined},{primary:null},{extra:'\ud800'}])assert.throws(()=>Config.normalize(v),TypeError);
assert.equal(Config.read({}).style,'auto');
assert.equal(Config.read({coverConfig:null}).style,'auto');
assert.equal(Config.read({coverConfig:{version:7}}).unsupported,true);
assert.equal(Config.read({coverConfig:{primary:'bad'}}).invalid,true);
// Test the output colors independently, not the implementation's contrast helper.
function luminance(hex){return hex.slice(1).match(/../g).map(c=>parseInt(c,16)/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4).reduce((s,c,i)=>s+c*[.2126,.7152,.0722][i],0);}
for(const primary of ['#000000','#ffffff','#777777','#c5ff43','#b39bff','#ff0000']){
 const c=Config.colors({primary},{}),a=luminance(c.background),b=luminance(c.foreground);
 assert.ok((Math.max(a,b)+.05)/(Math.min(a,b)+.05)>=4.5,primary);
 assert.equal(c.background,primary);
}
assert.equal(Config.colors({palette:'paper'},{}).background,'#f3efdf');
assert.equal(Config.colors({},{palette:'cyan'}).background,'#65e2e4');
console.log('PASS: portable cover preferences, bounded future JSON, safe colors and readable contrast');

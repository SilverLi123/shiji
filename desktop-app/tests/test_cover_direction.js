const assert=require('node:assert/strict'),D=require('../static/cover-direction');
const cases=[
 [{url:'https://github.com/silver/shiji',title:'拾集',kind:'website'},'developer','b'],
 [{url:'https://github.com/facebook/react',title:'React components',category:'开发工具'},'developer','c'],
 [{url:'https://github.com/example/models',title:'AI models',category:'开发工具'},'spatial','c'],
 [{title:'开发工具',category:'开发工具'},'developer','b'],
 [{url:'https://huggingface.co/models',title:'模型',kind:'website'},'spatial','c'],
 [{title:'机器人关节设计',description:'Robotics control',kind:'website'},'spatial','b'],
 [{title:'React UI components',category:'UI / 设计',kind:'website'},'developer','c'],
 [{title:'GSAP motion experiments',url:'https://motionsites.ai/'},'kinetic','a'],
 [{title:'字体排版灵感',category:'UI / 设计'},'editorial','c'],
 [{title:'实际代码',kind:'code',snippet:'const a = 1'},'developer','a'],
 [{title:'Prompt 提示',kind:'prompt',snippet:'真实内容'},'editorial','b'],
 [{title:'中文技术文章与随笔',kind:'website'},'editorial','a'],
 [{title:'',kind:'file',attachments:[{mime:'image/png'}]},'minimal','a'],
];
for(const [r,style,template] of cases){
 const original=JSON.stringify(r),first=D.recommend(r,{});
 assert.equal(first[0].style,style);assert.equal(first[0].template,template);
 assert.ok(first[0].reasons.length);assert.equal(new Set(first.map(x=>x.style)).size,5);
 assert.deepEqual(D.recommend({...r,id:'different-id'},{}),first,'ID must not choose art');
 assert.equal(JSON.stringify(r),original);
}
assert.notEqual(D.recommend({url:'https://github.com.evil.test/x',title:'普通收藏'}, {})[0].style,'developer');
const r={title:'接口代码',kind:'code'};
assert.equal(D.recommend(r,{seed:1})[0].template,'b');
assert.equal(D.recommend(r,{seed:2})[0].template,'c');
assert.equal(D.recommend(r,{style:'kinetic',template:'c'})[0].style,'kinetic');
assert.equal(D.recommend(r,{style:'kinetic',template:'c'})[0].template,'c');
assert.equal(D.recommend({title:'JavaScript component library'}, {})[0].style,'developer');
for(const c of require('./fixtures/cover-config.json').directions){const top=D.recommend(c.resource,{})[0];assert.equal(top.style,c.style);assert.equal(top.template,c.template);}
console.log('PASS: actual content selects explainable art, exact hosts, deterministic regeneration and no ID lottery');

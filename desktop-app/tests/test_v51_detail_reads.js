const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),{JSDOM}=require('jsdom'),{init}=require('../static/shiji-v2-motion');
const dom=new JSDOM('<button id="motion-mode"></button><div id="drawer"><h2>资源名</h2><div class="detail-block">说明</div></div><button id="source">真实封面</button><div id="target"></div>',{pretendToBeVisual:true,url:'http://localhost'}),w=dom.window,d=w.document;
w.matchMedia=()=>({matches:false,addEventListener(){},removeEventListener(){}});
const events=[];w.Element.prototype.animate=function(){events.push('animate');return {finished:new Promise(()=>{}),cancel(){},pause(){},play(){}};};
w.Element.prototype.getBoundingClientRect=function(){events.push('read');return {left:10,top:20,width:300,height:220,bottom:240};};
const ui=init({document:d,window:w});events.length=0;
ui.openDetail({sourceElement:d.querySelector('#source'),detailElement:d.querySelector('#target')});
assert.deepEqual(events.slice(0,2),['read','read'],'measure endpoints before starting drawer animations');
assert.equal(d.querySelectorAll('.shiji-detail-ghost').length,1);ui.closeDetail();assert.equal(d.querySelectorAll('.shiji-detail-ghost').length,0);ui.destroy();dom.window.close();
const source=fs.readFileSync(require.resolve('../static/app.js'),'utf8'),declarations=source.slice(source.indexOf('const date'),source.indexOf('const size'));
let constructions=0;const Real=Intl.DateTimeFormat;class Counting extends Real {constructor(...args){super(...args);constructions++;}}
const context=vm.createContext({Intl:{DateTimeFormat:Counting},Date});vm.runInContext(declarations+';globalThis.formatDate=date;',context);
for(const value of ['2026-10-10T00:00:00Z','2026-12-31T15:20:00Z','invalid'])assert.equal(context.formatDate(value),new Date(value).toLocaleString('zh-CN',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'}));
assert.equal(constructions,1,'reuse one date formatter rather than initialize ICU per detail/backup row');console.log('PASS: detail layout reads precede animation writes; cached formatter preserves dates including invalid values');

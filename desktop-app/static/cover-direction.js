(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiCoverDirection=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const catalog=[{style:'editorial',template:'a',palette:'paper',score:1,reasons:['文字内容']},{style:'spatial',template:'a',palette:'violet',score:0,reasons:['空间构图']},{style:'developer',template:'b',palette:'acid',score:0,reasons:['技术排版']},{style:'kinetic',template:'a',palette:'coral',score:0,reasons:['动态排版']},{style:'minimal',template:'c',palette:'ink',score:0,reasons:['简洁呈现']}];
 function features(r){let host='';try{host=new URL(r.url).hostname.toLowerCase().replace(/^www\./,'');}catch{}return{host,text:[r.title,r.description,r.category,r.language,...(Array.isArray(r.tags)?r.tags:[])].filter(Boolean).join(' '),kind:r.kind,category:r.category,hasImage:Boolean(r.coverId||r.thumbnail||(r.attachments||[]).some(a=>String(a.mime||'').startsWith('image/')))};}
 const rules=[
  {style:'developer',template:'b',weight:10,reason:'开发工具分类',match:f=>f.category==='开发工具'},
  {style:'editorial',template:'c',weight:10,reason:'设计素材分类',match:f=>['UI / 设计','美术素材'].includes(f.category)},
  {style:'developer',template:'a',weight:100,reason:'代码片段',match:f=>f.kind==='code'},
  {style:'editorial',template:'b',weight:100,reason:'Prompt 文本',match:f=>f.kind==='prompt'},
  {style:'developer',template:'b',weight:40,reason:'代码仓库来源',match:f=>['github.com','gitlab.com','codeberg.org'].includes(f.host)},
  {style:'developer',template:'c',weight:60,reason:'组件与界面系统',match:f=>/\breact\b|components?|组件|设计系统/i.test(f.text)||['reactbits.dev','ui.shadcn.com'].includes(f.host)},
  {style:'spatial',template:'b',weight:80,reason:'机器人与工程结构',match:f=>/robot|机器人|机械|关节/i.test(f.text)},
  {style:'spatial',template:'c',weight:55,reason:'AI 与模型内容',match:f=>['huggingface.co','openai.com','anthropic.com'].includes(f.host)||/\b(AI|ML|LLM)\b|人工智能|机器学习/i.test(f.text)},
  {style:'spatial',template:'a',weight:65,reason:'三维素材与空间工具',match:f=>['polyhaven.com','spline.design'].includes(f.host)||/\b3d\b|三维|建模|材质/i.test(f.text)},
  {style:'kinetic',template:'a',weight:75,reason:'动效内容',match:f=>['motionsites.ai','gsap.com'].includes(f.host)||/motion|animation|gsap|动效|动画/i.test(f.text)},
  {style:'kinetic',template:'b',weight:80,reason:'动态字体',match:f=>/kinetic|动态字体|逐帧/i.test(f.text)},
  {style:'kinetic',template:'c',weight:60,reason:'音频与节奏',match:f=>f.host==='freesound.org'||/音频|声效|\baudio\b/i.test(f.text)},
  {style:'editorial',template:'c',weight:50,reason:'视觉与排版参考',match:f=>/灵感|字体|排版|配色|inspiration|typograph|palette/i.test(f.text)||f.host==='recent.co'},
  {style:'minimal',template:'a',weight:20,reason:'已有真实图片',match:f=>f.hasImage},
  {style:'minimal',template:'b',weight:25,reason:'本地文档',match:f=>f.kind==='file'&&!f.hasImage},
 ];
 function recommend(resource,config={}){
  const f=features(resource||{}),rows=catalog.map(r=>({...r,reasons:[...r.reasons]}));
  for(const rule of rules)if(rule.match(f)){const row=rows.find(r=>r.style===rule.style);if(rule.weight>row.score){row.score=rule.weight;row.template=rule.template;row.reasons=[rule.reason];}else row.reasons.push(rule.reason);}
  if(config.style&&config.style!=='auto'&&config.style!=='v5'){const row=rows.find(r=>r.style===config.style);if(row){row.score+=1000;row.reasons.unshift('你选择的风格');}}
  for(const row of rows){if(config.template&&config.template!=='auto'&&['a','b','c'].includes(config.template))row.template=config.template;else row.template=['a','b','c'][(['a','b','c'].indexOf(row.template)+(Number.isInteger(config.seed)?config.seed>>>0:0))%3];if(config.palette&&config.palette!=='auto')row.palette=config.palette;}
  return rows.sort((a,b)=>b.score-a.score);
 }
 return{recommend,features};
});

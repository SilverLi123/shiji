(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.ShijiCoverConfig=api;})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 const defaults=Object.freeze({version:1,style:'auto',template:'auto',seed:0,palette:'auto',primary:'',customTitle:'',customSubtitle:'',titlePosition:'auto',density:'balanced',imageSource:'auto',imageFit:'fill',imageX:50,imageY:50});
 const enums={style:['auto','editorial','spatial','developer','kinetic','minimal','v5'],template:['auto','a','b','c'],palette:['auto','acid','paper','violet','cyan','coral','ink'],titlePosition:['auto','top','center','bottom'],density:['balanced','compact','bold'],imageSource:['auto','image','website','poster'],imageFit:['fill','fit']};
 const palettes=Object.freeze({acid:'#c5ff43',paper:'#f3efdf',violet:'#b39bff',cyan:'#65e2e4',coral:'#ff8d72',ink:'#17191c'});
 function jsonValue(v,depth=1){
  if(depth>4)throw new TypeError('封面设置层级过深');
  if(typeof v==='string'){for(const c of v)if(c.length===1&&c.charCodeAt(0)>=0xd800&&c.charCodeAt(0)<=0xdfff)throw new TypeError('封面设置包含无效 Unicode');return;}
  if(v===null||typeof v==='boolean')return;
  if(typeof v==='number'&&Number.isFinite(v))return;
  if(Array.isArray(v)){for(const x of v)jsonValue(x,depth+1);return;}
  if(v&&typeof v==='object'&&(Object.getPrototypeOf(v)===Object.prototype||Object.getPrototypeOf(v)===null)){for(const x of Object.values(v))jsonValue(x,depth+1);return;}
  throw new TypeError('封面设置必须是有限 JSON 数据');
 }
 function bounded(v){jsonValue(v);if(new TextEncoder().encode(JSON.stringify(v)).length>8192)throw new TypeError('封面设置超过 8 KiB');}
 function normalize(value){
  if(value==null)return null;
  if(typeof value!=='object'||Array.isArray(value))throw new TypeError('封面设置必须是对象');
  bounded(value);
  const version=value.version===undefined?1:value.version;
  if(!Number.isInteger(version)||version<1||version>2147483647)throw new TypeError('封面设置版本无效');
  const cloned=JSON.parse(JSON.stringify(value));if(version>1)return cloned;
  const result={...defaults,...cloned};
  for(const[key,options]of Object.entries(enums))if(!options.includes(result[key]))throw new TypeError('封面选项无效：'+key);
  if(!Number.isInteger(result.seed)||result.seed<0||result.seed>4294967295)throw new TypeError('封面种子无效');
  for(const[key,max]of [['customTitle',200],['customSubtitle',240]])if(typeof result[key]!=='string'||Array.from(result[key]).length>max)throw new TypeError('封面文字无效：'+key);
  if(typeof result.primary!=='string'||(result.primary&&!/^#[0-9a-fA-F]{6}$/.test(result.primary)))throw new TypeError('封面主色必须是六位十六进制颜色');
  result.primary=result.primary.toLowerCase();
  for(const key of ['imageX','imageY'])if(typeof result[key]!=='number'||!Number.isFinite(result[key])||result[key]<0||result[key]>100)throw new TypeError('封面图片位置无效');
  bounded(result);return result;
 }
 function read(resource){try{const value=normalize(resource&&resource.coverConfig);return value&&value.version>1?{...defaults,unsupported:true}:{...defaults,...value};}catch(_){return{...defaults,invalid:true};}}
 function luminance(hex){const c=hex.slice(1).match(/../g).map(x=>parseInt(x,16)/255).map(x=>x<=.04045?x/12.92:((x+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722;}
 function colors(config={},direction={}){
  const palette=config.palette&&config.palette!=='auto'?config.palette:direction.palette;
  const background=/^#[0-9a-fA-F]{6}$/.test(config.primary||'')?config.primary.toLowerCase():palettes[palette]||palettes.acid;
  const l=luminance(background),dark=(l+.05)/(luminance('#111111')+.05),light=1.05/(l+.05);
  return{background,foreground:dark>=4.5?'#111111':light>=4.5?'#ffffff':'#000000',accent:background===palettes.violet?palettes.acid:palettes.violet};
 }
 return{normalize,read,colors,defaults,palettes};
});

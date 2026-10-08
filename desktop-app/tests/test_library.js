const assert=require('node:assert/strict');const {matches,extractPalette}=require('../static/library.js');
const r={title:'React',tags:['动效','React'],projects:['首页','游戏'],snippet:'const widget = 1;',projectNotes:{首页:'导航'},colors:['#ff0000']};
assert(matches(r,{tags:['动效','React'],collection:'首页',search:'widget 导航'}));
assert(!matches(r,{tags:['动效','音频']}));assert(matches(r,{color:'#ee1100'}));assert(!matches(r,{color:'#0000ff'}));
assert.deepEqual(extractPalette(new Uint8ClampedArray([255,0,0,255,255,0,0,255,0,0,255,255,1,1,1,0])),['#ff0000','#0000ff']);
console.log('PASS: tag intersections, project/snippet search, perceptual colour matching and palette extraction.');

const tree=[{name:'游戏',parent:'',archived:false},{name:'界面',parent:'游戏',archived:false},{name:'按钮',parent:'界面',archived:false}];
assert(matches({...r,projects:['按钮']},{collection:'游戏'},tree));assert(!matches({...r,projects:['首页']},{collection:'游戏'},tree));
const lib=require('../static/library.js');assert.deepEqual(lib.projectPath(tree,'按钮'),['游戏','界面','按钮']);assert(lib.isProjectArchived([{name:'游戏',parent:'',archived:true},{name:'按钮',parent:'游戏'}],'按钮'));

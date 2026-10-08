'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{JSDOM}=require('jsdom');
const {score,create,duration}=require('../static/olla-motion');
// Asymmetric halves must return to the same orientation at every loop boundary.
for(const [selector,frames] of score().filter(([selector])=>selector.startsWith('.motion-fold i'))){
 const orientation=frame=>Number(frame.transform.match(/rotate\((-?[\d.]+)deg\)/)[1]);
 assert.equal(((orientation(frames.at(-1))-orientation(frames[0]))%360+360)%360,0,selector+' closes its loop without a jump');
}
const html=fs.readFileSync(path.join(__dirname,'fixtures/legacy-olla.html'),'utf8');
const dom=new JSDOM(html),doc=dom.window.document,win=dom.window,stage=doc.getElementById('motion-stage');
assert.ok(stage.contains(doc.getElementById('page-title')),'motion belongs to the real resource heading');
assert.ok(stage.contains(doc.getElementById('resource-total')),'slices accompany the real resource count');
assert.equal(doc.querySelectorAll('.motion-panel').length,0,'no detached animation tiles');
let preference,intersection,mutation,disconnected=0;
const reduce={matches:false,addEventListener(_,fn){preference=fn;},removeEventListener(){preference=null;}};
win.matchMedia=()=>reduce;
win.IntersectionObserver=class{constructor(fn){intersection=fn;}observe(){}disconnect(){disconnected++;}};
win.MutationObserver=class{constructor(fn){mutation=fn;}observe(){}disconnect(){disconnected++;}};
let hidden=false;Object.defineProperty(doc,'hidden',{get:()=>hidden});
const animations=[];
win.Element.prototype.animate=function(frames,options){const animation={frames,options,playing:true,canceled:false,currentTime:100,play(){this.playing=true;},pause(){this.playing=false;},cancel(){this.canceled=true;}};animations.push(animation);return animation;};
const values=new Map(),storage={getItem:key=>values.get(key),setItem:(key,value)=>values.set(key,value)};
const ui=create(stage,{doc,win,storage}),button=stage.querySelector('button');
assert.equal(animations.length,score().length);assert.ok(animations.every(a=>!a.playing),'offscreen initial state paused');
intersection([{isIntersecting:true}]);assert.ok(animations.every(a=>a.playing));assert.equal(stage.dataset.motion,'playing');
assert.ok(animations.every(a=>a.options.duration===duration&&a.options.iterations===Infinity));
button.click();assert.equal(values.get('shiji-olla-paused'),'true');assert.ok(animations.every(a=>!a.playing));assert.equal(button.getAttribute('aria-pressed'),'true');
intersection([{isIntersecting:false}]);intersection([{isIntersecting:true}]);assert.ok(animations.every(a=>!a.playing),'observer never overrides user pause');
button.click();assert.ok(animations.every(a=>a.playing));hidden=true;doc.dispatchEvent(new win.Event('visibilitychange'));assert.ok(animations.every(a=>!a.playing));hidden=false;doc.dispatchEvent(new win.Event('visibilitychange'));assert.ok(animations.every(a=>a.playing));
const n=animations.length;doc.querySelector('[data-action="scope"]')?.click(); // Nav is populated by app; simulate its real delegated button.
const category=doc.createElement('button');category.dataset.action='category';doc.body.append(category);category.click();assert.equal(animations.length,n);assert.ok(animations.every(a=>a.currentTime===0));
doc.getElementById('page-title').textContent='回收站';mutation();assert.equal(stage.dataset.quiet,'true');assert.equal(stage.hidden,false,'resource heading stays visible');assert.ok(animations.every(a=>!a.playing));doc.getElementById('page-title').textContent='灵感板';mutation();assert.equal(stage.dataset.quiet,'false');
reduce.matches=true;preference();assert.ok(animations.every(a=>a.canceled));assert.equal(stage.dataset.motion,'reduced');assert.equal(button.disabled,true);assert.equal(button.querySelector('span').textContent,'静态模式');
reduce.matches=false;preference();assert.equal(animations.length,n*2);assert.ok(animations.slice(n).every(a=>a.playing));
ui.destroy();assert.ok(animations.every(a=>a.canceled));assert.equal(disconnected,2);assert.equal(preference,null);button.click();assert.equal(values.get('shiji-olla-paused'),'false','destroy removes handlers');
const before=animations.length;values.set('shiji-olla-paused','true');const reopened=create(stage,{doc,win,storage});intersection([{isIntersecting:true}]);assert.ok(animations.slice(before).every(a=>!a.playing),'pause survives reopen');reopened.destroy();dom.window.close();
assert.match(html,/aria-label="资源库标题与浏览状态/);assert.equal(score().length,9);console.log('Olla score, pause persistence, visibility, scope, reduced motion, interruption and disposal passed');

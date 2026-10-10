const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),fs=require('fs');const {bind}=require('../static/liquid-glass');
const dom=new JSDOM('<nav id="browse-categories"><button class="browse-category active">All</button></nav>'),win=dom.window,doc=win.document;
let preference,changed,resized,next,animations=[];const reduce={matches:false,addEventListener(_,fn){preference=fn},removeEventListener(){preference=null;}};
win.matchMedia=()=>reduce;win.MutationObserver=class{constructor(fn){changed=fn}observe(){}disconnect(){}};win.ResizeObserver=class{constructor(fn){resized=fn}observe(){}disconnect(){}};win.requestAnimationFrame=fn=>(next=fn,1);win.cancelAnimationFrame=()=>next=null;
win.Element.prototype.animate=function(frames,options){const a={frames,options,cancel(){this.cancelled=true}};animations.push(a);return a;};
let x=5,w=70;const button=doc.querySelector('button');for(const [key,get] of Object.entries({offsetLeft:()=>x,offsetTop:()=>5,offsetWidth:()=>w,offsetHeight:()=>38}))Object.defineProperty(button,key,{get});
const ui=bind(doc,win);next();assert.ok(doc.querySelector('.glass-indicator'));assert.equal(animations.length,0);
x=90;w=85;changed();next();assert.equal(animations.length,1);assert.equal(animations[0].options.duration,320);assert.equal(animations[0].options.iterations,undefined);
reduce.matches=true;preference();x=150;resized();next();assert.ok(animations[0].cancelled);assert.equal(animations.length,1);
ui.destroy();assert.equal(doc.querySelector('.glass-indicator'),null);assert.equal(preference,null);
const html=fs.readFileSync(require('path').join(__dirname,'../static/index.html'),'utf8');assert.ok(!html.includes('src="olla-motion.js"'));assert.ok(!html.includes('motion-decor'));assert.ok(html.includes('liquid-glass.css'));dom.window.close();console.log('Functional glass finite morph, reduced motion and disposal passed');

const surface=new JSDOM(html),docSurface=surface.window.document;
// V5 moves capture into the studio toolbar; file import remains in management.
assert.equal(docSurface.querySelector('.capture-deck'),null);
assert.equal(docSurface.querySelectorAll('.topbar [data-action="add"]').length,1);
assert.equal(docSurface.querySelectorAll('.utility-nav [data-action="import-files"]').length,1);
assert.ok(docSurface.querySelector('#v5-mobile-nav [data-action="add"]'));
surface.window.close();

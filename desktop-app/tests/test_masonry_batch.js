'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
let dirty=false,flushes=0;
const measure=()=>{if(dirty){flushes++;dirty=false;}};
const style=()=>new Proxy({}, {set(target,key,value){target[key]=value;dirty=true;return true;}});
const cards=Array.from({length:1000},(_,i)=>({dataset:{resourceId:String(i)},style:style(),
 get offsetHeight(){measure();return 100+i%3*20;},
 getBoundingClientRect(){measure();return {left:parseFloat(this.style.left)||0,top:parseFloat(this.style.top)||0,width:parseFloat(this.style.width)||0,height:100+i%3*20};}
}));
const classes=new Set(),grid={children:cards,hidden:false,clientWidth:600,style:style(),classList:{contains:c=>classes.has(c),toggle(c,on){on?classes.add(c):classes.delete(c);}},querySelectorAll:()=>cards,addEventListener(){},removeEventListener(){}};
const ctx={module:{exports:{}},innerWidth:1280,matchMedia:()=>({matches:true,addEventListener(){},removeEventListener(){}}),addEventListener(){},removeEventListener(){},requestAnimationFrame:()=>1,cancelAnimationFrame(){}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/resource-bits.js'),'utf8'),ctx);
const ui=ctx.module.exports.create(grid,null);ui.render();assert.equal(flushes,2,'one width/height pass and one position/rect pass regardless of card count');
const columns=new Map();
for(const card of cards){const r=card.getBoundingClientRect(),previous=columns.get(r.left);if(previous)assert.ok(r.top>=previous.top+previous.height+22);columns.set(r.left,r);}
assert.equal(columns.size,3);
ui.begin();flushes=0;ctx.innerWidth=390;ui.render();assert.equal(flushes,2);assert.equal(cards[0].getBoundingClientRect().width,600);assert.equal(cards[1].getBoundingClientRect().top,118);
assert.equal(Number.parseFloat(grid.style.height),cards.at(-1).getBoundingClientRect().top+cards.at(-1).getBoundingClientRect().height);
ui.destroy();console.log('1000-card measured layout uses two bounded flush phases, correct shortest columns and responsive reflow');

const assert=require('node:assert/strict');const {create}=require('../static/desktop-sync');
(async()=>{
 let busy=false,loads=0,applied=[],timer,cleared=false;
 const clock={setInterval(fn){timer=fn;return 1;},clearInterval(){cleared=true;},setTimeout(){return 2;},clearTimeout(){}};
 let data={resources:[{id:'a'}]};
 const ui=create({clock,busy:()=>busy,load:async()=>{loads++;return data;},apply:async value=>applied.push(value)});
 await ui.tick();assert.equal(applied.length,1);await ui.tick();assert.equal(applied.length,1);
 busy=true;data={resources:[{id:'a'},{id:'b'}]};await ui.tick();assert.equal(loads,2);assert.equal(applied.length,1);
 busy=false;await ui.tick();assert.equal(applied.length,2);ui.destroy();await timer();assert.equal(loads,3);assert.ok(cleared);
 let resolve,signal;const late=create({clock,busy:()=>false,load:async s=>{signal=s;return new Promise(r=>resolve=r);},apply:async()=>assert.fail('disposed result')});const pending=late.tick();late.destroy();assert.ok(signal.aborted);resolve({});await pending;
 let block=false;const raced=create({clock,busy:()=>block,load:async()=>{block=true;return {};},apply:async()=>assert.fail('draft opened during fetch')});await raced.tick();raced.destroy();
 console.log('Desktop sync draft guard, race, deduplication, disposal and abort passed');
})().catch(e=>{console.error(e);process.exit(1)});

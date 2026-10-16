'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),Q=require('../static/resource-query');
const tick=()=>new Promise(r=>setImmediate(r));
function setup(){
 const requests=[],grid={setAttribute(){},inert:false},status={textContent:'',hidden:true,append(){}},state={scope:'all',scopeValue:'',filters:{search:''},sort:'new',resources:[{id:'all'}],trash:[],selected:new Set(),selectMode:true,remote:{page:{revision:1},key:JSON.stringify({scope:'all',scopeValue:'',filters:{search:''},sort:'new',limit:60})}};
 const ctx={state,ShijiQuery:Q,AbortController,DOMException,Map,Set,console,setTimeout,clearTimeout,$:s=>s==='#resource-grid'?grid:status,document:{activeElement:null,addEventListener(){}},window:{addEventListener(){}},render(){},toast(){},api:(path,method,body,signal)=>new Promise(resolve=>requests.push({path,body,signal,resolve})),browseWindow:{more(){}},localStorage:{getItem(){return null},setItem(){}}};vm.createContext(ctx);vm.runInContext(fs.readFileSync(require.resolve('../static/query-integration'),'utf8'),ctx);return {ctx,state,requests,run:s=>vm.runInContext(s,ctx)};
}
(async()=>{
 let h=setup();h.run("state.scope='favorite';queryRenderNeeded();state.scope='all';queryRenderNeeded();");h.requests[0].resolve({resources:[{id:'favorite'}],revision:1});await tick();assert.equal(h.state.resources[0].id,'all','Returning to a cached scope invalidates its in-flight predecessor');
 h=setup();h.run("state.scope='favorite';queryRenderNeeded();state.scope='health';queryRenderNeeded();state.scope='favorite';queryRenderNeeded();");assert.equal(h.requests.length,2,'Health cancellation cannot leave a loadingKey that suppresses the next request');h.requests[1].resolve({resources:[{id:'favorite2'}],revision:1});h.requests[0].resolve({resources:[{id:'stale'}],revision:1});await tick();assert.equal(h.state.resources[0].id,'favorite2');
 h=setup();const select=h.run('selectMatching(true)'),deselect=h.run('selectMatching(false)');h.requests[1].resolve({ids:['a','b'],revision:1});await tick();h.requests[0].resolve({ids:['a','b'],revision:1});await Promise.all([select,deselect]);assert.equal(h.state.selected.size,0,'Last selection intent wins independently of response order');
 h=setup();const pending=h.run('selectMatching(true)');h.run('invalidateSelection();state.selectMode=false;state.selected.clear()');h.requests[0].resolve({ids:['a','b'],revision:1});await pending;assert.equal(h.state.selected.size,0,'Ending selection invalidates a pending full-match response');
 h=setup();let opened=0;h.ctx.detail=()=>opened++;const late=h.run("hydratedAction('detail',{id:'all'})");h.run('cancelPendingDetail()');h.requests[0].resolve({resource:{id:'all'},children:[]});await late;assert.equal(opened,0,'cancelled hydration cannot open a late drawer');
 console.log('PASS: cached scope/health cancellation, stale results, selection response ordering and exiting selection');
})().catch(e=>{console.error(e);process.exitCode=1});
// A full-match selection belongs to one query identity, including filters.
{
 const source=require('node:fs').readFileSync(require('node:path').join(__dirname,'../static/query-integration.js'),'utf8');
 const code=source.slice(source.indexOf('function queryRenderNeeded()'),source.indexOf('\nasync function remoteReload'));
 const state={remote:{key:'old',loadingKey:'new'},scope:'all',selected:new Set(['off-page']),selectionAll:{key:'old'}};
 const ctx={state,remoteKey:()=> 'new',queryClient:{cancel(){}},queryBusy(){},remoteLoad:()=>Promise.resolve(),render(){},document:{activeElement:null},$:()=>({}),invalidateSelection(){state.selectionAll=null}};
 require('node:vm').runInNewContext(code+'\nqueryRenderNeeded();',ctx);
 assert.equal(state.selected.size,0,'changing query clears the old full-match selection');assert.equal(state.selectionAll,null);
}

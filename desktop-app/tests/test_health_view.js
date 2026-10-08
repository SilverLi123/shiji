// Run the shipped report renderer, including older reports without sharing fields.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const code=fs.readFileSync(path.join(__dirname,'../static/health.js'),'utf8');
const context={size:n=>`${n} bytes`,esc:v=>String(v??'').replaceAll('<','&lt;')};vm.createContext(context);vm.runInContext(code,context);
const report={checkedAt:'2026-10-03T00:00:00Z',attachments:3,trashAttachments:1,storedBytes:12000,uniqueStoredBytes:4000,sharedBytes:8000,sharedFiles:2,duplicates:[],issues:[],unregisteredFiles:[]};
let html=context.healthReport(report);assert.ok(html.includes('独立文件内容 4000 bytes'));assert.ok(html.includes('2 个附件复用内容'));assert.ok(html.includes('减少重复存储 8000 bytes'));
delete report.sharedBytes;html=context.healthReport(report);assert.ok(!html.includes('undefined'));assert.ok(!html.includes('个附件复用内容'));assert.ok(html.includes('12000 bytes'));
console.log('actual health report sharing statistics and old-report compatibility passed');

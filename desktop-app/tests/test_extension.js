const assert=require('node:assert/strict');const {settings,payload}=require('../browser-extension/utils.js');
assert.deepEqual(settings('http://127.0.0.1:8766/', 'x'.repeat(32)),{base:'http://127.0.0.1:8766',token:'x'.repeat(32)});
for(const bad of ['https://outside.example','http://127.0.0.1.evil.example','http://user:pass@localhost','http://localhost/admin'])assert.throws(()=>settings(bad,'x'.repeat(32)));
assert.throws(()=>settings('http://localhost:8765','short'));assert.throws(()=>payload({url:'chrome://settings'}));
assert.equal(payload({url:'https://reactbits.dev/',title:'React Bits'},'选中文字').selection,'选中文字');
assert.equal(payload({url:'https://example.com/',title:'a'.repeat(400)}).title.length,200);
console.log('PASS: extension loopback settings, credentials rejection and bounded page/selection capture.');

assert.equal(payload({url:'https://example.com/',favicon:'data:image/svg+xml,unsafe',thumbnail:'blob:invalid'}).favicon,'');assert.equal(payload({url:'https://example.com/',thumbnail:'blob:invalid'}).thumbnail,'');

(function(root){
 function status(info){if(!info.enabled)return '自动补全已关闭';if(info.paused)return '已暂停';if(info.running)return '正在读取一个网站…';return info.pending?'等待下一次读取':'本轮已完成';}
 function button(info){return !info.enabled?'开启自动补全':info.paused?'继续补全':'暂停补全';}
 const api={status,button};if(typeof module==='object')module.exports=api;else root.ShijiPreviewUI=api;
})(typeof window==='object'?window:globalThis);

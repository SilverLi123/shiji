"""One preview at a time, default-off, pause-safe and rate limited."""
import json
import threading
import time

class PreviewOperations:
    def init_previews(self):
        with self.connect() as c:
            row=c.execute('SELECT value FROM settings WHERE key="websitePreviews"').fetchone()
        self._preview_config=json.loads(row['value']) if row else {'enabled':False,'paused':False,'interval':30}
        self._preview_generation=0;self._preview_attempted=set();self._preview_next=0;self._preview_busy=False;self._preview_done=0;self._preview_failures=[];self._preview_stop=threading.Event();self._preview_step_lock=threading.Lock()
    def preview_status(self):
        from capture import chrome_binary
        with self.lock:
            pending=sum(1 for r in self.state()['resources'] if r['kind']=='website' and not r['coverId'] and not r['thumbnail'] and (r['id'],r['url']) not in self._preview_attempted)
            return {**self._preview_config,'running':self._preview_busy,'completed':self._preview_done,'pending':pending,'failed':len(self._preview_failures),'failures':self._preview_failures[-5:],'chromeAvailable':bool(chrome_binary())}
    def configure_previews(self,body):
        if not isinstance(body,dict) or set(body)-{'enabled','paused','interval','retry'}:raise ValueError('预览任务选项无效。')
        for key in ('enabled','paused','retry'):
            if key in body and type(body[key]) is not bool:raise ValueError('预览任务选项无效。')
        if 'interval' in body and (type(body['interval']) is not int or not 30<=body['interval']<=3600):raise ValueError('两次预览至少间隔 30 秒。')
        with self.lock,self.connect() as c:
            self._preview_config={**self._preview_config,**{k:v for k,v in body.items() if k!='retry'}};self._preview_generation+=1
            if body.get('retry'):self._preview_attempted.clear();self._preview_failures=[]
            c.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',('websitePreviews',json.dumps(self._preview_config)));self.dirty=True
        return self.preview_status()
    def preview_step(self):
        if not self._preview_step_lock.acquire(False):return False
        try:
            with self.lock:
                cfg=self._preview_config
                if not cfg['enabled'] or cfg['paused'] or time.monotonic()<self._preview_next:return False
                candidates=[r for r in self.state()['resources'] if r['kind']=='website' and not r['coverId'] and not r['thumbnail'] and (r['id'],r['url']) not in self._preview_attempted]
                if not candidates:return False
                # Oldest first, so newly imported batches do not starve earlier items.
                item=candidates[-1];generation=self._preview_generation;self._preview_busy=True
                self._preview_next=time.monotonic()+cfg['interval']
            error=None;result=None
            try:
                from capture import website_preview
                result=website_preview(item['url'])
            except Exception as e:error=str(e) or '预览读取失败。'
            with self.lock:
                # Pausing during I/O discards results. No late cover or attachment writes.
                if generation!=self._preview_generation or not self._preview_config['enabled'] or self._preview_config['paused']:return False
                self._preview_attempted.add((item['id'],item['url']))
                if error:self._preview_failures.append({'id':item['id'],'title':item['title'],'message':error[:200]});return False
                try:latest=self.get(item['id'])
                except ValueError:return False
                if latest['deleted'] or latest['kind']!='website' or latest['url']!=item['url'] or latest['coverId'] or latest['thumbnail'] or latest['thumbnail']!=item['thumbnail']:return False
                raw,url,method=result
                from storage import detect_mime
                if not raw or len(raw)>5*1024*1024 or not detect_mime(raw).startswith('image/'):raise ValueError('预览不是可用图片。')
                self.attachment(item['id'],raw,{'name':'网站预览.png' if method=='Chrome 截图' else '网站预览图','cover':True,'sourceUrl':url,'license':'待确认'})
                self._preview_done+=1;return True
        finally:
            with self.lock:self._preview_busy=False
            self._preview_step_lock.release()
    def start_preview_worker(self):
        if getattr(self,'_preview_worker',None) and self._preview_worker.is_alive():return
        self._preview_stop.clear()
        def run():
            while not self._preview_stop.wait(1):
                try:
                    self.cleanup_restore_staging()
                    self.preview_step()
                except Exception as e:
                    with self.lock:self._preview_failures.append({'id':'','title':'后台预览','message':str(e)[:200]})
        self._preview_worker=threading.Thread(target=run,daemon=True);self._preview_worker.start()
    def stop_preview_worker(self):
        self._preview_stop.set()
        if getattr(self,'_preview_worker',None):self._preview_worker.join(timeout=5)

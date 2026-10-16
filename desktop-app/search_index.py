"""Disposable local search index. SQL triggers only queue IDs, never index content.

Resource/attachment writes by older clients, sync, import and capture remain authoritative.
The optional FTS table is an accelerator; exact literal matching is always rechecked.
"""
from contextlib import contextmanager
import json
import sqlite3
import threading
import time
from datetime import datetime,timezone
from urllib.parse import urlsplit
from search_text import grams

@contextmanager
def write_batch(c):
    c.execute('BEGIN IMMEDIATE')
    try:
        yield c
        c.commit()
    except BaseException:
        c.rollback()
        raise

VERSION='3'

def probe_fts(c):
    try:
        c.execute('CREATE VIRTUAL TABLE temp.shiji_fts_probe USING fts5(tokens, tokenize="unicode61")')
        c.execute("INSERT INTO shiji_fts_probe VALUES('u52a8 b52a8x6548')")
        ok=c.execute("SELECT count(*) FROM shiji_fts_probe WHERE shiji_fts_probe MATCH 'b52a8x6548'").fetchone()[0]==1
        c.execute('DROP TABLE shiji_fts_probe');return ok
    except sqlite3.DatabaseError:return False


def document(item):
    assets=item['attachments']
    fields=[item.get(k,'') for k in ('title','url','description','notes','snippet','author','sourceUrl','category')]
    fields+=item.get('tags',[])+item.get('projects',[])+list(item.get('projectNotes',{}).values())
    for a in assets:fields += [a.get(k,'') for k in ('name','author','sourceUrl')]
    try:domain=(urlsplit(item.get('url','')).hostname or '').encode('idna').decode('ascii').lower().rstrip('.')
    except (ValueError,UnicodeError):domain=''
    try:day=datetime.fromisoformat(item['createdAt'].replace('Z','+00:00')).astimezone(timezone.utc).date().isoformat()
    except (ValueError,KeyError):day=''
    media=set()
    for a in assets:
        typ=a.get('mime','').split('/')[0];media.add(typ if typ in ('image','audio','video') else 'other')
    def stamp(key):
        try:return datetime.fromisoformat(item[key].replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
        except (ValueError,KeyError):return ''
    return (' '.join(str(x) for x in fields).lower(),item.get('title','').lower(),item.get('kind','website'),item.get('category',''),item.get('price',''),item.get('license',''),item.get('linkStatus','unchecked'),int(item.get('favorite',False)),int(item.get('inbox',False)),int(any(str(x or '').strip() for x in [item.get('notes',''),*item.get('projectNotes',{}).values()])),domain,day,stamp('createdAt'),stamp('updatedAt'),json.dumps(item.get('tags',[]),ensure_ascii=False),json.dumps(item.get('projects',[]),ensure_ascii=False),json.dumps(list(dict.fromkeys(item.get('colors',[])+[color for a in assets for color in a.get('colors',[])]))),json.dumps(sorted(media)),len(assets),int(item.get('deleted',False)),item.get('parentId',''))

COLUMNS='text,title,kind,category,price,license,link_status,favorite,inbox,has_notes,domain,created_day,created_at,updated_at,tags,projects,colors,media,asset_count,deleted,parent_id'

class SearchOperations:
    def init_search(self):
        self._search_lock=threading.RLock();self._fts_lock=threading.RLock();self._index_stop=threading.Event();self._index_worker=None
        with self.lock,self.connect() as c:
            self._fts=probe_fts(c)
            self._search_schema(c)

    def _search_schema(self,c):
        c.execute('CREATE INDEX IF NOT EXISTS attachment_resource ON attachments(resource_id,deleted)')
        c.execute('CREATE TABLE IF NOT EXISTS search_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        c.execute("INSERT OR IGNORE INTO search_meta VALUES('revision','0')")
        c.execute('CREATE TABLE IF NOT EXISTS search_dirty(id TEXT PRIMARY KEY)')
        c.execute('CREATE TABLE IF NOT EXISTS search_fts_dirty(id TEXT PRIMARY KEY)')
        existed=c.execute("SELECT 1 FROM sqlite_master WHERE name='search_docs'").fetchone()
        c.execute('CREATE TABLE IF NOT EXISTS search_docs(id TEXT UNIQUE NOT NULL,text TEXT NOT NULL,title TEXT,kind TEXT,category TEXT,price TEXT,license TEXT,link_status TEXT,favorite INTEGER,inbox INTEGER,has_notes INTEGER,domain TEXT,created_day TEXT,created_at TEXT,updated_at TEXT,tags TEXT,projects TEXT,colors TEXT,media TEXT,asset_count INTEGER,deleted INTEGER)')
        if 'parent_id' not in {r[1] for r in c.execute('PRAGMA table_info(search_docs)')}:c.execute("ALTER TABLE search_docs ADD COLUMN parent_id TEXT NOT NULL DEFAULT ''")
        for columns in ('deleted,parent_id,id','deleted,created_at,id','deleted,category,id','deleted,kind,id','deleted,title,id'):
            c.execute('CREATE INDEX IF NOT EXISTS search_'+columns.replace(',','_')+' ON search_docs('+columns+')')
        version=c.execute("SELECT value FROM search_meta WHERE key='version'").fetchone()
        mode=c.execute("SELECT value FROM search_meta WHERE key='fts_enabled'").fetchone()
        stale=not existed or not version or version[0]!=VERSION or not mode or mode[0]!=str(int(self._fts))
        if self._fts:
            try:
                present=c.execute("SELECT 1 FROM sqlite_master WHERE name='search_fts'").fetchone()
                c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS search_fts USING fts5(title_tokens,body_tokens,tokenize="unicode61")')
                if present:
                    c.execute("INSERT INTO search_fts(search_fts) VALUES('integrity-check')")
                    stale=stale or c.execute('SELECT count(*) FROM search_docs').fetchone()[0]!=c.execute('SELECT count(*) FROM search_fts').fetchone()[0]
                else:stale=True
            except sqlite3.DatabaseError:
                c.execute('DROP TABLE IF EXISTS search_fts')
                c.execute('CREATE VIRTUAL TABLE search_fts USING fts5(title_tokens,body_tokens,tokenize="unicode61")');stale=True
        bump="UPDATE search_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision';"
        for table in ('resources','attachments'):
            field='id' if table=='resources' else 'resource_id'
            for op in ('INSERT','UPDATE','DELETE'):
                refs=['NEW'] if op=='INSERT' else ['OLD'] if op=='DELETE' else ['OLD','NEW']
                body=''.join('INSERT INTO search_dirty SELECT '+ref+'.'+field+' WHERE NOT EXISTS(SELECT 1 FROM search_dirty WHERE id='+ref+'.'+field+');' for ref in refs)+bump
                c.execute('CREATE TRIGGER IF NOT EXISTS search_'+table+'_'+op.lower()+' AFTER '+op+' ON '+table+' BEGIN '+body+' END')
        for table in ('collections','smart_collections'):
            for op in ('INSERT','UPDATE','DELETE'):
                c.execute('CREATE TRIGGER IF NOT EXISTS search_'+table+'_'+op.lower()+' AFTER '+op+' ON '+table+' BEGIN '+bump+' END')
        # Missing derived rows are recoverable even after an older restore/replacement.
        c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM resources WHERE id NOT IN (SELECT id FROM search_docs)')
        c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM search_docs WHERE id NOT IN (SELECT id FROM resources)')
        if stale:
            c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM resources')
            c.execute('INSERT OR IGNORE INTO search_fts_dirty SELECT id FROM search_docs')
        c.execute("INSERT OR REPLACE INTO search_meta VALUES('version',?)",(VERSION,))
        c.execute("INSERT OR REPLACE INTO search_meta VALUES('fts_enabled',?)",(str(int(self._fts)),))

    def search_capabilities(self):
        with self.connect() as c:pending=c.execute('SELECT count(*) FROM search_fts_dirty').fetchone()[0]
        return {'fts5':self._fts,'tokenizer':'application-unigram-bigram','version':VERSION,'derived':True,'indexing':bool(self._fts and pending),'pending':pending}

    def _fts_ready(self,c):return self._fts and not c.execute('SELECT 1 FROM search_fts_dirty LIMIT 1').fetchone()

    def stop_search_worker(self):
        self._index_stop.set()
        if self._index_worker:self._index_worker.join(3)

    def _schedule_fts(self):
        if not self._fts:return
        with self._fts_lock:
            if self._index_worker and self._index_worker.is_alive():return
            self._index_stop.clear()
            def work():
                try:
                    with self.connect() as c:
                        while not self._index_stop.is_set() and self._fts_batch(c):time.sleep(.002)
                except (sqlite3.DatabaseError,OSError):pass # Exact document fallback remains available.
            self._index_worker=threading.Thread(target=work,name='shiji-search-index',daemon=True);self._index_worker.start()

    def _fts_batch(self,connection=None,limit=32):
        if connection is None:
            with self.connect() as c:return self._fts_batch(c,limit)
        with self._fts_lock,self.lock,write_batch(connection) as c:
            ids=[r[0] for r in c.execute('SELECT id FROM search_fts_dirty LIMIT ?',(limit,))]
            if not ids:return False
            for rid in ids:
                row=c.execute('SELECT rowid,title,text FROM search_docs WHERE id=?',(rid,)).fetchone()
                if row:
                    c.execute('DELETE FROM search_fts WHERE rowid=?',(row['rowid'],))
                    c.execute('INSERT INTO search_fts(rowid,title_tokens,body_tokens) VALUES(?,?,?)',(row['rowid'],grams(row['title']),grams(row['text'])))
                # Deleted document FTS entries are removed by the document flush before its rowid disappears.
                c.execute('DELETE FROM search_fts_dirty WHERE id=?',(rid,))
            return True

    def search_damage_repairable(self):
        """Diagnose only after an error. Never infer canonical safety from error wording."""
        with self.lock,self.connect() as c:
            for table in ('resources','attachments','collections','resource_projects','smart_collections','settings','capture_jobs','clip_receipts','asset_receipts','capture_control'):
                if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(table,)).fetchone():continue
                try:
                    if any(r[0]!='ok' for r in c.execute('PRAGMA integrity_check('+table+')')):return False
                    if table in ('resources','attachments'):
                        for row in c.execute('SELECT payload FROM '+table):json.loads(row[0])
                except (sqlite3.DatabaseError,ValueError):return False
            for table in ('search_meta','search_dirty','search_docs','search_fts_dirty'):
                if not c.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():return True
            try:
                c.execute('SELECT id,text FROM search_docs').fetchall()
                if self._fts:c.execute("INSERT INTO search_fts(search_fts) VALUES('integrity-check')")
            except sqlite3.DatabaseError:return True
        return False

    def rebuild_search(self,wait_fts=True):
        with self._search_lock,self._fts_lock:
            with self.lock,self.connect() as c:
                c.execute('DELETE FROM search_docs')
                c.execute('DELETE FROM search_fts_dirty')
                if self._fts:
                    c.execute('DROP TABLE IF EXISTS search_fts')
                    c.execute('CREATE VIRTUAL TABLE search_fts USING fts5(title_tokens,body_tokens,tokenize="unicode61")')
                c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM resources')
                c.execute("UPDATE search_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            self._query_counts={};self._library_meta={}
            self.flush_search(wait_fts=wait_fts)

    def flush_search(self,wait_fts=True):
        with self._search_lock,self.connect() as c:
            while True:
                # Short, atomic batches: no network, no lock held across the full rebuild.
                with self.lock,write_batch(c):
                    ids=[r[0] for r in c.execute('SELECT id FROM search_dirty LIMIT 128')]
                    if not ids:break
                    marks=','.join('?'*len(ids))
                    rows=c.execute('SELECT * FROM resources WHERE id IN ('+marks+')',ids).fetchall()
                    items={r['id']:r for r in self._read_many(c,rows)}
                    for rid in ids:
                        old=c.execute('SELECT rowid FROM search_docs WHERE id=?',(rid,)).fetchone()
                        if old and self._fts and rid not in items:c.execute('DELETE FROM search_fts WHERE rowid=?',(old[0],))
                        if rid not in items:
                            c.execute('DELETE FROM search_docs WHERE id=?',(rid,));continue
                        doc=document(items[rid])
                        c.execute('INSERT INTO search_docs(id,'+COLUMNS+') VALUES('+','.join('?'*22)+') ON CONFLICT(id) DO UPDATE SET '+','.join(k+'=excluded.'+k for k in COLUMNS.split(',')),(rid,)+doc)
                        c.execute('INSERT OR IGNORE INTO search_fts_dirty VALUES(?)',(rid,))
                    c.execute('DELETE FROM search_dirty WHERE id IN ('+marks+')',ids)

        if self._fts:
            with self.connect() as c:pending=c.execute('SELECT count(*) FROM search_fts_dirty').fetchone()[0]
            if wait_fts or pending<=128:
                with self.connect() as c:
                    while self._fts_batch(c,128):pass
            else:self._schedule_fts()

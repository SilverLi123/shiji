"""Disposable local search index. SQL triggers only queue IDs, never index content.

Resource/attachment writes by older clients, sync, import and capture remain authoritative.
The optional FTS table is an accelerator; exact literal matching is always rechecked.
"""
import json
import sqlite3
import threading
from datetime import datetime,timezone
from urllib.parse import urlsplit
from search_text import grams

VERSION='2'

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
        self._search_lock=threading.RLock()
        with self.lock,self.connect() as c:
            self._fts=probe_fts(c)
            self._search_schema(c)

    def _search_schema(self,c):
        c.execute('CREATE INDEX IF NOT EXISTS attachment_resource ON attachments(resource_id,deleted)')
        c.execute('CREATE TABLE IF NOT EXISTS search_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        c.execute("INSERT OR IGNORE INTO search_meta VALUES('revision','0')")
        c.execute('CREATE TABLE IF NOT EXISTS search_dirty(id TEXT PRIMARY KEY)')
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
        if stale:c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM resources')
        c.execute("INSERT OR REPLACE INTO search_meta VALUES('version',?)",(VERSION,))
        c.execute("INSERT OR REPLACE INTO search_meta VALUES('fts_enabled',?)",(str(int(self._fts)),))

    def search_capabilities(self):return {'fts5':self._fts,'tokenizer':'application-unigram-bigram','version':VERSION,'derived':True}

    def rebuild_search(self):
        with self._search_lock:
            with self.lock,self.connect() as c:
                c.execute('DELETE FROM search_docs')
                if self._fts:
                    c.execute('DROP TABLE IF EXISTS search_fts')
                    c.execute('CREATE VIRTUAL TABLE search_fts USING fts5(title_tokens,body_tokens,tokenize="unicode61")')
                c.execute('INSERT OR IGNORE INTO search_dirty SELECT id FROM resources')
                c.execute("UPDATE search_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            self.flush_search()

    def flush_search(self):
        with self._search_lock:
            while True:
                # Short, atomic batches: no network, no lock held across the full rebuild.
                with self.lock,self.connect() as c:
                    c.execute('BEGIN IMMEDIATE')
                    ids=[r[0] for r in c.execute('SELECT id FROM search_dirty LIMIT 128')]
                    if not ids:return
                    marks=','.join('?'*len(ids))
                    rows=c.execute('SELECT * FROM resources WHERE id IN ('+marks+')',ids).fetchall()
                    items={r['id']:r for r in self._read_many(c,rows)}
                    for rid in ids:
                        old=c.execute('SELECT rowid FROM search_docs WHERE id=?',(rid,)).fetchone()
                        if old and self._fts:c.execute('DELETE FROM search_fts WHERE rowid=?',(old[0],))
                        if rid not in items:
                            c.execute('DELETE FROM search_docs WHERE id=?',(rid,));continue
                        doc=document(items[rid])
                        c.execute('INSERT INTO search_docs(id,'+COLUMNS+') VALUES('+','.join('?'*22)+') ON CONFLICT(id) DO UPDATE SET '+','.join(k+'=excluded.'+k for k in COLUMNS.split(',')),(rid,)+doc)
                        if self._fts:
                            rowid=c.execute('SELECT rowid FROM search_docs WHERE id=?',(rid,)).fetchone()[0]
                            c.execute('INSERT INTO search_fts(rowid,title_tokens,body_tokens) VALUES(?,?,?)',(rowid,grams(doc[1]),grams(doc[0])))
                    c.execute('DELETE FROM search_dirty WHERE id IN ('+marks+')',ids)

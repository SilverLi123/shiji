"""Record runtime capabilities and actual short-token behavior, in memory only."""
import json
import sqlite3

c=sqlite3.connect(':memory:')
result={'sqlite':sqlite3.sqlite_version,'compileOptions':[r[0] for r in c.execute('PRAGMA compile_options')],'tokenizers':{}}
for tokenizer in ('unicode61','trigram'):
    try:
        c.execute('CREATE VIRTUAL TABLE probe USING fts5(text,tokenize="'+tokenizer+'")')
        c.execute('INSERT INTO probe VALUES(?)',('动效组件 React useState C++ foo::bar',))
        matches={term:c.execute('SELECT count(*) FROM probe WHERE probe MATCH ?',('"'+term+'"',)).fetchone()[0] for term in ('动','动效','动效组','React','C++','foo::bar')}
        result['tokenizers'][tokenizer]={'available':True,'matches':matches}
        c.execute('DROP TABLE probe')
    except sqlite3.Error as error:result['tokenizers'][tokenizer]={'available':False,'error':str(error)}
print(json.dumps(result,ensure_ascii=False,indent=2))

"""Literal search grammar and portable Unicode gram candidates (no user FTS syntax)."""
import re

MAX_QUERY=200

def parse_terms(query):
    if not isinstance(query,str) or len(query)>MAX_QUERY:raise ValueError('搜索内容须为不超过 200 字的文字。')
    # Paired quotes group a phrase; backslashes, operators and code symbols stay literal.
    return list(dict.fromkeys((a or b).lower() for a,b in re.findall(r'"([^"\n]+)"|([^\s]+)',query) if a or b))

def grams(text):
    text=text.lower()
    return ' '.join(sorted({'u'+format(ord(ch),'x') for ch in text} | {'b'+format(ord(a),'x')+'x'+format(ord(b),'x') for a,b in zip(text,text[1:])}))

def gram_query(terms):
    tokens=set()
    for term in terms:
        # Bigrams constrain long words, unigrams support single-character Chinese/symbols.
        tokens.update(grams(term).split())
    return ' AND '.join('"'+t+'"' for t in sorted(tokens))

def highlight_ranges(value,terms):
    # Indices are Unicode code points, not UTF-16 offsets; include lowercase expansions.
    folded='';positions=[]
    for i,ch in enumerate(value):
        lower=ch.lower();folded+=lower;positions.extend([i]*len(lower))
    spans=[]
    for term in terms:
        start=0
        while term:
            p=folded.find(term,start)
            if p<0:break
            spans.append([positions[p],positions[p+len(term)-1]+1]);start=p+len(term)
    result=[]
    for a,b in sorted(spans):
        if result and a<=result[-1][1]:result[-1][1]=max(b,result[-1][1])
        else:result.append([a,b])
    return result

import gzip, re, ssl, sys, urllib.request, html as H
from datetime import datetime, timezone
UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
def get(u):
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'text/html,*/*','Accept-Encoding':'gzip'})
    with urllib.request.urlopen(r, timeout=25, context=CTX) as resp:
        b=resp.read()
        if resp.headers.get('Content-Encoding')=='gzip': b=gzip.decompress(b)
        return resp.status, b, resp.geturl()
TAGS=re.compile(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>')
def paras(b):
    s=TAGS.sub(' ', b.decode('utf-8','replace'))
    out=[]
    for m in re.finditer(r'(?is)<(p|li|h2|h3)\b[^>]*>(.*?)</\1>', s):
        t=' '.join(H.unescape(re.sub(r'<[^>]+>',' ',m.group(2))).split())
        if t: out.append((m.group(1), t))
    return out
for u in sys.argv[1:]:
    try:
        st,b,fin=get(u)
        print(f'### {st}  {fin}   ({len(b)} bytes)')
        ps=paras(b)
        print(f'    {len(ps)} block elements')
        for tag,t in ps:
            if re.search(r'2011/833|creative commons|CC BY|reus[ea]|copyright notice', t, re.I):
                print(f'    [{tag}] {t[:700]}')
        print()
    except Exception as e:
        print(f'### ERR {u} {type(e).__name__} {str(e)[:70]}')

import sys, ssl, urllib.request, urllib.error, gzip, re
UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
def probe(u):
    r = urllib.request.Request(u, headers={'User-Agent':UA,
        'Accept':'application/rss+xml,application/atom+xml,application/xml,text/xml,*/*',
        'Accept-Encoding':'gzip'})
    try:
        with urllib.request.urlopen(r, timeout=20, context=CTX) as resp:
            b=resp.read()
            if resp.headers.get('Content-Encoding')=='gzip': b=gzip.decompress(b)
            kind='FEED' if re.match(rb'\s*(<\?xml|<rss|<feed|<rdf)', b, re.I) else 'not-xml'
            n=b.count(b'<item')+b.count(b'<entry')
            print(f'  {resp.status} {kind:<7} {len(b):>7}b items~{n:<4} {resp.geturl()[:96]}')
            if kind!='FEED':
                print(f'        head: {b[:80].decode("utf-8","replace").replace(chr(10)," ")}')
    except urllib.error.HTTPError as e:
        print(f'  {e.code} {"":<7} {"":>7}            {u[:96]}')
    except Exception as e:
        print(f'  ERR {type(e).__name__:<7} {"":>7}        {u[:70]}  {str(e)[:50]}')
for u in sys.argv[1:]: probe(u)

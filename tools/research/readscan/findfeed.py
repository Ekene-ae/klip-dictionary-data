import sys, ssl, urllib.request, urllib.error, gzip, re
UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
def get(u):
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':'text/html,*/*','Accept-Encoding':'gzip'})
    with urllib.request.urlopen(r, timeout=20, context=CTX) as resp:
        b=resp.read()
        if resp.headers.get('Content-Encoding')=='gzip': b=gzip.decompress(b)
        return resp.status, b, resp.geturl()
for u in sys.argv[1:]:
    try:
        st,b,fin=get(u)
        s=b.decode('utf-8','replace')
        links=set()
        for m in re.finditer(r'<link[^>]+type=["\']application/(?:rss|atom)\+xml["\'][^>]*>', s, re.I):
            h=re.search(r'href=["\']([^"\']+)["\']', m.group(0))
            if h: links.add(h.group(1))
        for m in re.finditer(r'href=["\']([^"\']*(?:rss|feed|atom)[^"\']*)["\']', s, re.I):
            if len(m.group(1))<140: links.add(m.group(1))
        print(f'{st} {fin[:80]}  ({len(b)}b)')
        for l in sorted(links)[:14]: print('    ', l)
        if not links: print('     (no rss/feed/atom link found in the HTML)')
    except urllib.error.HTTPError as e: print(f'{e.code} {u}')
    except Exception as e: print(f'ERR {u} {type(e).__name__} {str(e)[:60]}')

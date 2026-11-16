import gzip, re, ssl, sys, urllib.request, urllib.error, html as H
UA=('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
CTX=ssl.create_default_context()
def get(u, accept='*/*'):
    r=urllib.request.Request(u, headers={'User-Agent':UA,'Accept':accept,'Accept-Encoding':'gzip'})
    with urllib.request.urlopen(r, timeout=25, context=CTX) as resp:
        b=resp.read()
        if resp.headers.get('Content-Encoding')=='gzip':
            try: b=gzip.decompress(b)
            except Exception: pass
        return resp.status, b, resp.geturl(), dict(resp.headers)
if __name__=='__main__':
    for u in sys.argv[1:]:
        try:
            st,b,fin,h=get(u)
            print(f'  {st} {len(b):>8}b  {h.get("Content-Type","")[:34]:<34} {fin[:80]}')
            print(f'        {b[:110].decode("utf-8","replace").replace(chr(10)," ")}')
        except urllib.error.HTTPError as e: print(f'  {e.code} {"":>8}   {u[:90]}')
        except Exception as e: print(f'  ERR {type(e).__name__} {u[:70]} {str(e)[:40]}')

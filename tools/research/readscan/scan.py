#!/usr/bin/env python3 -I
"""readscan — the Read starter list's INPUT MEASUREMENT.

OUTSIDE THE KLIP REPOSITORY, BY RULING. Nothing here is imported by the app
and no list is built from it: this produces the data a starter list will later
be CHOSEN from, which is the same split podscan/ holds for the Listen door.

STDLIB ONLY, RUN UNDER `python3 -I`. No third-party packages, no site-packages.

PERSISTED PER FEED so it never needs re-running: feeds/<slug>.json. A feed
already on disk is SKIPPED unless --refresh names it. A measurement that costs
a fetch should cost it once.

WHAT IS MEASURED, AND THE ONE DEFINITION THAT MATTERS
-----------------------------------------------------
FULL TEXT = the item carries `content:encoded` (RSS) or `<content>` (Atom)
whose HTML-STRIPPED, WHITESPACE-COLLAPSED length is > 1,500 characters.

Stripped, not raw. The Listen starter list measured transcript coverage by
counting `podcast:transcript` TAGS and three feeds read 100% while carrying
nothing Klip could use; the criterion was superseded the same day to "formats
Klip can read". Raw HTML length is that same error in a new place — a 2,000-byte
`<div>` wrapper around a 200-character teaser is not full text. Both figures
are recorded; the verdict uses the stripped one.
"""
import gzip, io, json, os, re, ssl, sys, time, urllib.error, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

BASE = os.path.expanduser('~/dict-work/readscan')
FEEDS = os.path.join(BASE, 'feeds')
RAW   = os.path.join(BASE, 'raw')
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
FULLTEXT_CHARS = 1500
TIMEOUT = 25

NS = {
  'content': 'http://purl.org/rss/1.0/modules/content/',
  'dc':      'http://purl.org/dc/elements/1.1/',
  'atom':    'http://www.w3.org/2005/Atom',
  'rdf':     'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
  'rss1':    'http://purl.org/rss/1.0/',
}

def slug(s):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')[:90]

def fetch(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
        'Accept-Encoding': 'gzip',
        'Accept-Language': 'en,da,de,fr,es,it;q=0.8',
    })
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
        body = r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            body = gzip.decompress(body)
        return r.status, dict(r.headers), body, r.geturl()

TAG = re.compile(r'(?is)<(script|style)[^>]*>.*?</\1>|<[^>]+>')
ENT = re.compile(r'&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);')
import html as _html
def strip_html(s):
    if not s: return ''
    s = TAG.sub(' ', s)
    s = _html.unescape(s)
    return ' '.join(s.split())

def local(tag):
    return tag.rsplit('}', 1)[-1] if '}' in tag else tag

def first_text(el, names):
    for ch in el:
        if local(ch.tag) in names:
            t = ''.join(ch.itertext())
            if t and t.strip(): return t.strip()
    return None

def parse_date(s):
    if not s: return None
    s = s.strip()
    for f in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%f%z',
              '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d', '%Y-%m-%dT%H:%M%z'):
        try:
            d = datetime.strptime(s.replace('Z', '+0000') if f.endswith('%z') and s.endswith('Z') else s, f)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    try:
        d = parsedate_to_datetime(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        pass
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]), tzinfo=timezone.utc)
    return None

def measure(url, expect_lang, group, label):
    rec = {'label': label, 'group': group, 'url': url, 'expect_lang': expect_lang,
           'fetched_at': datetime.now(timezone.utc).isoformat(timespec='seconds')}
    try:
        status, hdrs, body, final = fetch(url)
    except urllib.error.HTTPError as e:
        rec.update(ok=False, error=f'HTTP {e.code}', http=e.code); return rec
    except Exception as e:
        rec.update(ok=False, error=f'{type(e).__name__}: {e}'[:160]); return rec
    rec['http'] = status
    rec['final_url'] = final
    rec['content_type'] = hdrs.get('Content-Type', '')
    rec['bytes'] = len(body)
    open(os.path.join(RAW, slug(label) + '.xml'), 'wb').write(body)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as e:
        rec.update(ok=False, error=f'ParseError: {e}'[:160]); return rec

    rt = local(root.tag)
    if rt == 'feed':
        dialect, items_parent, item_tag = 'Atom', root, 'entry'
    elif rt == 'rss':
        ch = root.find('channel')
        if ch is None:
            rec.update(ok=False, error='rss without <channel>'); return rec
        dialect, items_parent, item_tag = 'RSS', ch, 'item'
    elif rt == 'RDF':
        dialect, items_parent, item_tag = 'RSS1', root, 'item'
    else:
        rec.update(ok=False, error=f'not a feed: root <{rt}>'); return rec
    rec['dialect'] = dialect

    # ── declared language ──
    lang = None
    if dialect == 'Atom':
        lang = root.get('{http://www.w3.org/XML/1998/namespace}lang')
    if not lang:
        lang = first_text(items_parent, {'language'})
    if not lang:
        for ch in items_parent.iter():
            if local(ch.tag) == 'language' and (ch.text or '').strip():
                lang = ch.text.strip(); break
    rec['declared_lang'] = lang
    rec['declared_lang_base'] = (re.split(r'[-_]', lang)[0].lower() if lang else None)
    rec['lang_confirmed'] = (rec['declared_lang_base'] == expect_lang) if lang else False

    rec['title'] = first_text(items_parent, {'title'})
    # ── licence / terms, if stated ──
    lic = None
    for n in ('copyright', 'rights'):
        lic = lic or first_text(items_parent, {n})
    if not lic:
        for ch in items_parent.iter():
            if local(ch.tag) in ('rights', 'copyright', 'license', 'licence') and (ch.text or '').strip():
                lic = ch.text.strip(); break
    rec['licence_line'] = (strip_html(lic)[:300] if lic else None)

    # ── items ──
    items = [e for e in items_parent if local(e.tag) == item_tag]
    if dialect == 'RSS1':
        items = [e for e in root.iter() if local(e.tag) == 'item']
    rec['items'] = len(items)
    full = 0; dates = []; chars = []; raws = []; ids = []
    dchars = []; dfull = 0
    now = datetime.now(timezone.utc)
    last90 = 0
    for it in items:
        ctext = None
        for ch in it:
            if local(ch.tag) == 'encoded':                 # content:encoded
                ctext = ''.join(ch.itertext()); break
        if ctext is None and dialect == 'Atom':
            for ch in it:
                if local(ch.tag) == 'content':
                    ctext = ''.join(ch.itertext()); break
        if ctext is None:
            for ch in it:                                   # RSS1 / dc fallback
                if local(ch.tag) in ('description',) and dialect == 'RSS1':
                    ctext = ''.join(ch.itertext()); break
        n_raw = len(ctext or '')
        n = len(strip_html(ctext))
        raws.append(n_raw); chars.append(n)
        if n > FULLTEXT_CHARS: full += 1
        # ── AND THE SAME TEST ON <description> / <summary> ──────────────────
        # The owner's definition names content:encoded / Atom <content>. But the
        # EU press corner puts its whole text in <description> and scores 0% on
        # that definition while carrying full articles. A feed whose TEXT IS
        # THERE in a different element is not "no full text" — it is full text
        # Klip would have to read from somewhere else. BOTH are recorded; the
        # headline verdict stays on the ruled definition.
        dtext = None
        for ch in it:
            if local(ch.tag) in ('description', 'summary'):
                dtext = ''.join(ch.itertext()); break
        dn = len(strip_html(dtext))
        dchars.append(dn)
        if dn > FULLTEXT_CHARS: dfull += 1
        d = parse_date(first_text(it, {'pubDate', 'updated', 'published', 'date'}))
        if d:
            dates.append(d)
            if (now - d) <= timedelta(days=90): last90 += 1
        iid = first_text(it, {'guid', 'id'}) or first_text(it, {'link'})
        if iid is None:
            for ch in it:
                if local(ch.tag) == 'link' and ch.get('href'): iid = ch.get('href'); break
        ids.append(iid)
    rec['full_text_items'] = full
    rec['full_text_pct'] = round(100.0 * full / len(items), 1) if items else None
    rec['median_chars'] = sorted(chars)[len(chars)//2] if chars else None
    rec['max_chars'] = max(chars) if chars else None
    rec['median_raw_chars'] = sorted(raws)[len(raws)//2] if raws else None
    rec['latest_item'] = max(dates).date().isoformat() if dates else None
    rec['items_last_90d'] = last90
    rec['desc_full_items'] = dfull
    rec['desc_full_pct'] = round(100.0 * dfull / len(items), 1) if items else None
    rec['median_desc_chars'] = sorted(dchars)[len(dchars)//2] if dchars else None
    rec['max_desc_chars'] = max(dchars) if dchars else None
    rec['item_ids'] = [i for i in ids if i][:60]
    rec['ok'] = True
    return rec

def run(cands, refresh=False):
    done = 0; skipped = 0
    for (group, lang, label, url) in cands:
        p = os.path.join(FEEDS, slug(label) + '.json')
        if os.path.exists(p) and not refresh:
            skipped += 1; continue
        rec = measure(url, lang, group, label)
        rec['lang'] = lang
        json.dump(rec, open(p, 'w'), ensure_ascii=False, indent=1)
        flag = 'ok ' if rec.get('ok') else 'ERR'
        print(f"  {flag} {label:<46} {rec.get('dialect','-'):<5} "
              f"items={rec.get('items','-'):<4} full={rec.get('full_text_pct','-')}% "
              f"lang={rec.get('declared_lang_base')} {rec.get('error','')}", flush=True)
        done += 1
        time.sleep(1.1)          # one request a second; nobody's server is a target
    print(f'-- fetched {done}, skipped (already on disk) {skipped}')

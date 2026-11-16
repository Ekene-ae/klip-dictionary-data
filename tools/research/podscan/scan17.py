#!/usr/bin/env python3
"""Transcript availability for the remaining 17 Klip languages. OUTSIDE THE REPO.

Same instrument as scan.py: candidates from Apple's keyless search, LANGUAGE
CONFIRMED FROM EACH FEED'S OWN <language> TAG, transcript presence and type
read from the live RSS.

**THE METHOD IS DELIBERATELY SMALLER THAN THE da/en RUN AND THE NUMBERS MUST
SAY SO.** da/en used 24 search terms at limit=200 with a 2 MB read cap, which
cost ~4,300 feed fetches. Repeating that for 17 languages is ~35,000 fetches
and tens of GB of transfer. This run uses 12 terms at limit=150 with a 400 KB
cap. RATES stay comparable (they are ratios over a few hundred confirmed
feeds each); ABSOLUTE feed counts and tag totals are smaller by construction
and are NOT comparable to da/en's.
"""
import json, re, sys, time, gzip, io, urllib.parse
import urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

UA = 'KlipAudioIngestSizing/1.0 (+sizing transcript availability for a language-learning app)'
TRANSCRIPT = re.compile(rb'<podcast:transcript\b[^>]*', re.I)
TYPE_ATTR  = re.compile(rb'type\s*=\s*["\']([^"\']+)["\']', re.I)
LANG_TAG   = re.compile(rb'<language>\s*([^<\s]+)', re.I)
ITEM       = re.compile(rb'<item[\s>]', re.I)
CAP = 400_000

LANGS = {
 'ar': ('sa', ['بودكاست','أخبار','تاريخ','مجتمع','رياضة','ثقافة','صحة','تقنية','علوم','أعمال','قصص','تعليم']),
 'de': ('de', ['podcast','nachrichten','geschichte','gesellschaft','sport','kultur','gesundheit','technik','wissenschaft','wirtschaft','krimi','kinder']),
 'el': ('gr', ['podcast','ειδήσεις','ιστορία','κοινωνία','αθλητικά','πολιτισμός','υγεία','τεχνολογία','επιστήμη','οικονομία','παιδιά','μουσική']),
 'es': ('es', ['podcast','noticias','historia','sociedad','deporte','cultura','salud','tecnología','ciencia','negocios','crimen','niños']),
 'fr': ('fr', ['podcast','actualités','histoire','société','sport','culture','santé','technologie','science','économie','polar','enfants']),
 'hi': ('in', ['पॉडकास्ट','समाचार','इतिहास','समाज','खेल','संस्कृति','स्वास्थ्य','विज्ञान','कहानी','व्यापार','बच्चे','संगीत']),
 'it': ('it', ['podcast','notizie','storia','società','sport','cultura','salute','tecnologia','scienza','economia','giallo','bambini']),
 'ja': ('jp', ['ポッドキャスト','ニュース','歴史','社会','スポーツ','文化','健康','テクノロジー','科学','ビジネス','子ども','音楽']),
 'ko': ('kr', ['팟캐스트','뉴스','역사','사회','스포츠','문화','건강','기술','과학','비즈니스','아이','음악']),
 'nl': ('nl', ['podcast','nieuws','geschiedenis','samenleving','sport','cultuur','gezondheid','technologie','wetenschap','economie','misdaad','kinderen']),
 'no': ('no', ['podkast','nyheter','historie','samfunn','sport','kultur','helse','teknologi','vitenskap','økonomi','krim','barn']),
 'pl': ('pl', ['podcast','wiadomości','historia','społeczeństwo','sport','kultura','zdrowie','technologia','nauka','biznes','kryminał','dzieci']),
 'pt': ('pt', ['podcast','notícias','história','sociedade','desporto','cultura','saúde','tecnologia','ciência','negócios','crime','crianças']),
 'ru': ('ru', ['подкаст','новости','история','общество','спорт','культура','здоровье','технологии','наука','бизнес','детектив','дети']),
 'sv': ('se', ['podcast','nyheter','historia','samhälle','sport','kultur','hälsa','teknik','vetenskap','ekonomi','krim','barn']),
 'tr': ('tr', ['podcast','haber','tarih','toplum','spor','kültür','sağlık','teknoloji','bilim','iş','polisiye','çocuk']),
 'zh': ('tw', ['播客','新聞','歷史','社會','運動','文化','健康','科技','科學','商業','故事','兒童']),
}

def get(url, cap=None, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'gzip'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(cap) if cap else r.read()
        if r.headers.get('Content-Encoding') == 'gzip':
            try: raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
            except Exception: pass
        return raw

def probe(item):
    feed, name = item
    try: raw = get(feed, cap=CAP)
    except Exception as e: return {'feed': feed, 'name': name, 'error': type(e).__name__}
    lm = LANG_TAG.search(raw)
    tags = TRANSCRIPT.findall(raw)
    types = []
    for t in tags:
        m = TYPE_ATTR.search(t)
        types.append(m.group(1).decode('ascii','replace').lower() if m else '(none)')
    return {'feed': feed, 'name': name,
            'lang': lm.group(1).decode('ascii','replace').lower() if lm else '',
            'host': urllib.parse.urlparse(feed).netloc.lower(),
            'items_seen': len(ITEM.findall(raw)),
            'transcript_tags': len(tags), 'types': types}

for code, (country, terms) in LANGS.items():
    feeds = {}
    for t in terms:
        u = ('https://itunes.apple.com/search?term=%s&country=%s&entity=podcast&limit=150'
             % (urllib.parse.quote(t), country))
        try: d = json.loads(get(u).decode('utf-8','replace'))
        except Exception as e:
            print('  %s search %r failed: %s' % (code, t, e), file=sys.stderr); continue
        for r in d.get('results', []):
            f = r.get('feedUrl')
            if f: feeds[f] = r.get('collectionName','')
        time.sleep(0.3)
    rows = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        rows = list(ex.map(probe, list(feeds.items())))
    json.dump(rows, open('%s.json' % code, 'w'))
    ok = [r for r in rows if 'error' not in r]
    inl = [r for r in ok if r.get('lang','').startswith(code)]
    wt = [r for r in inl if r['transcript_tags'] > 0]
    print('%s | candidates %4d | ok %4d | confirmed %4d | with transcripts %3d (%4.1f%%)'
          % (code, len(feeds), len(ok), len(inl), len(wt),
             (100.0*len(wt)/len(inl)) if inl else 0.0), flush=True)
print('ALL 17 DONE')

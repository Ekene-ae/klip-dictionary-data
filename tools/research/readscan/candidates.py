# readscan candidates. (group, lang, label, url)
# URLs are CANDIDATES, not verified endpoints — availability is one of the
# columns being measured, so a 404 is a RESULT and is recorded as one.

A = 'a-broadcaster-press'
B = 'b-easy-language'
C = 'c-eu-institutions'
D = 'd-wikinews'

CANDIDATES = [
 # ── (a) DANISH ────────────────────────────────────────────────────────────
 (A,'da','da-dr-alle-nyheder',      'https://www.dr.dk/nyheder/service/feeds/allenyheder'),
 (A,'da','da-tv2-nyheder',          'https://nyheder.tv2.dk/rss'),
 (A,'da','da-politiken-senestenyt', 'https://politiken.dk/rss/senestenyt.rss'),
 (A,'da','da-information',          'https://www.information.dk/feed'),
 (A,'da','da-berlingske',           'https://www.berlingske.dk/content/rss'),
 (A,'da','da-jyllands-posten',      'https://jyllands-posten.dk/?service=rssfeed'),
 (A,'da','da-kristeligt-dagblad',   'https://www.kristeligt-dagblad.dk/rss'),
 # ── (a) GERMAN ────────────────────────────────────────────────────────────
 (A,'de','de-dw-alle',              'https://rss.dw.com/rdf/rss-de-all'),
 (A,'de','de-tagesschau',           'https://www.tagesschau.de/xml/rss2/'),
 (A,'de','de-zdf-nachrichten',      'https://www.zdf.de/rss/zdf/nachrichten'),
 (A,'de','de-spiegel-schlagzeilen', 'https://www.spiegel.de/schlagzeilen/index.rss'),
 (A,'de','de-zeit-index',           'https://newsfeed.zeit.de/index'),
 (A,'de','de-faz-aktuell',          'https://www.faz.net/rss/aktuell/'),
 (A,'de','de-sueddeutsche-top',     'https://rss.sueddeutsche.de/rss/Topthemen'),
 (A,'de','de-taz',                  'https://taz.de/!p4608;rss/'),
 # ── (a) FRENCH ────────────────────────────────────────────────────────────
 (A,'fr','fr-francetvinfo-titres',  'https://www.francetvinfo.fr/titres.rss'),
 (A,'fr','fr-rfi',                  'https://www.rfi.fr/fr/rss'),
 (A,'fr','fr-france24',             'https://www.france24.com/fr/rss'),
 (A,'fr','fr-lemonde-une',          'https://www.lemonde.fr/rss/une.xml'),
 (A,'fr','fr-liberation',           'https://www.liberation.fr/arc/outboundfeeds/rss/?outputType=xml'),
 (A,'fr','fr-lefigaro-actualites',  'https://www.lefigaro.fr/rss/figaro_actualites.xml'),
 (A,'fr','fr-mediapart',            'https://www.mediapart.fr/articles/feed'),
 # ── (a) SPANISH ───────────────────────────────────────────────────────────
 (A,'es','es-rtve-temas',           'https://api2.rtve.es/rss/temas_noticias.xml'),
 (A,'es','es-elpais-portada',       'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada'),
 (A,'es','es-elmundo-portada',      'https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml'),
 (A,'es','es-20minutos',            'https://www.20minutos.es/rss/'),
 (A,'es','es-eldiario',             'https://www.eldiario.es/rss/'),
 (A,'es','es-lavanguardia-home',    'https://www.lavanguardia.com/rss/home.xml'),
 (A,'es','es-abc-portada',          'https://www.abc.es/rss/feeds/abcPortada.xml'),
 # ── (a) ITALIAN ───────────────────────────────────────────────────────────
 (A,'it','it-rainews-tutti',        'https://www.rainews.it/rss/tutti'),
 (A,'it','it-ansa-sito',            'https://www.ansa.it/sito/ansait_rss.xml'),
 (A,'it','it-corriere-homepage',    'https://xml2.corriereobjects.it/rss/homepage.xml'),
 (A,'it','it-repubblica-homepage',  'https://www.repubblica.it/rss/homepage/rss2.0.xml'),
 (A,'it','it-ilpost',               'https://www.ilpost.it/feed/'),
 (A,'it','it-ilsole24ore-italia',   'https://www.ilsole24ore.com/rss/italia.xml'),
 # ── (a) ENGLISH ───────────────────────────────────────────────────────────
 (A,'en','en-bbc-news',             'https://feeds.bbci.co.uk/news/rss.xml'),
 (A,'en','en-guardian-world',       'https://www.theguardian.com/world/rss'),
 (A,'en','en-npr-1001',             'https://feeds.npr.org/1001/rss.xml'),
 (A,'en','en-abc-au-justin',        'https://www.abc.net.au/news/feed/51120/rss.xml'),
 (A,'en','en-cbc-topstories',       'https://www.cbc.ca/webfeed/rss/rss-topstories'),
 (A,'en','en-skynews-home',         'https://feeds.skynews.com/feeds/rss/home.xml'),
 (A,'en','en-irishtimes-news',      'https://www.irishtimes.com/arc/outboundfeeds/feed-rss/?outputType=xml'),
 # ── (b) EASY-LANGUAGE ─────────────────────────────────────────────────────
 (B,'da','b-da-dr-ligetil',         'https://www.dr.dk/nyheder/service/feeds/ligetil'),
 (B,'de','b-de-nachrichtenleicht',  'https://www.nachrichtenleicht.de/nachrichtenleicht-nachrichten-100-rss.xml'),
 (B,'de','b-de-ndr-einfache',       'https://www.ndr.de/nachrichten/info/Nachrichten-in-einfacher-Sprache,einfachesprache100-rss.xml'),
 (B,'de','b-de-dw-langsam',         'https://rss.dw.com/xml/podcast_langsam-gesprochene-nachrichten'),
 (B,'fr','b-fr-rfi-francais-facile','https://www.rfi.fr/fr/podcasts/journal-en-fran%C3%A7ais-facile/podcast'),
 (B,'en','b-en-newsinlevels',       'https://www.newsinlevels.com/feed/'),
 (B,'en','b-en-breaking-news-eng',  'https://breakingnewsenglish.com/rss.xml'),
 (B,'sv','b-sv-8sidor-REFERENCE',   'https://8sidor.se/feed/'),
 # ── (c) EU INSTITUTIONS ───────────────────────────────────────────────────
 (C,'en','c-ec-presscorner-en',     'https://ec.europa.eu/commission/presscorner/api/rss?language=en'),
 (C,'da','c-ec-presscorner-da',     'https://ec.europa.eu/commission/presscorner/api/rss?language=da'),
 (C,'de','c-ec-presscorner-de',     'https://ec.europa.eu/commission/presscorner/api/rss?language=de'),
 (C,'fr','c-ec-presscorner-fr',     'https://ec.europa.eu/commission/presscorner/api/rss?language=fr'),
 (C,'es','c-ec-presscorner-es',     'https://ec.europa.eu/commission/presscorner/api/rss?language=es'),
 (C,'it','c-ec-presscorner-it',     'https://ec.europa.eu/commission/presscorner/api/rss?language=it'),
 (C,'en','c-ep-topstories-en',      'https://www.europarl.europa.eu/rss/doc/top-stories/en.xml'),
 (C,'da','c-ep-topstories-da',      'https://www.europarl.europa.eu/rss/doc/top-stories/da.xml'),
 (C,'de','c-ep-topstories-de',      'https://www.europarl.europa.eu/rss/doc/top-stories/de.xml'),
 (C,'fr','c-ep-topstories-fr',      'https://www.europarl.europa.eu/rss/doc/top-stories/fr.xml'),
 (C,'es','c-ep-topstories-es',      'https://www.europarl.europa.eu/rss/doc/top-stories/es.xml'),
 (C,'it','c-ep-topstories-it',      'https://www.europarl.europa.eu/rss/doc/top-stories/it.xml'),
 # ── (d) WIKINEWS ──────────────────────────────────────────────────────────
 (D,'da','d-wikinews-da', 'https://da.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
 (D,'de','d-wikinews-de', 'https://de.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
 (D,'fr','d-wikinews-fr', 'https://fr.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
 (D,'es','d-wikinews-es', 'https://es.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
 (D,'it','d-wikinews-it', 'https://it.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
 (D,'en','d-wikinews-en', 'https://en.wikinews.org/w/index.php?title=Special:NewPages&feed=atom&namespace=0'),
]

# ── PASS 2, 2026-11-07: corrected URLs and alternates found by probing.
# The pass-1 failures are KEPT on disk as results (availability is a column).
CANDIDATES_P2 = [
 (A,'de','de-faz-aktuell-notrailingslash','https://www.faz.net/rss/aktuell'),
 (A,'da','da-dr-senestenyt',  'https://www.dr.dk/nyheder/service/feeds/senestenyt'),
 (A,'da','da-dr-indland',     'https://www.dr.dk/nyheder/service/feeds/indland'),
 # Wikinews: Special:NewPages?namespace=0 returns an EMPTY feed. The plain
 # RecentChanges Atom feed is what these wikis actually serve.
 (D,'de','d-wikinews-de-rc','https://de.wikinews.org/w/index.php?title=Special:RecentChanges&feed=atom'),
 (D,'fr','d-wikinews-fr-rc','https://fr.wikinews.org/w/index.php?title=Special:RecentChanges&feed=atom'),
 (D,'es','d-wikinews-es-rc','https://es.wikinews.org/w/index.php?title=Special:RecentChanges&feed=atom'),
 (D,'it','d-wikinews-it-rc','https://it.wikinews.org/w/index.php?title=Special:RecentChanges&feed=atom'),
 (D,'en','d-wikinews-en-rc','https://en.wikinews.org/w/index.php?title=Special:RecentChanges&feed=atom'),
]

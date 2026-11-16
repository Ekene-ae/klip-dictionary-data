import json
W=['da','de','fr','es','it','en']
R={w: json.load(open('wiki/%s.json'%w)) for w in W}
M={w: json.load(open('wiki/%s_mostread.json'%w)) for w in W}
L=[]
a=L.append
a('='*108)
a('readscan 3 (a) ADDENDUM — MOST-READ vs RANDOM.  featured feed `mostread`, 2026-11-06, up to 50 per wiki')
a('    RANDOM is the BASELINE: what the encyclopaedia CONTAINS.')
a('    MOSTREAD is THE END-OF-PIPELINE FIGURE: what a reader actually OPENS.')
a('    Same measures, same bar (READABLE = >=1,200 plain chars AND >=3 paragraphs).')
a('='*108)
a('')
a('%-7s%38s  %s' % ('', '-------- RANDOM (baseline) --------', '------- MOSTREAD (end of pipeline) -------'))
a('%-7s%4s%10s%8s%7s  |  %4s%10s%8s%7s%12s' % ('WIKI','n','READABLE','MEDIAN','MED P','n','READABLE','MEDIAN','MED P','VIEWS/med'))
a('-'*108)
for w in W:
    r,m=R[w],M[w]
    a('%-7s%4d%9.1f%%%8d%7d  |  %4d%9.1f%%%8d%7d%12d' % (
        w, r['measured_n'], r['readable_pct'], r['median_chars'], r['median_paragraphs'],
        m['measured_n'], m['readable_pct'], m['median_chars'], m['median_paragraphs'], m['median_views']))
a('')
a('THE SHIFT, STATED AS A SHIFT')
a('-'*108)
a('%-7s%22s%24s%16s%16s' % ('WIKI','READABLE','MEDIAN CHARS','p25 random','p25 mostread'))
for w in W:
    r,m=R[w],M[w]
    a('%-7s%22s%24s%16d%16d' % (w,
        '%.1f%% -> %.1f%%' % (r['readable_pct'], m['readable_pct']),
        '%d -> %d  (x%.1f)' % (r['median_chars'], m['median_chars'], m['median_chars']/r['median_chars']),
        r['p25_chars'], m['p25_chars']))
a('')
a('n IS 40-44, NOT 50, AND THAT IS THE FEED\'S OWN LIMIT.')
a('  The `mostread` list carries 41-48 articles for these dates, so "50 most-read"')
a('  caps at what the feed publishes; a few extract calls also failed. n is printed')
a('  rather than assumed, and every share above is over n.')
a('')
a('='*108)
a('WHAT THIS CHANGES')
a('='*108)
a('')
a('1. THE BASELINE UNDERSTATED THE READER\'S EXPERIENCE BY A WIDE MARGIN, AND')
a('   DANISH MOST OF ALL. Random Danish articles: 26.1% readable, median 740.')
a('   Most-read Danish articles: 86.4% readable, median 3,226 — FOUR TIMES the')
a('   median and more than three times the readable share. Every wiki moves the')
a('   same way; es, it and en reach 100%.')
a('')
a('   SO §3.12\'s DANISH FINDING NEEDS QUALIFYING, NOT RETRACTING. Danish')
a('   Wikipedia does contain mostly stubs — that is what the baseline measured and')
a('   it stands. But A DANISH READER OPENING WHAT DANISH READERS OPEN gets an')
a('   article 86% of the time. The two numbers answer different questions and the')
a('   document now carries both.')
a('')
a('2. THIS IS THE §1.6 RULE PAYING OFF RATHER THAN BEING BROKEN. The random sample')
a('   was not a carrier test — it measured real plain text at the end of the')
a('   pipeline. It measured THE WRONG POPULATION. "End of the pipeline" is about')
a('   WHAT, and this addendum is about WHO: the distribution a learner actually')
a('   meets, not the distribution the corpus holds.')
a('')
a('   A THIRD LESSON FOR THE SAME RULE, THEN: a measurement can be honest about')
a('   its instrument and still sample the wrong thing.')
a('')
a('3. DANISH\'S MEDIAN VIEW COUNT IS 477 AGAINST ENGLISH\'S 110,123 — a factor of')
a('   230. The most-read Danish article of the day is read by a few hundred people.')
a('   THE ARTICLES ARE GOOD; THE AUDIENCE IS SMALL. That bears on Wikipedia as a')
a('   STARTER SOURCE for Danish — the top of the list is thin, so a "most-read')
a('   today" door would cycle slowly — and it is a fact about the wiki, not about')
a('   Klip.')
a('')
a('4. BOTH FIGURES STAY. The random baseline is what a SEARCH or a random-article')
a('   door would meet; the mostread figure is what a FEATURED or trending door')
a('   would. Klip has not chosen a door, so neither number can be retired.')
open('reports/wikipedia_mostread.txt','w').write('\n'.join(L)+'\n')
print('\n'.join(L))

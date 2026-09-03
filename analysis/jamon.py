import collections
from parse_br import load
from brands import brand
import re
def collapse(p):
    rows=load(p)
    by=collections.defaultdict(list)
    for r in rows: by[r['child']].append(r)
    return {c: dict(child=c,title=rs[0]['title'],brand=brand(rs[0]),
            sessions=max(r['sessions'] for r in rs),units=sum(r['units'] for r in rs),
            sales=sum(r['sales'] for r in rs),bb=max(r['bb'] for r in rs)) for c,rs in by.items()}
A=collapse('data_BusinessReport_2025.csv'); B=collapse('data_BusinessReport_2026ytd.csv')
def cat(d): return {c:a for c,a in d.items() if re.search(r'JAMONER|PORTA ?JAMON|SOPORTE JAMON', a['title'].upper())}
ja, jb = cat(A), cat(B)
TA=sum(a['sales'] for a in ja.values()); TB=sum(b['sales'] for b in jb.values())
SA=sum(a['sessions'] for a in ja.values()); SB=sum(b['sessions'] for b in jb.values())
print(f"CATEGORIA JAMONEROS")
print(f"  2025 completo : {TA:,.0f} EUR | {SA:,.0f} ses | {sum(a['units'] for a in ja.values()):,.0f} uds | {len(ja)} ASINs")
print(f"  2026 YTD      : {TB:,.0f} EUR | {SB:,.0f} ses | {sum(b['units'] for b in jb.values()):,.0f} uds | {len(jb)} ASINs")
print(f"\n{'%cat25':>7}{'%cat26':>7}{'  ':>2}{'Vta25':>9}{'Vta26YTD':>10}{'Ses25':>8}{'Ses26':>8}{'%ses25':>7}{'%ses26':>7}{'BB25':>6}{'BB26':>6}  Titulo")
keys=sorted(set(ja)|set(jb), key=lambda c:-(jb.get(c,{}).get('sales',0)))
z=dict(sales=0,sessions=0,bb=0,units=0,title='')
for c in keys:
    a=ja.get(c,z); b=jb.get(c) or z
    t=(b['title'] or a['title'])[:58]
    print(f"{100*a['sales']/TA:>6.1f}%{100*b['sales']/TB:>6.1f}%  {a['sales']:>9,.0f}{b['sales']:>10,.0f}{a['sessions']:>8,.0f}{b['sessions']:>8,.0f}{100*a['sessions']/SA:>6.1f}%{100*b['sessions']/SB:>6.1f}%{a['bb']:>5.0f}%{b['bb']:>5.0f}%  {t}")

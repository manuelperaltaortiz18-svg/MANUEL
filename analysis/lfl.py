import sys, glob, collections, os, re
from parse_br import load
from brands import brand, SUPPLIER

def asins(paths):
    acc=collections.defaultdict(lambda: dict(sessions=0,units=0,sales=0,bbw=0,title='',brand=''))
    for p in paths:
        rows=load(p); by=collections.defaultdict(list)
        for r in rows: by[r['child']].append(r)
        for c,rs in by.items():
            s=max(r['sessions'] for r in rs)
            a=acc[c]; a['sessions']+=s; a['units']+=sum(r['units'] for r in rs)
            a['sales']+=sum(r['sales'] for r in rs); a['bbw']+=max(r['bb'] for r in rs)*s
            a['title']=rs[0]['title']; a['brand']=brand(rs[0])
    for a in acc.values(): a['bb']=a['bbw']/a['sessions'] if a['sessions'] else 0
    return acc

M25=[f'mensual/2025-{m:02d}.csv' for m in range(1,9)]
M26=[f'mensual/2026-{m:02d}.csv' for m in range(1,9)]
A,B = asins(M25), asins(M26)
def tot(d,f=lambda a:True):
    it=[a for a in d.values() if f(a)]
    s=sum(a['sessions'] for a in it); v=sum(a['sales'] for a in it); u=sum(a['units'] for a in it)
    bb=sum(a['bbw'] for a in it)/s if s else 0
    return dict(ses=s,uds=u,v=v,conv=100*u/s if s else 0,eur=v/s if s else 0,bb=bb,n=len(it))
def pd(n,o): return 100*(n-o)/o if o else float('inf')

print("=== LIKE-FOR-LIKE: ENE-AGO 2025 vs ENE-AGO 2026 ===\n")
ta,tb=tot(A),tot(B)
print(f"{'':<12}{'ene-ago 25':>13}{'ene-ago 26':>13}{'Δ%':>9}")
for k,lab,f in [('v','Ventas EUR','{:,.0f}'),('uds','Unidades','{:,.0f}'),('ses','Sesiones','{:,.0f}'),
                ('conv','Conversion','{:.2f}%'),('eur','EUR/sesion','{:.2f}'),('bb','BuyBox','{:.1f}%')]:
    print(f"{lab:<12}{f.format(ta[k]):>13}{f.format(tb[k]):>13}{pd(tb[k],ta[k]):>+8.1f}%")

print(f"\n{'Marca':<14}{'Vta 25':>11}{'Vta 26':>11}{'Δ%':>8}{'Ses25':>10}{'Ses26':>10}{'Δses%':>8}{'EUR/s25':>8}{'EUR/s26':>8}{'BB25':>7}{'BB26':>7}")
print('-'*112)
brands=sorted({a['brand'] for a in list(A.values())+list(B.values())},
    key=lambda b:-tot(B,lambda a:a['brand']==b)['v'])
for b in brands:
    x,y=tot(A,lambda a:a['brand']==b),tot(B,lambda a:a['brand']==b)
    if max(x['v'],y['v'])<500: continue
    d=f"{pd(y['v'],x['v']):+7.0f}%" if x['v'] else "  nueva"
    ds=f"{pd(y['ses'],x['ses']):+7.0f}%" if x['ses'] else "  nueva"
    print(f"{b:<14}{x['v']:>11,.0f}{y['v']:>11,.0f}{d:>8}{x['ses']:>10,.0f}{y['ses']:>10,.0f}{ds:>8}{x['eur']:>8.2f}{y['eur']:>8.2f}{x['bb']:>6.1f}%{y['bb']:>6.1f}%")

print(f"\n{'Proveedor':<16}{'Vta 25':>11}{'Vta 26':>11}{'Δ%':>8}{'% del total 26':>16}")
print('-'*62)
for p in sorted({SUPPLIER.get(a['brand'],'Otros') for a in B.values()},
        key=lambda p:-tot(B,lambda a:SUPPLIER.get(a['brand'],'Otros')==p)['v']):
    x,y=tot(A,lambda a:SUPPLIER.get(a['brand'],'Otros')==p),tot(B,lambda a:SUPPLIER.get(a['brand'],'Otros')==p)
    d=f"{pd(y['v'],x['v']):+7.0f}%" if x['v'] else "  nueva"
    print(f"{p:<16}{x['v']:>11,.0f}{y['v']:>11,.0f}{d:>8}{100*y['v']/tb['v']:>15.1f}%")

# JAMONEROS ventana identica
JA=lambda a: re.search(r'JAMONER|SOPORTE JAMON|JAMONERA', a['title'].upper())
x,y=tot(A,JA),tot(B,JA)
print(f"\n=== JAMONEROS, ventana identica ene-ago ===")
print(f"  2025: {x['v']:,.0f} EUR | {x['uds']:,.0f} uds | {x['ses']:,.0f} ses | {x['n']} ASINs | BB {x['bb']:.1f}%")
print(f"  2026: {y['v']:,.0f} EUR | {y['uds']:,.0f} uds | {y['ses']:,.0f} ses | {y['n']} ASINs | BB {y['bb']:.1f}%")
print(f"  Δ ventas {pd(y['v'],x['v']):+.1f}% | Δ uds {pd(y['uds'],x['uds']):+.1f}% | Δ ses {pd(y['ses'],x['ses']):+.1f}%")
print(f"\n  {'Vta25':>9}{'Vta26':>9}{'Δ EUR':>9}{'%cat25':>7}{'%cat26':>7}  Titulo")
ja={c:a for c,a in A.items() if JA(a)}; jb={c:a for c,a in B.items() if JA(a)}
z=dict(sales=0,sessions=0,bb=0,units=0,title='')
for c in sorted(set(ja)|set(jb), key=lambda c:-(jb.get(c,z)['sales']))[:14]:
    a=ja.get(c,z); b=jb.get(c,z)
    print(f"  {a['sales']:>9,.0f}{b['sales']:>9,.0f}{b['sales']-a['sales']:>+9,.0f}{100*a['sales']/x['v']:>6.1f}%{100*b['sales']/y['v']:>6.1f}%  {(b['title'] or a['title'])[:56]}")

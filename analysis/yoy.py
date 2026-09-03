import sys, collections
from parse_br import load
from brands import brand, SUPPLIER

DAYS = {'2025': 365, '2026': 246}   # 2026 YTD: 1 ene -> 3 sep

def collapse(path):
    rows = load(path)
    for r in rows: r['brand'] = brand(r)
    by = collections.defaultdict(list)
    for r in rows: by[r['child']].append(r)
    out=[]
    for child, rs in by.items():
        out.append(dict(child=child, title=rs[0]['title'], brand=rs[0]['brand'],
            nskus=len({r['sku'] for r in rs}), sessions=max(r['sessions'] for r in rs),
            units=sum(r['units'] for r in rs), sales=sum(r['sales'] for r in rs),
            b2b=sum(r['b2b_sales'] for r in rs), bb=max(r['bb'] for r in rs)))
    return out

A = collapse(sys.argv[1])   # 2025 completo
B = collapse(sys.argv[2])   # 2026 YTD

def agg(items):
    s=sum(a['sessions'] for a in items); u=sum(a['units'] for a in items)
    v=sum(a['sales'] for a in items)
    bb=sum(a['bb']*a['sessions'] for a in items)/s if s else 0
    return dict(ses=s, uds=u, ventas=v, conv=100*u/s if s else 0,
                ticket=v/u if u else 0, eur_ses=v/s if s else 0, bb=bb,
                asins=len(items), skus=sum(a['nskus'] for a in items))

def group(items, key):
    g=collections.defaultdict(list)
    for a in items: g[key(a)].append(a)
    return {k:agg(v) for k,v in g.items()}

def d(new, old):
    if not old: return float('inf') if new else 0.0
    return 100*(new-old)/old

def yoy(key, title):
    ga, gb = group(A,key), group(B,key)
    keys = sorted(set(ga)|set(gb), key=lambda k: -gb.get(k,{}).get('ventas',0))
    print(f"\n### {title}\n")
    h=(f"{'':<15}{'Vta2025':>10}{'Vta26YTD':>10}{'Run-rate26':>11}{'YoY%':>8}"
       f"{'Ses2025':>10}{'Ses26YTD':>10}{'SesYoY%':>9}"
       f"{'Conv25':>8}{'Conv26':>8}{'€/ses25':>8}{'€/ses26':>8}{'BB25':>7}{'BB26':>7}")
    print(h); print('-'*len(h))
    for k in keys:
        a=ga.get(k); b=gb.get(k)
        z=dict(ses=0,uds=0,ventas=0,conv=0,ticket=0,eur_ses=0,bb=0,asins=0,skus=0)
        a=a or z; b=b or z
        rr = b['ventas']*365/DAYS['2026']
        print(f"{k:<15}{a['ventas']:>10,.0f}{b['ventas']:>10,.0f}{rr:>11,.0f}{d(rr,a['ventas']):>+7.0f}%"
              f"{a['ses']:>10,.0f}{b['ses']:>10,.0f}{d(b['ses']*365/DAYS['2026'],a['ses']):>+8.0f}%"
              f"{a['conv']:>7.1f}%{b['conv']:>7.1f}%{a['eur_ses']:>8.2f}{b['eur_ses']:>8.2f}{a['bb']:>6.1f}%{b['bb']:>6.1f}%")
    ta, tb = agg(A), agg(B); rr=tb['ventas']*365/DAYS['2026']
    print('-'*len(h))
    print(f"{'TOTAL':<15}{ta['ventas']:>10,.0f}{tb['ventas']:>10,.0f}{rr:>11,.0f}{d(rr,ta['ventas']):>+7.0f}%"
          f"{ta['ses']:>10,.0f}{tb['ses']:>10,.0f}{d(tb['ses']*365/DAYS['2026'],ta['ses']):>+8.0f}%"
          f"{ta['conv']:>7.1f}%{tb['conv']:>7.1f}%{ta['eur_ses']:>8.2f}{tb['eur_ses']:>8.2f}{ta['bb']:>6.1f}%{tb['bb']:>6.1f}%")

print(f"2025 completo ({DAYS['2025']}d): {agg(A)['ventas']:,.0f} EUR | {agg(A)['ses']:,.0f} ses | {agg(A)['uds']:,.0f} uds | {agg(A)['asins']} ASINs")
print(f"2026 YTD     ({DAYS['2026']}d): {agg(B)['ventas']:,.0f} EUR | {agg(B)['ses']:,.0f} ses | {agg(B)['uds']:,.0f} uds | {agg(B)['asins']} ASINs")
print(f"Run-rate 2026 anualizado: {agg(B)['ventas']*365/DAYS['2026']:,.0f} EUR ({d(agg(B)['ventas']*365/DAYS['2026'], agg(A)['ventas']):+.1f}% vs 2025)")
print("AVISO: run-rate lineal ignora la estacionalidad de Q4. Con Q4 fuerte el cierre real sera superior.")

yoy(lambda a:a['brand'],'YoY POR MARCA')
yoy(lambda a:SUPPLIER.get(a['brand'],'Otros'),'YoY POR PROVEEDOR')

# --- Movimientos por ASIN ---
ia={a['child']:a for a in A}; ib={b['child']:b for b in B}
print("\n### ASINs que MAS CAEN (venta 2025 >5.000 EUR, run-rate 2026 por debajo)\n")
rows=[]
for c,a in ia.items():
    if a['sales']<5000: continue
    b=ib.get(c)
    rr=(b['sales']*365/DAYS['2026']) if b else 0
    rows.append((rr-a['sales'], a, b, rr))
rows.sort(key=lambda x:x[0])
print(f"{'Delta EUR':>10}{'2025':>9}{'RR2026':>9}{'BB25':>7}{'BB26':>7}{'Ses25':>9}{'Ses26':>9}  {'Marca':<11} Titulo")
for delta,a,b,rr in rows[:20]:
    print(f"{delta:>10,.0f}{a['sales']:>9,.0f}{rr:>9,.0f}{a['bb']:>6.1f}%{(b['bb'] if b else 0):>6.1f}%{a['sessions']:>9,.0f}{(b['sessions'] if b else 0):>9,.0f}  {a['brand']:<11} {a['title'][:52]}")

print("\n### ASINs que MAS SUBEN\n")
rows2=[]
for c,b in ib.items():
    a=ia.get(c); rr=b['sales']*365/DAYS['2026']
    base=a['sales'] if a else 0
    if rr<5000: continue
    rows2.append((rr-base, a, b, rr))
rows2.sort(key=lambda x:-x[0])
print(f"{'Delta EUR':>10}{'2025':>9}{'RR2026':>9}{'BB25':>7}{'BB26':>7}{'Ses25':>9}{'Ses26':>9}  {'Marca':<11} Titulo")
for delta,a,b,rr in rows2[:20]:
    print(f"{delta:>10,.0f}{(a['sales'] if a else 0):>9,.0f}{rr:>9,.0f}{(a['bb'] if a else 0):>6.1f}%{b['bb']:>6.1f}%{(a['sessions'] if a else 0):>9,.0f}{b['sessions']:>9,.0f}  {b['brand']:<11} {b['title'][:52]}")

nuevos=[b for c,b in ib.items() if c not in ia]
muertos=[a for c,a in ia.items() if c not in ib]
print(f"\nASINs nuevos en 2026: {len(nuevos)} -> {sum(x['sales'] for x in nuevos):,.0f} EUR")
print(f"ASINs desaparecidos:  {len(muertos)} -> valian {sum(x['sales'] for x in muertos):,.0f} EUR en 2025")

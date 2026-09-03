import sys, collections
from parse_br import load
from brands import brand, SUPPLIER

rows = load(sys.argv[1])
for r in rows: r['brand'] = brand(r)

byasin = collections.defaultdict(list)
for r in rows: byasin[r['child']].append(r)
asins=[]
for child, rs in byasin.items():
    sess = max(r['sessions'] for r in rs)
    asins.append(dict(child=child, parent=rs[0]['parent'], title=rs[0]['title'],
        brand=rs[0]['brand'], nskus=len({r['sku'] for r in rs}),
        sessions=sess, units=sum(r['units'] for r in rs), sales=sum(r['sales'] for r in rs),
        b2b=sum(r['b2b_sales'] for r in rs), bb=max(r['bb'] for r in rs),
        skus=', '.join(sorted({r['sku'] for r in rs}))))

TOT = sum(a['sales'] for a in asins); TOTS = sum(a['sessions'] for a in asins)
nsku = len({r['sku'] for r in rows})

def agg(items):
    s=sum(a['sessions'] for a in items); u=sum(a['units'] for a in items)
    v=sum(a['sales'] for a in items);    b=sum(a['b2b'] for a in items)
    bb=sum(a['bb']*a['sessions'] for a in items)/s if s else 0
    return dict(skus=sum(a['nskus'] for a in items), asins=len(items), ses=s, uds=u, ventas=v,
        conv=100*u/s if s else 0, ticket=v/u if u else 0, bb=bb,
        b2bp=100*b/v if v else 0, pct=100*v/TOT, pses=100*s/TOTS, eur_ses=v/s if s else 0)

def table(key,title):
    g=collections.defaultdict(list)
    for a in asins: g[key(a)].append(a)
    out=sorted(((k,agg(v)) for k,v in g.items()), key=lambda x:-x[1]['ventas'])
    print(f"\n### {title}\n")
    h=f"{'':<16}{'SKUs':>5}{'ASINs':>6}{'Sesiones':>10}{'%Ses':>6}{'Uds':>8}{'Ventas EUR':>11}{'%Vta':>6}{'Conv%':>7}{'Ticket':>7}{'EUR/ses':>8}{'BuyBox':>8}{'B2B%':>6}"
    print(h); print('-'*len(h))
    for k,a in out:
        print(f"{k:<16}{a['skus']:>5}{a['asins']:>6}{a['ses']:>10,.0f}{a['pses']:>5.1f}%{a['uds']:>8,.0f}{a['ventas']:>11,.0f}{a['pct']:>5.1f}%{a['conv']:>6.1f}%{a['ticket']:>7.1f}{a['eur_ses']:>8.2f}{a['bb']:>7.1f}%{a['b2bp']:>5.1f}%")
    t=agg(asins); print('-'*len(h))
    print(f"{'TOTAL':<16}{t['skus']:>5}{t['asins']:>6}{t['ses']:>10,.0f}{t['pses']:>5.1f}%{t['uds']:>8,.0f}{t['ventas']:>11,.0f}{t['pct']:>5.1f}%{t['conv']:>6.1f}%{t['ticket']:>7.1f}{t['eur_ses']:>8.2f}{t['bb']:>7.1f}%{t['b2bp']:>5.1f}%")

print(f"TOTAL REAL: {len(asins)} ASINs hijo / {nsku} SKUs / {TOTS:,.0f} sesiones / {sum(a['units'] for a in asins):,.0f} uds / {TOT:,.2f} EUR")
print(f"(sumando filas sin deduplicar: {sum(r['sessions'] for r in rows):,.0f} sesiones -> inflado {100*sum(r['sessions'] for r in rows)/TOTS-100:.0f}%)")
table(lambda a:a['brand'],'POR MARCA (deduplicado por ASIN)')
table(lambda a:SUPPLIER.get(a['brand'],'Otros'),'POR PROVEEDOR')

print("\n### TOP 25 ASINs por venta\n")
print(f"{'Ventas EUR':>11}{'Uds':>7}{'Sesiones':>10}{'Conv%':>7}{'BuyBox':>8}  {'Marca':<12} Titulo")
for a in sorted(asins,key=lambda x:-x['sales'])[:25]:
    print(f"{a['sales']:>11,.0f}{a['units']:>7,.0f}{a['sessions']:>10,.0f}{100*a['units']/a['sessions'] if a['sessions'] else 0:>6.1f}%{a['bb']:>7.1f}%  {a['brand']:<12} {a['title'][:62]}")

print("\n### BuyBox perdido: ASINs con demanda probada y BB bajo\n")
print("Regla: >3.000 sesiones y BB<70%. 'EUR en riesgo' = ventas * (1-BB) / BB, cap a 3x ventas.\n")
cand=[]
for a in asins:
    if a['sessions']>3000 and a['bb']<70 and a['sales']>0:
        risk=min(a['sales']*(100-a['bb'])/a['bb'], 3*a['sales'])
        cand.append((risk,a))
cand.sort(key=lambda x:-x[0])
print(f"{'EUR riesgo':>11}{'Ventas':>9}{'BuyBox':>8}{'Sesiones':>10}{'Conv%':>7}  {'Marca':<10} Titulo")
for risk,a in cand[:25]:
    print(f"{risk:>11,.0f}{a['sales']:>9,.0f}{a['bb']:>7.1f}%{a['sessions']:>10,.0f}{100*a['units']/a['sessions']:>6.1f}%  {a['brand']:<10} {a['title'][:58]}")
print(f"\n{len(cand)} ASINs afectados | ventas actuales {sum(a['sales'] for _,a in cand):,.0f} EUR | EUR en riesgo/recuperables {sum(r for r,_ in cand):,.0f}")

print("\n### Concentracion")
srt=sorted(asins,key=lambda a:-a['sales'])
for n in (10,25,50,100,200):
    print(f"  Top {n:>3} ASINs = {100*sum(a['sales'] for a in srt[:n])/TOT:>5.1f}% de la venta")
dead=[a for a in asins if a['sales']==0]
print(f"  ASINs con 0 EUR: {len(dead)} de {len(asins)} ({100*len(dead)/len(asins):.1f}%), consumen {sum(a['sessions'] for a in dead):,.0f} sesiones ({100*sum(a['sessions'] for a in dead)/TOTS:.1f}%)")

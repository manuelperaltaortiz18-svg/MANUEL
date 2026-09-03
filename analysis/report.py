import sys, collections
from parse_br import load
from brands import brand, SUPPLIER

rows = load(sys.argv[1])
for r in rows: r['brand'] = brand(r)

TOT = sum(r['sales'] for r in rows)

def agg(rows):
    s  = sum(r['sessions'] for r in rows)
    u  = sum(r['units'] for r in rows)
    v  = sum(r['sales'] for r in rows)
    b2b= sum(r['b2b_sales'] for r in rows)
    # BuyBox ponderado por sesiones (proxy de exposicion real)
    bb = sum(r['bb']*r['sessions'] for r in rows)/s if s else 0
    bb_simple = sum(r['bb'] for r in rows)/len(rows) if rows else 0
    return dict(skus=len({r['sku'] for r in rows}), asins=len({r['child'] for r in rows}),
                sesiones=s, uds=u, ventas=v, b2b=b2b,
                conv=100*u/s if s else 0, ticket=v/u if u else 0,
                bb_pond=bb, bb_simple=bb_simple, pct=100*v/TOT)

def table(key, title):
    g = collections.defaultdict(list)
    for r in rows: g[key(r)].append(r)
    out = sorted(((k, agg(v)) for k,v in g.items()), key=lambda x:-x[1]['ventas'])
    print(f"\n### {title}\n")
    print(f"{'':<16}{'SKUs':>5}{'Sesiones':>10}{'Uds':>8}{'Ventas €':>12}{'%Tot':>7}{'Conv%':>7}{'Ticket':>8}{'BB pond':>9}{'BB simp':>9}{'B2B%':>7}")
    for k,a in out:
        print(f"{k:<16}{a['skus']:>5}{a['sesiones']:>10,.0f}{a['uds']:>8,.0f}{a['ventas']:>12,.0f}{a['pct']:>6.1f}%{a['conv']:>6.1f}%{a['ticket']:>8.1f}{a['bb_pond']:>8.1f}%{a['bb_simple']:>8.1f}%{100*a['b2b']/a['ventas'] if a['ventas'] else 0:>6.1f}%")
    t = agg(rows)
    print(f"{'TOTAL':<16}{t['skus']:>5}{t['sesiones']:>10,.0f}{t['uds']:>8,.0f}{t['ventas']:>12,.0f}{t['pct']:>6.1f}%{t['conv']:>6.1f}%{t['ticket']:>8.1f}{t['bb_pond']:>8.1f}%{t['bb_simple']:>8.1f}%{100*t['b2b']/t['ventas']:>6.1f}%")

table(lambda r: r['brand'], 'POR MARCA')
table(lambda r: SUPPLIER.get(r['brand'],'Otros'), 'POR PROVEEDOR')

# --- Coste de BuyBox perdido ---
print("\n### TOP 20: € en juego por BuyBox perdido")
print("(venta_potencial = ventas / BB%; perdida = potencial - real; solo BB<90% y ventas>500€)\n")
cand=[]
for r in rows:
    if r['sales']>500 and 0 < r['bb'] < 90:
        pot = r['sales']*100/r['bb']
        cand.append((pot-r['sales'], r))
cand.sort(key=lambda x:-x[0])
print(f"{'Perdida €':>10}{'Ventas €':>10}{'BB%':>7}{'Ses':>9}{'Conv%':>7}  Marca      SKU / Titulo")
for loss, r in cand[:20]:
    conv = 100*r['units']/r['sessions'] if r['sessions'] else 0
    print(f"{loss:>10,.0f}{r['sales']:>10,.0f}{r['bb']:>6.1f}%{r['sessions']:>9,.0f}{conv:>6.1f}%  {r['brand']:<10} {r['sku'][:22]:<22} {r['title'][:52]}")
print(f"\nTotal 'perdida' teorica en esos {len(cand)} SKUs: {sum(l for l,_ in cand):,.0f} €")

# --- Trafico desperdiciado: muchas sesiones, poca conversion ---
print("\n### TOP 15: trafico alto, conversion baja (>5.000 sesiones, conv<3%)\n")
bad=[r for r in rows if r['sessions']>5000 and 100*r['units']/r['sessions']<3]
bad.sort(key=lambda r:-r['sessions'])
print(f"{'Sesiones':>10}{'Uds':>7}{'Conv%':>7}{'Ventas €':>10}{'BB%':>7}  Marca      Titulo")
for r in bad[:15]:
    print(f"{r['sessions']:>10,.0f}{r['units']:>7,.0f}{100*r['units']/r['sessions']:>6.2f}%{r['sales']:>10,.0f}{r['bb']:>6.1f}%  {r['brand']:<10} {r['title'][:60]}")
print(f"\n{len(bad)} SKUs, {sum(r['sessions'] for r in bad):,.0f} sesiones ({100*sum(r['sessions'] for r in bad)/sum(r['sessions'] for r in rows):.1f}% del trafico) generando {sum(r['sales'] for r in bad):,.0f} €")

# --- Concentracion ---
print("\n### Concentracion de ventas")
srt=sorted(rows,key=lambda r:-r['sales'])
acc=0
for n in (10,25,50,100,200):
    print(f"  Top {n:>3} SKUs = {100*sum(r['sales'] for r in srt[:n])/TOT:>5.1f}% de la venta")
dead=[r for r in rows if r['sales']==0]
print(f"  SKUs con 0 € : {len(dead)} ({100*len(dead)/len(rows):.1f}%), consumiendo {sum(r['sessions'] for r in dead):,.0f} sesiones")

"""Cruza el informe de campanas (ES) con los Business Reports del mismo periodo.
Periodo del fichero de ads: 1 jul 2025 - 31 jul 2026 (13 meses)."""
import csv, re, collections
from parse_br import load
from brands import brand, SUPPLIER

MESES = [f'2025-{m:02d}' for m in range(7,13)] + [f'2026-{m:02d}' for m in range(1,8)]

# marca inferida del nombre de campana
ADRULES = [
    ('Arcos',       r'ARCOS'),
    ('Cuperinox',   r'CUPERINOX'),
    ('Hendi',       r'HENDI'),
    ('Bioleaf',     r'BIOLEAF|GEL WC|MULTIUSOS|DESINCRUSTANTE|LIMPIACRISTALES|DETERGENTE BIBERONES'),
    ('Vinfermaton', r'INSECTICIDA|AVISPAS|HORMIGAS|CUCARACHAS|POLILLAS|MOSQUITOS|FRIEGASUELOS'),
    ('Wins',        r'\bWINS\b'),
    ('Vinfer',      r'\bVINFER\b|MOPAS'),
]
def ad_brand(name):
    u = name.upper()
    for b, p in ADRULES:
        if re.search(p, u): return b
    return 'Sin clasificar'

def money(s):
    s = (s or '').replace('€','').replace('GBP','').strip()
    return float(s.replace('.','').replace(',','.')) if any(c.isdigit() for c in s) else 0.0

def load_ads(path, pais='España'):
    g = collections.defaultdict(lambda: dict(gasto=0.0, vta=0.0, clics=0.0, n=0))
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        if r['País'] != pais: continue
        c = money(r['Coste total (convertido)'])
        if c <= 0: continue
        a = g[ad_brand(r['Nombre de la campaña'])]
        a['gasto'] += c; a['vta'] += money(r['Ventas (convertido)'])
        a['clics'] += money(r['Clics']); a['n'] += 1
    return g

def load_br(meses):
    g = collections.defaultdict(lambda: dict(v=0.0, ses=0.0, uds=0.0))
    for m in meses:
        rows = load(f'mensual/{m}.csv')
        by = collections.defaultdict(list)
        for r in rows: by[r['child']].append(r)
        for rs in by.values():
            a = g[brand(rs[0])]
            a['v'] += sum(r['sales'] for r in rs); a['uds'] += sum(r['units'] for r in rs)
            a['ses'] += max(r['sessions'] for r in rs)
    return g

MG = {'Arcos':(15,25),'Cuperinox':(25,35),'Hendi':(20,35),'Vinfermaton':(15,25),
      'Wins':(15,25),'Vinfer':(15,25),'Bioleaf':(15,25),'Vincare':(15,25)}

ads, br = load_ads('ads/campaigns_2025-07_2026-07.csv'), load_br(MESES)
print("PUBLICIDAD x NEGOCIO REAL — Espana, jul-25 a jul-26 (13 meses)\n")
h = (f"{'Marca':<14}{'Venta total':>12}{'Gasto ads':>10}{'Vta atrib':>11}{'ACOS':>7}"
     f"{'TACOS':>7}{'Margen min':>11}{'Margen-ads':>11}{'Veredicto':>12}")
print(h); print('-'*len(h))
tv=tg=0
for b in sorted(set(br)|set(ads), key=lambda b: -br.get(b,{}).get('v',0)):
    v = br.get(b,{}).get('v',0); a = ads.get(b, dict(gasto=0,vta=0))
    if v < 1000 and a['gasto'] < 50: continue
    tv += v; tg += a['gasto']
    lo,hi = MG.get(b,(15,25)); mn = v*lo/100
    neto = mn - a['gasto']
    acos  = 100*a['gasto']/a['vta'] if a['vta'] else 0
    tacos = 100*a['gasto']/v if v else 0
    ver = 'PIERDE' if neto < 0 else ('revisar' if tacos > lo*0.5 else 'ok')
    print(f"{b:<14}{v:>12,.0f}{a['gasto']:>10,.0f}{a['vta']:>11,.0f}"
          f"{acos:>6.1f}%{tacos:>6.1f}%{mn:>11,.0f}{neto:>11,.0f}{ver:>12}")
print('-'*len(h))
print(f"{'TOTAL':<14}{tv:>12,.0f}{tg:>10,.0f}{'':>11}{'':>7}{100*tg/tv:>6.1f}%")

print("\nEl veredicto usa el margen MINIMO de tu rango (el caso prudente).")
print("ACOS  = gasto / venta atribuida al anuncio (eficiencia del anuncio).")
print("TACOS = gasto / venta total de la marca (cuanto te cuesta sostenerla).")

"""Genera dashboard.html a partir de los CSV mensuales en mensual/.
Uso:  python3 build_dashboard.py      (desde analysis/)
Anade un mes nuevo como mensual/AAAA-MM.csv y vuelve a ejecutar."""
import glob, json, os, re, collections
from parse_br import load
from brands import brand, SUPPLIER

SUPS = ['Arcos','Cuperinox','Hendi','Vinfer (grupo)','Otros']
MARGINS = {'Arcos':[15,25],'Cuperinox':[25,35],'Hendi':[20,35],'Vinfer (grupo)':[15,25],'Otros':[15,25]}
JAM = re.compile(r'JAMONER|SOPORTE JAMON|JAMONERA')

def zero(): return dict(ses=0.0, uds=0.0, v=0.0, bbw=0.0, n=0)

def read_month(path):
    rows = load(path)
    by = collections.defaultdict(list)
    for r in rows: by[r['child']].append(r)
    out = []
    for child, rs in by.items():
        s = max(r['sessions'] for r in rs)
        out.append(dict(child=child, title=rs[0]['title'], brand=brand(rs[0]),
                        ses=s, uds=sum(r['units'] for r in rs),
                        v=sum(r['sales'] for r in rs), bb=max(r['bb'] for r in rs),
                        skus=len({r['sku'] for r in rs})))
    return out

files = sorted(glob.glob('mensual/*.csv'))
months = [os.path.basename(f)[:-4] for f in files]
data = {m: read_month(f) for m, f in zip(months, files)}

def bucket(items):
    a = zero()
    for x in items:
        a['ses'] += x['ses']; a['uds'] += x['uds']; a['v'] += x['v']
        a['bbw'] += x['bb'] * x['ses']; a['n'] += 1
    return a

series   = {s: [bucket([x for x in data[m] if SUPPLIER.get(x['brand'],'Otros') == s]) for m in months] for s in SUPS}
brands   = sorted({x['brand'] for m in months for x in data[m]},
                  key=lambda b: -sum(x['v'] for m in months for x in data[m] if x['brand'] == b))
bseries  = {b: [bucket([x for x in data[m] if x['brand'] == b]) for m in months] for b in brands}
total    = [bucket(data[m]) for m in months]
jamon    = [bucket([x for x in data[m] if JAM.search(x['title'].upper())]) for m in months]
asin_ct  = [len(data[m]) for m in months]

# BuyBox perdido: ultimos 8 meses agregados, ASINs con demanda y BB bajo
last8 = months[-8:]
agg = collections.defaultdict(lambda: dict(ses=0.0, uds=0.0, v=0.0, bbw=0.0, title='', brand=''))
for m in last8:
    for x in data[m]:
        a = agg[x['child']]
        a['ses'] += x['ses']; a['uds'] += x['uds']; a['v'] += x['v']
        a['bbw'] += x['bb'] * x['ses']; a['title'] = x['title']; a['brand'] = x['brand']
bbloss = []
for c, a in agg.items():
    bb = a['bbw'] / a['ses'] if a['ses'] else 0
    if a['ses'] > 5000 and bb < 70 and a['v'] > 1000:
        bbloss.append(dict(title=a['title'], brand=a['brand'], v=round(a['v']),
                           bb=round(bb, 1), ses=round(a['ses']),
                           conv=round(100 * a['uds'] / a['ses'], 2),
                           riesgo=round(min(a['v'] * (100 - bb) / bb, 3 * a['v']))))
bbloss.sort(key=lambda x: -x['riesgo'])

def clean(lst): return [{k: round(v, 2) for k, v in d.items()} for d in lst]

payload = dict(
    months=months, suppliers=SUPS, margins=MARGINS,
    series={k: clean(v) for k, v in series.items()},
    brands={k: clean(v) for k, v in bseries.items()},
    brandOrder=brands, total=clean(total), jamon=clean(jamon), asins=asin_ct,
    bbloss=bbloss[:20], periodo=f"{months[0]} → {months[-1]}",
)

try:
    payload['ads'] = json.load(open('ads_summary.json', encoding='utf-8'))
except FileNotFoundError:
    payload['ads'] = None

tpl = open('dashboard_template.html', encoding='utf-8').read()
out = tpl.replace('/*__DATA__*/null', json.dumps(payload, ensure_ascii=False))
open('dashboard.html', 'w', encoding='utf-8').write(out)
print(f"dashboard.html generado · {len(months)} meses ({months[0]} → {months[-1]}) · "
      f"{sum(t['v'] for t in total):,.0f} EUR · {len(bbloss)} ASINs con BuyBox bajo")

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


# ---------- mercados exteriores ----------
# Cada export cubre un rango distinto; se normaliza a EUR/mes.
MERCADOS = [
    ('España',   None,                    8.0,  'ene–ago 2026'),
    ('Francia',  'fr/br_fr_2026ytd.csv',  8.1,  'ene–3 sep 2026'),
    ('Italia',   'it/br_it.csv',         20.2,  '1 ene 2025 – 6 sep 2026'),
    ('Alemania', 'de/br_de.csv',         20.2,  '1 ene 2025 – 6 sep 2026'),
]

def mercado(items, meses):
    ses = sum(x['ses'] for x in items); v = sum(x['v'] for x in items)
    uds = sum(x['uds'] for x in items)
    quema = [x for x in items if x['ses'] > 3000 and x['bb'] < 25]
    qs = sum(x['ses'] for x in quema)
    mix = collections.Counter()
    for x in items: mix[x['brand']] += x['v']
    return dict(
        meses=meses, v=round(v), vmes=round(v/meses), ses=round(ses), sesmes=round(ses/meses),
        uds=round(uds), conv=round(100*uds/ses, 2) if ses else 0,
        eur=round(v/ses, 2) if ses else 0, ticket=round(v/uds, 1) if uds else 0,
        bb=round(sum(x['bb']*x['ses'] for x in items)/ses, 1) if ses else 0,
        asins=len(items),
        quema_n=len(quema), quema_ses=round(qs), quema_pct=round(100*qs/ses, 1) if ses else 0,
        quema_v=round(sum(x['v'] for x in quema)),
        quema_eur=round(sum(x['v'] for x in quema)/qs, 2) if qs else 0,
        mix={k: round(100*val/v, 1) for k, val in mix.most_common() if v and 100*val/v >= 0.3})

def flat(path):
    out = []
    for x in read_month(path):
        out.append(dict(brand=x['brand'], ses=x['ses'], uds=x['uds'], v=x['v'], bb=x['bb']))
    return out

# Espana: agregar los meses de 2026 a nivel ASIN
_es = collections.defaultdict(lambda: dict(ses=0.0, uds=0.0, v=0.0, bbw=0.0, brand=''))
for m in [x for x in months if x.startswith('2026')]:
    for x in read_month(f'mensual/{m}.csv'):
        a = _es[x['child']]
        a['ses'] += x['ses']; a['uds'] += x['uds']; a['v'] += x['v']
        a['bbw'] += x['bb']*x['ses']; a['brand'] = x['brand']
ES = [dict(brand=a['brand'], ses=a['ses'], uds=a['uds'], v=a['v'],
           bb=a['bbw']/a['ses'] if a['ses'] else 0) for a in _es.values()]

mercados = []
for nombre, path, meses, etiqueta in MERCADOS:
    try:
        items = ES if path is None else flat(path)
    except FileNotFoundError:
        continue
    d = mercado(items, meses); d['nombre'] = nombre; d['etiqueta'] = etiqueta
    mercados.append(d)
mercados.sort(key=lambda d: -d['vmes'])
payload['mercados'] = mercados

for _k, _f in (('asinYoY','asin_yoy.json'), ('asinFR','asin_yoy_fr.json')):
    try:
        payload[_k] = json.load(open(_f, encoding='utf-8'))
    except FileNotFoundError:
        payload[_k] = None

try:
    payload['ads'] = json.load(open('ads_summary.json', encoding='utf-8'))
except FileNotFoundError:
    payload['ads'] = None

tpl = open('dashboard_template.html', encoding='utf-8').read()
out = tpl.replace('/*__DATA__*/null', json.dumps(payload, ensure_ascii=False))
open('dashboard.html', 'w', encoding='utf-8').write(out)
print(f"dashboard.html generado · {len(months)} meses ({months[0]} → {months[-1]}) · "
      f"{sum(t['v'] for t in total):,.0f} EUR · {len(bbloss)} ASINs con BuyBox bajo")

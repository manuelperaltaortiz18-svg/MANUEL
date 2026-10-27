"""Canal Makro/Metro. El export es UN agregado del 01/01/2025 al 24/10/2026
(22 meses): no trae fecha por fila, asi que no se puede partir por anos.
Todo se muestra tambien en EUR/mes para poder compararlo con otros canales."""
import json, collections, re
from openpyxl import load_workbook

XLS = 'makro_raw/makro.xlsx'
PLAT = {'makro.es': 'Makro España', 'makro.pt': 'Makro Portugal',
        'metro.it': 'Metro Italia', 'makro.nl': 'Makro Países Bajos'}

def num(x):
    if x is None: return 0.0
    if isinstance(x, (int, float)): return float(x)
    try: return float(str(x).replace('€', '').strip())
    except ValueError: return 0.0

ws = load_workbook(XLS, data_only=True, read_only=True)['Export']
todo = list(ws.iter_rows(min_row=2, values_only=True))

# la fila 'Total' y la de filtros no son productos
rows = [r for r in todo if r[1]]
tot_decl = next((num(r[4]) for r in todo if str(r[0] or '').strip() == 'Total'), None)
filtro = next((str(c) for r in todo for c in r if c and 'Applied filters' in str(c)), '')
m = re.search(r'after (\d{2}/\d{2}/\d{4}).*?before (\d{2}/\d{2}/\d{4})', filtro)
desde, hasta = (m.group(1), m.group(2)) if m else ('?', '?')
MESES = 22.0   # 1 ene 2025 -> 24 oct 2026

def marca(r):
    mm = str(r[10] or '').upper(); g = str(r[2] or '')
    if 'HENDI' in mm or 'ARKTIC' in mm or g.startswith('8711369'): return 'Hendi'
    if 'ARCOS' in mm or g.startswith('84210022'): return 'Arcos'
    if 'CUPERINOX' in mm: return 'Cuperinox'
    if 'VINFER' in mm: return 'Vinfer'
    return mm.title()[:18] if mm.strip() else 'Sin clasificar'

def agrupa(fn):
    D = collections.defaultdict(lambda: dict(v=0., u=0., n=0))
    for r in rows:
        a = D[fn(r)]; a['v'] += num(r[4]); a['u'] += num(r[5]); a['n'] += 1
    return [dict(k=k, v=round(d['v'], 2), u=int(d['u']), n=d['n'],
                 mes=round(d['v'] / MESES, 2))
            for k, d in sorted(D.items(), key=lambda kv: -kv[1]['v'])]

V = sum(num(r[4]) for r in rows); U = sum(num(r[5]) for r in rows)
prods = sorted(rows, key=lambda r: -num(r[4]))[:60]

json.dump(dict(
    desde=desde, hasta=hasta, meses=MESES,
    total=round(V, 2), uds=int(U), refs=len(rows),
    cuadra=(tot_decl is None or abs(tot_decl - V) < 1),
    total_declarado=round(tot_decl, 2) if tot_decl else None,
    plataformas=[{**g, 'k': PLAT.get(g['k'], g['k'])} for g in agrupa(lambda r: r[1])],
    marcas=agrupa(marca),
    categorias=agrupa(lambda r: str(r[6] or 'Sin categoría')),
    top=[dict(mpn=str(r[9] or ''), gtin=str(r[2] or ''), nombre=str(r[3] or '')[:70],
              plat=PLAT.get(r[1], str(r[1])), marca=marca(r), cat=str(r[7] or ''),
              v=round(num(r[4]), 2), u=int(num(r[5])),
              pvp=round(num(r[4]) / num(r[5]), 2) if num(r[5]) else None)
         for r in prods]),
    open('makro.json', 'w'), ensure_ascii=False, indent=1)

print(f"periodo {desde} → {hasta} ({MESES:.0f} meses, agregado unico)")
print(f"total {V:,.2f} € · {U:,.0f} uds · {len(rows)} referencias · {V/MESES:,.0f} €/mes")
print(f"cuadra con la fila Total del fichero: {'si' if tot_decl and abs(tot_decl-V)<1 else 'NO'}")
for lab, g in (('PLATAFORMA', 'plataformas'), ('MARCA', 'marcas')):
    print(f"\n{lab:20s}{'ventas':>12s}{'€/mes':>10s}{'uds':>8s}{'refs':>6s}")
    for x in json.load(open('makro.json'))[g]:
        print(f"{x['k'][:20]:20s}{x['v']:12,.0f}{x['mes']:10,.0f}{x['u']:8,.0f}{x['n']:6d}")

"""Empareja la tabla de costes VINFER con las ventas y recalcula el margen."""
import json, re, collections
from parse_br import load
from brands import brand

MARCAS = ('Vinfermaton','Wins','Bioleaf','Vinfer','Vincare','La Garrafita','Maton','Xpartan')
rows = load('data_BusinessReport_2026ytd_22sep.csv')
V = collections.defaultdict(lambda: dict(u=0.0, v=0.0, title='', marca=''))
for r in rows:
    b = brand(r)
    if b not in MARCAS: continue
    a = V[r['sku']]; a['u'] += r['units']; a['v'] += r['sales']
    a['title'] = r['title']; a['marca'] = b

F = json.load(open('vinfer_costes.json'))
def N(s): return re.sub(r'[^A-Z0-9]', '', (s or '').upper())

def candidatos(ref, marca):
    """SKUs de venta que corresponden a esta REF."""
    if not ref: return []
    nr = N(ref)
    alt = {nr}
    m = re.fullmatch(r'W(\d{3})', nr)        # W007 -> WINS007
    if m: alt |= {'WINS'+m.group(1), 'WINS'+m.group(1).lstrip('0')}
    out = []
    for s in V:
        ns = N(s)
        if ns in alt or any(ns.startswith(a) and len(a) >= 4 for a in alt):
            out.append(s)
    return out

usados = set()
for f in F:
    f['skus'] = [s for s in candidatos(f['ref'], f['marca']) if s not in usados]
    usados |= set(f['skus'])
    f['uds']   = round(sum(V[s]['u'] for s in f['skus']))
    f['venta'] = round(sum(V[s]['v'] for s in f['skus']), 2)
    f['precio_real'] = round(f['venta']/f['uds'], 2) if f['uds'] else None
    p = f["precio_real"] or f["pvp"] or 0
    tasa = f['tasa'] or 0.15
    iva  = p*0.21/1.21
    neto = p - iva
    mg   = neto - p*tasa - (f["envio"] or 0) - f["coste_neto"] if p else 0
    f.update(precio=round(p, 2), iva_real=round(iva, 3), fee_real=round(p*tasa, 3),
             neto_real=round(neto, 3), margen=round(mg, 3),
             pct=round(100*mg/neto, 1) if neto else 0,
             contrib=round(mg*f['uds'], 2),
             base=round(neto - p*tasa - f['coste_neto'], 3))
    for k in ('coste_neto','margen_ok','pct_ok','iva_ok','neto','pct_sobre_pvp','tasa'):
        if f.get(k) is not None: f[k] = round(f[k], 4)

TV = sum(a['v'] for a in V.values()); TU = sum(a['u'] for a in V.values())
CV = sum(f['venta'] for f in F);      CU = sum(f['uds'] for f in F)

if __name__ == '__main__':
    print("VINFER — cobertura de la tabla de costes (ventas 2026 hasta 22 sep)\n")
    print(f"  Venta del grupo : {TV:>11,.0f} EUR | {TU:>7,.0f} uds | {len(V)} SKUs")
    print(f"  Con coste casado: {CV:>11,.0f} EUR ({100*CV/TV:.1f}%) | {CU:>7,.0f} uds")
    print(f"  SIN coste       : {TV-CV:>11,.0f} EUR ({100*(TV-CV)/TV:.1f}%)\n")
    porm = collections.defaultdict(lambda: [0.0, 0.0])
    for s, a in V.items():
        if s not in usados: porm[a['marca']][0] += a['v']; porm[a['marca']][1] += a['u']
    print("  Venta sin coste, por marca de venta:")
    for k, (v, u) in sorted(porm.items(), key=lambda x: -x[1][0]):
        print(f"    {k:<14}{v:>11,.0f} EUR{u:>8,.0f} uds")

    con = [f for f in F if f['uds'] > 0]
    con.sort(key=lambda f: -f['contrib'])
    print(f"\n\nMARGEN RECALCULADO — {len(con)} referencias con venta\n")
    h = (f"{'Marca':<13}{'REF':<16}{'Uds':>6}{'Venta':>9}{'P.real':>8}{'Coste n':>8}"
         f"{'Comis':>7}{'Envio':>7}{'Mg/ud':>8}{'%':>6}{'Contrib':>9}{'% hoja':>8}")
    print(h); print('-'*len(h))
    for f in con[:18]:
        print(f"{f['marca']:<13}{(f['ref'] or '—')[:15]:<16}{f['uds']:>6,}{f['venta']:>9,.0f}"
              f"{f['precio']:>8.2f}{f['coste_neto']:>8.2f}{f['fee_real']:>7.2f}{f['envio'] or 0:>7.2f}"
              f"{f['margen']:>8.2f}{f['pct']:>5.0f}%{f['contrib']:>9,.0f}"
              f"{100*(f['pct_hoja'] or 0):>7.0f}%")
    T = dict(v=sum(f['venta'] for f in con), neto=sum(f['neto_real']*f['uds'] for f in con),
             c=sum(f['contrib'] for f in con), u=sum(f['uds'] for f in con))
    print('-'*len(h))
    print(f"{'TOTAL':<13}{'':<16}{T['u']:>6,}{T['v']:>9,.0f}{'':>8}{'':>8}{'':>7}{'':>7}{'':>8}"
          f"{100*T['c']/T['neto']:>5.0f}%{T['c']:>9,.0f}")
    json.dump(dict(filas=F, cobertura=dict(
        venta_total=round(TV), venta_cubierta=round(CV), uds_total=round(TU),
        uds_cubiertas=round(CU), skus=len(V))), open('vinfer_pl.json','w'), ensure_ascii=False)
    print("\n-> vinfer_pl.json")

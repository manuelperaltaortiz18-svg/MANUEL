import collections, re
from pl import COSTES, casados, V

cubiertos = {s for hs in casados.values() for s in hs}
cup = {s: a for s, a in V.items() if a['brand'] == 'Cuperinox'}
falt = {s: a for s, a in cup.items() if s not in cubiertos}
TV = sum(a['v'] for a in cup.values()); TU = sum(a['u'] for a in cup.values())
FV = sum(a['v'] for a in falt.values()); FU = sum(a['u'] for a in falt.values())
print(f"CUPERINOX 2026 (hasta 22 sep): {len(cup)} SKUs con venta | {TV:,.0f} EUR | {TU:,.0f} uds")
print(f"  con coste  : {len(cup)-len(falt):>4} SKUs | {TV-FV:>10,.0f} EUR ({100*(TV-FV)/TV:.1f}%)")
print(f"  SIN coste  : {len(falt):>4} SKUs | {FV:>10,.0f} EUR ({100*FV/TV:.1f}%) | {FU:,.0f} uds\n")

# agrupar por raiz de SKU para que la lista sea manejable
def raiz(s): return re.sub(r'[_\-]?(fba|fbm|FBA|FBM|us|uss|caja|pp|premium|solo.*|\d{0,2})$','',s).rstrip('_-')
g = collections.defaultdict(lambda: dict(u=0.0, v=0.0, skus=set(), title=''))
for s, a in falt.items():
    k = raiz(s); d = g[k]
    d['u'] += a['u']; d['v'] += a['v']; d['skus'].add(s)
    if a['v'] > 0 and (not d['title'] or a['v'] > 0): d['title'] = a['title']
print(f"LISTA PARA COMPLETAR — {len(g)} referencias, ordenadas por venta\n")
print(f"{'Venta':>10}{'Uds':>7}  {'SKUs a dar de alta':<40} Producto")
print('-'*120)
for k, d in sorted(g.items(), key=lambda x: -x[1]['v']):
    if d['v'] < 1: continue
    print(f"{d['v']:>10,.0f}{d['u']:>7,.0f}  {', '.join(sorted(d['skus']))[:38]:<40} {d['title'][:56]}")
cero = [k for k, d in g.items() if d['v'] < 1]
print(f"\n(+{len(cero)} referencias con 0 EUR de venta, no urgentes)")

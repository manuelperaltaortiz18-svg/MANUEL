"""Publicidad por ASIN, 2025.
   El informe de productos publicitados trae ventas, clics y unidades por ASIN
   pero NO gasto; el de facturacion trae gasto por campana. Se cruzan por ID de
   campana y el gasto se reparte entre los ASIN de cada campana segun sus CLICS
   (es un reparto, no una medicion: Amazon no publica el gasto por ASIN)."""
import csv, collections, json, re
from parse_br import load
from brands import brand

def n(s):
    s=(s or '').strip().replace('%','')
    try: return float(s)
    except: return 0.0
def cid(s): return re.sub(r'[^0-9]', '', (s or ''))

GASTO = {}
for r in csv.DictReader(open('ads/gasto_2025.csv', encoding='utf-8-sig')):
    c = n(r['Coste total'])
    if c > 0: GASTO[cid(r['ID de la campaña'])] = c

FILAS = list(csv.DictReader(open('ads/asin_2025.csv', encoding='utf-8-sig')))
clics_camp = collections.Counter()
for r in FILAS: clics_camp[cid(r['ID de la campaña'])] += n(r['Clics'])

A = collections.defaultdict(lambda: dict(gasto=0.0, vta=0.0, vta_prop=0.0, clics=0.0,
                                         uds=0.0, title='', marca='', camps=set()))
for r in FILAS:
    c = cid(r['ID de la campaña'])
    if r['País de la campaña'] != 'ES': continue
    asin = r['ID del producto anunciado']
    if not asin: continue
    cl = n(r['Clics'])
    cuota = cl/clics_camp[c] if clics_camp[c] else 0
    a = A[asin]
    a['gasto'] += GASTO.get(c, 0)*cuota
    a['vta']   += n(r['Ventas'])
    a['vta_prop'] += n(r['Ventas (promocionadas)'])
    a['clics'] += cl
    a['uds']   += n(r['Unidades vendidas debidas a clics'])
    a['title'] = r['Nombre del producto anunciado'] or a['title']
    a['marca'] = r['Marca del producto anunciado'] or a['marca']
    a['camps'].add(c)

# ventas totales 2025 por ASIN (Business Report), para el TACOS
BR = collections.defaultdict(lambda: dict(v=0.0, u=0.0, title='', brand=''))
for m in [f'2025-{i:02d}' for i in range(1, 13)]:
    for r in load(f'mensual/{m}.csv'):
        b = BR[r['child']]
        b['v'] += r['sales']; b['u'] += r['units']
        b['title'] = r['title']; b['brand'] = brand(r)

OUT = []
for asin, a in A.items():
    b = BR.get(asin, dict(v=0.0, u=0.0, title='', brand=''))
    OUT.append(dict(asin=asin, title=(b['title'] or a['title'])[:80],
        marca=b['brand'] or a['marca'],
        gasto=round(a['gasto'], 2), vta_atrib=round(a['vta'], 2),
        vta_prop=round(a['vta_prop'], 2), clics=round(a['clics']),
        uds_ads=round(a['uds']), venta_total=round(b['v'], 2), uds_total=round(b['u']),
        acos=round(100*a['gasto']/a['vta'], 1) if a['vta'] else None,
        tacos=round(100*a['gasto']/b['v'], 2) if b['v'] else None,
        cpc=round(a['gasto']/a['clics'], 2) if a['clics'] else None,
        pct_organico=round(100*(1-a['vta']/b['v']), 1) if b['v'] else None,
        ncamp=len(a['camps'])))
OUT.sort(key=lambda x: -x['gasto'])
json.dump(OUT, open('ads_asin_2025.json', 'w'), ensure_ascii=False)

if __name__ == '__main__':
    tg = sum(x['gasto'] for x in OUT); tv = sum(x['vta_atrib'] for x in OUT)
    print(f"PUBLICIDAD POR ASIN — Espana 2025  ({len(OUT)} ASINs anunciados)\n")
    print(f"  Gasto repartido : {tg:>10,.0f} EUR")
    print(f"  Venta atribuida : {tv:>10,.0f} EUR   ->  ACOS global {100*tg/tv:.1f}%")
    print(f"  Clics           : {sum(x['clics'] for x in OUT):>10,.0f}   ->  CPC medio {tg/sum(x['clics'] for x in OUT):.2f} EUR\n")
    h = (f"{'ASIN':<12}{'Marca':<12}{'Gasto':>8}{'Vta atrib':>11}{'ACOS':>7}"
         f"{'Venta total':>12}{'TACOS':>7}{'CPC':>6}  Producto")
    print(h); print('-'*len(h))
    for x in OUT[:20]:
        print(f"{x['asin']:<12}{(x['marca'] or '?')[:11]:<12}{x['gasto']:>8,.0f}{x['vta_atrib']:>11,.0f}"
              f"{(x['acos'] or 0):>6.1f}%{(x['venta_total'] or 0):>12,.0f}"
              f"{(x['tacos'] or 0):>6.1f}%{(x['cpc'] or 0):>6.2f}  {x['title'][:38]}")
    print("\n\nDONDE LA PUBLICIDAD NO SALE A CUENTA (ACOS alto o sin venta total conocida)\n")
    mal = [x for x in OUT if x['gasto'] > 100 and (x['acos'] is None or x['acos'] > 25)]
    print(f"{'ASIN':<12}{'Marca':<12}{'Gasto':>8}{'Vta atrib':>11}{'ACOS':>8}{'TACOS':>8}  Producto")
    for x in sorted(mal, key=lambda x: -(x['acos'] or 999))[:14]:
        print(f"{x['asin']:<12}{(x['marca'] or '?')[:11]:<12}{x['gasto']:>8,.0f}{x['vta_atrib']:>11,.0f}"
              f"{(x['acos'] if x['acos'] is not None else float('nan')):>7.1f}%"
              f"{(x['tacos'] or 0):>7.1f}%  {x['title'][:40]}")
    print(f"\n  {len(mal)} ASINs, {sum(x['gasto'] for x in mal):,.0f} EUR de gasto "
          f"({100*sum(x['gasto'] for x in mal)/tg:.0f}% del total)")
    print(f"\n-> ads_asin_2025.json")

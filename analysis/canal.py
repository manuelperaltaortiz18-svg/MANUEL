"""Margen por producto en los dos canales.
   FBM = tu coste de envio propio (columna 'AMZ. PRIME' del Excel, media 3,30).
   FBA = tarifa de Amazon, pendiente de cargar SKU a SKU.
   Precio = precio medio REALMENTE cobrado en 2026 (venta/uds)."""
import csv, re, collections, json
from parse_br import load
from brands import brand
from pl import COSTES, V

RATE     = 0.1545   # comision observada
FBM_DEF  = 3.30     # media declarada de tu envio propio
# Tarifas FBA reales, a rellenar segun las vayas sacando:  {'SKU': 4.12, ...}
FBA_TARIFA = {}

def norm(s): return re.sub(r'[^A-Z0-9]', '', s.upper())

def ventas(base):
    nb = norm(base); u = v = 0.0; hit = []
    for s, a in V.items():
        ns = norm(s)
        if (ns == nb
            or re.fullmatch(r'F?' + re.escape(nb) + r'(FBA|FBM|US|USS|CAJA|PP|PREMIUM|PACK|\d{0,3})?', ns)
            or (nb == '2210522106' and re.fullmatch(r'F?22105(Y|PACK)?22106(PACK)?', ns))):
            u += a['u']; v += a['v']; hit.append(s)
    return u, v, hit

# --- catalogo de costes: hoja original + altas nuevas ---
CAT = {}
for cs, d in COSTES.items():
    CAT[cs] = dict(sku=cs, coste=d['COSTE'], fbm=d['FBA'], fuente='hoja')
for r in csv.DictReader(open('costes/nuevos.tsv', encoding='utf-8'), delimiter='\t'):
    if r['COSTE'].strip() == '-':
        CAT[r['SKU_COSTE']] = dict(sku=r['SKU_COSTE'], baja=True, nota=r['NOTA']); continue
    her = r['FBA_HEREDADA_DE'].strip()
    fbm = COSTES[her]['FBA'] if her in COSTES else None
    CAT[r['SKU_COSTE']] = dict(sku=r['SKU_COSTE'], coste=float(r['COSTE']),
                               fbm=fbm, fuente='alta', nota=r['NOTA'])

filas = []
for cs, c in CAT.items():
    if c.get('baja'):
        u, v, _ = ventas(cs)
        filas.append(dict(sku=cs, baja=True, uds=round(u), venta=round(v), nota=c['nota']))
        continue
    u, v, hit = ventas(cs)
    if u == 0: continue
    p = v / u
    iva = p * 0.21 / 1.21
    fee = p * RATE
    neto = p - iva
    base = neto - fee - c['coste']            # margen ANTES de logistica
    fbm = c['fbm'] if c['fbm'] is not None else FBM_DEF
    fbm_sup = c['fbm'] is None
    m_fbm = base - fbm
    tfba = FBA_TARIFA.get(cs)
    m_fba = base - tfba if tfba is not None else None
    ref = V[hit[0]]
    filas.append(dict(
        sku=cs, skus=', '.join(sorted(hit)), title=ref['title'][:80], brand=ref['brand'],
        uds=round(u), venta=round(v, 2), precio=round(p, 2),
        coste=round(c['coste'], 3), fee=round(fee, 3), iva=round(iva, 3), neto=round(neto, 3),
        base=round(base, 3),                              # margen antes de logistica
        envio_fbm=round(fbm, 2), fbm_supuesto=fbm_sup,
        m_fbm=round(m_fbm, 3), pct_fbm=round(100*m_fbm/neto, 1),
        contrib_fbm=round(m_fbm*u, 2),
        tarifa_fba=tfba,
        m_fba=round(m_fba, 3) if m_fba is not None else None,
        pct_fba=round(100*m_fba/neto, 1) if m_fba is not None else None,
        equilibrio=round(fbm, 2),     # tarifa FBA a la que empata con tu envio
        fuente=c['fuente'], baja=False))
filas.sort(key=lambda f: -(f.get('contrib_fbm') or 0))

if __name__ == '__main__':
    act = [f for f in filas if not f['baja']]
    sup = [f for f in act if f['fbm_supuesto']]
    T = dict(u=sum(f['uds'] for f in act), v=sum(f['venta'] for f in act),
             neto=sum(f['neto']*f['uds'] for f in act),
             base=sum(f['base']*f['uds'] for f in act),
             log=sum(f['envio_fbm']*f['uds'] for f in act),
             c=sum(f['contrib_fbm'] for f in act))
    print("MARGEN POR PRODUCTO — escenario FBM (tu envio propio)\n")
    print(f"  SKUs con venta        : {len(act)}")
    print(f"  Unidades              : {T['u']:,.0f}")
    print(f"  Venta (con IVA)       : {T['v']:,.0f} EUR")
    print(f"  Venta neta            : {T['neto']:,.0f} EUR")
    print(f"  Margen antes logistica: {T['base']:,.0f} EUR ({100*T['base']/T['neto']:.1f}% s/neto)")
    print(f"  Coste de envio propio : {T['log']:,.0f} EUR ({100*T['log']/T['neto']:.1f}% s/neto)")
    print(f"  CONTRIBUCION FBM      : {T['c']:,.0f} EUR ({100*T['c']/T['neto']:.1f}% s/neto)")
    print(f"\n  La logistica se lleva el {100*T['log']/T['base']:.0f}% de tu margen antes de enviar nada.")
    print(f"  FBM supuesto en {len(sup)} SKUs ({sum(f['uds'] for f in sup):,.0f} uds).\n")
    h = (f"{'SKU':<13}{'Uds':>6}{'Precio':>8}{'Coste':>7}{'Comis':>7}{'Mg s/log':>9}"
         f"{'Envio':>7}{'Mg FBM':>8}{'%':>5}{'Contrib':>9}{'FBA empata si <':>16}")
    print(h); print('-'*len(h))
    for f in act[:16]:
        print(f"{f['sku']:<13}{f['uds']:>6,}{f['precio']:>8.2f}{f['coste']:>7.2f}{f['fee']:>7.2f}"
              f"{f['base']:>9.2f}{f['envio_fbm']:>7.2f}{f['m_fbm']:>8.2f}{f['pct_fbm']:>4.0f}%"
              f"{f['contrib_fbm']:>9,.0f}{f['equilibrio']:>15.2f} ")
    print('  ...')
    for f in act[-5:]:
        print(f"{f['sku']:<13}{f['uds']:>6,}{f['precio']:>8.2f}{f['coste']:>7.2f}{f['fee']:>7.2f}"
              f"{f['base']:>9.2f}{f['envio_fbm']:>7.2f}{f['m_fbm']:>8.2f}{f['pct_fbm']:>4.0f}%"
              f"{f['contrib_fbm']:>9,.0f}{f['equilibrio']:>15.2f} ")
    print("\nDONDE LA LOGISTICA SE COME MAS DE LA MITAD DEL MARGEN (candidatos a FBA o a subir precio)\n")
    peor = sorted([f for f in act if f['base'] > 0 and f['uds'] > 30],
                  key=lambda f: -f['envio_fbm']/f['base'])[:12]
    print(f"{'SKU':<13}{'Uds':>6}{'Precio':>8}{'Mg s/log':>9}{'Envio':>7}{'% del mg':>10}{'Mg FBM':>8}{'%neto':>7}")
    for f in peor:
        print(f"{f['sku']:<13}{f['uds']:>6,}{f['precio']:>8.2f}{f['base']:>9.2f}{f['envio_fbm']:>7.2f}"
              f"{100*f['envio_fbm']/f['base']:>9.0f}%{f['m_fbm']:>8.2f}{f['pct_fbm']:>6.0f}%")
    json.dump(filas, open('canal.json', 'w'), ensure_ascii=False)
    print(f"\n-> canal.json ({len(filas)} filas)")

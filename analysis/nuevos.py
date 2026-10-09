"""Calcula el margen de los SKUs de Cuperinox recien costeados.
   El precio usado es el PRECIO MEDIO REALMENTE COBRADO en 2026 (venta/uds),
   no una tarifa: incluye promos, multipack y B2B."""
import csv, re, collections
from parse_br import load
from brands import brand
from pl import COSTES, V

RATE = 0.1545          # comision observada en toda la hoja
FBA_DEF = 3.39         # valor mas frecuente, usado SOLO como hipotesis

HERED = {}
for cs, d in COSTES.items(): HERED[cs] = d['FBA']

nuevos = []
for r in csv.DictReader(open('costes/nuevos.tsv', encoding='utf-8'), delimiter='\t'):
    if r['COSTE'].strip() == '-':
        nuevos.append(dict(sku=r['SKU_COSTE'], baja=True, nota=r['NOTA'])); continue
    fba = HERED.get(r['FBA_HEREDADA_DE'])
    nuevos.append(dict(sku=r['SKU_COSTE'], coste=float(r['COSTE']), fba=fba,
                       fba_origen=r['FBA_HEREDADA_DE'] if fba else None,
                       nota=r['NOTA'], baja=False))

def norm(s): return re.sub(r'[^A-Z0-9]', '', s.upper())
def ventas_de(base):
    nb = norm(base); u = v = 0.0; hit = []
    for s, a in V.items():
        ns = norm(s)
        # prefijo opcional (F...) y sufijos de variante; cubre 22105y22106, F22105-22106, +pack
        if (ns == nb or re.fullmatch(r'F?' + re.escape(nb) + r'(FBA|FBM|US|USS|CAJA|PP|PREMIUM|PACK|\d{0,3})?', ns)
                or (nb == '2210522106' and re.fullmatch(r'F?22105(Y|PACK)?22106(PACK)?', ns))):
            u += a['u']; v += a['v']; hit.append(s)
    return u, v, hit

print("NUEVOS COSTES DE CUPERINOX — margen al precio medio realmente cobrado en 2026\n")
h = (f"{'SKU':<11}{'Uds':>6}{'Venta':>9}{'P.medio':>9}{'Coste':>7}{'FBA':>6}{'Comis':>7}"
     f"{'IVA':>7}{'Mg/ud':>8}{'%neto':>7}{'Contrib':>9}")
print(h); print('-' * len(h))
tot_c = tot_v = tot_u = 0.0; sinfba = []
for n in nuevos:
    if n['baja']:
        u, v, _ = ventas_de(n['sku'])
        print(f"{n['sku']:<11}{u:>6,.0f}{v:>9,.0f}   DESCATALOGADO — {n['nota']}")
        continue
    u, v, hit = ventas_de(n['sku'])
    if u == 0:
        print(f"{n['sku']:<11}{0:>6}{0:>9}   sin ventas localizadas con ese SKU")
        continue
    p = v / u
    fba = n['fba'] if n['fba'] is not None else FBA_DEF
    if n['fba'] is None: sinfba.append(n['sku'])
    iva = p * 0.21 / 1.21; fee = p * RATE; neto = p - iva
    m = neto - fee - fba - n['coste']
    marca = '*' if n['fba'] is None else ' '
    tot_c += m * u; tot_v += v; tot_u += u
    print(f"{n['sku']:<11}{u:>6,.0f}{v:>9,.0f}{p:>9.2f}{n['coste']:>7.2f}{fba:>5.2f}{marca}"
          f"{fee:>7.2f}{iva:>7.2f}{m:>8.2f}{100*m/neto:>6.0f}%{m*u:>9,.0f}")
print('-' * len(h))
print(f"{'TOTAL':<11}{tot_u:>6,.0f}{tot_v:>9,.0f}{'':>9}{'':>7}{'':>6}{'':>7}{'':>7}{'':>8}"
      f"{100*tot_c/(tot_v/1.21):>6.0f}%{tot_c:>9,.0f}")
print(f"\n* FBA no declarada: uso {FBA_DEF} EUR como hipotesis en {len(sinfba)} SKUs -> {', '.join(sinfba)}")
print(f"  Cada 1 EUR de error en la tarifa FBA mueve {tot_u:,.0f} EUR de contribucion en estos SKUs.")

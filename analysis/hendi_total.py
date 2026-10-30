"""Hendi consolidado: Amazon (5 mercados) + Makro/Metro (4 paises).
Cruza referencias entre canales por MPN y calcula margen con la hoja maestra."""
import sys, csv, json, collections, re
sys.path.insert(0, '.')
from openpyxl import load_workbook
from parse_br import load
from brands import brand

# Amazon reporta la venta CON IVA; Makro reporta "Net Sales", ya neto.
IVA = {'ES': 1.21, 'FR': 1.20, 'IT': 1.22, 'DE': 1.19, 'NL': 1.21, 'PT': 1.23}
DTO, FEE_AMZ = 0.55, 0.1545

def num(x):
    if x is None: return 0.0
    if isinstance(x, (int, float)): return float(x)
    s = str(x).replace('€', '').strip()
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    try: return float(s)
    except ValueError: return 0.0

# ---- coste: hoja maestra por MPN
COSTE = {}
for r in load_workbook('costes/hendi_raw/hendi.xlsx', data_only=True,
                       read_only=True)['Hoja1'].iter_rows(min_row=2, values_only=True):
    mpn = str(r[3]).strip() if r[3] is not None else ''
    if mpn and num(r[4]): COSTE[mpn] = num(r[4]) * (1 - DTO)

mpn_de_sku = lambda s: (s or '').upper().lstrip('H').split('_')[0]

# ---- Amazon: Espana por SKU (ene-sep 2026 y 2025), + mercados exteriores
def amz(ms):
    D = collections.defaultdict(lambda: dict(v=0., u=0., t=''))
    for m in ms:
        for r in load(f'mensual/{m}.csv'):
            if brand(r) != 'Hendi': continue
            d = D[mpn_de_sku(r['sku'])]
            d['v'] += r['sales']; d['u'] += r['units']
            if not d['t']: d['t'] = r['title'][:60]
    return D
A25 = amz([f'2025-{i:02d}' for i in range(1, 10)])
A26 = amz([f'2026-{i:02d}' for i in range(1, 10)])
# (bruto, meses, pais) -> se netea con el IVA de cada mercado
EXT = {'Francia': (3035.0, 8.2, 'FR'), 'Italia': (11406.0, 20.2, 'IT'),
       'Alemania': (339.0, 20.2, 'DE')}

# ---- Makro por MPN
def makro(p, meses):
    D = collections.defaultdict(lambda: dict(v=0., u=0., t='', plats=set()))
    for r in load_workbook(p, data_only=True, read_only=True)['Export'].iter_rows(
            min_row=2, values_only=True):
        if not r[1]: continue
        mm = str(r[10] or '').upper(); g = str(r[2] or '')
        if not ('HENDI' in mm or 'ARKTIC' in mm or g.startswith('8711369')): continue
        k = str(r[9] or g)
        d = D[k]; d['v'] += num(r[4]); d['u'] += num(r[5]); d['plats'].add(str(r[1]))
        if not d['t']: d['t'] = str(r[3] or '')[:60]
    return D, meses
M25, m25 = makro('makro_raw/makro_2025.xlsx', 12.0)
M26, m26 = makro('makro_raw/makro_2026.xlsx', 10.0)

sv = lambda D: sum(d['v'] for d in D.values())
A_ES_25, A_ES_26 = sv(A25)/IVA['ES'], sv(A26)/IVA['ES']   # neteado
MK_25, MK_26 = sv(M25), sv(M26)
ext_mes = sum(v / IVA[c] / m for v, m, c in EXT.values())

print("="*78); print("HENDI CONSOLIDADO — TODO NETO DE IVA"); print("="*78)
print(f"{'canal':28s}{'base':>16s}{'€/mes':>11s}{'anualizado':>13s}")
fil = [('Amazon España', A_ES_26, 9.0, A_ES_25, 9.0),
       ('Makro / Metro (4 países)', MK_26, m26, MK_25, m25)]
for n, v, m, va, ma in fil:
    print(f"{n:28s}{v:13,.0f} €{v/m:11,.0f}{v/m*12:13,.0f}")
print(f"{'Amazon FR + IT + DE':28s}{'ver nota':>15s}{ext_mes:11,.0f}{ext_mes*12:13,.0f}")
TM = A_ES_26/9 + MK_26/m26 + ext_mes
print(f"{'TOTAL':28s}{'':15s}{TM:11,.0f}{TM*12:13,.0f}")
print(f"\nCrecimiento en €/mes, mismos canales:")
am = (A_ES_26/9)/(A_ES_25/9)-1; mm = (MK_26/m26)/(MK_25/m25)-1
print(f"  Amazon España    {A_ES_25/9:9,.0f} → {A_ES_26/9:9,.0f} €/mes  {am*100:+.0f}%")
print(f"  Makro / Metro    {MK_25/m25:9,.0f} → {MK_26/m26:9,.0f} €/mes  {mm*100:+.0f}%")
tv25 = A_ES_25/9 + MK_25/m25; tv26 = A_ES_26/9 + MK_26/m26
print(f"  Los dos juntos   {tv25:9,.0f} → {tv26:9,.0f} €/mes  {(tv26/tv25-1)*100:+.0f}%")

print(f"\nReferencias con facturacion:")
print(f"  Amazon ES   2025 {len(A25):5d}  2026 {len(A26):5d}")
print(f"  Makro       2025 {len(M25):5d}  2026 {len(M26):5d}")
sa, sm = set(A26), set(M26)
print(f"\nCRUCE DE REFERENCIAS 2026 (por MPN)")
print(f"  solo Amazon        {len(sa-sm):5d}  {sum(A26[k]['v'] for k in sa-sm):11,.0f} €")
print(f"  solo Makro         {len(sm-sa):5d}  {sum(M26[k]['v'] for k in sm-sa):11,.0f} €")
print(f"  en los dos canales {len(sa&sm):5d}  {sum(A26[k]['v'] for k in sa&sm)+sum(M26[k]['v'] for k in sa&sm):11,.0f} €")
print(f"  universo conjunto  {len(sa|sm):5d} referencias distintas")

# margen
def margen(D, fee_pct):
    M = C = 0.0
    for k, d in D.items():
        c = COSTE.get(k)
        if c is None or not d['u']: continue
        p = d['v'] / d['u']
        M += (p / IVA['ES'] - p * fee_pct - c) * d['u']; C += d['v']
    return M, C
ma_, ca_ = margen(A26, FEE_AMZ)
mm_, cm_ = margen(M26, 0.0)      # en Makro la comision va en el neto reportado
print(f"\nMARGEN (coste real, dto {DTO:.0%}) — solo interno, NO va en la propuesta")
print(f"  Amazon ES: cubre {ca_:,.0f} € de {A_ES_26:,.0f} ({ca_/A_ES_26:.0%}) → margen {100*ma_/ca_:.1f}% s/bruto")
print(f"  Makro:     cubre {cm_:,.0f} € de {MK_26:,.0f} ({cm_/MK_26:.0%}) → margen {100*mm_/cm_:.1f}% s/neto reportado")

json.dump(dict(amz_es=dict(v25=A_ES_25, v26=A_ES_26, meses=9),
               makro=dict(v25=MK_25, v26=MK_26, m25=m25, m26=m26),
               ext_mes=ext_mes, total_mes=TM,
               refs=dict(amz=len(sa), makro=len(sm), solo_amz=len(sa-sm),
                         solo_makro=len(sm-sa), ambos=len(sa&sm), union=len(sa|sm))),
          open('hendi_total.json','w'), ensure_ascii=False, indent=1)

"""Cruza el informe de campanas (ES) con los Business Reports del mismo periodo.
Periodo del fichero de ads: 1 jul 2025 - 31 jul 2026 (13 meses)."""
import csv, re, collections
from parse_br import load
from brands import brand, SUPPLIER

# Publicidad: 1 ene 2026 - 15 oct 2026 (288 dias)
# Ventas:     1 ene 2026 - 22 sep 2026 (265 dias) -> el gasto se prorratea
# Gasto completo (200 filas ordenadas por gasto desc: cubre el 98,9% del total
# declarado, 85.851,61 EUR de 86.808,68). NO trae ventas atribuidas.
ADS_CSV = 'ads/campaigns_2026_full.csv'
# Export anterior, truncado a 200 filas sin ordenar: solo sirve para el ACOS
# de las campanas que si aparecen.
ADS_ATRIB = 'ads/campaigns_2026-01_2026-10-15.csv'
DIAS_ADS, DIAS_BR = 288, 273   # ads a 15 oct; ventas ene-sep
MESES = [f'2026-{m:02d}' for m in range(1,10)]  # ene-sep completos

# marca inferida del nombre de campana
ADRULES = [
    ('Arcos',       r'ARCOS'),
    ('Cuperinox',   r'CUPERINOX'),
    ('Hendi',       r'HENDI'),
    ('Bioleaf',     r'BIOLEAF|GEL WC|MULTIUSOS|DESINCRUSTANTE|LIMPIACRISTALES|DETERGENTE BIBERONES'),
    ('Vinfermaton', r'INSECTICIDA|AVISPAS|HORMIGAS|CUCARACHAS|POLILLAS|MOSQUITOS|FRIEGASUELOS'),
    ('Wins',        r'\bWINS\b'),
    ('Vinfer',      r'\bVINFER\b|MOPAS'),
    # Campanas de video y de SKU suelto, sin marca en el nombre ni cartera
    ('Cuperinox',   r'CUCHILLOS NI[NÑ]OS|BALANC[IÍ]N|TUPPERS|JAMONER|CAFETER|ACEITER|TETERA'
                    r'|^\s*SP_CU|NAVAJA SETAS|CUCHILLO[S]? (DE )?(SIERRA|CARNE|MESA|COCINA)'
                    r'|^\s*\d{5}\s*$'),
    ('Vincare',     r'VINCARE|BIBERON'),
]
def ad_brand(name):
    u = name.upper()
    for b, p in ADRULES:
        if re.search(p, u): return b
    return 'Sin clasificar'

def money(s):
    s = (s or '').replace('€','').replace('GBP','').strip()
    return float(s.replace('.','').replace(',','.')) if any(c.isdigit() for c in s) else 0.0

def col(r, *nombres):
    """El export cambia de cabeceras entre versiones."""
    for n in nombres:
        if n in r: return r[n]
    return None

def load_ads(path, pais='España'):
    """Agrupa por marca. Usa la cartera cuando existe (agrupa mejor que el
       nombre de campana) y cae al nombre cuando no."""
    g = collections.defaultdict(lambda: dict(gasto=0.0, vta=0.0, clics=0.0,
                                             impr=0.0, n=0))
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        if col(r, 'País', 'País de la campaña') != pais: continue
        c = money(r['Coste total (convertido)'])
        if c <= 0: continue
        # El NOMBRE de campana nombra el producto y manda; la cartera solo
        # desempata cuando el nombre no dice nada ("20280", "VIDEO BALANCIN").
        # Ojo: la cartera "AZ - VINFER (Cuperinox)" lleva campanas de
        # insecticidas, asi que fiarse de ella invierte la marca.
        marca = ad_brand(r['Nombre de la campaña'])
        if marca == 'Sin clasificar':
            marca = ad_brand(col(r, 'Nombre de la cartera') or '')
        a = g[marca]
        a['gasto'] += c; a['vta'] += money(col(r, 'Ventas (convertido)') or '0')
        a['clics'] += money(r.get('Clics', '0'))
        a['impr']  += money(r.get('Impresiones', '0'))
        a['n'] += 1
    return g

def combinar(pais='España'):
    """Gasto del export completo + ventas atribuidas del export que las trae.
       Devuelve tambien que parte del gasto tiene atribucion conocida."""
    full = load_ads(ADS_CSV, pais)
    atr  = load_ads(ADS_ATRIB, pais)
    out = {}
    for b in set(full) | set(atr):
        f, a = full.get(b, {}), atr.get(b, {})
        out[b] = dict(gasto=f.get('gasto', 0.0), clics=f.get('clics', 0.0),
                      n=f.get('n', 0),
                      vta=a.get('vta', 0.0), gasto_atr=a.get('gasto', 0.0))
    return out

def load_br(meses):
    """Ventas 2026 hasta el 22 de septiembre (el YTD, no solo los meses)."""
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

ads, br = combinar(), load_br(MESES)
print(f"PUBLICIDAD x NEGOCIO REAL — Espana\n"
      f"  Publicidad: 1 ene - 15 oct 2026 ({DIAS_ADS} dias)\n"
      f"  Ventas    : 1 ene - 30 sep 2026 ({DIAS_BR} dias)\n"
      f"  El TACOS se calcula con el gasto prorrateado a la ventana de ventas.\n")
h = (f"{'Marca':<14}{'Venta total':>12}{'Gasto ads':>10}{'% con atrib':>12}{'ACOS':>7}"
     f"{'TACOS':>7}{'Margen min':>11}{'Margen-ads':>11}{'Veredicto':>12}")
print(h); print('-'*len(h))
tv=tg=0
for b in sorted(set(br)|set(ads), key=lambda b: -br.get(b,{}).get('v',0)):
    v = br.get(b,{}).get('v',0); a = ads.get(b, dict(gasto=0,vta=0,gasto_atr=0))
    if v < 1000 and a['gasto'] < 50: continue
    gasto_pro = a['gasto']*DIAS_BR/DIAS_ADS          # a la ventana de ventas
    tv += v; tg += gasto_pro
    lo,hi = MG.get(b,(15,25)); mn = v*lo/100
    neto = mn - gasto_pro
    acos  = 100*a['gasto_atr']/a['vta'] if a['vta'] else 0   # solo el subconjunto con atribucion
    tacos = 100*gasto_pro/v if v else 0
    ver = 'PIERDE' if neto < 0 else ('revisar' if tacos > lo*0.5 else 'ok')
    cob = 100*a['gasto_atr']/a['gasto'] if a['gasto'] else 0
    print(f"{b:<14}{v:>12,.0f}{gasto_pro:>10,.0f}{cob:>11.0f}%"
          f"{acos:>6.1f}%{tacos:>6.1f}%{mn:>11,.0f}{neto:>11,.0f}{ver:>12}")
print('-'*len(h))
print(f"{'TOTAL':<14}{tv:>12,.0f}{tg:>10,.0f}{'':>11}{'':>7}{100*tg/tv:>6.1f}%")

print("\nEl veredicto usa el margen MINIMO de tu rango (el caso prudente).")
print("'% con atrib' = parte del gasto para la que conozco la venta atribuida;")
print("el ACOS solo es fiable cuando ese porcentaje es alto.")
print("ACOS  = gasto / venta atribuida al anuncio (eficiencia del anuncio).")
print("TACOS = gasto / venta total de la marca (cuanto te cuesta sostenerla).")

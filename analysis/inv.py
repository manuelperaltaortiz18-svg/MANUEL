"""Cruza el Inventory Planning Forecast de FBA con la velocidad de venta real.
   OJO: el forecast NO trae stock disponible ni en transito, asi que esto es la
   MITAD de una recomendacion de reposicion: cubre la demanda, no la cobertura."""
import openpyxl, collections, json, warnings
from parse_br import load
from brands import brand
warnings.filterwarnings('ignore')

wb = openpyxl.load_workbook('inv/forecast_fba.xlsx', read_only=True, data_only=True)
ws = wb['Inventory Planning Forecast']
raw = list(ws.iter_rows(values_only=True))
semanas = [str(c).replace('\n', ' ').split('(')[1].split('-')[0] for c in raw[0][4:30]]
F = {}
for r in raw[1:]:
    F.setdefault(r[0], {})[r[2]] = [float(x or 0) for x in r[4:30]]

def porasin(f):
    rr = load(f); by = collections.defaultdict(list); out = {}
    for r in rr: by[r['child']].append(r)
    for c, rs in by.items():
        out[c] = dict(title=rs[0]['title'], brand=brand(rs[0]),
                      sku=', '.join(sorted({r['sku'] for r in rs if r['sku']})),
                      v=sum(r['sales'] for r in rs), u=sum(r['units'] for r in rs))
    return out

YTD = porasin('data_BusinessReport_2026ytd_22sep.csv')
ENE_AGO = collections.defaultdict(lambda: dict(u=0.0, v=0.0))
for m in [f'2026-{i:02d}' for i in range(1, 9)]:
    for c, x in porasin(f'mensual/{m}.csv').items():
        ENE_AGO[c]['u'] += x['u']; ENE_AGO[c]['v'] += x['v']
AGO = porasin('mensual/2026-08.csv')
JUL = porasin('mensual/2026-07.csv')

# Ventanas de velocidad disponibles con los datos que tengo
VENT = [('sep 1-22', 22), ('agosto', 31), ('jul+ago+sep', 84)]
filas = []
for a, d in F.items():
    y = YTD.get(a); 
    if not y: y = dict(title='(sin ventas en 2026)', brand='?', sku='', u=0, v=0)
    u_sep = y['u'] - ENE_AGO[a]['u']
    u_ago = AGO.get(a, {'u': 0})['u']
    u_jul = JUL.get(a, {'u': 0})['u']
    vel = {'sep 1-22': u_sep/22, 'agosto': u_ago/31, 'jul+ago+sep': (u_jul+u_ago+u_sep)/84}
    mean, p90 = d.get('MEAN', [0]*26), d.get('P90', [0]*26)
    filas.append(dict(asin=a, title=y['title'], brand=y['brand'], sku=y['sku'],
        u2026=round(y['u']), v2026=round(y['v']),
        vsep=round(vel['sep 1-22'], 2), vago=round(vel['agosto'], 2),
        v84=round(vel['jul+ago+sep'], 2),
        m4=round(sum(mean[:4])), m8=round(sum(mean[:8])), m13=round(sum(mean[:13])),
        p4=round(sum(p90[:4])), p8=round(sum(p90[:8])), p13=round(sum(p90[:13])),
        mean=[round(x) for x in mean[:13]], p90=[round(x) for x in p90[:13]],
        # cuanto se desvia el forecast de Amazon de tu propia velocidad reciente
        ratio=round((sum(mean[:4])/4/7) / vel['sep 1-22'], 2) if vel['sep 1-22'] > 0.01 else None))
filas.sort(key=lambda f: -f['m13'])

tot = dict(
    asins=len(filas),
    asins_catalogo=len(YTD),
    v_cubierta=round(sum(YTD[a]['v'] for a in F if a in YTD)),
    v_total=round(sum(x['v'] for x in YTD.values())),
    u_cubierta=round(sum(YTD[a]['u'] for a in F if a in YTD)),
    u_total=round(sum(x['u'] for x in YTD.values())),
    semanas=semanas[:13],
    mean=[round(sum(F[a]['MEAN'][i] for a in F)) for i in range(13)],
    p90=[round(sum(F[a]['P90'][i] for a in F)) for i in range(13)],
    creado=raw[1][3])
json.dump(dict(resumen=tot, filas=filas), open('inventario.json', 'w'), ensure_ascii=False)

print(f"Forecast FBA creado {tot['creado']} | {tot['asins']} ASINs de {tot['asins_catalogo']} del catalogo")
print(f"Cubre {100*tot['v_cubierta']/tot['v_total']:.1f}% de la venta y "
      f"{100*tot['u_cubierta']/tot['u_total']:.1f}% de las unidades\n")
print("DEMANDA PREVISTA POR SEMANA (unidades, los 157 ASINs FBA)")
print(f"{'Semana':<12}{'MEAN':>8}{'P90':>8}{'P90/MEAN':>10}")
for i, s in enumerate(tot['semanas']):
    print(f"{s:<12}{tot['mean'][i]:>8,}{tot['p90'][i]:>8,}{tot['p90'][i]/max(tot['mean'][i],1):>9.1f}x")
print(f"{'13 semanas':<12}{sum(tot['mean']):>8,}{sum(tot['p90']):>8,}")

print("\nDONDE EL FORECAST DE AMAZON NO CUADRA CON TU VELOCIDAD REAL")
print("(ratio = uds/dia que prevé Amazon ÷ uds/dia reales de sep 1-22)\n")
print(f"{'ratio':>7}{'v.sep/dia':>10}{'prev/dia':>10}{'MEAN 13s':>10}  {'SKU':<24} Producto")
cand = [f for f in filas if f['ratio'] and f['u2026'] > 100]
for f in sorted(cand, key=lambda f: -f['ratio'])[:8]:
    print(f"{f['ratio']:>6.1f}x{f['vsep']:>10.2f}{f['m4']/28:>10.2f}{f['m13']:>10,}  {f['sku'][:23]:<24} {f['title'][:38]}")
print('  ...')
for f in sorted(cand, key=lambda f: f['ratio'])[:6]:
    print(f"{f['ratio']:>6.1f}x{f['vsep']:>10.2f}{f['m4']/28:>10.2f}{f['m13']:>10,}  {f['sku'][:23]:<24} {f['title'][:38]}")

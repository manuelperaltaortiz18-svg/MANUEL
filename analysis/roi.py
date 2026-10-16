"""Que ha pasado con las ventas cuando ha subido la inversion publicitaria.
   Ventana identica ene-ago, Espana. El gasto anual se prorratea a esa ventana."""
import csv, collections, json, re
from parse_br import load
from brands import brand
from ads import ad_brand, money, col, load_ads, ADS_CSV

D25, D26, W = 365, 288, 243        # dias del ano / del export 2026 / de ene-ago

def n(s):
    try: return float((s or '').strip())
    except: return 0.0

# --- publicidad por marca ---
def marca25(r):
    m = ad_brand(r['Nombre de la campaña'])
    return m if m != 'Sin clasificar' else ad_brand(r.get('Nombre de la cartera') or '')
A25 = collections.Counter()
for r in csv.DictReader(open('ads/gasto_2025.csv', encoding='utf-8-sig')):
    if r['País de la campaña'] == 'ES' and n(r['Coste total']) > 0:
        A25[marca25(r)] += n(r['Coste total']) * W / D25
A26 = collections.Counter()
for b, v in load_ads(ADS_CSV, 'España').items():
    A26[b] += v['gasto'] * W / D26

# --- ventas por marca, ene-ago ---
def ventas(anio):
    g = collections.Counter()
    for m in [f'{anio}-{i:02d}' for i in range(1, 9)]:
        for r in load(f'mensual/{m}.csv'): g[brand(r)] += r['sales']
    return g
V25, V26 = ventas(2025), ventas(2026)

MG = {'Arcos':15,'Cuperinox':25,'Hendi':20,'Vinfermaton':15,'Wins':15,'Bioleaf':15,
      'Vinfer':15,'Vincare':15,'La Garrafita':15,'Tradineur':15,'Sin marca':15}

filas = []
for b in set(V25) | set(V26) | set(A25) | set(A26):
    v25, v26 = V25.get(b, 0), V26.get(b, 0)
    a25, a26 = A25.get(b, 0), A26.get(b, 0)
    if max(v25, v26) < 5000 and max(a25, a26) < 200: continue
    dv, da = v26 - v25, a26 - a25
    mg = MG.get(b, 15)
    filas.append(dict(marca=b, v25=round(v25), v26=round(v26), dv=round(dv),
        a25=round(a25), a26=round(a26), da=round(da), mg=mg,
        # margen bruto que aporta el crecimiento, menos lo que ha costado en ads
        mg_extra=round(dv*mg/100), neto=round(dv*mg/100 - da),
        roas_inc=round(dv/da, 1) if da > 0 else None,
        # cuanto tendria que haber crecido para pagar el aumento de publicidad
        umbral=round(da*100/mg) if da > 0 else 0))
filas.sort(key=lambda f: -f['dv'])
json.dump(filas, open('roi.json', 'w'), ensure_ascii=False)

if __name__ == '__main__':
    T = {k: sum(f[k] for f in filas) for k in ('v25','v26','dv','a25','a26','da','mg_extra','neto')}
    print("¿HA SALIDO A CUENTA SUBIR LA PUBLICIDAD?")
    print("Ventana identica ene-ago, Espana. Margen = el minimo de tu rango.\n")
    print(f"  Ventas    {T['v25']:>11,.0f}  ->  {T['v26']:>11,.0f}   {T['dv']:>+11,.0f}  ({100*T['dv']/T['v25']:+.0f}%)")
    print(f"  Publicidad{T['a25']:>11,.0f}  ->  {T['a26']:>11,.0f}   {T['da']:>+11,.0f}  ({100*T['da']/T['a25']:+.0f}%)")
    print(f"\n  Margen bruto que aporta ese crecimiento : {T['mg_extra']:>+10,.0f} EUR")
    print(f"  Coste del aumento de publicidad         : {-T['da']:>+10,.0f} EUR")
    print(f"  NETO                                    : {T['neto']:>+10,.0f} EUR")
    print(f"\n  Por cada euro extra de publicidad entran {T['dv']/T['da']:,.0f} EUR de venta extra.\n")
    h = (f"{'Marca':<14}{'Vta 25':>10}{'Vta 26':>10}{'Δ venta':>11}{'Ads 25':>8}{'Ads 26':>8}"
         f"{'Δ ads':>8}{'Mg%':>5}{'Mg extra':>10}{'NETO':>10}{'ROAS inc':>9}")
    print(h); print('-'*len(h))
    for f in filas:
        print(f"{f['marca']:<14}{f['v25']:>10,.0f}{f['v26']:>10,.0f}{f['dv']:>+11,.0f}"
              f"{f['a25']:>8,.0f}{f['a26']:>8,.0f}{f['da']:>+8,.0f}{f['mg']:>4}%"
              f"{f['mg_extra']:>+10,.0f}{f['neto']:>+10,.0f}"
              f"{(('%.0fx' % f['roas_inc']) if f['roas_inc'] else '—'):>9}")
    print('-'*len(h))
    print(f"{'TOTAL':<14}{T['v25']:>10,.0f}{T['v26']:>10,.0f}{T['dv']:>+11,.0f}"
          f"{T['a25']:>8,.0f}{T['a26']:>8,.0f}{T['da']:>+8,.0f}{'':>5}"
          f"{T['mg_extra']:>+10,.0f}{T['neto']:>+10,.0f}{T['dv']/T['da']:>8,.0f}x")

    print("\n\nLA PRUEBA DE CONTROL: crecimiento CON y SIN publicidad\n")
    con = [f for f in filas if f['da'] > 200]
    sin = [f for f in filas if f['da'] <= 200]
    for et, g in [('Marcas donde SUBISTE la inversion', con), ('Marcas donde NO la subiste', sin)]:
        v25 = sum(f['v25'] for f in g); v26 = sum(f['v26'] for f in g)
        da = sum(f['da'] for f in g)
        print(f"  {et:<36} {v25:>10,.0f} -> {v26:>10,.0f}  ({100*(v26-v25)/v25:+.0f}%)"
              f"   ads {da:>+8,.0f}")
        print(f"     {', '.join(f['marca'] for f in g)}")

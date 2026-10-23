"""Publicidad por pais y marca, ventana identica en los dos anos (ene-20 oct).
Fuente: informe de producto anunciado, que es el unico que trae el mercado."""
import csv, json, collections

F25, F26 = 'ads/terminos/producto_anunciado_2025.csv', 'ads/terminos/producto_anunciado_2026.csv'
VENTANA = 'ene–20 oct'
PAIS = 'País del producto anunciado-Advertised product marketplace'
# margen declarado/real sobre venta bruta: ACOS de equilibrio por marca
EQUILIBRIO = {'CUPERINOX': 28.1, 'HENDI': 17.5, 'VINFERMATON': 16.4, 'VINFER': 16.4,
              'BIOLEAF': 16.4, 'VINCARE': 16.4, 'ARCOS': 14.5}
NOMBRE = {'AMAZON_ES': 'España', 'AMAZON_IT': 'Italia', 'UAMAZON_FR': 'Francia',
          'AMAZON_DE': 'Alemania', 'AMAZON_NL': 'Países Bajos'}

f = lambda s: float(s) if (s or '').strip() else 0.0

def leer(p):
    """{(pais, marca): dict} con coste, clics, impresiones y venta promo/halo."""
    D = collections.defaultdict(lambda: dict(c=0., cl=0., im=0., vp=0., vh=0., u=0.))
    for x in csv.DictReader(open(p, encoding='utf-8-sig')):
        pais = x[PAIS] or 'OTROS'
        marca = (x['Marca del producto anunciado'] or 'Sin marca').upper()
        a = D[(pais, marca)]
        a['c'] += f(x['Coste total']); a['cl'] += f(x['Clics']); a['im'] += f(x['Impresiones'])
        a['vp'] += f(x['Ventas (promocionadas)']); a['vh'] += f(x['Ventas (halo)'])
        a['u'] += f(x['Unidades vendidas (producto promocionado)'])
    return D

A, B = leer(F25), leer(F26)

def mix(d):
    v = d['vp'] + d['vh']
    return dict(c=round(d['c'], 2), cl=int(d['cl']), im=int(d['im']),
                vp=round(d['vp'], 2), vh=round(d['vh'], 2), v=round(v, 2),
                u=int(d['u']),
                cpc=round(d['c'] / d['cl'], 4) if d['cl'] else None,
                roas=round(v / d['c'], 2) if d['c'] else None,
                acos=round(100 * d['c'] / v, 1) if v else None,
                halo=round(100 * d['vh'] / v, 1) if v else None)

paises = sorted({p for p, _ in list(A) + list(B)},
                key=lambda p: -sum(d['c'] for (q, _), d in B.items() if q == p))
OUT = []
for p in paises:
    def tot(D):
        t = dict(c=0., cl=0., im=0., vp=0., vh=0., u=0.)
        for (q, _), d in D.items():
            if q != p: continue
            for k in t: t[k] += d[k]
        return t
    t26 = tot(B)
    # 'OTROS' son filas sin mercado asignado: ruido, fuera del selector
    if t26['c'] < 20 or p == 'OTROS': continue
    marcas = []
    for m in sorted({mm for (q, mm) in list(A) + list(B) if q == p},
                    key=lambda m: -B.get((p, m), dict(c=0))['c']):
        a, b = A.get((p, m)), B.get((p, m))
        if (b or a)['c'] < 10: continue
        marcas.append(dict(marca=m.title(), eq=EQUILIBRIO.get(m),
                           a=mix(a) if a else None, b=mix(b) if b else None))
    OUT.append(dict(code=p, nombre=NOMBRE.get(p, p), a=mix(tot(A)), b=mix(t26), marcas=marcas))

json.dump(dict(ventana=VENTANA, paises=OUT), open('ads_pais.json', 'w'),
          ensure_ascii=False, indent=1)

print(f"ventana {VENTANA} · {len(OUT)} mercados")
print(f"{'pais':14s}{'gasto 25':>11s}{'gasto 26':>11s}{'ACOS 25':>9s}{'ACOS 26':>9s}{'ROAS 26':>9s}{'marcas':>8s}")
for o in OUT:
    g = lambda d, k, fm: (fm.format(d[k]) if d.get(k) is not None else '—')
    print(f"{o['nombre']:14s}{g(o['a'],'c','{:,.0f}'):>11s}{g(o['b'],'c','{:,.0f}'):>11s}"
          f"{g(o['a'],'acos','{:.1f}%'):>9s}{g(o['b'],'acos','{:.1f}%'):>9s}"
          f"{g(o['b'],'roas','{:.2f}'):>9s}{len(o['marcas']):>8d}")

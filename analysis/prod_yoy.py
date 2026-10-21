import csv, collections, json
f = lambda s: float(s) if (s or '').strip() else 0.0
SKU = 'SKU del producto anunciado-Advertised product SKU'
PAIS = 'País del producto anunciado-Advertised product marketplace'

def load(p):
    R = list(csv.DictReader(open(p, encoding='utf-8-sig')))
    for x in R:
        x['_c'] = f(x['Coste total']); x['_cl'] = f(x['Clics']); x['_im'] = f(x['Impresiones'])
        x['_vp'] = f(x['Ventas (promocionadas)']); x['_vh'] = f(x['Ventas (halo)'])
        x['_up'] = f(x['Unidades vendidas (producto promocionado)'])
        x['_pp'] = f(x['Compras (promocionadas)'])
    return R

A, B = load('ads/terminos/producto_anunciado_2025.csv'), load('ads/terminos/producto_anunciado_2026.csv')

def tot(R):
    c = sum(x['_c'] for x in R); vp = sum(x['_vp'] for x in R); vh = sum(x['_vh'] for x in R)
    return dict(c=c, cl=sum(x['_cl'] for x in R), vp=vp, vh=vh, v=vp+vh,
                cpc=c/sum(x['_cl'] for x in R) if sum(x['_cl'] for x in R) else 0,
                roas=(vp+vh)/c if c else 0, acos=c/(vp+vh) if vp+vh else 0,
                acos_p=c/vp if vp else 0, halo=vh/(vp+vh) if vp+vh else 0)

def pct(n, o): return f"{(n/o-1)*100:+.1f}%" if o else "n/a"

ta, tb = tot(A), tot(B)
print("="*74)
print("GLOBAL  ene-20 oct   (todos los mercados)")
print("="*74)
print(f"{'':22s}{'2025':>14s}{'2026':>14s}{'var':>12s}")
for k, lab, fm in [('c','Gasto','{:,.0f} €'), ('cl','Clics','{:,.0f}'), ('cpc','CPC','{:.3f} €'),
                   ('vp','Ventas producto','{:,.0f} €'), ('vh','Ventas halo','{:,.0f} €'),
                   ('v','Ventas totales','{:,.0f} €'), ('roas','ROAS','{:.2f}'),
                   ('acos','ACOS total','{:.1%}'), ('acos_p','ACOS producto','{:.1%}'),
                   ('halo','% halo','{:.1%}')]:
    print(f"{lab:22s}{fm.format(ta[k]):>14s}{fm.format(tb[k]):>14s}{pct(tb[k],ta[k]):>12s}")

def grupo(R, key):
    D = collections.defaultdict(list)
    for x in R: D[key(x)].append(x)
    return {k: tot(v) for k, v in D.items()}

for nombre, key in [('MARCA', lambda x: (x['Marca del producto anunciado'] or '(vacio)').upper()),
                    ('MERCADO', lambda x: x[PAIS] or '(vacio)')]:
    print("\n" + "="*74); print(f"POR {nombre}"); print("="*74)
    a, b = grupo(A, key), grupo(B, key)
    print(f"{nombre[:12]:14s}{'gasto 25':>10s}{'gasto 26':>10s}{'ACOS 25':>9s}{'ACOS 26':>9s}{'ROAS 25':>9s}{'ROAS 26':>9s}")
    for k in sorted(set(a) | set(b), key=lambda k: -(b.get(k, {}).get('c', 0))):
        x, y = a.get(k), b.get(k)
        if (y or x)['c'] < 30: continue
        g = lambda d, f_, fmt: fmt.format(d[f_]) if d else '—'
        print(f"{k[:14]:14s}{g(x,'c','{:,.0f}'):>10s}{g(y,'c','{:,.0f}'):>10s}"
              f"{g(x,'acos','{:.1%}'):>9s}{g(y,'acos','{:.1%}'):>9s}"
              f"{g(x,'roas','{:.2f}'):>9s}{g(y,'roas','{:.2f}'):>9s}")

# ---- SKUs que pierden dinero en 2026 ----
UMBRAL = {'CUPERINOX': .30, 'ARCOS': .20, 'VINFERMATON': .20, 'VINFER': .20,
          'BIOLEAF': .20, 'VINCARE': .20, 'XPARTAN': .20, 'HENDI': .25}
D = collections.defaultdict(lambda: dict(c=0., vp=0., vh=0., cl=0., up=0., n=''))
for x in B:
    k = (x[SKU] or '(sin sku)', x[PAIS] or '?', (x['Marca del producto anunciado'] or '?').upper())
    a = D[k]
    a['c'] += x['_c']; a['vp'] += x['_vp']; a['vh'] += x['_vh']; a['cl'] += x['_cl']; a['up'] += x['_up']
    if not a['n']: a['n'] = x['Nombre del producto anunciado'][:46]
F = []
for (sku, p, m), a in D.items():
    v = a['vp'] + a['vh']; u = UMBRAL.get(m, .25)
    F.append(dict(sku=sku, pais=p.replace('AMAZON_','').replace('U',''), marca=m, n=a['n'], c=a['c'],
                  vp=a['vp'], v=v, cl=a['cl'],
                  acos=a['c']/v if v else 9.99, acos_p=a['c']/a['vp'] if a['vp'] else 9.99,
                  exc=a['c'] - u*v, u=u))
F.sort(key=lambda r: -r['exc'])
print("\n" + "="*112)
print("SKUs QUE QUEMAN DINERO EN PUBLICIDAD 2026 (gasto - umbral x ventas totales, halo incluido)")
print("="*112)
print(f"{'exceso':>9s} {'gasto':>8s} {'ventas':>9s} {'ACOS':>7s}{'umb':>6s} {'SKU':16s}{'pais':5s}{'marca':12s} producto")
tq = 0
for r in F:
    if r['exc'] <= 0 or r['c'] < 25: continue
    tq += r['exc']
    print(f"{r['exc']:9,.0f} {r['c']:8,.0f} {r['v']:9,.0f} {min(r['acos'],9.99):7.1%}{r['u']:6.0%} {r['sku'][:16]:16s}{r['pais']:5s}{r['marca'][:12]:12s}{r['n']}")
print(f"\nTOTAL exceso sobre umbral (filas >25 € de gasto): {tq:,.0f} €  =  {tq/tb['c']:.1%} del gasto")

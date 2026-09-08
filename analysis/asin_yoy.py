"""YoY por ASIN a ventana identica, con descomposicion del movimiento.
   venta = sesiones x conversion x precio
   Descomposicion secuencial: efecto trafico, efecto conversion, efecto precio."""
import collections, sys
from parse_br import load
from brands import brand

def window(meses):
    acc = collections.defaultdict(lambda: dict(ses=0.0, uds=0.0, v=0.0, bbw=0.0,
                                               title='', brand='', n=0))
    for m in meses:
        rows = load(f'mensual/{m}.csv')
        by = collections.defaultdict(list)
        for r in rows: by[r['child']].append(r)
        for c, rs in by.items():
            s = max(r['sessions'] for r in rs)
            a = acc[c]
            a['ses'] += s; a['uds'] += sum(r['units'] for r in rs)
            a['v'] += sum(r['sales'] for r in rs); a['bbw'] += max(r['bb'] for r in rs)*s
            a['title'] = rs[0]['title']; a['brand'] = brand(rs[0]); a['n'] += 1
    for a in acc.values():
        a['bb']   = a['bbw']/a['ses'] if a['ses'] else 0
        a['conv'] = a['uds']/a['ses'] if a['ses'] else 0
        a['p']    = a['v']/a['uds'] if a['uds'] else 0
    return acc

A = window([f'2025-{m:02d}' for m in range(1,9)])
B = window([f'2026-{m:02d}' for m in range(1,9)])
Z = dict(ses=0.0, uds=0.0, v=0.0, bb=0.0, conv=0.0, p=0.0, title='', brand='', n=0)

def descompon(a, b):
    """Efecto de cada factor sobre el delta de venta, en euros."""
    s0,c0,p0 = a['ses'], a['conv'], a['p']
    s1,c1,p1 = b['ses'], b['conv'], b['p']
    if p0 == 0: p0 = p1
    if p1 == 0: p1 = p0
    e_traf = (s1-s0)*c0*p0
    e_conv = s1*(c1-c0)*p0
    e_prec = s1*c1*(p1-p0)
    return e_traf, e_conv, e_prec

filas = []
for ch in set(A) | set(B):
    a, b = A.get(ch, Z), B.get(ch, Z)
    if max(a['v'], b['v']) < 300: continue
    et, ec, ep = descompon(a, b)
    causa = max([('tráfico',et),('conversión',ec),('precio',ep)], key=lambda x: abs(x[1]))[0]
    if a['v'] == 0: causa = 'ASIN nuevo'
    elif b['v'] == 0: causa = 'ASIN retirado'
    filas.append(dict(ch=ch, title=(b['title'] or a['title']), brand=(b['brand'] or a['brand']),
        v0=a['v'], v1=b['v'], d=b['v']-a['v'],
        s0=a['ses'], s1=b['ses'], bb0=a['bb'], bb1=b['bb'],
        c0=100*a['conv'], c1=100*b['conv'], p0=a['p'], p1=b['p'],
        et=et, ec=ec, ep=ep, causa=causa,
        meses0=a['n'], meses1=b['n']))

filas.sort(key=lambda f: f['d'])
TOT_D = sum(f['d'] for f in filas)
neg = [f for f in filas if f['d'] < 0]; pos = [f for f in filas if f['d'] > 0]

def tabla(fs, titulo):
    print(f"\n{titulo}\n")
    h = (f"{'Δ EUR':>9}{'2025':>9}{'2026':>9}{'Ses25':>8}{'Ses26':>8}{'BB25':>6}{'BB26':>6}"
         f"{'Cv25':>6}{'Cv26':>6}{'P25':>6}{'P26':>6}  {'Causa':<13} Producto")
    print(h); print('-'*118)
    for f in fs:
        print(f"{f['d']:>+9,.0f}{f['v0']:>9,.0f}{f['v1']:>9,.0f}{f['s0']:>8,.0f}{f['s1']:>8,.0f}"
              f"{f['bb0']:>5.0f}%{f['bb1']:>5.0f}%{f['c0']:>5.1f}%{f['c1']:>5.1f}%"
              f"{f['p0']:>6.1f}{f['p1']:>6.1f}  {f['causa']:<13} {f['title'][:42]}")

print(f"ESPANA — ene-ago 2025 vs ene-ago 2026, {len(filas)} ASINs con >300 EUR en algun periodo")
print(f"Delta neto: {TOT_D:>+,.0f} EUR   |   {len(pos)} suben (+{sum(f['d'] for f in pos):,.0f})"
      f"   |   {len(neg)} bajan ({sum(f['d'] for f in neg):,.0f})")
tabla(filas[:20], "=== LOS 20 QUE MAS VENTA PIERDEN ===")
tabla(filas[-20:][::-1], "=== LOS 20 QUE MAS VENTA GANAN ===")

print("\n=== DE QUE VIENE EL CRECIMIENTO: descomposicion agregada ===\n")
for etiqueta, fs in [('Los que caen', neg), ('Los que suben', pos), ('TOTAL', filas)]:
    t = sum(f['et'] for f in fs); c = sum(f['ec'] for f in fs); p = sum(f['ep'] for f in fs)
    print(f"{etiqueta:<15} trafico {t:>+11,.0f}   conversion {c:>+11,.0f}   precio {p:>+11,.0f}"
          f"   suma {t+c+p:>+11,.0f}")

print("\n=== CAUSA DOMINANTE DE CADA MOVIMIENTO ===\n")
g = collections.defaultdict(lambda: [0,0.0])
for f in filas:
    k = (f['causa'], 'sube' if f['d']>0 else 'baja')
    g[k][0]+=1; g[k][1]+=f['d']
print(f"{'Causa':<15}{'Sentido':<8}{'ASINs':>7}{'Δ EUR':>13}")
for (c,s),(n,v) in sorted(g.items(), key=lambda x:-abs(x[1][1])):
    print(f"{c:<15}{s:<8}{n:>7}{v:>+13,.0f}")

print("\n=== POR MARCA ===\n")
gm = collections.defaultdict(lambda: dict(n=0,d=0.0,et=0.0,ec=0.0,ep=0.0,sube=0,baja=0))
for f in filas:
    a=gm[f['brand']]; a['n']+=1; a['d']+=f['d']; a['et']+=f['et']; a['ec']+=f['ec']; a['ep']+=f['ep']
    a['sube' if f['d']>0 else 'baja']+=1
print(f"{'Marca':<14}{'ASINs':>7}{'suben':>7}{'bajan':>7}{'Δ EUR':>12}{'ef.tráfico':>13}{'ef.conv':>12}{'ef.precio':>12}")
for k,a in sorted(gm.items(), key=lambda x:-x[1]['d']):
    print(f"{k:<14}{a['n']:>7}{a['sube']:>7}{a['baja']:>7}{a['d']:>+12,.0f}"
          f"{a['et']:>+13,.0f}{a['ec']:>+12,.0f}{a['ep']:>+12,.0f}")

import json
json.dump([{k:(round(v,2) if isinstance(v,float) else v) for k,v in f.items()} for f in filas],
          open('asin_yoy.json','w'), ensure_ascii=False)
print(f"\n-> asin_yoy.json ({len(filas)} ASINs)")

# ---------- Francia: solo cuota (periodos distintos) ----------
def col(f):
    rows = load(f); by = collections.defaultdict(list); out = {}
    for r in rows: by[r['child']].append(r)
    for c, rs in by.items():
        s = max(r['sessions'] for r in rs); u = sum(r['units'] for r in rs)
        out[c] = dict(title=rs[0]['title'], brand=brand(rs[0]), ses=s, uds=u,
                      v=sum(r['sales'] for r in rs), bb=max(r['bb'] for r in rs),
                      conv=100*u/s if s else 0)
    return out
FA, FB = col('fr/br_fr_2025.csv'), col('fr/br_fr_2026ytd.csv')
TA, TB = sum(x['v'] for x in FA.values()), sum(x['v'] for x in FB.values())
SA, SB = sum(x['ses'] for x in FA.values()), sum(x['ses'] for x in FB.values())
ZF = dict(title='', brand='', ses=0, uds=0, v=0, bb=0, conv=0)
fr = []
for ch in set(FA) | set(FB):
    a, b = FA.get(ch, ZF), FB.get(ch, ZF)
    pa, pb = 100*a['v']/TA, 100*b['v']/TB
    qa, qb = 100*a['ses']/SA, 100*b['ses']/SB
    if max(a['v'], b['v']) < 300: continue
    fr.append(dict(ch=ch, title=(b['title'] or a['title']), brand=(b['brand'] or a['brand']),
        cuota0=round(pa,2), cuota1=round(pb,2), d=round(pb-pa,2),
        qses0=round(qa,2), qses1=round(qb,2), dses=round(qb-qa,2),
        v0=round(a['v']), v1=round(b['v']), s0=round(a['ses']), s1=round(b['ses']),
        bb0=round(a['bb'],1), bb1=round(b['bb'],1), c0=round(a['conv'],2), c1=round(b['conv'],2)))
fr.sort(key=lambda f: f['d'])
json.dump(fr, open('asin_yoy_fr.json','w'), ensure_ascii=False)

print(f"\n\nFRANCIA — cuota de la venta del pais (2025 completo vs 2026 YTD), {len(fr)} ASINs")
print("Los euros no son comparables (12m vs 8m); la cuota si.\n")
h=f"{'Δcuota':>8}{'%25':>7}{'%26':>7}{'Δ%ses':>8}{'Ses25':>8}{'Ses26':>8}{'BB25':>6}{'BB26':>6}{'Cv25':>6}{'Cv26':>6}  Producto"
print("=== LOS 12 QUE MAS CUOTA PIERDEN ===\n"); print(h); print('-'*112)
for f in fr[:12]:
    print(f"{f['d']:>+7.1f}p{f['cuota0']:>6.1f}%{f['cuota1']:>6.1f}%{f['dses']:>+7.1f}p"
          f"{f['s0']:>8,.0f}{f['s1']:>8,.0f}{f['bb0']:>5.0f}%{f['bb1']:>5.0f}%"
          f"{f['c0']:>5.1f}%{f['c1']:>5.1f}%  {f['title'][:44]}")
print("\n=== LOS 12 QUE MAS CUOTA GANAN ===\n"); print(h); print('-'*112)
for f in fr[-12:][::-1]:
    print(f"{f['d']:>+7.1f}p{f['cuota0']:>6.1f}%{f['cuota1']:>6.1f}%{f['dses']:>+7.1f}p"
          f"{f['s0']:>8,.0f}{f['s1']:>8,.0f}{f['bb0']:>5.0f}%{f['bb1']:>5.0f}%"
          f"{f['c0']:>5.1f}%{f['c1']:>5.1f}%  {f['title'][:44]}")

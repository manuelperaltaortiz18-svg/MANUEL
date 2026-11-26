"""ASIN a ASIN del mes en curso. Lo que el ASIN a ASIN anual no puede dar.

   Existe porque el dueño manda el Business Report parcial sobre todo para
   esto, y yo lo estaba metiendo en parcial/ donde solo lo leia ritmo.py. Le
   decia "sin el parcial de 2025 no puedo comparar" y bloqueaba la pestaña
   entera por una columna, cuando hay dos cosas que si son medibles:

   1. NIVEL Y TENDENCIA DENTRO DEL MES. Con los parciales de este mismo mes
      (1-16, 1-21, 1-26) sale el ritmo diario por ASIN de cada tramo. No hace
      falta el año anterior para nada: la campaña de Q4 se ve en el tramo.

   2. INTERANUAL DE LAS VENTANAS QUE SI TIENEN PAREJA. Para cada parcial de
      este año se busca parcial/AAAA-MM-DD.csv del anterior con el MISMO dia
      de corte (regla 2). Si existe, interanual por ASIN con descomposicion
      de causa. Si no, esa ventana se queda sin interanual y se dice.

   Las sesiones se toman con max() por ASIN hijo (regla 5): varios SKU
   comparten hijo y Amazon repite la sesion en cada fila.
"""
import collections, glob, json, os, re
from parse_br import load
from brands import herencia, marca_de

HER = herencia([r for f in sorted(glob.glob('mensual/*.csv')) for r in load(f)])

def corte(p):
    m = re.search(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(p))
    return int(m.group(1)), int(m.group(2)), int(m.group(3))

TODOS = sorted(glob.glob('parcial/*.csv'))
ANIO, MES, _ = corte(TODOS[-1])
# los parciales de este mes y año, por dia de corte
MIOS = sorted([p for p in TODOS if corte(p)[:2] == (ANIO, MES)], key=lambda p: corte(p)[2])

def leer(p):
    """ASIN hijo -> agregados. Neto de IVA, sesiones con max()."""
    acc = collections.defaultdict(lambda: dict(ses=0.0, uds=0.0, v=0.0, bb=0.0,
                                               title='', brand='', skus=set()))
    by = collections.defaultdict(list)
    for r in load(p, iva='ES'): by[r['child']].append(r)
    for c, rs in by.items():
        a = acc[c]
        a['ses'] = max(r['sessions'] for r in rs)          # regla 5: max, no suma
        a['uds'] = sum(r['units'] for r in rs)
        a['v']   = sum(r['sales'] for r in rs)
        a['bb']  = max(r['bb'] for r in rs)
        a['title'] = rs[0]['title']; a['brand'] = marca_de(rs[0], HER)
        a['skus'] = {r['sku'] for r in rs if r['sku']}
    for a in acc.values():
        a['conv'] = a['uds']/a['ses'] if a['ses'] else 0
        a['p']    = a['v']/a['uds'] if a['uds'] else 0
    return acc

Z = dict(ses=0.0, uds=0.0, v=0.0, bb=0.0, conv=0.0, p=0.0, title='', brand='', skus=set())

def descompon(a, b):
    """venta = sesiones x conversion x precio. Mismo metodo que asin_yoy.py."""
    s0,c0,p0 = a['ses'], a['conv'], a['p']
    s1,c1,p1 = b['ses'], b['conv'], b['p']
    if p0 == 0: p0 = p1
    if p1 == 0: p1 = p0
    return (s1-s0)*c0*p0, s1*(c1-c0)*p0, s1*c1*(p1-p0)

# --- acumulados de cada corte de este mes ---
CORTES = [corte(p)[2] for p in MIOS]
ACUM = [leer(p) for p in MIOS]
HOY, DIAS = ACUM[-1], CORTES[-1]

# --- tramos: el ritmo diario entre corte y corte ---
TRAMOS = []
for i, d in enumerate(CORTES):
    d0 = CORTES[i-1] if i else 0
    TRAMOS.append(dict(ini=d0+1, fin=d, dias=d-d0))

# --- interanual: solo las ventanas con pareja exacta ---
PAREJAS = []
for i, p in enumerate(MIOS):
    d = CORTES[i]
    ref = f'parcial/{ANIO-1}-{MES:02d}-{d:02d}.csv'
    if os.path.exists(ref):
        PAREJAS.append(dict(dia=d, ref=os.path.basename(ref), ant=leer(ref), i=i))

filas = []
for ch in HOY:
    h = HOY[ch]
    if h['v'] < 200: continue
    f = dict(ch=ch, title=h['title'], brand=h['brand'], sku=', '.join(sorted(h['skus'])),
             v=round(h['v'],2), u=round(h['uds']), s=round(h['ses']),
             bb=round(h['bb'],1), cvr=round(100*h['conv'],2), p=round(h['p'],2))
    # ritmo diario de cada tramo
    rt = []
    for i, t in enumerate(TRAMOS):
        prev = ACUM[i-1].get(ch, Z)['v'] if i else 0.0
        rt.append(round((ACUM[i].get(ch, Z)['v'] - prev)/t['dias'], 1))
    f['tramos'] = rt
    f['acel'] = round(100*(rt[-1]/rt[0]-1), 1) if len(rt) > 1 and rt[0] > 0 else None
    # interanual de la ventana mas larga que tenga pareja
    if PAREJAS:
        P = PAREJAS[-1]
        a, b = P['ant'].get(ch, Z), ACUM[P['i']].get(ch, Z)
        if max(a['v'], b['v']) >= 200:
            et, ec, ep = descompon(a, b)
            causa = max([('tráfico',et),('conversión',ec),('precio',ep)], key=lambda x: abs(x[1]))[0]
            if a['v'] == 0: causa = 'ASIN nuevo'
            elif b['v'] == 0: causa = 'ASIN retirado'
            f['yoy'] = dict(dia=P['dia'], v0=round(a['v'],2), v1=round(b['v'],2),
                            d=round(b['v']-a['v'],2),
                            pct=round(100*(b['v']/a['v']-1),1) if a['v'] else None,
                            s0=round(a['ses']), s1=round(b['ses']),
                            bb0=round(a['bb'],1), bb1=round(b['bb'],1),
                            c0=round(100*a['conv'],2), c1=round(100*b['conv'],2),
                            p0=round(a['p'],2), p1=round(b['p'],2),
                            et=round(et), ec=round(ec), ep=round(ep), causa=causa)
    filas.append(f)
filas.sort(key=lambda x: -x['v'])

MESES_ES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
            'septiembre','octubre','noviembre','diciembre']
T = dict(anio=ANIO, mes=MESES_ES[MES-1], dias=DIAS,
         cortes=CORTES, tramos=TRAMOS,
         v=round(sum(f['v'] for f in filas)), u=sum(f['u'] for f in filas),
         n=len(filas),
         yoy_dia=PAREJAS[-1]['dia'] if PAREJAS else None,
         yoy_ref=PAREJAS[-1]['ref'] if PAREJAS else None,
         falta=None if any(P['dia'] == DIAS for P in PAREJAS)
               else f'parcial/{ANIO-1}-{MES:02d}-{DIAS:02d}.csv')
json.dump(dict(total=T, filas=filas), open('asin_mes.json','w'), ensure_ascii=False)

if __name__ == '__main__':
    print(f"ASIN A ASIN DE {T['mes'].upper()} {ANIO} — dias 1 a {DIAS}\n")
    print(f"  {T['n']} ASIN con mas de 200 EUR  ·  {T['v']:,.0f} EUR netos  ·  {T['u']:,} uds")
    print(f"  cortes cargados: {', '.join('dia '+str(c) for c in CORTES)}")
    if PAREJAS: print(f"  interanual por ASIN: ventana 1-{T['yoy_dia']} contra {T['yoy_ref']}")
    if T['falta']: print(f"  interanual de 1-{DIAS}: NO MEDIBLE, falta {T['falta']}")
    th = ' '.join(f"{t['ini']}-{t['fin']}".rjust(9) for t in TRAMOS)
    print(f"\n{'ASIN':12s}{'marca':11s}{'venta':>9s}{'BB':>6s}{'conv':>7s}" + th + f"{'YoY 1-16':>10s}{'causa':>13s}")
    print('-'*(12+11+9+6+7+len(th)+10+13))
    for f in filas[:22]:
        y = f.get('yoy') or {}
        yy = f"{y['pct']:+.0f}%" if y.get('pct') is not None else 'n/d'
        print(f"{f['ch']:12s}{f['brand'][:10]:11s}{f['v']:9,.0f}{f['bb']:5.0f}%{f['cvr']:6.1f}%"
              + ' '.join(f"{x:,.0f}".rjust(9) for x in f['tramos'])
              + f"{yy:>10s}{y.get('causa','—'):>13s}")

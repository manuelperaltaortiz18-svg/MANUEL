"""Como va el mes en curso. Un mes parcial no entra en la serie mensual
   (rompería la ventana comparable), asi que se lee como ritmo diario."""
import collections, json, glob, os, re
from parse_br import load
from brands import brand

PARCIAL = sorted(glob.glob('parcial/*.csv'))[-1]           # p.ej. parcial/2026-10-15.csv
m = re.search(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(PARCIAL))
ANIO, MES, DIAS = int(m.group(1)), int(m.group(2)), int(m.group(3))
DIAS_MES = [31,28,31,30,31,30,31,31,30,31,30,31][MES-1]
MESES_ES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
            'septiembre','octubre','noviembre','diciembre']

def por_marca(path):
    g = collections.Counter(); u = collections.Counter()
    for r in load(path):
        g[brand(r)] += r['sales']; u[brand(r)] += r['units']
    return g, u

AC, AU = por_marca(PARCIAL)                                  # mes en curso, parcial
PV, PU = por_marca(f'mensual/{ANIO-1}-{MES:02d}.csv')        # mismo mes del ano pasado
AN, _  = por_marca(f'mensual/{ANIO}-{MES-1:02d}.csv')        # mes anterior de este ano

filas = []
for b in set(AC) | set(PV):
    d_act = AC.get(b, 0)/DIAS
    d_ant = PV.get(b, 0)/DIAS_MES
    d_pre = AN.get(b, 0)/[31,28,31,30,31,30,31,31,30,31,30,31][MES-2]
    if max(AC.get(b,0), PV.get(b,0)) < 500: continue
    filas.append(dict(marca=b, v=round(AC.get(b,0)), u=round(AU.get(b,0)),
        dia=round(d_act,1), dia_ant=round(d_ant,1), dia_pre=round(d_pre,1),
        yoy=round(100*(d_act-d_ant)/d_ant,1) if d_ant else None,
        mom=round(100*(d_act-d_pre)/d_pre,1) if d_pre else None,
        proy=round(d_act*DIAS_MES), v_ant=round(PV.get(b,0))))
filas.sort(key=lambda f: -f['v'])
T = dict(dias=DIAS, dias_mes=DIAS_MES, mes=MESES_ES[MES-1], anio=ANIO,
         v=round(sum(AC.values())), u=round(sum(AU.values())),
         dia=round(sum(AC.values())/DIAS,1),
         dia_ant=round(sum(PV.values())/DIAS_MES,1),
         dia_pre=round(sum(AN.values())/[31,28,31,30,31,30,31,31,30,31,30,31][MES-2],1),
         proy=round(sum(AC.values())/DIAS*DIAS_MES), v_ant=round(sum(PV.values())))
json.dump(dict(total=T, filas=filas), open('ritmo.json','w'), ensure_ascii=False)

if __name__ == '__main__':
    print(f"RITMO DE {MESES_ES[MES-1].upper()} {ANIO} — dias 1 a {DIAS} de {DIAS_MES}\n")
    print(f"  Vendido      : {T['v']:>10,.0f} EUR  ({T['u']:,.0f} uds)")
    print(f"  Ritmo        : {T['dia']:>10,.0f} EUR/dia")
    print(f"  Mismo mes {ANIO-1}: {T['dia_ant']:>10,.0f} EUR/dia   ({100*(T['dia']-T['dia_ant'])/T['dia_ant']:+.0f}%)")
    print(f"  Mes anterior : {T['dia_pre']:>10,.0f} EUR/dia   ({100*(T['dia']-T['dia_pre'])/T['dia_pre']:+.0f}%)")
    print(f"  Proyeccion   : {T['proy']:>10,.0f} EUR  frente a {T['v_ant']:,.0f} del ano pasado\n")
    h=f"{'Marca':<14}{'Vendido':>10}{'EUR/dia':>9}{'dia '+str(ANIO-1):>10}{'YoY':>8}{'vs mes ant.':>13}{'Proyeccion':>12}"
    print(h); print('-'*len(h))
    for f in filas:
        yoy = ('%+.0f%%' % f['yoy']) if f['yoy'] is not None else '—'
        mom = ('%+.0f%%' % f['mom']) if f['mom'] is not None else '—'
        print(f"{f['marca']:<14}{f['v']:>10,.0f}{f['dia']:>9,.0f}{f['dia_ant']:>10,.0f}"
              f"{yoy:>8}{mom:>13}{f['proy']:>12,.0f}")
    print('-'*len(h))
    print(f"{'TOTAL':<14}{T['v']:>10,.0f}{T['dia']:>9,.0f}{T['dia_ant']:>10,.0f}"
          f"{100*(T['dia']-T['dia_ant'])/T['dia_ant']:>+7.0f}%"
          f"{100*(T['dia']-T['dia_pre'])/T['dia_pre']:>+12.0f}%{T['proy']:>12,.0f}")

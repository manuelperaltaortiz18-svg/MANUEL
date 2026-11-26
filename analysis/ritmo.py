"""Como va el mes en curso. Un mes parcial no entra en la serie mensual
   (rompería la ventana comparable), asi que se lee como ritmo diario.

   Regla 2 del proyecto: NUNCA comparar una ventana parcial contra la media
   de un mes completo. Los dias 1-16 de noviembre de 2025 fueron el 36% del
   mes, no el 53%: usar la media de 30 dias infla la referencia un 50%, y en
   jamoneros, donde esos dias fueron el 20% del mes, la infla un 160%.
   Asi que la referencia del ano anterior sale del parcial equivalente, con
   el mismo dia de corte. Si no existe, no hay interanual: se pide.

   Regla 3: tampoco se proyecta el mes en linea recta. La proyeccion sale de
   la forma real que tuvo el mes el ano pasado (que parte del mes llevaba a
   este mismo dia), y si falta ese dato no se proyecta.
"""
import collections, json, glob, os, re
from parse_br import load
from brands import brand, herencia, marca_de

PARCIAL = sorted(glob.glob('parcial/*.csv'))[-1]           # p.ej. parcial/2026-11-26.csv
m = re.search(r'(\d{4})-(\d{2})-(\d{2})', os.path.basename(PARCIAL))
ANIO, MES, DIAS = int(m.group(1)), int(m.group(2)), int(m.group(3))
LARGO = [31,28,31,30,31,30,31,31,30,31,30,31]
DIAS_MES = LARGO[MES-1]
MESES_ES = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
            'septiembre','octubre','noviembre','diciembre']

# la herencia de marca se calcula sobre todo el historico, igual que en el panel
HER = herencia([r for f in sorted(glob.glob('mensual/*.csv')) for r in load(f)])

def por_marca(path):
    g = collections.Counter(); u = collections.Counter()
    for r in load(path, iva='ES'):   # neto
        b = marca_de(r, HER)
        g[b] += r['sales']; u[b] += r['units']
    return g, u

AC, AU = por_marca(PARCIAL)                                  # mes en curso, parcial

# --- referencia del ano anterior: el parcial equivalente, mismo dia de corte ---
REF = f'parcial/{ANIO-1}-{MES:02d}-{DIAS:02d}.csv'
HAY_REF = os.path.exists(REF)
PV = por_marca(REF)[0] if HAY_REF else collections.Counter()

# --- mes completo del ano anterior: solo para la forma del mes y el cierre ---
MES_ANT_ANIO = f'mensual/{ANIO-1}-{MES:02d}.csv'
PM = por_marca(MES_ANT_ANIO)[0] if os.path.exists(MES_ANT_ANIO) else collections.Counter()

# que fraccion del mes llevaba el ano pasado a este mismo dia
CUOTA = (sum(PV.values())/sum(PM.values())) if (HAY_REF and sum(PM.values())) else None

# --- mes anterior de este ano: comparacion de ritmo diario, no like-for-like ---
AN = por_marca(f'mensual/{ANIO}-{MES-1:02d}.csv')[0] if MES > 1 else collections.Counter()
DIAS_PRE = LARGO[MES-2] if MES > 1 else 30

def pct(a, b): return round(100*(a-b)/b, 1) if b else None

filas = []
for b in set(AC) | set(PV):
    if max(AC.get(b,0), PV.get(b,0)) < 500: continue
    d_act = AC.get(b,0)/DIAS
    d_ant = PV.get(b,0)/DIAS if HAY_REF else None          # misma ventana, mismos dias
    d_pre = AN.get(b,0)/DIAS_PRE
    # cuota propia de la marca: la estacionalidad intramensual no es igual en todas
    cu = (PV.get(b,0)/PM[b]) if (HAY_REF and PM.get(b)) else CUOTA
    filas.append(dict(marca=b, v=round(AC.get(b,0)), u=round(AU.get(b,0)),
        dia=round(d_act,1),
        dia_ant=round(d_ant,1) if d_ant is not None else None,
        dia_pre=round(d_pre,1),
        yoy=pct(d_act, d_ant) if d_ant else None,
        mom=pct(d_act, d_pre),
        proy=round(AC.get(b,0)/cu) if cu else None,
        v_ant=round(PM.get(b,0)) if PM else None))
filas.sort(key=lambda f: -f['v'])

v_act = sum(AC.values())
T = dict(dias=DIAS, dias_mes=DIAS_MES, mes=MESES_ES[MES-1], anio=ANIO,
         v=round(v_act), u=round(sum(AU.values())),
         dia=round(v_act/DIAS,1),
         dia_ant=round(sum(PV.values())/DIAS,1) if HAY_REF else None,
         dia_pre=round(sum(AN.values())/DIAS_PRE,1),
         yoy=pct(v_act/DIAS, sum(PV.values())/DIAS) if HAY_REF else None,
         cuota=round(100*CUOTA,1) if CUOTA else None,
         proy=round(v_act/CUOTA) if CUOTA else None,
         v_ant=round(sum(PM.values())) if PM else None,
         ref=os.path.basename(REF), hay_ref=HAY_REF,
         falta=None if HAY_REF else REF)
json.dump(dict(total=T, filas=filas), open('ritmo.json','w'), ensure_ascii=False)

if __name__ == '__main__':
    print(f"RITMO DE {MESES_ES[MES-1].upper()} {ANIO} — dias 1 a {DIAS} de {DIAS_MES}\n")
    print(f"  Vendido      : {T['v']:>10,.0f} EUR netos ({T['dia']:,.0f} EUR/dia)")
    if HAY_REF:
        print(f"  Misma ventana de {ANIO-1}: {sum(PV.values()):>10,.0f} EUR ({T['dia_ant']:,.0f} EUR/dia)  {T['yoy']:+.1f}%")
        print(f"  El ano pasado a este dia llevaba el {T['cuota']:.1f}% del mes")
        print(f"  Proyeccion   : {T['proy']:>10,.0f} EUR  frente a {T['v_ant']:,.0f} del ano pasado")
    else:
        print(f"  Interanual   : NO MEDIBLE. Falta {REF}")
        print(f"                 (comparar contra la media del mes completo infla la referencia)")
        print(f"  Proyeccion   : no se calcula sin la forma real del mes")
    print(f"  Mes anterior : {T['dia_pre']:,.0f} EUR/dia  ({T['dia']/T['dia_pre']-1:+.0%} de ritmo diario)\n")
    hd = f"{'Marca':14s}{'Vendido':>10s}{'EUR/dia':>9s}"
    hd += f"{'dia '+str(ANIO-1):>10s}{'YoY':>8s}" if HAY_REF else f"{'dia '+str(ANIO-1):>10s}{'YoY':>8s}"
    print(hd + f"{'vs mes ant.':>13s}{'Proyeccion':>12s}")
    print('-'*len(hd+' '*25))
    for f in filas:
        da = f"{f['dia_ant']:,.0f}" if f['dia_ant'] is not None else 'n/d'
        yy = f"{f['yoy']:+.0f}%" if f['yoy'] is not None else 'n/d'
        pr = f"{f['proy']:,.0f}" if f['proy'] is not None else 'n/d'
        print(f"{f['marca']:14s}{f['v']:>10,.0f}{f['dia']:>9,.0f}{da:>10s}{yy:>8s}{f['mom']:>+12.0f}%{pr:>12s}")

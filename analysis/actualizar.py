#!/usr/bin/env python3
"""Un solo comando para regenerar el panel entero: python3 actualizar.py

   Existe porque regenerar a mano se olvida. Ha pasado: pnl.json llego a ir un
   8,3% desfasado y hendi_total.json publicaba 68.795 EUR/mes cuando el dato
   real eran 62.995, de modo que el panel y los informes decian cosas
   distintas del mismo negocio.

   Hace tres cosas:
     1. Ejecuta cada script en orden de dependencia y para si uno falla.
     2. Comprueba frescura: si un JSON es mas viejo que cualquiera de sus
        ficheros de entrada, lo avisa en rojo. Es la red de seguridad.
     3. Construye dashboard.html al final y recuerda que falta por cargar.
"""
import glob, os, subprocess, sys, time

# script -> (salidas, patrones de entrada)
PASOS = [
    ('asin_yoy.py',    ['asin_yoy.json','asin_yoy_fr.json'], ['mensual/*.csv','fr/*.csv','brands.py','parse_br.py']),
    ('ritmo.py',       ['ritmo.json'],        ['parcial/*.csv','mensual/*.csv','brands.py','parse_br.py']),
    ('asin_mes.py',    ['asin_mes.json'],     ['parcial/*.csv','mensual/*.csv','brands.py','parse_br.py']),
    ('inv.py',         ['inventario.json'],   ['mensual/*.csv']),
    ('pl.py',          ['pnl.json'],          ['mensual/*.csv','costes/margenes.tsv']),
    ('canal.py',       ['canal.json'],        ['mensual/*.csv','costes/nuevos.tsv']),
    ('vinfer_pl.py',   ['vinfer_pl.json'],    ['mensual/*.csv','costes/vinfer_raw/*.xlsx']),
    ('hendi.py',       [],                    ['mensual/*.csv','costes/hendi_raw/*.xlsx']),
    ('hendi_total.py', ['hendi_total.json'],  ['mensual/*.csv','costes/hendi_raw/*.xlsx','makro_raw/*.xlsx']),
    # OJO: ads.py solo imprime, no escribe JSON. ads_summary.json esta a mano y
    # ningun script lo regenera, asi que no se le puede exigir frescura: se
    # declara aparte, en SIN_FUENTE.
    ('ads.py',         [],                    ['ads/*.csv','mensual/*.csv']),
    ('ads_pais.py',    ['ads_pais.json'],     ['ads/terminos/*.csv']),
    ('roi.py',         ['roi.json'],          ['ads/*.csv','mensual/*.csv']),
    ('b2b.py',         ['b2b.json'],          ['b2b_raw/*.xlsx']),
    ('makro.py',       ['makro.json'],        ['makro_raw/*.xlsx']),
]

# JSON que alimentan el panel y que NINGUN script sabe reconstruir. Es la deuda
# mas peligrosa del repo: el panel publica un numero que nadie puede volver a
# calcular, y cuando la conversacion da otro, no hay forma de saber cual vale.
SIN_FUENTE = [
    ('ads_summary.json', 'pestaña de Publicidad',
     'ads.py solo imprime. Hecho a mano; su ventana se quedo en 15 oct (gasto) y 30 sep (ventas).'),
]

# ficheros que el panel NO lee todavia, para que no se queden olvidados en el repo
HUERFANOS = [
    ('ads/maestro/*.csv',    'informe maestro de publicidad',
     'ads.py y ads_pais.py leen ads/terminos/ y ads/campaigns_*. El maestro, no.'),
    ('ads/estructura/*.csv', 'presupuestos, estado de entrega y top de busquedas',
     'no hay script que lo lea: presupuesto por campaña y top de busquedas quedan fuera del panel.'),
]

R, V, N = '\033[31m', '\033[33m', '\033[0m'
if not sys.stdout.isatty(): R = V = N = ''

def mtime(pats):
    t, f = 0, None
    for p in pats:
        for x in glob.glob(p):
            if os.path.getmtime(x) > t: t, f = os.path.getmtime(x), x
    return t, f

fallos, avisos = [], []
print("REGENERANDO EL PANEL\n")
for script, salidas, entradas in PASOS:
    if not os.path.exists(script):
        avisos.append(f"{script} no existe"); print(f"  {V}· {script:16s} no existe{N}"); continue
    r = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if r.returncode:
        fallos.append(script)
        print(f"  {R}✗ {script:16s} FALLO{N}")
        print('    ' + (r.stderr.strip().splitlines() or ['sin stderr'])[-1][:150])
        continue
    print(f"  ✓ {script:16s} " + ', '.join(salidas or ['(solo imprime)']))

print("\nCOMPROBACION DE FRESCURA")
for script, salidas, entradas in PASOS:
    te, fe = mtime(entradas)
    for s in salidas:
        if not os.path.exists(s):
            print(f"  {R}✗ {s:22s} no se ha generado{N}"); fallos.append(s); continue
        ts = os.path.getmtime(s)
        if ts < te:
            print(f"  {R}✗ {s:22s} mas viejo que {fe}{N}"); fallos.append(s)
        else:
            print(f"  ✓ {s:22s} al dia ({time.strftime('%H:%M', time.localtime(ts))})")

print("\nJSON DEL PANEL QUE NINGUN SCRIPT REGENERA")
for f, que, por in SIN_FUENTE:
    ed = time.strftime('%d-%b', time.localtime(os.path.getmtime(f))) if os.path.exists(f) else 'no existe'
    print(f"  {R}· {f}  ->  {que}{N}\n      ultimo cambio {ed}. {por}")
    avisos.append(f)

print("\nDATOS EN EL REPO QUE EL PANEL NO LEE")
for pat, que, por in HUERFANOS:
    fs = sorted(glob.glob(pat))
    if fs: print(f"  {V}· {que}{N}\n      {len(fs)} fichero(s), el ultimo {os.path.basename(fs[-1])}\n      {por}")

print("\nCONSTRUYENDO dashboard.html")
r = subprocess.run([sys.executable, 'build_dashboard.py'], capture_output=True, text=True)
print('  ' + (r.stdout.strip() or r.stderr.strip())[:200])
if r.returncode: fallos.append('build_dashboard.py')

print()
if fallos:
    print(f"{R}NO PUBLICAR. Han fallado: {', '.join(dict.fromkeys(fallos))}{N}"); sys.exit(1)
print("Scripts al dia. Publicar dashboard.html al artefacto de siempre.")
if avisos: print(f"{V}Con {len(avisos)} aviso(s) arriba: hay partes del panel que no se regeneran solas.{N}")
print("Recordatorio: el panel lleva costes y margenes, y esta compartido por enlace.")

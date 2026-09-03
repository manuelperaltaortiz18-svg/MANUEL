import collections
from parse_br import load
from brands import brand, SUPPLIER

M26=[f'mensual/2026-{m:02d}.csv' for m in range(1,9)]
acc=collections.defaultdict(lambda: dict(ses=0,v=0,u=0))
for p in M26:
    rows=load(p); by=collections.defaultdict(list)
    for r in rows: by[r['child']].append(r)
    for rs in by.values():
        k=SUPPLIER.get(brand(rs[0]),'Otros'); a=acc[k]
        a['ses']+=max(r['sessions'] for r in rs); a['v']+=sum(r['sales'] for r in rs)
        a['u']+=sum(r['units'] for r in rs)

MG={'Arcos':(15,25),'Cuperinox':(25,35),'Hendi':(20,35),'Vinfer (grupo)':(15,25),'Otros':(15,25)}
TS=sum(a['ses'] for a in acc.values()); TV=sum(a['v'] for a in acc.values())

print("MARGEN BRUTO ene-ago 2026 (8 meses reales)\n")
h=f"{'Proveedor':<16}{'Ventas':>11}{'%Ses':>7}{'Margen%':>10}{'Margen min':>12}{'Margen max':>12}{'cts/ses min':>12}{'cts/ses max':>12}"
print(h); print('-'*len(h))
tmin=tmax=0
for k,a in sorted(acc.items(), key=lambda x:-x[1]['v']):
    lo,hi=MG[k]; mn,mx=a['v']*lo/100, a['v']*hi/100; tmin+=mn; tmax+=mx
    print(f"{k:<16}{a['v']:>11,.0f}{100*a['ses']/TS:>6.1f}%{f'{lo}-{hi}%':>10}{mn:>12,.0f}{mx:>12,.0f}{100*mn/a['ses']:>11.1f}c{100*mx/a['ses']:>11.1f}c")
print('-'*len(h))
print(f"{'TOTAL':<16}{TV:>11,.0f}{100:>6.1f}%{'':>10}{tmin:>12,.0f}{tmax:>12,.0f}{100*tmin/TS:>11.1f}c{100*tmax/TS:>11.1f}c")

print("\nTEST ADVERSARIAL: Arcos en su MEJOR caso (25%) vs cada rival en su PEOR caso\n")
base=acc['Arcos']['v']*0.25/acc['Arcos']['ses']
print(f"  Arcos al 25% de margen = {100*base:.2f} centimos de margen por sesion\n")
print(f"{'Proveedor':<16}{'Margen peor':>12}{'cts/ses':>10}{'vs Arcos':>10}")
for k,a in sorted(acc.items(), key=lambda x:-x[1]['v']):
    if k=='Arcos': continue
    lo,_=MG[k]; c=a['v']*lo/100/a['ses']
    print(f"{k:<16}{f'{lo}%':>12}{100*c:>9.2f}c{c/base:>9.1f}x")

print("\nCOSTE DE OPORTUNIDAD: reasignar tráfico de Arcos\n")
for pct in (5,10,20):
    ses=acc['Arcos']['ses']*pct/100
    perdido=ses*acc['Arcos']['v']*0.20/acc['Arcos']['ses']
    for k in ('Cuperinox','Hendi'):
        lo,hi=MG[k]; g=ses*acc[k]['v']*((lo+hi)/2/100)/acc[k]['ses']
        print(f"  {pct:>2}% del trafico de Arcos ({ses:>9,.0f} ses) -> {k:<11}: {g-perdido:>+10,.0f} EUR de margen en 8 meses")

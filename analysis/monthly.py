import glob, collections, os
from parse_br import load
from brands import brand

def month(path):
    rows = load(path)
    by = collections.defaultdict(list)
    for r in rows: by[r['child']].append(r)
    asins=[dict(brand=brand(rs[0]), sessions=max(r['sessions'] for r in rs),
                units=sum(r['units'] for r in rs), sales=sum(r['sales'] for r in rs),
                bb=max(r['bb'] for r in rs)) for rs in by.values()]
    return asins

files = sorted(glob.glob('mensual/*.csv'))
data = {os.path.basename(f)[:-4]: month(f) for f in files}

print(f"{'Mes':<9}{'Ventas EUR':>12}{'Sesiones':>10}{'Uds':>8}{'ASINs':>7}{'Conv%':>7}{'Ticket':>7}{'EUR/ses':>8}{'BuyBox':>8}")
print('-'*76)
for m, a in data.items():
    s=sum(x['sessions'] for x in a); u=sum(x['units'] for x in a); v=sum(x['sales'] for x in a)
    bb=sum(x['bb']*x['sessions'] for x in a)/s if s else 0
    print(f"{m:<9}{v:>12,.0f}{s:>10,.0f}{u:>8,.0f}{len(a):>7}{100*u/s:>6.1f}%{v/u if u else 0:>7.1f}{v/s:>8.2f}{bb:>7.1f}%")

brands = sorted({x['brand'] for a in data.values() for x in a},
                key=lambda b: -sum(x['sales'] for a in data.values() for x in a if x['brand']==b))
print(f"\nVENTAS EUR POR MARCA Y MES\n")
print(f"{'Marca':<14}" + ''.join(f"{m[2:]:>10}" for m in data) + f"{'TOTAL':>11}")
print('-'*(14+10*len(data)+11))
for b in brands:
    vals=[sum(x['sales'] for x in data[m] if x['brand']==b) for m in data]
    if sum(vals)<200: continue
    print(f"{b:<14}" + ''.join(f"{v:>10,.0f}" for v in vals) + f"{sum(vals):>11,.0f}")
tot=[sum(x['sales'] for x in data[m]) for m in data]
print('-'*(14+10*len(data)+11))
print(f"{'TOTAL':<14}" + ''.join(f"{v:>10,.0f}" for v in tot) + f"{sum(tot):>11,.0f}")

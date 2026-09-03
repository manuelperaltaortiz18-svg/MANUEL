import csv, re, sys, json

def num(s):
    s = (s or "").strip().replace('"','')
    if not s or s in ('-','—'): return 0.0
    return float(s.replace(',',''))

def eur(s):
    s = (s or "").strip().replace('€','').replace('\xa0','').strip()
    if not s: return 0.0
    return float(s.replace('.','').replace(',','.'))

def pct(s):
    s = (s or "").strip().replace('%','')
    if not s: return 0.0
    return float(s)

def load(path):
    rows=[]
    with open(path, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            rows.append({
                'parent': r['ASIN (parent)'], 'child': r['ASIN (child)'],
                'title': r['Título'], 'sku': r['SKU'],
                'sessions': num(r['Sesiones: total']),
                'bb': pct(r['Porcentaje de ofertas destacadas (Buy Box)']),
                'units': num(r['Unidades encargadas']),
                'sales': eur(r['Ventas de productos encargados']),
                'b2b_sales': eur(r['Ventas de productos encargados: B2B']),
                'b2b_units': num(r['Unidades encargadas - B2B']),
            })
    return rows

if __name__ == '__main__':
    rows = load(sys.argv[1])
    print(len(rows), 'rows')
    print('sesiones', sum(r['sessions'] for r in rows))
    print('unidades', sum(r['units'] for r in rows))
    print('ventas', round(sum(r['sales'] for r in rows),2))
    print('b2b ventas', round(sum(r['b2b_sales'] for r in rows),2))
    print('parents', len({r['parent'] for r in rows}), 'skus', len({r['sku'] for r in rows}))

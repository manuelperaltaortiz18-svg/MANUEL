import csv, re, sys, json

# Amazon reporta la venta CON IVA. load(path, iva='ES') la devuelve neta.
# Los scripts de margen NO lo usan: necesitan el precio bruto para la
# comision de referencia, y netean ellos por dentro.
IVA = {'ES': 1.21, 'FR': 1.20, 'IT': 1.22, 'DE': 1.19, 'NL': 1.21, 'PT': 1.23}

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

# Amazon exporta el mismo informe en dos idiomas y dos formatos de numero.
# La version inglesa NO trae columna de SKU: lo que dependa del SKU
# (margenes, inventario, listados por SKU) necesita el export en espanol.
CAMPOS = {
  'es': dict(parent='ASIN (parent)', child='ASIN (child)', title='Título', sku='SKU',
             sessions='Sesiones: total',
             bb='Porcentaje de ofertas destacadas (Buy Box)',
             units='Unidades encargadas', sales='Ventas de productos encargados',
             b2b_sales='Ventas de productos encargados: B2B',
             b2b_units='Unidades encargadas - B2B'),
  'en': dict(parent='(Parent) ASIN', child='(Child) ASIN', title='Title', sku=None,
             sessions='Sessions – Total',
             bb='Featured Offer (Buy Box) percentage',
             units='Units ordered', sales='Ordered Product Sales',
             b2b_sales='Ordered product sales – B2B',
             b2b_units='Units ordered – B2B'),
}

def ang(s):
    """1,234.56 -> 1234.56 (formato anglosajon, con o sin simbolo)."""
    s = (s or "").replace('€', '').replace('\xa0', '').replace(',', '').strip()
    if not s or s in ('-', '—'): return 0.0
    try: return float(s)
    except ValueError: return 0.0

def idioma(cab):
    cab = [c.lstrip('\ufeff') for c in cab]
    return 'es' if 'ASIN (parent)' in cab else 'en'

def load(path, iva=None):
    k = IVA[iva] if iva else 1.0
    rows = []
    with open(path, encoding='utf-8-sig') as f:
        rd = csv.DictReader(f)
        lang = idioma(rd.fieldnames or [])
        C = CAMPOS[lang]
        n, e = (num, eur) if lang == 'es' else (ang, ang)
        for r in rd:
            rows.append({
                'parent': r[C['parent']], 'child': r[C['child']],
                'title': r[C['title']],
                'sku': r[C['sku']] if C['sku'] else '',
                'sessions': n(r[C['sessions']]),
                'bb': pct(r[C['bb']]),
                'units': n(r[C['units']]),
                'sales': e(r[C['sales']]) / k,
                'b2b_sales': e(r[C['b2b_sales']]) / k,
                'b2b_units': n(r[C['b2b_units']]),
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

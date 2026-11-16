import collections
import re
BRAND_RULES = [
    ('Vinfermaton',  r'VINFERMAT[OÓ]N'),
    ('Bioleaf',      r'BIOLEAF'),
    ('Vincare',      r'VINCARE'),
    ('Wins',         r'\bWINS\b'),
    ('Vinfer',       r'\bVINFER\b'),
    ('Cuperinox',    r'CUPERINOX'),
    ('Arcos',        r'\bARCOS\b'),
    ('Hendi',        r'\bHENDI\b'),
    ('Xpartan',      r'XPARTAN'),
    ('Tradineur',    r'TRADINEUR'),
    ('La Garrafita', r'LA\s*GARRAFITA|LAGARRAFI[TR]A'),
    ('Maton',        r'\bMATON\b'),
]
# proveedor -> marcas
SUPPLIER = {
    'Arcos':'Arcos', 'Hendi':'Hendi', 'Cuperinox':'Cuperinox',
    'Vinfermaton':'Vinfer (grupo)', 'Wins':'Vinfer (grupo)', 'Vinfer':'Vinfer (grupo)',
    'Bioleaf':'Vinfer (grupo)', 'Vincare':'Vinfer (grupo)',
    'Xpartan':'Otros', 'Tradineur':'Otros', 'La Garrafita':'Otros',
    'Maton':'Otros', 'Sin marca':'Otros',
}
def brand(row):
    hay = (row['title'] + ' ' + row['sku']).upper()
    for name, pat in BRAND_RULES:
        if re.search(pat, hay):
            return name
    return 'Sin marca'


def herencia(rows):
    """child -> marca, para los hijos que brand() no clasifica.
    Hereda la marca de sus hermanos bajo el mismo ASIN padre cuando todos
    coinciden. Amazon crea variantes nuevas sin la marca en el titulo, y
    sin esto caen en 'Sin marca' aunque su familia este clasificada.
    Pasa TODOS los meses disponibles: cuantos mas hermanos, mas cobertura."""
    por_padre = collections.defaultdict(set)
    for r in rows:
        b = brand(r)
        if b != 'Sin marca' and r.get('parent'):
            por_padre[r['parent']].add(b)
    out = {}
    for r in rows:
        if brand(r) != 'Sin marca': continue
        hs = por_padre.get(r.get('parent'), set())
        if len(hs) == 1:
            out[r['child']] = next(iter(hs))
    return out


def marca_de(row, mapa=None):
    """brand() con la herencia por padre aplicada."""
    b = brand(row)
    if b != 'Sin marca' or not mapa: return b
    return mapa.get(row.get('child'), b)

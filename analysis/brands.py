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

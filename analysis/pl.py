"""P&L por producto: cruza la tabla de costes con las ventas reales."""
import csv, re, collections, json
from parse_br import load
from brands import brand

def n(s): return float(s.replace('.','').replace(',','.')) if ',' in s else float(s)
def norm(s): return re.sub(r'[^A-Z0-9]', '', s.upper())

COSTES = {}
for r in csv.DictReader(open('costes/margenes.tsv', encoding='utf-8'), delimiter='\t'):
    d = {k: (n(v) if k not in ('SKU','PCT') else v) for k, v in r.items()}
    COSTES[d['SKU']] = d

rows = load('data_BusinessReport_2026ytd_22sep.csv')
V = collections.defaultdict(lambda: dict(u=0.0, v=0.0, title='', brand='', asin=''))
for r in rows:
    a = V[r['sku']]
    a['u'] += r['units']; a['v'] += r['sales']
    a['title'] = r['title']; a['brand'] = brand(r); a['asin'] = r['child']

# emparejar SKU de coste -> SKUs de venta (admite sufijos FBA/FBM/_/us...)
casados = collections.defaultdict(list)
for cs in COSTES:
    base = norm(cs[:-1] if cs.endswith('b') and cs[:-1] in COSTES else cs)
    for s in V:
        ns = norm(s)
        if ns == base or re.fullmatch(re.escape(base) + r'(FBA|FBM|US|USS|CAJA|PP|\d{0,3})?', ns):
            casados[cs].append(s)

if __name__ == '__main__':
    todos = {s for hs in casados.values() for s in hs}
    cu = sum(V[s]['u'] for s in todos); cv = sum(V[s]['v'] for s in todos)
    TU = sum(a['u'] for a in V.values()); TV = sum(a['v'] for a in V.values())
    print("COBERTURA DE LA TABLA DE COSTES (ventas 2026 hasta 22 sep)\n")
    print(f"  SKUs con coste declarado : {len(COSTES)}   |   SKUs con venta 2026: {len(V)}")
    print(f"  SKUs de venta que casan  : {len(todos)}")
    print(f"  Cubren {cv:,.0f} EUR de {TV:,.0f} ({100*cv/TV:.1f}%) | {cu:,.0f} uds de {TU:,.0f} ({100*cu/TU:.1f}%)")
    print(f"  SIN COSTE: {TV-cv:,.0f} EUR ({100*(TV-cv)/TV:.1f}%)\n")
    g = collections.Counter(); gu = collections.Counter()
    for s, a in V.items():
        if s not in todos: g[a['brand']] += a['v']; gu[a['brand']] += a['u']
    print("VENTA SIN COSTE DECLARADO, POR MARCA:")
    for k, v in g.most_common(9): print(f"  {k:<14}{v:>12,.0f} EUR{gu[k]:>9,.0f} uds")
    sin = [c for c in COSTES if not casados[c]]
    print(f"\n{len(sin)} SKUs de la tabla sin ventas en 2026:\n  {', '.join(sin)}")

# ---------------- P&L por producto ----------------
# TACOS por marca (jul25-jul26, Espana) del cruce de campanas. Es una ASIGNACION
# por cuota de venta dentro de la marca, NO publicidad medida por ASIN.
TACOS = {'Arcos': 0.33, 'Cuperinox': 0.29, 'Hendi': 0.0, 'Vinfermaton': 0.94,
         'Wins': 0.0, 'Bioleaf': 22.76, 'Vinfer': 0.0, 'Vincare': 0.0}

def pnl():
    out = []
    for cs, d in COSTES.items():
        skus = casados.get(cs, [])
        u = sum(V[s]['u'] for s in skus)
        vta = sum(V[s]['v'] for s in skus)
        ref = V[skus[0]] if skus else dict(title='(sin ventas 2026)', brand='?', asin='')
        rate = d['FEE_AMZ'] / d['MINIMO_PRIME']          # comision real observada
        pvp = d['PVP']
        # precio medio realmente cobrado (incluye promos, multipack, B2B)
        pvp_real = vta / u if u else pvp
        def calc(p):
            iva = p * 0.21 / 1.21
            fee = p * rate
            neto = p - iva
            m = neto - fee - d['FBA'] - d['COSTE']
            return dict(iva=iva, fee=fee, neto=neto, margen=m,
                        pct=100*m/neto if neto else 0)
        tar, real = calc(pvp), calc(pvp_real)
        tacos = TACOS.get(ref['brand'], 0.0)
        publi_ud = pvp_real * tacos / 100
        m_tras = real['margen'] - publi_ud
        out.append(dict(
            sku=cs, skus_venta=', '.join(sorted(skus)), title=ref['title'][:80],
            brand=ref['brand'], asin=ref['asin'],
            uds=round(u), venta=round(vta, 2),
            pvp=round(pvp, 2), pvp_real=round(pvp_real, 2),
            coste=round(d['COSTE'], 3), fee=round(real['fee'], 3), fba=round(d['FBA'], 2),
            iva=round(real['iva'], 3), neto=round(real['neto'], 3), rate=round(100*rate, 2),
            margen=round(real['margen'], 3), pct=round(real['pct'], 1),
            margen_tarifa=round(tar['margen'], 3), pct_tarifa=round(tar['pct'], 1),
            hoja=round(d['MARGEN'], 2), hoja_pct=round(100*d['MARGEN']/pvp, 1),
            publi_ud=round(publi_ud, 3), tacos=tacos,
            margen_tras_publi=round(m_tras, 3),
            pct_tras_publi=round(100*m_tras/real['neto'], 1) if real['neto'] else 0,
            contrib=round(m_tras * u, 2)))
    out.sort(key=lambda x: -x['contrib'])
    return out

if __name__ == '__main__':
    P = pnl()
    con = [p for p in P if p['uds'] > 0]
    print("\n\nP&L POR PRODUCTO — los 10 que mas margen aportan (2026 hasta 22 sep)\n")
    h = (f"{'SKU':<14}{'Uds':>6}{'Venta':>10}{'PVP tar':>8}{'PVP real':>9}"
         f"{'Mg/ud':>8}{'%':>6}{'Publi/ud':>9}{'Contrib.':>10}")
    print(h); print('-'*len(h))
    for p in con[:10]:
        print(f"{p['sku']:<14}{p['uds']:>6,}{p['venta']:>10,.0f}{p['pvp']:>8.2f}{p['pvp_real']:>9.2f}"
              f"{p['margen']:>8.2f}{p['pct']:>5.0f}%{p['publi_ud']:>9.3f}{p['contrib']:>10,.0f}")
    print('  ...')
    for p in con[-6:]:
        print(f"{p['sku']:<14}{p['uds']:>6,}{p['venta']:>10,.0f}{p['pvp']:>8.2f}{p['pvp_real']:>9.2f}"
              f"{p['margen']:>8.2f}{p['pct']:>5.0f}%{p['publi_ud']:>9.3f}{p['contrib']:>10,.0f}")
    tot = sum(p['contrib'] for p in con); tv = sum(p['venta'] for p in con)
    print('-'*len(h))
    print(f"{'TOTAL':<14}{sum(p['uds'] for p in con):>6,}{tv:>10,.0f}"
          f"{'':>8}{'':>9}{'':>8}{100*tot/tv:>5.0f}%{'':>9}{tot:>10,.0f}")

    print("\n\nDONDE EL PRECIO REAL SE ALEJA DE LA TARIFA (promos, multipack, B2B)\n")
    dif = sorted([p for p in con if abs(p['pvp_real']-p['pvp']) > 0.5], key=lambda p: p['pvp_real']-p['pvp'])
    print(f"{'SKU':<14}{'PVP tar':>9}{'PVP real':>9}{'Dif':>8}{'% tarifa':>10}{'% real':>8}{'Uds':>7}")
    for p in dif[:8] + ['...'] + dif[-4:]:
        if p == '...': print('  ...'); continue
        print(f"{p['sku']:<14}{p['pvp']:>9.2f}{p['pvp_real']:>9.2f}{p['pvp_real']-p['pvp']:>+8.2f}"
              f"{p['pct_tarifa']:>9.0f}%{p['pct']:>7.0f}%{p['uds']:>7,}")

    json.dump(dict(filas=P, cobertura=dict(
        skus_coste=len(COSTES), skus_venta=len(V),
        venta_cubierta=round(sum(p['venta'] for p in P)),
        venta_total=round(sum(a['v'] for a in V.values())),
        uds_cubiertas=round(sum(p['uds'] for p in P)),
        uds_total=round(sum(a['u'] for a in V.values())),
        tacos=TACOS)), open('pnl.json', 'w'), ensure_ascii=False)
    print(f"\n-> pnl.json ({len(P)} SKUs)")

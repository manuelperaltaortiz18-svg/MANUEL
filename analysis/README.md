# Panel Marketplace

Dashboard: https://claude.ai/code/artifact/a430e013-c06e-4e3a-a434-3a046a1c5445

## Actualizar con un mes nuevo

1. Exporta el Business Report del mes desde Seller Central (nivel ASIN hijo / SKU,
   mismas columnas que los existentes).
2. Guardalo como `analysis/mensual/AAAA-MM.csv`.
3. `cd analysis && python3 build_dashboard.py`
4. Republica `dashboard.html` en el mismo artifact (misma URL).

Todo lo demas se recalcula solo: KPIs, ventana identica, margenes, BuyBox.

## Scripts

| Script | Que hace |
|---|---|
| `parse_br.py` | Parsea el CSV (millares con coma en metricas, punto/coma europeo en importes) |
| `brands.py` | Clasifica marca y mapea marca -> proveedor. **Edita aqui si anades una marca** |
| `monthly.py` | Serie mensual en consola |
| `lfl.py` | Comparativa a ventana identica |
| `margen.py` | Margen bruto y coste de oportunidad |
| `report2.py` | Informe de un periodo suelto |
| `build_dashboard.py` | Genera `dashboard.html` desde `mensual/*.csv` |

## Notas de datos

- Las sesiones se deduplican a nivel ASIN hijo: varios SKU comparten ASIN y Amazon
  repite la sesion en cada fila (inflaba el trafico un 52-65%).
- Sumar los 12 meses de 2025 cuadra al centimo en ventas y unidades con el informe
  anual; las sesiones quedan un 9% por encima porque Amazon deduplica visitantes
  dentro de cada periodo. Para sesiones y conversion de un ano completo, usa el
  informe anual.
- Nov+dic = 34,2% del ano. No anualices linealmente un ano parcial.

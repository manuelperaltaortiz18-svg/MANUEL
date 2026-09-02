# MANUEL

## Análisis de red comercial

Facturación mensual por comercial (2022–2026) y las métricas que el
seguimiento manual no daba: comparativa en ventana homogénea, peso estacional,
concentración en el comercial dominante, plazas con relevo y proyección de
cierre.

```bash
python -m sales.report
```

Para actualizar: añadir los meses nuevos a `sales/data.py`. Las listas de
meses pueden ser más cortas que 12 — el año en curso se compara siempre contra
los mismos meses del año anterior, nunca contra su total.

# Automatización en Chrome

Ciclo completo que genera un panel de cartera, lo sirve en local, lo maneja
con Chrome (Chromium vía Playwright) y verifica que lo que se ve en pantalla
coincide con lo que calcula el motor Python.

## Uso

```bash
pip install playwright
python -m automation.run_cycle              # sin ventana (headless)
python -m automation.run_cycle --headed     # con ventana visible
```

En este entorno remoto el navegador ya viene instalado en
`/opt/pw-browsers`; `automation/browser.py` lo localiza solo. En una máquina
propia, `playwright install chromium` basta.

## Qué hace el ciclo

1. **Genera** `build/dashboard.html` a partir de las carteras definidas en
   `src/config/portfolio_myinvestor.py`.
2. **Sirve** la carpeta `build/` en un puerto libre de `127.0.0.1`.
3. **Abre** Chrome y carga el panel.
4. **Interactúa**: recorre las tres pestañas de cartera y escribe una
   aportación mensual nueva en el campo real del formulario.
5. **Extrae** del DOM la composición y las 16 filas de proyección.
6. **Verifica** contra `src/core/compounding.py`: número de posiciones,
   pesos al 100 %, TER ponderado y cada valor nominal/real/aportado
   (tolerancia de 0,01 €). También vigila la consola del navegador.
7. **Informa**: `build/automation_report.json`, `build/automation_report.md`
   y una captura por cartera en `build/screenshots/`.

El proceso devuelve código de salida distinto de cero si falla cualquier
comprobación, así que sirve igual como prueba end-to-end en CI.

## Por qué duplicar el cálculo en JavaScript

El panel recalcula las proyecciones en el navegador para que sea
interactivo. Esa duplicación es intencionada: el ciclo compara las dos
implementaciones y falla si divergen, de modo que ningún cambio en
`future_value` puede desincronizarse en silencio del panel.

## Límites del entorno

El contenedor remoto tiene la salida a internet restringida por política,
así que este ciclo trabaja contra un objetivo local. Para automatizar sitios
públicos (datos de fondos, etc.) hace falta un entorno con esos dominios
permitidos, o ejecutarlo en una máquina propia.

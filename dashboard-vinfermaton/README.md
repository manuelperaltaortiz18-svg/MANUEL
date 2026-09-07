# Dashboard Vinfermaton

Seguimiento semanal de las 5 marcas de Laboratorios Vinfer S.A. en Amazon España
(Vinfermaton, Wins, Bioleaf, Vinfer, Vincare).

## Uso

```bash
npm install
npm run dev      # http://localhost:5173
npm test         # tests del parser y del cálculo de velocidad
npm run build
```

Flujo semanal: pestaña **Datos** → arrastra el `BusinessReport-DD-MM-AA.csv` →
el resto del dashboard se actualiza. Los informes se guardan en `localStorage`,
así que persisten entre sesiones en el mismo navegador.

## Decisiones que conviene conocer

**Parseo por tipo de columna, no por heurística única.** Los CSV de Amazon España
mezclan formatos: `2,800` son 2800 unidades, `48.541,14` son 48541,14 € y `95.11`
es un 95,11 %. Una sola función que adivine el formato falla en algún caso, así
que cada columna se parsea sabiendo qué es (`src/lib/parseValue.js`). El caso
`2,800 → 2.8` está cubierto por un test explícito.

**Velocidad normalizada a 7 días.** Amazon da ventas acumuladas, y los cortes
reales no caen siempre a 7 días (17 jul → 28 jul son 11). La velocidad es
`Δ acumulado / días × 7`, nunca `Δ acumulado` a secas.

**BuyBox agregado ponderado por ventas.** Al agrupar por ASIN parent o por marca,
el BB se pondera por ventas, no se promedia a pelo: lo que importa es el BB del
dinero, no el de la referencia. Esto hace que el BB de marca no coincida con una
media simple de los informes anteriores.

**Agrupación por ASIN parent.** Los child se suman al parent, nunca se listan por
SKU individual.

**Fuga BuyBox.** Estimación de ventas perdidas: `ventas / (bb/100) − ventas`.
Asume que la demanda perdida durante el tiempo sin BuyBox se la lleva un
competidor y es proporcional al tiempo sin BB. Es una cota, no una medición.

## Umbrales de alerta

Definidos en `src/lib/alerts.js` (`UMBRALES`):

| Nivel | Condición |
|---|---|
| URGENTE | BB < 55 % con más de 500 € de ventas |
| MEDIO | BB < 70 %, o velocidad −30 % o peor vs periodo anterior |
| POSITIVO | Velocidad +20 % o más, o producto nuevo por encima de 100 €/sem |
| NUEVO | ASIN que no aparecía en el informe anterior |

## Datos de arranque

`src/data/seed.js` carga el histórico de consultoría (3 jun → 1 sep 2026): la
serie de velocidad semanal, el acumulado por marca en cada corte y los 23 ASINs
de Vinfermaton a 1 de septiembre. El botón "Reiniciar a datos iniciales" de la
pestaña Datos vuelve a este estado.

## Limitación conocida

El parser está escrito contra la especificación de columnas del Business Report,
**no contra un CSV real** — no había ninguno disponible al construirlo. La
detección de columnas es tolerante (busca por nombre aproximado y detecta el
delimitador), pero el primer informe real es la prueba de verdad: si la pestaña
Datos avisa de ASINs sin clasificar o de columnas no encontradas, hay que
ajustar `findCol` en `src/lib/csv.js`.

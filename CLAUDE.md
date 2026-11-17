# CUPERINOX · Inteligencia de negocio multicanal

## Qué es esto

CUPERINOX, S.L. es una empresa española de menaje y equipamiento profesional de
cocina que vende en nueve canales y siete países. Este repositorio contiene el
análisis de ese negocio y el panel que lo resume.

**El trabajo vive en `analysis/`.** Las carpetas `src/` y `tests/` son el
andamiaje de una plantilla distinta (un sistema de inversión) que se quedó aquí
y no tiene relación con nada: no las toques y no las tomes como referencia.

**Antes de pedir o interpretar cualquier fichero, lee
[`analysis/INFORMES.md`](analysis/INFORMES.md).** Recoge, para cada fuente, la
ruta exacta en la consola, las casillas que hay que marcar, el nombre que debe
llevar el fichero y la trampa que tiene. Casi todos los errores de este proyecto
han salido de saltarse ese documento.

## El negocio, en cifras

Ritmo anual 2026, **neto de IVA**:

| Canal | Tipo | Ritmo anual |
|---|---|---|
| Amazon España | marketplace | ~3,08 M € |
| Amazon Francia, Italia, Alemania, P. Bajos | marketplace | ~0,40 M € |
| Red comercial + web B2B | venta directa | ~0,87 M € |
| Makro / Metro (ES, PT, IT, NL) | marketplace | ~0,45 M € |
| Miravia, Leroy Merlin, Carrefour | marketplace | pendiente de cargar |
| Ecommerce propio | propio | ~0,005 M € |
| **Total** | | **~4,8 M €** |

Amazon es el 73 % del negocio. Marcas, por peso en Amazon España: **Arcos**
(distribución, ~44 %), **Cuperinox** (marca propia, ~33 %), **Hendi**
(distribución, ~8 %), **Vinfermatón / Wins / Bioleaf / Vincare** (grupo Vinfer).

Objetivo estratégico declarado por el dueño: **reducir la dependencia de Arcos**,
que es marca ajena sin apoyo del proveedor, y crecer en marca propia. En un año
Arcos ha bajado del 70 % al 44 % de la facturación de Amazon.

## Cómo se trabaja aquí

### Regenerar el panel

```bash
cd analysis
python3 build_dashboard.py      # lee mensual/*.csv y todos los *.json
```

Cada pestaña se alimenta de un script que emite su JSON. Si se añade un mes o un
fichero nuevo, hay que volver a ejecutar el script correspondiente **y después**
`build_dashboard.py`:

| Script | Emite | Alimenta |
|---|---|---|
| `build_dashboard.py` | `dashboard.html` | serie mensual, mercados, BuyBox, lectura |
| `asin_yoy.py` | `asin_yoy.json`, `asin_yoy_fr.json` | ASIN a ASIN, con descomposición de causa |
| `ritmo.py` | `ritmo.json` | ritmo del mes en curso (lee `parcial/`) |
| `inv.py` | `inventario.json` | inventario frente a velocidad real |
| `pl.py` | `pnl.json` | P&L por producto |
| `canal.py` | `canal.json` | márgenes Cuperinox, FBM frente a FBA |
| `vinfer_pl.py` | `vinfer_pl.json` | márgenes Vinfer |
| `hendi.py` / `hendi_total.py` | — | márgenes Hendi y consolidado entre canales |
| `ads.py` | `ads_summary.json` | publicidad frente a negocio |
| `ads_pais.py` | `ads_pais.json` | publicidad por mercado |
| `roi.py` | `roi.json` | ¿salió a cuenta subir la inversión? |
| `b2b.py` | `b2b.json` | red comercial |
| `makro.py` | `makro.json` | canal Makro / Metro |

`parse_br.py` es el parser de los Business Report y `brands.py` la
clasificación de marcas. Todo lo demás depende de esos dos.

### Publicar

El panel es un artefacto que se actualiza publicando el mismo
`analysis/dashboard.html` a su URL. Está compartido como «cualquiera con el
enlace» y **lleva costes y márgenes dentro**.

### Git

Rama de trabajo: `claude/amazon-brands-analysis-m2ccbu`. Commits en español,
explicando **por qué** cambia algo, no solo qué. Los ficheros de datos se
versionan: son la trazabilidad del análisis.

## Reglas que no se negocian

Están todas razonadas en `analysis/INFORMES.md`. El resumen:

1. **IVA.** Amazon reporta con IVA; Makro y la red comercial vienen netos. El
   panel va **todo neto**, con el tipo de cada mercado. Dos excepciones
   deliberadas: la pestaña de Publicidad va en bruto para que el ACOS cuadre con
   la consola de Amazon Ads, y los scripts de margen necesitan el precio bruto
   para la comisión de referencia.
   **Al hablar del día a día de ventas, dar las cifras en bruto** — es lo que se
   ve en Seller Central. El neto, para comparar canales y calcular margen.

2. **Ventanas idénticas.** Nunca comparar una ventana parcial contra la media de
   un mes completo. Los días 1-16 de noviembre de 2025 fueron el 36 % del mes:
   usar la media de 30 días infla la referencia un 50 %. Si falta el parcial
   equivalente del año anterior, **pedirlo** en lugar de estimar.

3. **Nunca anualizar en línea recta.** Noviembre y diciembre son el 34 % del año
   y el 45 % de Cuperinox. Vinfer es marzo-julio. Enero es el mes más grande en
   cuchillería fuera de Q4.

4. **Acumulado no es situación actual.** Un informe de gasto del año incluye
   campañas ya pausadas. Leerlo como estado de hoy ha producido tres falsas
   alarmas (Vinfer, Bioleaf, Alemania): las tres estaban corregidas antes de que
   las señalara. Separar por `Estado de entrega` o por mes.

5. **Sesiones.** Varios SKU comparten ASIN hijo y Amazon repite las sesiones en
   cada fila: hay que tomar `max()` por ASIN hijo, no sumar. Ventas y unidades sí
   suman. Y las sesiones **no suman entre meses** (Amazon deduplica visitantes
   dentro de cada periodo): cualquier conversión de ventana larga sale de un solo
   export.

6. **Comprobar el total antes de analizar.** Un export truncado a 199 o 200 filas
   exactas es un corte, no un dato. Ha pasado tres veces.

7. **Preguntar antes de suponer.** Los errores más caros de este proyecto han
   sido suposiciones sobre cosas verificables: dar Makro por cliente mayorista
   cuando es un marketplace (y la columna `Id Platform` lo decía), o atribuir una
   caída a la BuyBox global cuando las fichas grandes la tenían al 99 %.

## Estado abierto

**Lo que falta y bloquea conclusiones:**

- **Costes reales de Arcos.** Es el 44 % de la venta y el 24 % del gasto
  publicitario, y su punto de equilibrio está calculado sobre un margen estimado
  del 17,5 %. Si el real es del 15 %, hoy Arcos pierde dinero en publicidad.
- **Tarifas FBA** de 12 SKU de Cuperinox donde se asume 3,30 €.
- **Stock disponible**: sin él no hay plan de reposición, solo velocidad.
- **Origen del pedido** en la red comercial (web / teléfono / visita).
- **Miravia, Leroy Merlin, Carrefour.**

**Frentes vivos:**

- **Publicidad.** Agencia externa (Azumi) desde mayo de 2026. Techos de ACOS
  acordados por marca; el gasto va un 37 % por encima del presupuesto del
  trimestre. El plan es que la gestión pase a hacerse aquí: el circuito previsto
  es informe maestro semanal + **bulk file de doble sentido** (se descarga, se
  devuelve modificado, se sube en Operaciones masivas).
- **Arcos.** Tres referencias con tráfico alto y BuyBox a cero o casi: entra la
  visita y la venta se la lleva otro vendedor. Es la acción de mayor retorno
  abierta y no depende de nadie externo.
- **Hendi.** Propuesta de fondo de marketing al fabricante (18.000 €/año, el 4 %
  de la compra), con una condición: catálogo diferenciado que Hendi Holanda no
  suministre a Amazon como vendor. Hendi consolidado va a ~756.000 € netos
  anuales entre Amazon y Makro, creciendo al 325 %.

## Cómo quiere el dueño que se trabaje

- **Primero la conclusión incómoda**, no enterrada en el tercer párrafo.
- **Etiquetar la confianza**: hecho medido, inferencia o suposición. Y decir
  cuándo algo no es medible con los datos disponibles, en lugar de estimarlo.
- **Retractarse rápido y explícito** cuando aparece un dato mejor. Ha pasado
  muchas veces en este proyecto y es lo que lo mantiene fiable.
- **Conciso.** Tablas antes que párrafos.
- Para cualquier plan: supuesto clave, mayor riesgo, cuello de botella y acción
  más apalancada.

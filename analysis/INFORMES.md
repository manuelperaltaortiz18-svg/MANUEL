# Informes: de dónde sale cada dato

Catálogo de las fuentes del panel: ruta exacta, casillas, nombre del fichero y
la trampa que tiene cada una. Si un fichero llega sin seguir esto, el panel se
puede construir igual pero alguna conclusión saldrá mal — abajo está la lista de
los errores que ya hemos cometido por saltarnos esto.

---

## 1. Bulk file de publicidad

El fichero más importante de los que hay aquí, por dos razones: es lo único que
guarda la **estructura completa de campañas y las listas de negativos**, y es
una **puerta de doble sentido** — el mismo formato que se descarga sirve para
subir cambios en masa.

**Ruta:** Seller Central → Publicidad → **Operaciones masivas** → Descargar

**Ajustes:**
- Marcar **«Incluir métricas de rendimiento»**
- Periodo: **últimos 60 días**
- Todos los productos publicitarios (SP, SB, SD)

**Nombre:** `BULK_2026-11-17.xlsx` (fecha de descarga)

**Para qué sirve:**
- Juzgar la estructura de campañas, no solo su resultado
- Ver la puja de cada keyword y el estado de cada grupo
- Saber qué está ya negativizado (no está en ningún otro informe)
- **Devolverlo modificado**: pujas, presupuestos, estados y negativos nuevos se
  aplican subiendo la hoja editada. Cientos de cambios en una operación.

**Circuito de trabajo:**
1. Se descarga el bulk + el informe maestro (apartado 2)
2. Se devuelve el bulk con los cambios dentro
3. Se sube en Operaciones masivas → Cargar

---

## 2. Informe maestro de publicidad  ·  semanal

Sustituye a cuatro informes anteriores. Se genera en el **constructor de
informes personalizados** de Amazon Ads y se deja guardado.

**Dimensiones — 9:**

| | |
|---|---|
| `Mes` | la que fecha el informe; sin ella no se sabe qué ventana cubre |
| `ID de la campaña` | llave de unión con todo lo demás |
| `Nombre de la campaña` | de aquí sale la marca |
| `Nombre de la cartera` | desempata cuando el nombre no dice la marca |
| `Estado de entrega de la campaña` | separa gasto vivo de pausado |
| `País de la campaña` | |
| `Producto publicitario` | separa SP / SB / SD |
| `SKU del producto anunciado-Advertised product SKU` | ACOS por referencia |
| `Marca del producto anunciado` | |

> `Mes` y `Rango de fechas` no se pueden marcar a la vez. Manda `Mes`.

**Métricas — 12:**

`Impresiones` · `Clics` · `Coste total` · `CPC` · `Compras` · `Ventas` ·
`Unidades vendidas` · `ROAS` · `Ventas (promocionadas)` ·
`Unidades vendidas (producto promocionado)` · `Ventas (halo)` ·
`Porcentaje de impresiones del top de búsquedas`

**Rango:** `2026-01-01` → hoy. Si el constructor admite un rango relativo
(«año en curso»), usarlo: así el informe no se queda viejo.

**Nombre: `ADS_2026_hasta_16nov.csv` — obligatorio con la fecha de corte.**
Sin `Rango de fechas` dentro, el nombre es lo único que dice hasta qué día
llega el último mes.

**Control de calidad, diez segundos:**
1. Que exista la columna `Mes` y que incluya el mes en curso
2. Que la suma de `Coste total` cuadre con el gasto conocido del año
3. Entre 10.000 y 25.000 filas. **199 o 200 exactas = truncado**

**Mes cerrado para comparar interanual:** generarlo aparte con rango
`1 → último día del mes` y nombrarlo `ADS_2026_oct_cerrado.csv`.

---

## 3. Business Report mensual  ·  mensual

**Ruta:** Seller Central → Informes de negocio → **Ventas y tráfico por página
de producto secundaria**

**Pedirlo en español.** El export en inglés viene con formato de número
anglosajón y, lo importante, **sin columna de SKU**: sin SKU no hay márgenes,
ni inventario, ni P&L por producto. El parser lee los dos idiomas
(`parse_br.py`), pero lo que depende del SKU se queda fuera.

**Nombre:** `BR_2026-10.csv` para un mes cerrado,
`BR_2026-11-16.csv` para un parcial.

**Dónde va:** `mensual/AAAA-MM.csv` si es mes cerrado,
`parcial/AAAA-MM-DD.csv` si está a medias. `build_dashboard.py` lee
`mensual/*.csv` y `ritmo.py` el más reciente de `parcial/`.

**Para comparar un mes en curso hace falta el parcial equivalente del año
anterior**, con el mismo día de corte: `parcial/2025-11-16.csv`. Se saca con
rango personalizado. Sin él, la comparación no es medible.

---

## 4. Informes ocasionales de publicidad

Una o dos veces al año, no entran en la cadencia semanal.

**Términos de búsqueda** — para negativizar.
Dimensiones: `Término de búsqueda`, `Segmentación`, `Tipo de coincidencia de la
segmentación`, más las 9 comunes. Métricas: las 12 comunes.
*Aprendido por las malas: sin `Coste total` no sirve de nada. El 85 % de los
términos no tiene ninguna compra, y sin coste no se pueden ordenar por euros
desperdiciados.*

**Segmentación con pujas** — para tocar pujas una a una.
Añadir `Segmentación`, `Puja objetivo`, `Estado del segmento`,
`Porcentaje de impresiones`, `Porcentaje de impresiones del top de búsquedas`.
Es lo que dice si una campaña manual caras es defensiva de marca o trabajo mal
hecho.

**Producto convertido** — para separar arrastre real de canibalización.
Añadir `ID del producto convertido`, `Nombre del producto convertido`,
`Marca del producto convertido`.

---

## 5. Makro / Metro

**Ruta:** panel de vendedor de Makro → Sold Products → Export

**Un fichero por año**, con el filtro de fecha puesto. Un export que abarque
dos años viene como **un único agregado sin fecha por línea** y no permite
medir crecimiento.

**Nombre:** `MAKRO_2025.xlsx`, `MAKRO_2026_hasta_29oct.xlsx`
**Dónde va:** `makro_raw/`

El fichero trae una fila `Total` al final que **no es un producto**: hay que
descartarla o duplica la mitad del canal. `makro.py` ya lo hace y cuadra el
total contra ella.

**Ojo con la base:** la columna se llama `Net Sales` y viene **neta**. Amazon
reporta con IVA. No son comparables sin netear Amazon.

---

## 6. Red comercial B2B

Fichero interno: `RENDIMIENTO_COMERCIALES_MES-TRIMESTRE.xlsx` → `b2b_raw/`

**Leer siempre la hoja `MENSUAL`, nunca la `ANUAL`.** La hoja anual tiene la
columna del año en curso desplazada una fila desde el primer comercial que
causa baja: atribuye a cada uno la cifra del siguiente, duplica un importe y
omite al último. Su total es incorrecto.

**Decir siempre hasta qué mes está cerrado.** Un export a medio cargar
comparado contra un año cerrado produjo una caída del 13 % que no existía: el
canal crecía un 1,6 %.

La web B2B y la red comercial **son lo mismo**: los pedidos web van dentro de
la cifra del comercial de la cartera. No se suman aparte.

---

## 7. Convenciones que no se negocian

**IVA.** Amazon reporta **con IVA**; Makro y la red comercial vienen **netos**.
El panel va **todo neto**, con el tipo de cada mercado (ES 21 %, FR 20 %,
IT 22 %, DE 19 %, NL 21 %, PT 23 %). `load(path, iva='ES')` lo hace.

Dos excepciones deliberadas:
- **La pestaña de Publicidad va en bruto**, para que el ACOS y el TACOS cuadren
  con la consola de Amazon Ads y con lo que maneja la agencia. Los puntos de
  equilibrio están en esa misma base.
- **Los scripts de margen** (`pl.py`, `canal.py`, `vinfer_pl.py`, `hendi.py`)
  necesitan el precio bruto para la comisión de referencia y netean por dentro.
  No se les pasa `iva=`.

**Al hablar del día a día de ventas, dar las cifras en bruto**, que es lo que se
ve en Seller Central. El neto, para comparar canales y calcular margen.

**Ventanas.** Nunca comparar una ventana parcial contra una media de mes
completo. Los días 1-16 de noviembre de 2025 fueron el **36 %** del mes, no el
53 %: usar la media de 30 días como referencia infla el dato un 50 %.
Black Friday y la segunda quincena se llevan el 64 % de noviembre.

**Estacionalidad.** Noviembre y diciembre son el 34 % del año y el 45 % de
Cuperinox. Enero es el mes más grande en cuchillería fuera de Q4. Vinfer es
marzo-julio con pico en junio y julio. No anualizar nunca de forma lineal.

**Acumulado frente a vivo.** Un informe de gasto de todo el año incluye
campañas hoy pausadas. Leer el acumulado como situación actual ha llevado tres
veces a conclusiones falsas (Vinfer, Bioleaf, Alemania): las tres estaban ya
corregidas cuando las señalé como problema. **Separar siempre por
`Estado de entrega` o por mes.**

---

## 8. Lo que hace falta y no está

- **Costes de Arcos.** Es el 44 % de la venta y el 24 % del gasto publicitario,
  y su punto de equilibrio está calculado sobre un margen estimado del 17,5 %.
  Si el real es del 15 %, hoy Arcos pierde dinero en publicidad.
- **Costes de Hendi por referencia** más allá de la hoja maestra actual
  (cubre el 86 % de la venta en Amazon y el 74 % en Makro).
- **Tarifas FBA** de 12 SKU de Cuperinox donde se asume 3,30 €.
- **Miravia, Leroy Merlin, Carrefour.** Juntos, menos del 5 % de la
  facturación, pero cierran el mapa de canales.
- **Stock disponible.** Sin él no hay plan de reposición real, solo velocidad
  de venta.
- **Origen del pedido en la red comercial** (web / teléfono / visita). Sin eso
  no se puede separar actividad comercial de reposición automática.

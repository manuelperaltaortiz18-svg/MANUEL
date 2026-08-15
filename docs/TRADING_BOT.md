# Bot de trading intradía S&P 500 — estrategia 1:1

Bot automático que opera rupturas de rango en el S&P 500 (futuro ES/MES, CFD o
ETF) con un bracket **estrictamente simétrico**: cada operación arriesga
exactamente lo mismo que busca ganar.

> **Aviso de alcance.** Este módulo vive en `src/trading/` y es independiente del
> sistema de inversión a largo plazo del repositorio. Su horizonte son horas,
> no 40 años. Sus señales **no** deben usarse nunca para modificar la asignación
> estratégica (`CLAUDE.md` §2, §42, §63).

---

## 1. La aritmética del 1:1

Con ratio 1:1 no hay ninguna operación que rescate una racha: toda la ventaja
está en el **porcentaje de acierto**. El umbral de rentabilidad es:

```
tasa de acierto mínima = (1 + coste_en_R) / (1 + ratio)
```

- Sin costes y ratio 1:1 → **50 %**.
- Con MES, stop de 8 puntos y comisión + 1 tick de deslizamiento por lado, el
  coste ronda 0,04 R → **52,3 %**.
- Con stops más ajustados el coste en R sube rápido: un stop de 4 puntos
  duplica el peso relativo de comisión y horquilla.

`PerformanceReport.required_hit_rate_pct` calcula esa línea con los costes
reales del backtest, y `edge_pct` muestra a cuántos puntos porcentuales está la
tasa real por encima o por debajo de ella. Es la única cifra que decide si la
estrategia funciona.

El coste incluye **comisiones y horquilla**, no solo comisiones: en un CFD la
comisión es cero y todo el coste está en el precio de ejecución. Cada operación
guarda el deslizamiento aplicado (`entry_slippage_points`,
`exit_slippage_points`) y el informe lo suma en `friction`. Un CFD "sin
comisiones" con horquilla de 5 ticks exige en la práctica ~57 % de aciertos,
frente al 50 % teórico.

## 2. Arquitectura

```
src/trading/
├── models.py       Bar, InstrumentSpec, BracketOrder, Position, Trade, Signal
├── indicators.py   ATR (Wilder), EMA/SMA, extremos móviles — versión incremental O(1)
├── data.py         carga CSV, resampleo, filtro de sesión, feed sintético
├── strategy.py     interfaz Strategy + BreakoutStrategy (bracket 1:1)
├── risk.py         tamaño de posición y cortacircuitos diarios
├── broker.py       interfaz Broker + SimulatedBroker (motor de casación)
├── engine.py       TradingBot: el bucle por vela
├── metrics.py      métricas de rendimiento y umbral de acierto
└── backtest.py     run_backtest() y LiveSession
```

El bucle por vela es el mismo en backtest y en vivo. Esa es la razón de la
separación: lo que se prueba es lo que se ejecuta.

Orden de operaciones dentro de cada vela **cerrada**:

1. el bróker casa las órdenes que ya estaban puestas;
2. se notifican ejecuciones a estrategia y gestión de riesgo;
3. se aplican las reglas de sesión (cierre forzado, corte de entradas);
4. solo entonces se puede armar un bracket nuevo, **para la vela siguiente**.

Nunca se opera al precio de una vela que ya se ha visto.

## 3. La estrategia

`BreakoutStrategy` admite dos modos:

| modo | rango que se rompe |
|---|---|
| `opening_range` | máximo/mínimo de los primeros N minutos de sesión (por defecto 30, es decir 2 velas de 15m) |
| `donchian` | máximo/mínimo de las últimas `lookback_bars` velas cerradas |

Reglas comunes:

- **Entrada**: orden *stop* a 1 tick por encima (largo) o por debajo (corto) del
  rango. Sin ruptura efectiva no hay operación.
- **Stop-limit**: la entrada lleva un límite de deslizamiento
  (`max_entry_slippage_ticks`, 4 por defecto). Si el precio se va con un hueco
  muy por encima del disparo, la operación **se descarta**: entrar 5 puntos
  tarde en un bracket de 8 puntos consume el objetivo antes de empezar.
- **Distancia del stop**: `atr_multiple × ATR(14)` o la anchura del rango roto,
  acotada entre `min_stop_points` y `max_stop_points`.
- **Objetivo**: la misma distancia, exactamente. La distancia se cuadra a la
  rejilla de ticks para que el 1:1 sea exacto y no aproximado.
- **Dirección**: si el cierre está por encima del punto medio del rango se arma
  el lado largo; si no, el corto. La orden en reposo se reemplaza cuando ese
  sesgo cambia, así que sigue al precio en lugar de quedarse obsoleta.
- **Filtro de tendencia opcional** (`trend_filter_period`): EMA sobre cierres;
  bloquea entradas contra la tendencia.

## 4. Riesgo

`RiskManager` decide el tamaño a partir del stop, nunca al revés:

```
unidades = (equity × risk_per_trade_pct / 100) / (puntos_de_stop × valor_del_punto)
```

redondeado a la baja al escalón del contrato. Si el tamaño mínimo arriesga más
del presupuesto, **no se opera** (no se redondea hacia arriba).

Cortacircuitos por sesión, todos configurables:

| límite | por defecto |
|---|---|
| operaciones por día | 3 |
| pérdidas consecutivas | 3 |
| pérdida diaria máxima | 2 % del capital al abrir la sesión |
| objetivo de beneficio diario | desactivado |
| capital mínimo para operar | desactivado |

Además, el bot **nunca mantiene posiciones de un día para otro**: cierra a
`flat_at` (15:45 por defecto) y deja de armar entradas a `entry_cutoff` (15:30).

`flat_at` es una **fecha límite**, y se compara contra el *final* de la vela,
no contra su inicio. Con velas de 15 minutos la última vela que termina a las
15:45 es la de las 15:30, así que ahí se cierra. Si se comparase el inicio, en
15m no existiría ninguna vela a las 15:55 y el cierre forzado no se dispararía
nunca — ese fallo existió y tiene su test de regresión.

## 5. Supuestos del simulador (leer antes de creerse un backtest)

`SimulatedBroker` es deliberadamente pesimista:

- Cuando una vela contiene **stop y objetivo a la vez, se asume el stop**. Con
  datos OHLC el orden intravela es desconocido; suponer lo bueno es exactamente
  como mienten los backtests.
- Los huecos por debajo del stop se ejecutan **en la apertura**, no en el stop.
- Las entradas por stop y las salidas por stop pagan deslizamiento; el objetivo
  (orden límite) no.
- Comisión en ambos lados.
- La salida se evalúa también en la **vela de entrada**.

Ese último punto tiene un coste medible. Sobre 400 sesiones sintéticas, sin
comisiones ni deslizamiento (donde un bracket simétrico debería resolverse
cerca de una moneda al aire):

| medición | velas 5m | velas 15m |
|---|---|---|
| todas las operaciones | 40,8 % | 40,1 % |
| excluyendo salidas en la vela de entrada | 47,3 % | 43,9 % |

Es decir: el motor **no** genera dinero de la nada — sesga en contra. Para
evaluar de verdad la estrategia hacen falta datos de 1 minuto o de tick que
resuelvan la secuencia intravela; con velas de 15 minutos el resultado es un
suelo, no una estimación centrada, y el sesgo es mayor que en 5m porque cada
vela abarca más recorrido.

**Cómo mitigarlo:** exporta el histórico en M1 y deja que
`run_backtest.py --timeframe 15` agregue las velas. El bot opera igual en 15
minutos, pero conviene comparar con una pasada en M1 para ver cuánto del
resultado viene del supuesto intravela.

Un detalle relacionado: ninguna operación ganadora rinde exactamente +1,00 R.
El deslizamiento de entrada y las dos comisiones ya están descontados, así que
un objetivo alcanzado paga entre 0,5 R y 1,0 R según lo ajustado que sea el
stop.

## 6. Uso

### Backtest desde línea de comandos

```bash
# Datos sintéticos, valores por defecto (MES, 15m, ruptura del rango de apertura, 1:1)
python scripts/run_backtest.py

# Datos reales de 1 minuto agregados a 15m, modo Donchian, con blotter
python scripts/run_backtest.py --csv data/SP500m_M5.csv --timeframe 15 \
    --mode donchian --lookback 20 --risk-pct 0.5 --list-trades

# CFD, solo largos, sesión europea
python scripts/run_backtest.py --instrument US500 --longs-only \
    --session-start 09:00 --session-end 17:30 --entry-cutoff 16:30 --flat-at 17:15
```

### Datos

El cargador acepta directamente lo que exportan brókeres y plataformas:
separador coma, punto y coma o tabulador; cabeceras `<DATE>`/`<TIME>` de
MetaTrader; marcas de tiempo ISO, `2026.01.05 09:30`, `05/01/2026 09:30` o
epoch Unix (TradingView). Mínimo: una columna de fecha/hora y open/high/low/close.

```
timestamp,open,high,low,close,volume
2026-01-02T09:30:00,4780.25,4783.50,4779.00,4782.75,15230
```

**La marca de tiempo es la apertura de la vela y debe estar en hora local del
mercado.** Un error de zona horaria no da error: desplaza en silencio el rango
de apertura y la hora de cierre forzado. Los epoch se interpretan como UTC.

#### Exportar desde MetaTrader 5

Con el terminal abierto y con sesión iniciada, en la máquina Windows:

```bash
pip install MetaTrader5
python scripts/export_mt5.py --symbol SP500m --timeframe M1 --days 180
```

Exporta en **M1** aunque el bot opere en 15 minutos: el agregado a 15m lo hace
`run_backtest.py --timeframe 15`, y tener el M1 permite medir después cuánto
del resultado depende del supuesto de secuencia intravela.

Escribe `data/SP500m_M5.csv` y además imprime:

- el **desfase horario del servidor** del bróker (MT5 no da las velas en hora
  del mercado, sino en hora del servidor);
- un `InstrumentSpec` listo para pegar, construido con el tick, el valor del
  tick y la **horquilla real** de tu símbolo;
- cuántos aciertos exige esa horquilla para cada tamaño de stop.

Por GUI el camino equivalente es **Ver › Símbolos (Ctrl+U) › pestaña Barras**:
elegir símbolo y periodo, *Solicitar*, y *Exportar barras*. No está en
Herramientas › Opciones.

Otras fuentes:

- **TradingView** — botón de exportar datos del gráfico (requiere plan de pago
  para intradía histórico largo).
- **Interactive Brokers** — `reqHistoricalData` vía API.
- **Databento / FirstRate / Kibot** — datos de futuro ES de pago, con calidad
  de tick.

#### La horquilla decide si esto es viable

Con la horquilla de 0,7 puntos de un CFD tipo `SP500m`, pagada al entrar y al
salir, el umbral de acierto de una estrategia 1:1 es:

| stop | aciertos necesarios |
|---|---|
| 3 pts | 73,3 % |
| 4 pts | 67,5 % |
| 6 pts | 61,7 % |
| 8 pts | 58,8 % |
| 12 pts | 55,8 % |
| 20 pts | 53,5 % |

Ninguna estrategia intradía sostiene un 70 % de aciertos. La conclusión
práctica es que con horquilla ancha **los stops muy ajustados son inviables por
aritmética**, antes incluso de mirar si la estrategia funciona: sube
`min_stop_points` o usa un vehículo más barato (futuro MES/ES). `cost_hurdle()`
en `src/trading/mt5_export.py` calcula esta tabla para tu horquilla real.

### Desde Python

```python
from src.config.trading_config import BotConfig, BreakoutConfig, RiskConfig
from src.trading.backtest import run_backtest
from src.trading.data import filter_session, load_csv, resample

bars = resample(load_csv("data/es_1m.csv"), 5)
config = BotConfig(
    strategy=BreakoutConfig(mode="opening_range", atr_multiple=1.0, reward_risk_ratio=1.0),
    risk=RiskConfig(risk_per_trade_pct=0.5, max_trades_per_day=3),
    starting_equity=25_000,
)
bars = filter_session(bars, config.session.session_start, config.session.session_end)
result = run_backtest(bars, config)
print(result.report.summary())
```

### Sesión en vivo (papel)

```python
from src.trading.backtest import LiveSession

session = LiveSession(config, logger=print)
for bar in mi_feed_de_velas_cerradas():   # solo velas ya cerradas
    session.on_bar(bar)
session.shutdown()                        # cancela y cierra al terminar
```

## 7. Conectar un bróker real

`SimulatedBroker` sirve para backtest y para papel. Para ir a real, hay que
implementar `src.trading.broker.Broker` mapeando cinco operaciones a la API del
bróker:

| método | qué debe hacer |
|---|---|
| `equity` | capital de la cuenta |
| `position` | posición abierta o `None` |
| `pending_order` | orden de entrada en reposo o `None` |
| `submit_bracket(...)` | enviar entrada stop-limit con SL y TP adjuntos |
| `cancel_pending(...)` | cancelar la orden en reposo |
| `close_position(...)` | cerrar a mercado |

`on_bar` se deja vacío (el bróker real casa por su cuenta); el adaptador empuja
las ejecuciones a `_new_entries` y `_new_trades` para que la contabilidad del
bot siga siendo idéntica. El bracket debe enviarse como orden **OCO nativa del
bróker**: si el proceso se cae, el stop tiene que sobrevivir en el servidor.

Antes de operar con dinero real, como mínimo: comprobar la zona horaria de las
velas, los vencimientos y rolos del futuro, el horario de mantenimiento del
bróker, y la reconexión del feed (una vela perdida es una señal perdida).

## 8. Tests

```bash
python -m pytest tests/ -v
```

Los tests del bot cubren la aritmética del instrumento, los indicadores, la
simetría exacta del bracket 1:1, los supuestos de ejecución (huecos, stop antes
que objetivo, stop-limit), el dimensionamiento, los cortacircuitos, las reglas
de sesión y el hecho de que nunca se mantenga riesgo de un día para otro.

## 9. Qué no hace este bot

- No opera fuera del horario configurado ni mantiene posiciones nocturnas.
- No promedia a la baja, no mueve el stop, no usa trailing (con 1:1 no aplica).
- No lleva más de una posición a la vez.
- No conoce noticias, dividendos, vencimientos ni rolos de contrato.
- No optimiza parámetros: si se ajustan hasta que el backtest brille, lo único
  que se ha medido es el ruido. Con 665 operaciones el intervalo de confianza
  del 95 % de la tasa de acierto sigue siendo de ±4 puntos porcentuales, y esa
  cifra la imprime el propio runner por ese motivo.

## 10. TradingView (Pine) y prop firms

### Comprobar el Pine antes de pegarlo

El compilador de Pine vive dentro de TradingView, así que estos scripts no se
pueden construir desde el repo. `scripts/lint_pine.py` cubre esa ceguera con
las reglas que ya han fallado de verdad:

```bash
python scripts/lint_pine.py          # revisa pine/*.pine
```

| regla | error que da TradingView |
|---|---|
| `shorttitle` de más de 10 caracteres | `SHORT_TITLE_TOO_LONG` |
| `nz()` con una fuente booleana | `CE10123` — espera `simple int` |
| línea de continuación con sangría múltiplo de 4 | `CE10156` — *end of line without line continuation* |
| tabuladores, paréntesis desbalanceados | varios |

La tercera es la menos evidente: **Pine distingue una línea partida de un
bloque nuevo por la sangría**. Un múltiplo de 4 abre bloque; cualquier otra
cantidad continúa la expresión. Un test comprueba que los scripts publicados
pasan todas las reglas.

### El script

`pine/sp500_orb_1to1.pine` es el mismo bot en Pine v6: mismo rango de apertura,
mismo stop-limit de entrada, mismo bracket 1:1, mismos cortacircuitos. Todo se
calcula en **minutos desde la apertura de la sesión**, así que funciona en
cualquier temporalidad, símbolo y zona horaria sin tocar el código.

Al pegarlo en TradingView, lo primero es **Propiedades → comisión y
deslizamiento**. Sin eso el backtest no significa nada: la horquilla es el coste
dominante de una estrategia 1:1.

La lógica de dirección del port está fijada contra el motor Python por un test
(`test_pine_port_direction_logic_matches_the_engine`), para que los dos no se
separen en silencio.

### Qué hace falta para "un 70 % de rentabilidad"

Con el coste medido del CFD en 15m (0,118 R por operación, empate en 55,9 % de
aciertos), 250 sesiones y 2 operaciones al día:

| riesgo por operación | acierto necesario para +70 % |
|---|---|
| 0,5 % | 66,5 % |
| 1,0 % | 61,2 % |
| 2,0 % | 58,6 % |

Y la probabilidad real, simulando 20 000 caminos (ruina = perder la mitad):

| acierto | riesgo | llega a +70 % | se arruina antes |
|---|---|---|---|
| 56 % | 1 % | 1,4 % | 0,5 % |
| 56 % | 2 % | 18,0 % | 26,1 % |
| 58 % | 2 % | 46,5 % | 7,4 % |
| 60 % | 2 % | 77,8 % | 1,4 % |

Es decir: el 70 % no es imposible, pero exige un acierto sostenido de ~58-60 %
en una estrategia 1:1 **después de costes**, y la vía rápida (subir el riesgo)
compra rentabilidad pagando con probabilidad de ruina.

### En una evaluación de prop firm el objetivo no es el 70 %

Objetivo típico +10 %, pérdida diaria −5 %, drawdown máximo −10 %:

| acierto | riesgo | pasa | revienta |
|---|---|---|---|
| 55 % | 1 % | 15,3 % | 32,9 % |
| 58 % | 1 % | 27,9 % | 19,4 % |
| 58 % | 2 % | 49,4 % | 48,7 % |
| 62 % | 1 % | 50,0 % | 7,8 % |

Dos lecturas que importan más que cualquier promesa:

1. **Subir el riesgo del 1 % al 2 % sube el aprobado del 27,9 % al 49,4 %, pero
   el reventón del 19,4 % al 48,7 %.** Deja de ser una estrategia y pasa a ser
   una apuesta.
2. **El límite de pérdida diaria no salta nunca** (0,0 % en toda la tabla). Con
   3 operaciones al día al 1 % no se puede perder un 5 % en una sesión. Lo que
   tumba la cuenta es siempre el **drawdown acumulado**. Por eso el parámetro
   que hay que configurar con cuidado en el Pine es `Drawdown máx. total`, no el
   diario.

`src/trading/propfirm.py` genera estas tablas para tus propios números:

```python
from src.trading.propfirm import StrategyStats, simulate_challenge
stats = StrategyStats(hit_rate=0.58, cost_r=0.118, trades_per_day=2)
print(simulate_challenge(stats, risk_per_trade_pct=1.0).summary())
```

Todo lo anterior parte de una tasa de acierto **supuesta**. Cuál es la real solo
lo dicen tus datos.

## 11. Estrategia 2 — Cierre fuera del rango de la primera vela (Nasdaq)

La regla:

1. La **primera vela de 15 minutos** de la apertura americana define un rango.
2. La primera vela que **cierre por encima del máximo** entra **larga**; la
   primera que **cierre por debajo del mínimo** entra **corta**.

Entrada a **mercado en la apertura de la vela siguiente**, stop **estructural**
al otro lado del rango, objetivo a 1:1 medido desde el llenado real.

El disparo es el **cierre**, no el nivel tocado. Una vela puede perforar el
rango con la mecha y volver dentro: eso no es señal. Es la diferencia con una
ruptura por orden stop, y es más restrictivo — pide confirmación, a cambio de
entrar más tarde y peor.

Código: `FirstCandleBreakStrategy` en `src/trading/strategy.py`,
`FirstCandleBreakConfig` en `src/config/trading_config.py`, TradingView en
`pine/nasdaq_first_candle_1to1.pine`.

```bash
python scripts/run_backtest.py --mode first-candle --instrument NAS100 \
    --equity 100000 --max-trades 1 --list-trades
```

### Variante opcional: fallo y recuperación

Con `--require-excursion` (o el check del Pine) el precio tiene que salir del
rango, volver a cerrar dentro, y solo entonces se opera el siguiente cierre
fuera. Así, una ruptura al alza que falla y cierra bajo el mínimo se opera en
corto. Sobre los mismos 250 días sintéticos:

| variante | instrumento | operaciones | stop medio | coste/R | acierto necesario |
|---|---|---|---|---|---|
| Cierre fuera | MNQ | 250 | 74 pts | 0,016 | **50,8 %** |
| Cierre fuera | NAS100 | 250 | 75 pts | 0,034 | 51,7 % |
| Fallo y recuperación | MNQ | 178 | 74 pts | 0,017 | 50,8 % |
| Fallo y recuperación | NAS100 | 178 | 75 pts | 0,037 | 51,9 % |

Misma estructura de costes; la variante con recuperación simplemente opera un
28 % menos de días. Cuál acierta más es empírico.

### Dos cambios que exigió en el motor

**Entradas a mercado.** La señal es un *cierre*, no un nivel tocado, así que la
orden entra en la apertura siguiente. Fingir que entramos al mismo cierre que
usamos para decidir sería mentir en el backtest.

**Tope de riesgo aplicado en el llenado.** El tamaño se calcula con el cierre
que confirma, pero el llenado real llega después y puede ser peor, lo que
ensancha el stop real. Sin corregirlo el riesgo se pasa del presupuesto: en el
primer test la operación arriesgaba 503 $ con un tope de 500 $. Ahora el bróker
recalcula el volumen sobre el precio real de entrada y lo recorta, o rechaza la
operación si no cabe ningún tamaño. Con una cuenta de prop firm, pasarse del
riesgo es exactamente lo que no puede ocurrir.

### Por qué encaja mucho mejor con un 1:1 que la ruptura por ATR

El stop es la anchura del rango de apertura, no un múltiplo de ATR — mucho más
ancho (74 puntos frente a 40 en los mismos datos). Y como el coste de ejecución
es fijo, un stop ancho lo diluye: **0,016 R en el futuro MNQ, un acierto
necesario del 50,8 %**, casi el 50 % teórico. La ruptura por ATR necesita 53,0 %
sobre los mismos datos.

Otras dos propiedades que van a favor en una evaluación de prop firm: **una sola
operación al día** (menos exposición a la regla de consistencia) y **posiciones
pequeñas** por el stop ancho.

### Lo que sigue sin saberse

Todo lo anterior es estructura de costes, que es calculable. Si el patrón acierta
más del 51 % es una pregunta empírica que estos datos sintéticos no responden —
son un paseo aleatorio, y ahí sale justo lo que debe salir, ~50 %.

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
| `opening_range` | máximo/mínimo de los primeros N minutos de sesión (por defecto 15) |
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
`flat_at` (15:55 por defecto) y deja de armar entradas a `entry_cutoff` (15:30).

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

| medición | aciertos |
|---|---|
| todas las operaciones | 40,8 % |
| excluyendo salidas en la vela de entrada | 47,3 % |

Es decir: el motor **no** genera dinero de la nada — sesga en contra. Para
evaluar de verdad la estrategia hacen falta datos de 1 minuto o de tick que
resuelvan la secuencia intravela; con velas de 5 minutos el resultado es un
suelo, no una estimación centrada.

Un detalle relacionado: ninguna operación ganadora rinde exactamente +1,00 R.
El deslizamiento de entrada y las dos comisiones ya están descontados, así que
un objetivo alcanzado paga entre 0,5 R y 1,0 R según lo ajustado que sea el
stop.

## 6. Uso

### Backtest desde línea de comandos

```bash
# Datos sintéticos, valores por defecto (MES, 5m, ruptura del rango de apertura, 1:1)
python scripts/run_backtest.py

# Datos reales de 1 minuto agregados a 15m, modo Donchian, con blotter
python scripts/run_backtest.py --csv data/es_1m.csv --timeframe 15 \
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

De dónde sacar velas de 5 minutos del S&P 500:

- **MetaTrader 5** — Herramientas › Centro de histórico › exportar (gratis con
  cualquier bróker de CFD).
- **TradingView** — botón de exportar datos del gráfico (requiere plan de pago
  para intradía histórico largo).
- **Interactive Brokers** — `reqHistoricalData` vía API.
- **Databento / FirstRate / Kibot** — datos de futuro ES de pago, con calidad
  de tick.

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

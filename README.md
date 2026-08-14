# MANUEL

Dos sistemas independientes conviven en este repositorio.

## 1. Sistema de inversión a largo plazo

Marco de análisis de cartera orientado a maximizar la riqueza real compuesta a
~40 años: puntuación estratégica y táctica, motor de decisión, rotación y
asignación. Las reglas están en [`CLAUDE.md`](CLAUDE.md).

```
src/config/  src/models/  src/core/  src/analysis/  src/scoring/
src/engines/ src/visualization/
```

## 2. Bot de trading intradía S&P 500 (1:1)

Bot automático de ruptura de rango con bracket estrictamente simétrico, motor
de simulación propio e interfaz de bróker enchufable.
Documentación: [`docs/TRADING_BOT.md`](docs/TRADING_BOT.md).

Opera en velas de **15 minutos** por defecto.

```bash
python scripts/run_backtest.py                    # backtest con datos sintéticos
python scripts/run_backtest.py --csv datos.csv --timeframe 15 --list-trades
python scripts/export_mt5.py --symbol SP500m --timeframe M1   # en Windows con MT5
```

Dos estrategias, ambas con bracket 1:1:

- **Ruptura del rango de apertura** (S&P 500) — [`pine/sp500_orb_1to1.pine`](pine/sp500_orb_1to1.pine)
- **Recuperación del rango de la primera vela** (Nasdaq) — [`pine/nasdaq_range_reclaim_1to1.pine`](pine/nasdaq_range_reclaim_1to1.pine)

```
src/config/trading_config.py   src/trading/   scripts/   pine/
```

Las señales del bot **no** deben usarse para modificar la asignación
estratégica del sistema anterior (`CLAUDE.md` §2, §42).

## Tests

```bash
python -m pytest tests/ -v
```

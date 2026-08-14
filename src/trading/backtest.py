"""
Backtest and live-session runners.

`run_backtest` replays historical bars through exactly the same objects a live
session uses; `LiveSession` wraps the bot for a streaming feed. Swapping the
`SimulatedBroker` for a real `Broker` adapter is the only change needed to go
from paper to live.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional, Sequence

from src.config.trading_config import BotConfig, DEFAULT_CONFIG
from src.trading.broker import Broker, SimulatedBroker
from src.trading.engine import Logger, TradingBot
from src.trading.metrics import PerformanceReport, analyse
from src.trading.models import Bar, Trade
from src.trading.risk import RiskManager
from src.trading.strategy import BreakoutStrategy, Strategy


@dataclass
class BacktestResult:
    config: BotConfig
    trades: list[Trade]
    report: PerformanceReport
    equity_curve: list[float] = field(default_factory=list)
    rejected_signals: list[tuple] = field(default_factory=list)

    @property
    def net_pnl(self) -> float:
        return self.report.net_pnl


def build_bot(
    config: BotConfig = DEFAULT_CONFIG,
    broker: Optional[Broker] = None,
    strategy: Optional[Strategy] = None,
    logger: Optional[Logger] = None,
) -> TradingBot:
    """Assemble strategy + risk + broker into a ready-to-run bot."""
    broker = broker or SimulatedBroker(config.instrument, config.starting_equity)
    strategy = strategy or BreakoutStrategy(
        config.strategy, config.instrument, config.session
    )
    risk = RiskManager(config.risk, config.instrument)
    return TradingBot(config, strategy, broker, risk, logger=logger)


def run_backtest(
    bars: Sequence[Bar],
    config: BotConfig = DEFAULT_CONFIG,
    logger: Optional[Logger] = None,
    strategy: Optional[Strategy] = None,
) -> BacktestResult:
    """Replay `bars` and return trades plus a full performance report."""
    broker = SimulatedBroker(config.instrument, config.starting_equity)
    bot = build_bot(config, broker=broker, strategy=strategy, logger=logger)
    bot.run(bars)

    report = analyse(
        broker.trades,
        config.starting_equity,
        reward_risk_ratio=getattr(config.strategy, "reward_risk_ratio", 1.0),
    )
    equity = [config.starting_equity] + [e for _, e in broker.equity_curve]
    return BacktestResult(
        config=config,
        trades=list(broker.trades),
        report=report,
        equity_curve=equity,
        rejected_signals=list(bot.rejected_signals),
    )


class LiveSession:
    """
    Thin wrapper for a streaming feed.

    Feed it closed bars as they complete (`session.on_bar(bar)`); it keeps no
    wall-clock state of its own, so a paper run and a backtest of the same bars
    produce identical results.
    """

    def __init__(
        self,
        config: BotConfig = DEFAULT_CONFIG,
        broker: Optional[Broker] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        self.config = config
        self.broker = broker or SimulatedBroker(
            config.instrument, config.starting_equity
        )
        self.bot = build_bot(config, broker=self.broker, logger=logger)

    def on_bar(self, bar: Bar) -> None:
        self.bot.on_bar(bar)

    def consume(self, feed: Iterable[Bar]) -> None:
        for bar in feed:
            self.on_bar(bar)

    def shutdown(self) -> None:
        """Cancel resting orders and flatten — call this before exiting."""
        self.bot.finish()

    @property
    def report(self) -> PerformanceReport:
        trades = getattr(self.broker, "trades", [])
        return analyse(
            trades,
            self.config.starting_equity,
            reward_risk_ratio=self.config.strategy.reward_risk_ratio,
        )

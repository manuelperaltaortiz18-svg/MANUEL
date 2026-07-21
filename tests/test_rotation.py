"""Tests for rotation engine."""
from src.engines.rotation import (
    RotationCost,
    RotationProposal,
    five_year_hold_test,
    buy_and_hold_benchmark_test,
)
from src.models.asset import AssetRole


def test_core_rotation_blocked_when_marginal():
    proposal = RotationProposal(
        source_ticker="IWDA",
        target_ticker="VWCE",
        role=AssetRole.CORE,
        source_strategic_score=88,
        target_strategic_score=90,
        source_tactical_score=55,
        target_tactical_score=70,
        expected_cagr_improvement=0.002,
        cost_improvement_pct=0.05,
        rotation_cost=RotationCost(transaction_cost_pct=0.10, estimated_tax_pct=2.0),
    )
    assert not proposal.should_rotate


def test_satellite_rotation_allowed():
    proposal = RotationProposal(
        source_ticker="XLK",
        target_ticker="SOXX",
        role=AssetRole.SATELLITE,
        source_strategic_score=60,
        target_strategic_score=75,
        source_tactical_score=40,
        target_tactical_score=80,
        expected_cagr_improvement=0.02,
        cost_improvement_pct=0.0,
        rotation_cost=RotationCost(transaction_cost_pct=0.10),
    )
    assert proposal.should_rotate


def test_five_year_hold_test_passes():
    proposal = RotationProposal(
        source_ticker="A", target_ticker="B",
        role=AssetRole.CORE,
        source_strategic_score=60, target_strategic_score=85,
        source_tactical_score=50, target_tactical_score=70,
        expected_cagr_improvement=0.02,
        cost_improvement_pct=0.0,
        rotation_cost=RotationCost(),
    )
    assert five_year_hold_test(proposal)


def test_buy_and_hold_benchmark():
    result = buy_and_hold_benchmark_test(
        strategy_cagr=0.08, buyhold_cagr=0.07,
        strategy_sharpe=0.55, buyhold_sharpe=0.45,
        strategy_max_dd=-0.30, buyhold_max_dd=-0.35,
        strategy_turnover=0.5,
    )
    assert result["adds_value"]
    assert result["recommendation"] == "KEEP STRATEGY"


def test_buy_and_hold_wins():
    result = buy_and_hold_benchmark_test(
        strategy_cagr=0.065, buyhold_cagr=0.07,
        strategy_sharpe=0.40, buyhold_sharpe=0.45,
        strategy_max_dd=-0.32, buyhold_max_dd=-0.35,
        strategy_turnover=1.5,
    )
    assert not result["adds_value"]
    assert result["recommendation"] == "PREFER BUY & HOLD"

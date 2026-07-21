"""Tests for scoring systems."""
from src.scoring.scores import (
    CompoundingScore,
    ConsistencyScore,
    ResilienceScore,
    StrategicScore,
    TacticalScore,
    strategic_tactical_matrix,
    LongTermPortfolioScore,
    CompoundingInterruptionRisk,
    BehavioralRisk,
    PortfolioComplexity,
    AlphaPersistence,
)


def test_compounding_score_range():
    score = CompoundingScore(
        historical_cagr=80, real_returns=75, drawdown_quality=70,
        recovery_speed=70, volatility=65, consistency=80,
        diversification=85, cost_efficiency=90, tracking_quality=80,
        structural_growth=70, survivability=85, liquidity=80,
        fund_size=75, replication_quality=80, index_methodology=75,
        historical_resilience=70, risk_adjusted_return=75,
    )
    assert 0 <= score.total <= 100


def test_strategic_tactical_matrix_all_quadrants():
    assert "STRONG CORE" in strategic_tactical_matrix(80, 70)
    assert "CORE HOLD" in strategic_tactical_matrix(80, 40)
    assert "SATELLITE" in strategic_tactical_matrix(50, 70)
    assert "AVOID" in strategic_tactical_matrix(50, 40)


def test_strategic_score():
    s = StrategicScore(
        compounding_score=85, consistency_score=80,
        resilience_score=75, cost_efficiency=90,
        diversification=85, failure_risk_inv=90,
    )
    assert 70 <= s.total <= 100


def test_tactical_score():
    t = TacticalScore(
        momentum_1m=60, momentum_3m=65, momentum_6m=70,
        relative_strength=75, trend=80, regime_fit=70, valuation=65,
    )
    assert 0 <= t.total <= 100


def test_alpha_not_persistent_short_history():
    a = AlphaPersistence(rolling_alpha_3y=0.02)
    assert not a.is_persistent


def test_alpha_persistent():
    a = AlphaPersistence(
        rolling_alpha_5y=0.01, consistency_vs_benchmark=70, downside_capture=85,
    )
    assert a.is_persistent


def test_portfolio_score():
    ps = LongTermPortfolioScore(
        compounding_potential=80, diversification=85,
        cost_efficiency=90, historical_resilience=75,
        risk_adjusted_return=70, drawdown_sustainability=65,
        tax_efficiency=80, structural_growth=75,
        simplicity=85, turnover_efficiency=90,
    )
    assert 60 <= ps.total <= 100


def test_behavioral_risk():
    br = BehavioralRisk(
        trading_temptation=30, panic_sell_risk=20,
        complexity_confusion=10, performance_chasing=15,
    )
    assert br.total < 30


def test_complexity_score():
    pc = PortfolioComplexity(
        position_count=40, overlap_degree=60,
        rebalancing_difficulty=50, monitoring_burden=45,
    )
    assert pc.total > 40

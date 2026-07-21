"""Tests for decision engine."""
from src.engines.decision import evaluate_decision
from src.scoring.scores import StrategicScore, TacticalScore


def test_core_hold_despite_weak_tactical():
    """§2 — A tactical signal must NOT destroy a good strategic decision."""
    strategic = StrategicScore(
        compounding_score=90, consistency_score=85,
        resilience_score=80, cost_efficiency=95,
        diversification=90, failure_risk_inv=90,
    )
    tactical = TacticalScore(
        momentum_1m=30, momentum_3m=35, momentum_6m=40,
        relative_strength=45, trend=50, regime_fit=55, valuation=60,
    )
    decision = evaluate_decision("IWDA", strategic, tactical, current_holding=True, is_core=True)
    assert decision.action == "HOLD"
    assert decision.passes_five_year_test


def test_exit_candidate_when_both_low():
    strategic = StrategicScore(
        compounding_score=30, consistency_score=35,
        resilience_score=25, cost_efficiency=20,
        diversification=30, failure_risk_inv=25,
    )
    tactical = TacticalScore(
        momentum_1m=20, momentum_3m=25, momentum_6m=30,
        relative_strength=25, trend=20, regime_fit=30, valuation=25,
    )
    decision = evaluate_decision("JUNK", strategic, tactical, current_holding=True)
    assert "EXIT" in decision.action


def test_performance_chasing_warning():
    """§42 — Detect performance chasing."""
    strategic = StrategicScore(
        compounding_score=30, consistency_score=35,
        resilience_score=30, cost_efficiency=40,
        diversification=35, failure_risk_inv=30,
    )
    tactical = TacticalScore(
        momentum_1m=90, momentum_3m=85, momentum_6m=85,
        relative_strength=80, trend=80, regime_fit=75, valuation=70,
    )
    decision = evaluate_decision("HYPE", strategic, tactical, current_holding=False)
    assert "chasing" in decision.rationale.lower()


def test_buy_candidate_strong_both():
    strategic = StrategicScore(
        compounding_score=85, consistency_score=80,
        resilience_score=75, cost_efficiency=90,
        diversification=85, failure_risk_inv=85,
    )
    tactical = TacticalScore(
        momentum_1m=70, momentum_3m=75, momentum_6m=70,
        relative_strength=70, trend=65, regime_fit=60, valuation=65,
    )
    decision = evaluate_decision("VWCE", strategic, tactical, current_holding=False)
    assert "BUY" in decision.action

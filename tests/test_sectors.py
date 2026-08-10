"""Tests for the sector analysis engine."""
import pytest
from src.analysis.sectors import (
    GICSSector,
    CyclePhase,
    MoatType,
    SectorStructuralScore,
    SectorCyclicalScore,
    SectorRiskScore,
    SectorCompoundingProfile,
    SectorProfile,
    ValueChainSegment,
    ValueChainPosition,
    CompetitiveDynamics,
    SectorOpportunity,
    build_sector_database,
    rank_sectors,
    find_opportunities,
    get_cycle_favored_sectors,
    value_chain_deep_dive,
)


class TestSectorStructuralScore:
    def test_weights_sum_to_one(self):
        weights = {
            "secular_growth": 0.20,
            "pricing_power": 0.15,
            "margin_trajectory": 0.12,
            "innovation_intensity": 0.10,
            "barriers_to_entry": 0.13,
            "capital_efficiency": 0.12,
            "cash_generation": 0.10,
            "esg_alignment": 0.08,
        }
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_total_all_100(self):
        s = SectorStructuralScore(
            secular_growth=100, pricing_power=100, margin_trajectory=100,
            innovation_intensity=100, barriers_to_entry=100,
            capital_efficiency=100, cash_generation=100, esg_alignment=100,
        )
        assert s.total == 100.0

    def test_total_all_zero(self):
        assert SectorStructuralScore().total == 0.0


class TestSectorCyclicalScore:
    def test_weights_sum_to_one(self):
        weights = {
            "earnings_momentum": 0.20,
            "relative_valuation": 0.20,
            "credit_conditions": 0.15,
            "inventory_cycle": 0.10,
            "capex_cycle": 0.10,
            "labor_market": 0.10,
            "policy_environment": 0.15,
        }
        assert abs(sum(weights.values()) - 1.0) < 1e-9


class TestSectorRiskScore:
    def test_weights_sum_to_one(self):
        weights = {
            "regulatory_risk": 0.15,
            "technological_disruption": 0.15,
            "geopolitical_exposure": 0.12,
            "concentration_risk": 0.13,
            "leverage_risk": 0.12,
            "commodity_sensitivity": 0.10,
            "currency_risk": 0.10,
            "tail_risk": 0.13,
        }
        assert abs(sum(weights.values()) - 1.0) < 1e-9


class TestSectorCompoundingProfile:
    def test_total_shareholder_yield(self):
        p = SectorCompoundingProfile(
            dividend_contribution_pct=2.0, buyback_yield_avg=1.5
        )
        assert p.total_shareholder_yield == 3.5

    def test_organic_growth_quality_zero_earnings(self):
        p = SectorCompoundingProfile(earnings_growth_cagr=0)
        assert p.organic_growth_quality == 0


class TestSectorProfile:
    def test_composite_score(self):
        p = SectorProfile(
            sector=GICSSector.TECHNOLOGY,
            structural_score=SectorStructuralScore(
                secular_growth=80, pricing_power=70, margin_trajectory=75,
                innovation_intensity=90, barriers_to_entry=70,
                capital_efficiency=65, cash_generation=70, esg_alignment=60,
            ),
            cyclical_score=SectorCyclicalScore(
                earnings_momentum=70, relative_valuation=60,
                credit_conditions=65, inventory_cycle=55,
                capex_cycle=60, labor_market=50, policy_environment=65,
            ),
            risk_score=SectorRiskScore(
                regulatory_risk=40, technological_disruption=30,
                geopolitical_exposure=45, concentration_risk=50,
                leverage_risk=25, commodity_sensitivity=15,
                currency_risk=30, tail_risk=35,
            ),
        )
        score = p.composite_score
        assert 0 <= score <= 100

    def test_investment_verdict_strong_overweight(self):
        p = SectorProfile(
            sector=GICSSector.TECHNOLOGY,
            structural_score=SectorStructuralScore(
                **{k: 90 for k in [
                    "secular_growth", "pricing_power", "margin_trajectory",
                    "innovation_intensity", "barriers_to_entry",
                    "capital_efficiency", "cash_generation", "esg_alignment",
                ]}
            ),
            cyclical_score=SectorCyclicalScore(
                **{k: 80 for k in [
                    "earnings_momentum", "relative_valuation",
                    "credit_conditions", "inventory_cycle",
                    "capex_cycle", "labor_market", "policy_environment",
                ]}
            ),
        )
        assert p.investment_verdict == "STRONG OVERWEIGHT"


class TestBuildSectorDatabase:
    def test_all_11_sectors_present(self):
        db = build_sector_database()
        assert len(db) == 11
        for sector in GICSSector:
            assert sector in db

    def test_each_sector_has_value_chain(self):
        db = build_sector_database()
        for sector, profile in db.items():
            assert len(profile.value_chain) > 0, f"{sector} has no value chain"

    def test_each_sector_has_primary_etfs(self):
        db = build_sector_database()
        for sector, profile in db.items():
            assert len(profile.primary_etfs) > 0, f"{sector} has no ETFs"

    def test_each_segment_has_companies(self):
        db = build_sector_database()
        for sector, profile in db.items():
            for seg in profile.value_chain:
                assert len(seg.key_companies) > 0, (
                    f"{sector}/{seg.name} has no companies"
                )


class TestRankSectors:
    def test_returns_all_sectors(self):
        db = build_sector_database()
        ranked = rank_sectors(db)
        assert len(ranked) == 11

    def test_sorted_descending(self):
        db = build_sector_database()
        ranked = rank_sectors(db)
        scores = [r[1] for r in ranked]
        assert scores == sorted(scores, reverse=True)


class TestFindOpportunities:
    def test_returns_list(self):
        db = build_sector_database()
        opps = find_opportunities(db, min_structural_score=0)
        assert isinstance(opps, list)
        assert len(opps) > 0

    def test_moat_filter(self):
        db = build_sector_database()
        # With scores at 0, min_structural_score=0 should still work
        opps = find_opportunities(
            db,
            min_structural_score=0,
            preferred_moats=[MoatType.NETWORK_EFFECTS],
        )
        for opp in opps:
            profile = db[opp.sector]
            segment = next(
                s for s in profile.value_chain if s.name == opp.segment
            )
            assert MoatType.NETWORK_EFFECTS in segment.primary_moats


class TestGetCycleFavoredSectors:
    def test_recession_favorites(self):
        db = build_sector_database()
        favored = get_cycle_favored_sectors(db, CyclePhase.RECESSION)
        sector_names = {s.value for s, _ in favored}
        assert "Health Care" in sector_names
        assert "Consumer Staples" in sector_names


class TestValueChainDeepDive:
    def test_returns_all_segments(self):
        db = build_sector_database()
        profile = db[GICSSector.TECHNOLOGY]
        dive = value_chain_deep_dive(profile)
        assert len(dive) == len(profile.value_chain)
        for seg in profile.value_chain:
            assert seg.name in dive

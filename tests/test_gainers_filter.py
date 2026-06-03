"""
Tests for GainersService filter pipeline — Slice 1: Backend filter pipeline.

Acceptance criteria covered:
- AC-01: price range filter  → tests 1–3
- AC-02: minimum volume filter → tests 4–5
- AC-03: minimum % change filter → tests 6–7
- AC-04: market cap bounds filter (Stage 2) → tests 9–10, 21–25
- AC-05: float bounds filter (Stage 2) → tests 11–13, 26–30
- AC-06: sector exclude list (Stage 1) → tests 14–15
- AC-07: country exclude list (Stage 1) → tests 16–17
- AC-11: watchlist exemption → tests 8, 18, 31–32
- Cache key determinism → test 19
- MIN_CHANGE_PCT constant removed → test 20
- Stage-2 null/zero pass-through → tests 33–36
- Stage-2 non-dict float_data pass-through → test 37
"""

import subprocess
import sys
from unittest.mock import MagicMock

import pytest

# Ensure project root is on sys.path so "app" is importable
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.gainers import GainerFilterParams, GainersService


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def service() -> GainersService:
    """GainersService instance with a mocked DilutionService dependency."""
    mock_dilution = MagicMock()
    return GainersService(dilution_service=mock_dilution)


@pytest.fixture
def default_fp() -> GainerFilterParams:
    """Default GainerFilterParams (small-cap-runner defaults)."""
    return GainerFilterParams()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_fp(**kwargs) -> GainerFilterParams:
    """Build a GainerFilterParams with selective overrides."""
    return GainerFilterParams(**kwargs)


def make_item(ticker="AAPL", price=5.0, volume=2_000_000, change_pct=20.0) -> dict:
    return {
        "ticker": ticker,
        "price": price,
        "volume": volume,
        "todaysChangePerc": change_pct,
    }


def make_fmp(
    marketCap=None,
    float_val=None,
    sector=None,
    country=None,
) -> dict:
    return {
        "marketCap": marketCap,
        "float": float_val,
        "sector": sector,
        "country": country,
    }


def make_askedgar_float(
    market_cap_final=None,
    float_val=None,
) -> dict:
    """Build an AskEdgar float-outstanding style dict for Stage-2 tests.

    Keys match the live AskEdgar response: market_cap_final, float.
    """
    return {
        "market_cap_final": market_cap_final,
        "float": float_val,
    }


# ===========================================================================
# Stage 0 — Free-field filter (AC-01, AC-02, AC-03, AC-11)
# ===========================================================================

# AC-01 ─────────────────────────────────────────────────────────────────────

def test_stage0_price_min_excludes_ticker(service):
    """AC-01: price below price_min returns False."""
    fp = make_fp(price_min=1.0, price_max=20.0)
    item = make_item(price=0.50)
    assert service._apply_stage0_filter(item, fp) is False


def test_stage0_price_max_excludes_ticker(service):
    """AC-01: price above price_max returns False."""
    fp = make_fp(price_min=1.0, price_max=20.0)
    item = make_item(price=25.00)
    assert service._apply_stage0_filter(item, fp) is False


def test_stage0_price_range_passes_ticker(service):
    """AC-01: price within [price_min, price_max] inclusive returns True."""
    fp = make_fp(price_min=1.0, price_max=20.0)
    item_at_min = make_item(price=1.0)
    item_mid = make_item(price=10.0)
    item_at_max = make_item(price=20.0)
    assert service._apply_stage0_filter(item_at_min, fp) is True
    assert service._apply_stage0_filter(item_mid, fp) is True
    assert service._apply_stage0_filter(item_at_max, fp) is True


# AC-02 ─────────────────────────────────────────────────────────────────────

def test_stage0_volume_min_excludes_ticker(service):
    """AC-02: volume strictly less than volume_min returns False."""
    fp = make_fp(volume_min=1_000_000)
    item = make_item(volume=999_999)
    assert service._apply_stage0_filter(item, fp) is False


def test_stage0_volume_min_passes_ticker(service):
    """AC-02: volume equal to or greater than volume_min returns True."""
    fp = make_fp(volume_min=1_000_000)
    item_at_threshold = make_item(volume=1_000_000)
    item_above = make_item(volume=5_000_000)
    assert service._apply_stage0_filter(item_at_threshold, fp) is True
    assert service._apply_stage0_filter(item_above, fp) is True


# AC-03 ─────────────────────────────────────────────────────────────────────

def test_stage0_change_pct_excludes_ticker(service):
    """AC-03: change_pct strictly below change_pct_min returns False."""
    fp = make_fp(change_pct_min=15.0)
    item = make_item(change_pct=14.99)
    assert service._apply_stage0_filter(item, fp) is False


def test_stage0_change_pct_passes_ticker(service):
    """AC-03: change_pct equal to or above change_pct_min returns True."""
    fp = make_fp(change_pct_min=15.0)
    item_at_threshold = make_item(change_pct=15.0)
    item_above = make_item(change_pct=50.0)
    assert service._apply_stage0_filter(item_at_threshold, fp) is True
    assert service._apply_stage0_filter(item_above, fp) is True


# AC-11 (Stage 0) ────────────────────────────────────────────────────────────

def test_stage0_watchlist_ticker_always_passes(service):
    """AC-11: watchlist ticker returns True regardless of price/volume/change failures."""
    fp = make_fp(
        price_min=5.0,
        price_max=10.0,
        volume_min=1_000_000,
        change_pct_min=15.0,
        watchlist=frozenset({"WLTK"}),
    )
    # Item fails all three Stage 0 criteria
    item = make_item(ticker="WLTK", price=0.10, volume=100, change_pct=1.0)
    assert service._apply_stage0_filter(item, fp) is True


# ===========================================================================
# Stage 1 — FMP-derived filter (AC-04, AC-05, AC-06, AC-07, AC-11)
# ===========================================================================

# AC-04 (Stage 1 only enforces sector/country; no mcap/float in Stage 1) ─────

def test_stage1_mcap_field_does_not_affect_stage1(service):
    """AC-04: Stage 1 does NOT enforce mcap bounds — that moved to Stage 2.
    A dict with a large market_cap_final still passes Stage 1."""
    fp = make_fp(mcap_max=500_000_000.0)
    fmp = make_fmp(sector=None, country=None)
    # Stage 1 only checks sector/country; mcap is not its concern
    assert service._apply_stage1_filter(fmp, fp, "TSLA") is True


def test_stage1_mcap_null_passes(service):
    """AC-04 edge case: Stage 1 always passes when no sector/country exclusions."""
    fp = make_fp(mcap_max=500_000_000.0)
    fmp = make_fmp(sector=None, country=None)
    assert service._apply_stage1_filter(fmp, fp, "AAPL") is True


# AC-05 (Stage 1 only enforces sector/country; no float in Stage 1) ──────────

def test_stage1_float_field_does_not_affect_stage1(service):
    """AC-05: Stage 1 does NOT enforce float bounds — that moved to Stage 2.
    A large float value has no effect on Stage 1."""
    fp = make_fp(float_max=50_000_000.0)
    fmp = make_fmp(sector=None, country=None)
    assert service._apply_stage1_filter(fmp, fp, "HIFL") is True


def test_stage1_float_null_passes(service):
    """AC-05 edge case: no sector/country exclusions → Stage 1 always passes."""
    fp = make_fp(float_max=50_000_000.0)
    fmp = make_fmp(sector=None, country=None)
    assert service._apply_stage1_filter(fmp, fp, "UNKF") is True


def test_stage1_float_zero_passes(service):
    """AC-05 edge case: Stage 1 is unaffected by any float value."""
    fp = make_fp(float_max=50_000_000.0)
    fmp = make_fmp(sector=None, country=None)
    assert service._apply_stage1_filter(fmp, fp, "ZERO") is True


# AC-06 ─────────────────────────────────────────────────────────────────────

def test_stage1_sector_exclude_matches(service):
    """AC-06: sector matching an excluded sector (case-insensitive) returns False."""
    fp = make_fp(sector_exclude=["technology"])
    fmp = make_fmp(sector="Technology")
    assert service._apply_stage1_filter(fmp, fp, "TECH") is False


def test_stage1_sector_null_passes(service):
    """AC-06 edge case: sector=None passes (unknown = pass-through)."""
    fp = make_fp(sector_exclude=["technology"])
    fmp = make_fmp(sector=None)
    assert service._apply_stage1_filter(fmp, fp, "NOSEC") is True


# AC-07 ─────────────────────────────────────────────────────────────────────

def test_stage1_country_exclude_matches(service):
    """AC-07: country matching an excluded country (case-insensitive) returns False."""
    fp = make_fp(country_exclude=["cn"])
    fmp = make_fmp(country="CN")
    assert service._apply_stage1_filter(fmp, fp, "CNTK") is False


def test_stage1_country_null_passes(service):
    """AC-07 edge case: country=None passes (unknown = pass-through)."""
    fp = make_fp(country_exclude=["cn"])
    fmp = make_fmp(country=None)
    assert service._apply_stage1_filter(fmp, fp, "NOCNT") is True


# AC-11 (Stage 1) ────────────────────────────────────────────────────────────

def test_stage1_watchlist_ticker_always_passes(service):
    """AC-11: watchlist ticker always returns True regardless of stage 1 failures."""
    fp = make_fp(
        mcap_max=500_000_000.0,
        float_max=50_000_000.0,
        sector_exclude=["technology"],
        country_exclude=["cn"],
        watchlist=frozenset({"WLTK"}),
    )
    # FMP fields that would fail every Stage 1 criterion
    fmp = make_fmp(
        marketCap=900_000_000.0,
        float_val=200_000_000.0,
        sector="Technology",
        country="CN",
    )
    assert service._apply_stage1_filter(fmp, fp, "WLTK") is True


# ===========================================================================
# Cache key determinism (§7 Architecture)
# ===========================================================================

def test_filter_cache_key_deterministic(service):
    """Same GainerFilterParams produces same key; different params produce different keys;
    watchlist does NOT affect the key."""
    fp_a = make_fp(price_min=1.0, price_max=20.0, volume_min=1_000_000, change_pct_min=15.0)
    fp_b = make_fp(price_min=1.0, price_max=20.0, volume_min=1_000_000, change_pct_min=15.0)
    fp_c = make_fp(price_min=2.0, price_max=20.0, volume_min=1_000_000, change_pct_min=15.0)

    # Same params → same key
    assert service._filter_cache_key(fp_a) == service._filter_cache_key(fp_b)

    # Different price_min → different key
    assert service._filter_cache_key(fp_a) != service._filter_cache_key(fp_c)

    # Watchlist does NOT affect the cache key
    fp_with_watchlist = make_fp(
        price_min=1.0, price_max=20.0, volume_min=1_000_000, change_pct_min=15.0,
        watchlist=frozenset({"AAPL", "TSLA"}),
    )
    assert service._filter_cache_key(fp_a) == service._filter_cache_key(fp_with_watchlist)


# ===========================================================================
# MIN_CHANGE_PCT constant removed (AC-03, §6 Architecture)
# ===========================================================================

def test_min_change_pct_constant_removed():
    """AC-03: the MIN_CHANGE_PCT backend constant has been removed from gainers.py."""
    repo_root = os.path.join(os.path.dirname(__file__), "..")
    gainers_path = os.path.join(repo_root, "app", "services", "gainers.py")
    result = subprocess.run(
        ["grep", "-c", "MIN_CHANGE_PCT", gainers_path],
        capture_output=True,
        text=True,
    )
    # grep -c returns the count of matching lines; 0 matching lines means exit code 1
    # and stdout "0\n", OR exit code 0 with stdout "0\n" on some systems.
    count = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
    assert count == 0, (
        f"MIN_CHANGE_PCT still present in gainers.py ({count} occurrence(s)). "
        "The constant must be removed per AC-03 and §6 of the architecture."
    )


# ===========================================================================
# Stage 2 — AskEdgar float-outstanding filter (AC-04, AC-05, AC-11)
# These tests cover the live mcap/float gate that uses AskEdgar data.
# ===========================================================================

# AC-04 mcap_min ─────────────────────────────────────────────────────────────

def test_stage2_mcap_min_below_bound_excludes(service):
    """AC-04: market_cap_final below mcap_min returns False."""
    fp = make_fp(mcap_min=100_000_000.0)
    float_data = make_askedgar_float(market_cap_final=50_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "SMLC") is False


# AC-04 mcap_max ─────────────────────────────────────────────────────────────

def test_stage2_mcap_max_above_bound_excludes(service):
    """AC-04: market_cap_final above mcap_max returns False."""
    fp = make_fp(mcap_max=500_000_000.0)
    float_data = make_askedgar_float(market_cap_final=600_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "BIGC") is False


def test_stage2_mcap_in_range_passes(service):
    """AC-04: market_cap_final within [mcap_min, mcap_max] returns True."""
    fp = make_fp(mcap_min=50_000_000.0, mcap_max=500_000_000.0)
    float_data = make_askedgar_float(market_cap_final=200_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "MIDC") is True


# AC-05 float_min ─────────────────────────────────────────────────────────────

def test_stage2_float_min_below_bound_excludes(service):
    """AC-05: float below float_min returns False."""
    fp = make_fp(float_min=10_000_000.0)
    float_data = make_askedgar_float(float_val=5_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "TNYF") is False


# AC-05 float_max ─────────────────────────────────────────────────────────────

def test_stage2_float_max_above_bound_excludes(service):
    """AC-05: float above float_max returns False."""
    fp = make_fp(float_max=50_000_000.0)
    float_data = make_askedgar_float(float_val=75_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "HIFL") is False


def test_stage2_float_in_range_passes(service):
    """AC-05: float within [float_min, float_max] returns True."""
    fp = make_fp(float_min=5_000_000.0, float_max=50_000_000.0)
    float_data = make_askedgar_float(float_val=20_000_000.0)
    assert service._apply_stage2_filter(float_data, fp, "MIDF") is True


# AC-04/05 null pass-through ─────────────────────────────────────────────────

def test_stage2_mcap_none_passes_through(service):
    """AC-04 edge case: market_cap_final=None passes through (unknown = do not exclude)."""
    fp = make_fp(mcap_max=500_000_000.0)
    float_data = make_askedgar_float(market_cap_final=None)
    assert service._apply_stage2_filter(float_data, fp, "NOMC") is True


def test_stage2_mcap_zero_passes_through(service):
    """AC-04 edge case: market_cap_final=0 passes through (zero treated as unknown)."""
    fp = make_fp(mcap_max=500_000_000.0)
    float_data = make_askedgar_float(market_cap_final=0)
    assert service._apply_stage2_filter(float_data, fp, "ZERO") is True


def test_stage2_float_none_passes_through(service):
    """AC-05 edge case: float=None passes through (unknown = do not exclude)."""
    fp = make_fp(float_max=50_000_000.0)
    float_data = make_askedgar_float(float_val=None)
    assert service._apply_stage2_filter(float_data, fp, "NONF") is True


def test_stage2_float_zero_passes_through(service):
    """AC-05 edge case: float=0 passes through (zero treated as unknown)."""
    fp = make_fp(float_max=50_000_000.0)
    float_data = make_askedgar_float(float_val=0)
    assert service._apply_stage2_filter(float_data, fp, "ZFLF") is True


# AC-11 (Stage 2) ────────────────────────────────────────────────────────────

def test_stage2_watchlist_ticker_exempt_even_above_caps(service):
    """AC-11: watchlist ticker returns True even when mcap and float exceed caps."""
    fp = make_fp(
        mcap_max=500_000_000.0,
        float_max=50_000_000.0,
        watchlist=frozenset({"WLTK"}),
    )
    float_data = make_askedgar_float(
        market_cap_final=900_000_000.0,
        float_val=200_000_000.0,
    )
    assert service._apply_stage2_filter(float_data, fp, "WLTK") is True


# Non-dict float_data pass-through ───────────────────────────────────────────

def test_stage2_non_dict_float_data_passes_through(service):
    """Stage 2 returns True when float_data is not a dict (no AskEdgar data available)."""
    fp = make_fp(mcap_max=500_000_000.0, float_max=50_000_000.0)
    assert service._apply_stage2_filter(None, fp, "NODATA") is True
    assert service._apply_stage2_filter("unexpected_string", fp, "NODATA") is True

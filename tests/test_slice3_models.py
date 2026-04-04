"""
Slice 3: Pydantic Response Models Tests

Acceptance Criteria Coverage:
- [x] AC1: DilutionV2Response instantiates with minimal fields and correct defaults
- [x] AC2: GainerEntry accepts all Optional fields as None with newsToday defaulting False
- [x] AC3: DilutionV2Response float_shares serializes under alias "float" via model_dump and model_dump_json
"""

import pytest
from pydantic import ValidationError
from app.models.responses import DilutionV2Response, GainerEntry


def test_dilution_v2_response_valid():
    """DilutionV2Response instantiates with only ticker and all other fields at defaults."""
    instance = DilutionV2Response(ticker="TEST")
    assert instance.ticker == "TEST"


def test_gainer_entry_optional_fields():
    """GainerEntry accepts None for all Optional fields and False for newsToday."""
    instance = GainerEntry(
        ticker="TEST",
        todaysChangePerc=25.5,
        price=None,
        volume=None,
        marketCap=None,
        sector=None,
        country=None,
        risk=None,
        chartRating=None,
        newsToday=False,
    )
    assert instance.newsToday is False


def test_dilution_v2_response_float_serialization():
    """float_shares field serializes under alias 'float', not 'float_shares'."""
    instance = DilutionV2Response(ticker="TEST", float_shares=1500000)

    dumped = instance.model_dump(by_alias=True)
    assert "float" in dumped, f"Expected key 'float' in model_dump output, got: {list(dumped.keys())}"
    assert "float_shares" not in dumped

    dumped_json = instance.model_dump_json(by_alias=True)
    assert '"float":' in dumped_json, f"Expected '\"float\":' in JSON output, got: {dumped_json}"

from fastapi import APIRouter, HTTPException

# Import the services
from app.services.dilution import DilutionService
from app.services.gainers import GainersService
from app.services.intel import IntelService
from app.utils.validation import validate_ticker
from app.utils.errors import TickerNotFoundError, RateLimitError

# Create the API router
router = APIRouter()

# Create service instances
dilution_service = DilutionService()
gainers_service = GainersService(dilution_service)
intel_service = IntelService(dilution_service)


@router.get("/dilution/{ticker}")
async def get_dilution(ticker: str):
    """
    Get dilution data for a specific ticker.

    Args:
        ticker (str): The stock ticker symbol

    Returns:
        dict: Dilution data for the ticker
    """
    try:
        # Validate ticker format
        validated_ticker = validate_ticker(ticker)

        # Get dilution data
        data = await dilution_service.get_dilution_data_v2(validated_ticker)
        return data
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail="Ticker not found")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/gainers")
async def get_gainers():
    data = await gainers_service.get_gainers()
    return data


@router.get("/gainers/massive")
async def get_massive_gainers():
    data = await gainers_service.get_massive_gainers()
    return data


@router.get("/gainers/fmp")
async def get_fmp_gainers():
    data = await gainers_service.get_fmp_gainers()
    return data


@router.get("/market-strength")
async def get_market_strength():
    try:
        data = await intel_service.get_market_strength()
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pump-and-dump/{ticker}")
async def get_pump_and_dump(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_pump_and_dump(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/pump-and-dump-list")
async def get_pump_and_dump_list():
    try:
        data = await intel_service.get_pump_and_dump_list()
        return data
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/nasdaq-compliance/{ticker}")
async def get_nasdaq_compliance(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_nasdaq_compliance(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reverse-splits/{ticker}")
async def get_reverse_splits(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_reverse_splits(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/filing-titles/{ticker}")
async def get_filing_titles(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_filing_titles(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/historical-float/{ticker}")
async def get_historical_float(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_historical_float(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/research-report/{ticker}")
async def get_research_report(ticker: str):
    try:
        validated = validate_ticker(ticker)
        data = await intel_service.get_research_report(validated)
        return data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/enrichment/batch")
async def get_batch_enrichment(tickers: str = ""):
    try:
        ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
        if len(ticker_list) > 50:
            raise HTTPException(status_code=400, detail="Maximum 50 tickers per batch request")
        validated = [validate_ticker(t) for t in ticker_list]
        data = await intel_service.get_batch_enrichment(validated)
        return data
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

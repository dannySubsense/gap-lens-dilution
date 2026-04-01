from fastapi import APIRouter, HTTPException

# Import the service
from app.services.dilution import DilutionService
from app.utils.validation import validate_ticker
from app.utils.errors import TickerNotFoundError, RateLimitError

# Create the API router
router = APIRouter()

# Create service instance
dilution_service = DilutionService()


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
        data = await dilution_service.get_dilution_data(validated_ticker)
        return data
    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail="Ticker not found")
    except RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

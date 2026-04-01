# Gap Lens Dilution Project

This project provides a dashboard for analyzing stock dilution risk based on SEC filings and market data.

## Features

- Real-time dilution risk analysis for publicly traded companies
- Integration with Ask-Edgar for dilution data
- Interactive dashboard with data visualization

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   Copy `.env.example` to `.env` and update the values as needed.

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Usage

The API is available at `http://localhost:8000` by default.

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /static/` - Static file serving
- `GET /api/dilution/{ticker}` - Dilution data endpoint (to be implemented)

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
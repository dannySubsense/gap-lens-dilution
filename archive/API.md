# API Documentation

## Base URL
`http://localhost:8000`

## Overview

The Gap Lens Dilution API provides endpoints for analyzing stock dilution, retrieving health status, and accessing detailed financial metrics. The API is built with FastAPI and follows REST principles.

## Authentication

API endpoints require a valid Polygon.io API key configured in the backend environment variables. No additional authentication is required for the API itself.

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests:

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid request parameters |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Request validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Unexpected server error |
| 503 | Service Unavailable - External API error |

## Endpoints

### GET /health

Check the health status of the API service.

**Response:**
```json
{
  "status": "ok"
}
```

### POST /api/analyze

Analyze stock dilution for a given ticker symbol.

**Request Body:**
```json
{
  "ticker": "string"
}
```

**Parameters:**
- `ticker` (string, required): Stock ticker symbol (1-10 uppercase letters)

**Response:**
```json
{
  "ticker": "string",
  "company_name": "string",
  "metrics": {
    "metric_name": {
      "value": "number or string",
      "label": "string",
      "interpretation": "string"
    }
  },
  "chart_data": {
    "points": [
      {
        "date": "string",
        "value": "number"
      }
    ],
    "title": "string",
    "y_label": "string"
  },
  "timestamp": "string"
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticker` | string | The stock ticker symbol |
| `company_name` | string | Full name of the company |
| `metrics` | object | Dictionary of exactly 12 metrics with values, labels, and interpretations |
| `chart_data` | object | Chart data for visualization |
| `chart_data.points` | array | List of data points with date and value |
| `chart_data.title` | string | Title for the chart |
| `chart_data.y_label` | string | Label for the Y-axis |
| `timestamp` | string | ISO format timestamp of when the analysis was performed |

**Metric Categories:**
The metrics object contains exactly 12 metrics covering:
1. Company profile information
2. Split history analysis
3. Dilution impact measurements
4. Financial health indicators

**Example Request:**
```json
{
  "ticker": "AAPL"
}
```

**Example Response:**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "metrics": {
    "market_cap": {
      "value": 2500000000000,
      "label": "Market Capitalization",
      "interpretation": "Total market value of the company"
    },
    "dilution_percentage": {
      "value": 15.3,
      "label": "Dilution Percentage",
      "interpretation": "Percentage decrease due to stock splits over 5 years"
    }
  },
  "chart_data": {
    "points": [
      {
        "date": "2023-01-01",
        "value": 150.00
      }
    ],
    "title": "AAPL Price Chart with Dilution Events",
    "y_label": "Price (USD)"
  },
  "timestamp": "2023-06-15T10:30:00Z"
}
```

## Rate Limiting

The API implements rate limiting based on the underlying Polygon.io API limits. If rate limits are exceeded, the API will return a 429 status code.

## Data Sources

The API pulls data from:
- Polygon.io for stock prices and company information
- Historical stock split data for dilution calculations

## Models

### AnalysisRequest

**Fields:**
- `ticker` (string, required): Stock ticker symbol (1-10 uppercase letters)

### AnalysisResponse

**Fields:**
- `ticker` (string): Stock ticker symbol
- `company_name` (string): Full name of the company
- `metrics` (object): Dictionary of metrics (exactly 12)
- `chart_data` (object): Chart data for visualization
- `timestamp` (string): ISO format timestamp

### MetricValue

**Fields:**
- `value` (number or string, optional): Value of the metric
- `label` (string): Display label for the metric
- `interpretation` (string): Explanation of what this metric means

### ChartData

**Fields:**
- `points` (array): List of data points for the chart
- `title` (string): Title for the chart
- `y_label` (string): Label for the Y-axis

### ChartDataPoint

**Fields:**
- `date` (string): Date in YYYY-MM-DD format
- `value` (number): Value for this date

## Implementation Details

The API follows a service-oriented architecture with the following components:

1. **main.py**: Application entry point with FastAPI setup and route definitions
2. **models/**: Pydantic models for request/response validation
3. **services/**: Business logic for metric calculation and chart preparation
4. **clients/**: External API clients (Polygon.io)
5. **config.py**: Configuration management using Pydantic Settings

The analysis flow:
1. Validate ticker symbol
2. Fetch company details from Polygon.io
3. Fetch stock split history (5-year)
4. Calculate dilution metrics
5. Prepare chart data
6. Assemble and return response
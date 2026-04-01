# Gap Lens Dilution

Gap Lens Dilution is a financial analysis tool designed to measure and visualize the dilution effects in market gaps, helping traders and analysts understand potential risk factors and price movement patterns.

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/gap-lens-dilution.git
   cd gap-lens-dilution
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables (see Environment Variables section below)

4. Run the application:
   ```bash
   npm start
   ```

5. Access the API at `http://localhost:3000`

## Environment Variables

Create a `.env` file in the root directory with the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `3000` |
| `NODE_ENV` | Environment mode | `development` |
| `API_KEY` | API key for data providers | `""` |
| `DATABASE_URL` | Database connection string | `sqlite://data.db` |
| `LOG_LEVEL` | Logging level (debug, info, warn, error) | `info` |
| `CACHE_TTL` | Cache time-to-live in seconds | `300` |

Example `.env` file:
```env
PORT=3000
NODE_ENV=development
API_KEY=your_api_key_here
DATABASE_URL=sqlite://data.db
LOG_LEVEL=info
CACHE_TTL=300
```

## API Documentation

### Base URL
`http://localhost:3000/api/v1`

### Endpoints

#### GET /gaps
Retrieve market gaps data

**Query Parameters:**
- `symbol` (string) - Trading symbol (e.g., AAPL)
- `startDate` (string) - Start date in YYYY-MM-DD format
- `endDate` (string) - End date in YYYY-MM-DD format
- `limit` (number) - Number of records to return (default: 50)

**Response:**
```json
{
  "data": [
    {
      "id": "string",
      "symbol": "string",
      "date": "string",
      "gapType": "up|down",
      "gapSize": "number",
      "dilution": "number",
      "volume": "number"
    }
  ]
}
```

#### GET /gaps/:id
Get specific gap details by ID

**Response:**
```json
{
  "id": "string",
  "symbol": "string",
  "date": "string",
  "open": "number",
  "close": "number",
  "gapSize": "number",
  "dilutionPercentage": "number",
  "volume": "number",
  "relatedGaps": "array"
}
```

#### POST /analyze
Run gap dilution analysis

**Request Body:**
```json
{
  "symbol": "string",
  "startDate": "string",
  "endDate": "string",
  "parameters": {
    "sensitivity": "number",
    "timeframe": "string"
  }
}
```

**Response:**
```json
{
  "analysisId": "string",
  "symbol": "string",
  "totalGaps": "number",
  "averageDilution": "number",
  "maxDilution": "number",
  "minDilution": "number",
  "report": "object"
}
```

#### GET /health
Check service health status

**Response:**
```json
{
  "status": "ok|error",
  "timestamp": "string",
  "version": "string"
}
```

## Testing Instructions

### Unit Tests
Run unit tests with coverage:
```bash
npm test
```

### Integration Tests
Run integration tests:
```bash
npm run test:integration
```

### End-to-End Tests
Run end-to-end tests:
```bash
npm run test:e2e
```

### Test Data
Test data is located in `test/data/` directory:
- `sample-gaps.json` - Sample market gap data
- `historical-data.json` - Historical price data for testing

### Writing New Tests
1. Create test files in the appropriate directory under `test/`
2. Use the Jest testing framework
3. Follow the existing test patterns
4. Ensure tests are isolated and mock external dependencies

### CI/CD
Tests are automatically run in the CI pipeline on every pull request. View results in the GitHub Actions tab.

## Development

### Project Structure
```
gap-lens-dilution/
├── src/
│   ├── controllers/     # API route handlers
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── routes/          # API route definitions
├── test/
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
├── docs/                # Documentation
├── config/              # Configuration files
└── scripts/             # Utility scripts
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add or update tests as necessary
5. Ensure all tests pass
6. Submit a pull request

## License
MIT
# Developer Setup Guide

This guide provides instructions for setting up the Gap Lens Dilution development environment.

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm 6 or higher
- Git

## Project Structure

```
gap-lens-dilution/
├── backend/              # Python FastAPI backend
│   ├── clients/          # External API clients (Polygon)
│   ├── models/           # Data models and schemas
│   ├── services/        # Business logic
│   ├── tests/            # Test suite
│   ├── main.py           # Application entry point
│   ├── config.py         # Configuration management
│   ├── requirements.txt  # Python dependencies
│   └── run_tests.sh      # Test runner script
├── frontend/             # Static frontend files
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── index.html        # Main HTML file
├── docs/                 # Documentation (you are here)
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment variables
├── README.md             # Project overview
└── package.json         # Node.js dependencies and scripts
```

## Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Then edit the `.env` file to add your actual API keys and configuration values.

## Frontend Setup

1. Install frontend dependencies:
   ```bash
   npm install
   ```

## Running the Application

### Backend

To start the backend server in development mode:
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

To serve the frontend files, you can use any static file server. For development, you can use:
```bash
npx serve frontend
```

Or use a Python simple server:
```bash
cd frontend
python -m http.server 3000
```

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `POLYGON_API_KEY` | API key for Polygon.io | `""` |
| `FRONTEND_URL` | Allowed frontend origin for CORS | `"http://localhost:3000"` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `"INFO"` |

Example `.env` file:
```env
POLYGON_API_KEY=your_polygon_api_key_here
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=INFO
```

## Configuration

The application uses Pydantic Settings for configuration management. The configuration is defined in `backend/config.py` and can be overridden by environment variables.

## Development Workflow

1. Make sure your virtual environment is activated
2. Run tests to ensure everything is working
3. Make your changes
4. Run tests again to ensure nothing is broken
5. Commit your changes

## Running Tests

To run the test suite:
```bash
cd backend
source venv/bin/activate
./run_tests.sh
```

Or run tests directly with pytest:
```bash
python -m pytest tests/ -v
```

## IDE Setup

Recommended IDEs:
- Visual Studio Code with Python extension
- PyCharm

Recommended extensions:
- Python (for syntax highlighting and linting)
- Pylint or Flake8 (for code quality)
- Black (for code formatting)

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Make sure your virtual environment is activated and dependencies are installed.

2. **Connection refused**: Ensure the backend server is running before accessing the API.

3. **CORS errors**: Check that `FRONTEND_URL` in your `.env` matches where your frontend is being served.

4. **API key errors**: Verify your Polygon API key is valid and has the necessary permissions.

### Getting Help

If you encounter issues not covered in this guide:
1. Check the project README.md for additional information
2. Review the existing code and tests for examples
3. Contact the project maintainers
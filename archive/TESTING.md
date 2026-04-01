# Testing Guide

This guide explains how to run and write tests for the Gap Lens Dilution backend.

## Test Structure

The tests are organized in the `backend/tests/` directory following a logical structure:

```
backend/tests/
├── unit/                 # Unit tests for individual components
├── integration/          # Integration tests for combined components
├── e2e/                  # End-to-end tests for complete workflows
├── conftest.py          # Pytest configuration and fixtures
├── test-requirements.txt # Test-specific dependencies
└── README.md            # Test suite documentation
```

## Running Tests

### Prerequisites

1. Activate the virtual environment:
   ```bash
   cd backend
   source venv/bin/activate
   ```

2. Install test dependencies:
   ```bash
   pip install -r test-requirements.txt
   ```

### Test Runner Script

The project includes a convenient test runner script:

```bash
./run_tests.sh
```

This script will:
1. Activate the virtual environment
2. Run all tests with verbose output
3. Generate coverage report

### Manual Test Execution

Run all tests with pytest:
```bash
python -m pytest tests/ -v
```

Run specific test files:
```bash
python -m pytest tests/test_slice1.py -v
```

Run tests with coverage:
```bash
python -m pytest tests/ --cov=.
```

Run tests in parallel:
```bash
python -m pytest tests/ -n auto
```

## Test Categories

### Unit Tests

Unit tests verify individual functions and classes in isolation. They are located in `tests/unit/` and focus on:

- Model validation
- Service function logic
- Client method behavior
- Utility function correctness

Run unit tests:
```bash
python -m pytest tests/unit/ -v
```

### Integration Tests

Integration tests verify that multiple components work together correctly. They are located in `tests/integration/` and focus on:

- API endpoint behavior
- Service interaction with clients
- Database operations (if applicable)
- External API integration

Run integration tests:
```bash
python -m pytest tests/integration/ -v
```

### End-to-End Tests

End-to-end tests verify complete user workflows from start to finish. They are located in `tests/e2e/` and focus on:

- Complete analysis workflows
- Full API request/response cycles
- User-facing functionality

Run end-to-end tests:
```bash
python -m pytest tests/e2e/ -v
```

## Test Environment

### Environment Variables

Tests require specific environment variables to be set. Create a `.env.test` file in the backend directory:

```env
POLYGON_API_KEY=test_key_here
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=DEBUG
```

### Test Data

Test data is stored in `tests/data/` and includes:

- Sample API responses
- Mock data for external services
- Historical stock data for testing calculations

## Writing Tests

### Test File Structure

New test files should follow this structure:

```python
import pytest
from unittest.mock import patch, MagicMock

# Import the modules being tested
from services.metric_service import compute_metric

def test_compute_metric_valid_input():
    """Test that compute_metric works with valid input."""
    # Arrange
    input_data = {"value": 100}
    
    # Act
    result = compute_metric(input_data)
    
    # Assert
    assert result == 90  # Expected result
```

### Using Fixtures

Pytest fixtures are defined in `conftest.py` and provide reusable test setup:

```python
@pytest.fixture
def sample_ticker_data():
    """Provide sample ticker data for tests."""
    return {
        "ticker": "AAPL",
        "name": "Apple Inc."
    }
```

Use fixtures in tests by including them as parameters:

```python
def test_analyze_with_sample_data(sample_ticker_data):
    """Test analysis with sample data fixture."""
    # Test implementation
```

### Mocking External Services

Use the `unittest.mock` module to mock external services:

```python
@patch('clients.polygon_client.PolygonClient.get_ticker_details')
def test_analysis_with_mocked_client(mock_get_details):
    """Test analysis with mocked Polygon client."""
    # Setup mock
    mock_get_details.return_value = {"name": "Apple Inc."}
    
    # Test implementation
```

### Test Assertions

Use pytest's built-in assertions for clear test failures:

```python
def test_value_calculation():
    """Test that calculation produces expected value."""
    result = calculate_value(10, 5)
    assert result == 50
    assert isinstance(result, int)
```

## Continuous Integration

Tests are automatically run in the CI pipeline on every pull request using GitHub Actions. The workflow includes:

1. Setting up the test environment
2. Installing dependencies
3. Running all test suites
4. Publishing test results
5. Checking code coverage

View CI results in the GitHub Actions tab of the repository.

## Test Coverage

The project aims for comprehensive test coverage:

- Unit tests: 90%+ coverage
- Integration tests: 80%+ coverage
- End-to-end tests: 70%+ coverage

Run coverage analysis:
```bash
python -m pytest tests/ --cov=. --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Debugging Tests

### Verbose Output

Run tests with increased verbosity:
```bash
python -m pytest tests/ -v -s
```

### Debugging with PDB

Add breakpoints to debug test execution:
```python
def test_problematic_function():
    import pdb; pdb.set_trace()  # Breakpoint
    result = function_to_test()
    assert result == expected
```

Run with Python debugger:
```bash
python -m pytest tests/test_file.py::test_problematic_function -s
```

## Best Practices

### Test Naming

Use descriptive test names that explain what is being tested:
```python
def test_calculate_dilution_with_no_splits_returns_zero():
    # Good: Describes the specific condition and expected result
    pass

def test_calc():
    # Bad: Not descriptive
    pass
```

### Test Isolation

Ensure tests are independent and can run in any order:
```python
def test_first_scenario():
    # Setup only what this test needs
    pass

def test_second_scenario():
    # Setup only what this test needs, don't rely on test_first_scenario
    pass
```

### Test Data Management

Use factories or fixtures for complex test data:
```python
@pytest.fixture
def complex_test_data():
    return generate_test_data(size=1000)  # Generate as needed
```

### Performance Considerations

- Mock external services to avoid network calls
- Use in-memory databases for database tests
- Limit test data size to essential minimum
- Use pytest-xdist for parallel test execution

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure PYTHONPATH includes the backend directory
2. **Missing dependencies**: Install both requirements.txt and test-requirements.txt
3. **Environment variables**: Check that required variables are set
4. **Mock issues**: Verify mock paths match actual module paths

### Getting Help

If tests are failing and you're unable to resolve the issue:
1. Check the test logs for specific error messages
2. Run individual test files to isolate the problem
3. Review recent code changes that might have affected tests
4. Contact team members for assistance
# Running Tests in VS Code

## Setup

Tests are configured to run with pytest. Make sure dependencies are installed:

```bash
pip install -r requirements.txt
```

## Running Tests in VS Code

### Method 1: Using the Test Explorer
1. Open the Test Explorer sidebar (flask icon in the left sidebar)
2. VS Code will automatically discover all tests in the `tests/` directory
3. Click the play button next to any test to run it
4. Right-click on a test for more options (Run, Debug, etc.)

### Method 2: Right-Click in Editor
1. Open any test file (e.g., `test_count.py`)
2. Right-click in the editor
3. Select "Run Current Test File" or "Debug Current Test File"

### Method 3: Command Line
```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_count.py

# Run with verbose output
pytest -v

# Run and see print statements
pytest -s
```

## Test File Naming Convention

- Test files must start with `test_` or end with `_test.py`
- Test functions must start with `test_`
- Async test functions are automatically supported with `pytest-asyncio`

## Configuration Files

- `.vscode/settings.json` - VS Code Python test configuration
- `pytest.ini` - Pytest configuration and options
- `requirements.txt` - Includes pytest and pytest-asyncio

#!/bin/bash

# Activate the Python 3.9 virtual environment
source venv_py39/bin/activate

# Print Python path and version for debugging
echo "Using Python: $(which python)"
echo "Python version: $(python --version)"
echo "Checking for yfinance:"
python -c "import sys; print(sys.path); import yfinance; print('yfinance version:', yfinance.__version__)" || echo "Failed to import yfinance"

# Create cache directory if it doesn't exist
mkdir -p cache/stocks

# Run the API server
python simple_api.py

# Deactivate the virtual environment when done
deactivate 
#!/bin/bash

# Kill any existing Python processes
pkill -f "python simple_api.py" || true

# Run the simple API server
python simple_api.py 
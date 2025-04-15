#!/bin/bash

echo "AWS Cost Explorer MCP Server Launcher"
echo "==============================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    echo "Please install Python 3.7 or later from your package manager or https://www.python.org/downloads/"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
if ! python3 -c "import fastmcp" &> /dev/null; then
    echo "Installing required packages..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error installing dependencies. Please check requirements.txt and try again."
        exit 1
    fi
fi

echo "Starting MCP server..."
python3 mcp_server.py --transport sse --port 8000 
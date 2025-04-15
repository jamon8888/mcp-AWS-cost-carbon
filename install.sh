#!/bin/bash

echo "AWS Cost Explorer - Installation Script for Linux/macOS"
echo "====================================================="
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

echo "Detected Python version: $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "ERROR: Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Run the installation script
echo "Running installation script..."
python3 easy_install.py "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation failed. Please check the error messages above."
    exit 1
else
    echo ""
    echo "Installation completed successfully!"
    echo ""
    echo "To run the MCP server:"
    echo "  python3 mcp_server.py --port 8000"
    echo ""
    echo "To run the comprehensive test:"
    echo "  python3 comprehensive_test.py"
    echo ""
fi 
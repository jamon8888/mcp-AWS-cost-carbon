@echo off
echo AWS Cost Explorer MCP Server Launcher
echo ===============================

rem Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo Error: Python is not installed or not in PATH.
  echo Please install Python 3.7 or later from https://www.python.org/downloads/
  pause
  exit /b 1
)

rem Check if required packages are installed
echo Checking dependencies...
pip show fastmcp >nul 2>&1
if %errorlevel% neq 0 (
  echo Installing required packages...
  pip install -r requirements.txt
  if %errorlevel% neq 0 (
    echo Error installing dependencies. Please check requirements.txt and try again.
    pause
    exit /b 1
  )
)

echo Starting MCP server...
python mcp_server.py --transport sse --port 8000

pause 
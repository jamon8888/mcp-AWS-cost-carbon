@echo off
echo AWS Cost Explorer - Installation Script for Windows
echo ===================================================
echo.

:: Check Python installation
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Detected Python version: %PYVER%

:: Run the installation script
echo Running installation script...
python easy_install.py %*

if errorlevel 1 (
    echo.
    echo Installation failed. Please check the error messages above.
    exit /b 1
) else (
    echo.
    echo Installation completed successfully!
    echo.
    echo To run the MCP server:
    echo   python mcp_server.py --port 8000
    echo.
    echo To run the comprehensive test:
    echo   python comprehensive_test.py
    echo.
)

pause 
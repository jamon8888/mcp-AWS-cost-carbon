#!/usr/bin/env python3
"""
AWS Cost Explorer MCP Server - Easy Installation Script
This script automates the installation process for the AWS Cost Explorer MCP Server.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def run_command(command, show_output=True):
    """Run a shell command and return success status and output"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=False,
            stdout=subprocess.PIPE if not show_output else None,
            stderr=subprocess.PIPE if not show_output else None,
            text=True
        )
        return result.returncode == 0, result.stdout if not show_output else None
    except Exception as e:
        print(f"Error running command '{command}': {str(e)}")
        return False, None

def check_python():
    """Check Python version"""
    required_version = (3, 8)
    current_version = sys.version_info
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required")
        print(f"Current version: {current_version[0]}.{current_version[1]}")
        return False
    
    print(f"Python version {current_version[0]}.{current_version[1]} detected (✓)")
    return True

def check_pip():
    """Check if pip is installed"""
    success, _ = run_command("pip --version", show_output=False)
    if not success:
        # Try pip3 on Unix systems
        success, _ = run_command("pip3 --version", show_output=False)
        if not success:
            print("Error: pip is not installed or not in PATH")
            return False
    
    print("pip is installed (✓)")
    return True

def check_git():
    """Check if git is installed"""
    success, _ = run_command("git --version", show_output=False)
    if not success:
        print("Error: git is not installed or not in PATH")
        return False
    print("git is installed (✓)")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\nInstalling dependencies...")
    
    # Determine pip command (pip or pip3)
    pip_cmd = "pip"
    if platform.system() != "Windows":
        success, _ = run_command("pip --version", show_output=False)
        if not success:
            pip_cmd = "pip3"
    
    # Install from requirements file if it exists
    if os.path.exists("requirements.txt"):
        print(f"Installing from requirements.txt...")
        success, _ = run_command(f"{pip_cmd} install -r requirements.txt")
        if not success:
            print("Failed to install dependencies from requirements.txt")
            return False
    else:
        # Install core dependencies individually
        core_packages = [
            "fastmcp>=0.8.0",
            "pandas>=1.3.0",
            "boto3>=1.26.0",
            "plotly>=5.3.0",
            "numpy>=1.20.0",
            "flask>=2.0.0",
            "requests>=2.25.0"
        ]
        
        for package in core_packages:
            print(f"Installing {package}...")
            success, _ = run_command(f"{pip_cmd} install {package}")
            if not success:
                print(f"Failed to install {package}")
                return False
    
    print("All dependencies installed successfully (✓)")
    return True

def create_data_directories():
    """Create necessary data directories"""
    print("\nCreating data directories...")
    
    directories = ["data", "mock", "visualizations", "output"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    print("\nCreating startup scripts...")
    
    # Windows batch file
    if platform.system() == "Windows":
        with open("start_mcp_server.bat", "w") as f:
            f.write('@echo off\n')
            f.write('echo AWS Cost Explorer MCP Server Launcher\n')
            f.write('echo ===============================\n\n')
            f.write('python mcp_server.py --transport sse --port 8000\n')
            f.write('pause\n')
        print("Created Windows startup script: start_mcp_server.bat")
    
    # Unix shell script
    else:
        with open("start_mcp_server.sh", "w") as f:
            f.write('#!/bin/bash\n\n')
            f.write('echo "AWS Cost Explorer MCP Server Launcher"\n')
            f.write('echo "==============================="\n\n')
            f.write('python3 mcp_server.py --transport sse --port 8000\n')
        
        # Make the shell script executable
        os.chmod("start_mcp_server.sh", 0o755)
        print("Created Unix startup script: start_mcp_server.sh")
    
    return True

def main():
    """Main installation function"""
    print("AWS Cost Explorer MCP Server - Installation Script")
    print("================================================\n")
    
    # Check prerequisites
    if not check_python():
        return 1
    
    if not check_pip():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create data directories
    if not create_data_directories():
        return 1
    
    # Create startup scripts
    if not create_startup_scripts():
        return 1
    
    print("\n================================================")
    print("Installation completed successfully!")
    print("================================================\n")
    
    print("To start the MCP server:")
    if platform.system() == "Windows":
        print("  - Double-click start_mcp_server.bat")
        print("  - Or run: python mcp_server.py --transport sse --port 8000")
    else:
        print("  - Run: ./start_mcp_server.sh")
        print("  - Or run: python3 mcp_server.py --transport sse --port 8000")
    
    print("\nFor more information, see the README.md file.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

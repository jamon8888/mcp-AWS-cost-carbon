import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
import tempfile
import argparse

def run_command(command, show_output=True):
    """Run a shell command and return the output"""
    try:
        if show_output:
            print(f"Running: {command}")
        
        process = subprocess.Popen(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0 and show_output:
            print(f"Command failed with exit code {process.returncode}")
            print(f"Error: {stderr.strip()}")
            return False, stderr
        
        return True, stdout
    except Exception as e:
        if show_output:
            print(f"Error executing command: {e}")
        return False, str(e)

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 8):
        print(f"Error: Python 3.8 or higher is required. You have Python {major}.{minor}")
        return False
    print(f"Python version check passed: {major}.{minor}")
    return True

def check_pip():
    """Check if pip is installed"""
    success, _ = run_command("pip --version", show_output=False)
    if not success:
        print("Error: pip is not installed or not in PATH")
        return False
    print("pip is installed")
    return True

def check_git():
    """Check if git is installed"""
    success, _ = run_command("git --version", show_output=False)
    if not success:
        print("Error: git is not installed or not in PATH")
        return False
    print("git is installed")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\nInstalling dependencies...")
    packages = [
        "fastmcp>=0.8.0",
        "pandas>=1.3.0",
        "boto3>=1.20.0",
        "plotly>=5.3.0",
        "numpy>=1.20.0",
        "flask>=2.0.0",
        "requests>=2.25.0"
    ]
    
    for package in packages:
        print(f"Installing {package}...")
        success, output = run_command(f"pip install {package}")
        if not success:
            print(f"Failed to install {package}")
            return False
    
    print("All dependencies installed successfully")
    return True

def install_from_setup():
    """Install the package using setup.py"""
    print("\nInstalling AWS Cost Explorer from setup.py...")
    success, output = run_command("pip install -e .")
    if not success:
        print("Failed to install package from setup.py")
        return False
    print("Package installed successfully in development mode")
    return True

def setup_aws_credentials():
    """Help the user set up AWS credentials"""
    print("\n=== AWS Credentials Setup ===")
    
    # Check if AWS credentials already exist
    credentials_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(credentials_path):
        print(f"AWS credentials file found at {credentials_path}")
        setup_new = input("Do you want to set up new credentials? (y/n): ").lower()
        if setup_new != 'y':
            return True
    
    # Get AWS credentials from user
    print("\nPlease enter your AWS credentials:")
    aws_access_key = input("AWS Access Key ID: ")
    aws_secret_key = input("AWS Secret Access Key: ")
    region = input("Default region (e.g., us-east-1): ") or "us-east-1"
    
    # Create credentials file
    credentials_dir = os.path.dirname(credentials_path)
    os.makedirs(credentials_dir, exist_ok=True)
    
    with open(credentials_path, 'w') as f:
        f.write("[default]\n")
        f.write(f"aws_access_key_id = {aws_access_key}\n")
        f.write(f"aws_secret_access_key = {aws_secret_key}\n")
    
    # Create config file
    config_path = os.path.expanduser("~/.aws/config")
    with open(config_path, 'w') as f:
        f.write("[default]\n")
        f.write(f"region = {region}\n")
    
    print(f"AWS credentials saved to {credentials_path}")
    print(f"AWS config saved to {config_path}")
    return True

def create_test_script():
    """Create a simple test script to verify installation"""
    test_script = """
import os
import sys
from pprint import pprint

# Try to import the AWS Cost Explorer package
try:
    from aws_cost_carbon_calculator import AWSEnvironmentalCalculator
    print("Successfully imported AWSEnvironmentalCalculator")
except ImportError as e:
    print(f"Error importing AWSEnvironmentalCalculator: {e}")
    sys.exit(1)

def test_calculator():
    # Initialize the calculator
    calculator = AWSEnvironmentalCalculator()
    
    # Print basic information
    print(f"\\nLoaded {len(calculator.regions)} regions with carbon intensity data")
    
    # Get the top 5 regions with lowest carbon intensity
    regions_data = calculator.get_regions_carbon_intensity()
    sorted_regions = sorted(regions_data.items(), key=lambda x: x[1])
    
    print("\\nTop 5 lowest carbon regions:")
    for region, intensity in sorted_regions[:5]:
        print(f"{region}: {intensity:.1f} gCO2e/kWh")
    
    return True

if __name__ == "__main__":
    print("\\n=== AWS Cost Explorer Test ===")
    test_calculator()
    print("\\nTest completed successfully")
"""
    
    with open("test_installation.py", "w") as f:
        f.write(test_script)
    
    print("\nCreated test script: test_installation.py")
    return True

def test_installation():
    """Run the test script to verify installation"""
    print("\nTesting installation...")
    success, output = run_command("python test_installation.py")
    print(output)
    if not success:
        print("Installation test failed")
        return False
    print("Installation test passed")
    return True

def main():
    parser = argparse.ArgumentParser(description="Easy installer for AWS Cost Explorer")
    parser.add_argument("--skip-deps", action="store_true", help="Skip installing dependencies")
    parser.add_argument("--skip-aws", action="store_true", help="Skip AWS credentials setup")
    parser.add_argument("--skip-test", action="store_true", help="Skip installation test")
    args = parser.parse_args()
    
    print("=== AWS Cost Explorer Easy Install ===")
    print(f"Current directory: {os.getcwd()}")
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # Install dependencies
    if not args.skip_deps and not install_dependencies():
        sys.exit(1)
    
    # Install from setup.py
    if not install_from_setup():
        sys.exit(1)
    
    # Setup AWS credentials
    if not args.skip_aws and not setup_aws_credentials():
        sys.exit(1)
    
    # Create and run test
    if not create_test_script():
        sys.exit(1)
    
    if not args.skip_test and not test_installation():
        sys.exit(1)
    
    print("\n=== Installation Complete ===")
    print("You can now use the AWS Cost Explorer package.")
    print("To run the MCP server: python mcp_server.py --port 8000")
    print("To run tests: python comprehensive_test.py")

if __name__ == "__main__":
    main() 
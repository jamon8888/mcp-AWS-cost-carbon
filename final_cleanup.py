#!/usr/bin/env python3
"""
Final Repository Cleanup Script

This script cleans up any remaining duplicate files in subdirectories
and ensures the repository has a clean module structure.
"""

import os
import shutil
import glob
import stat
import platform

def remove_readonly(func, path, _):
    """Clear the readonly bit and reattempt the removal."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def remove_file(file_path):
    """Remove a file if it exists."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Removed file: {file_path}")
        except Exception as e:
            print(f"Failed to remove {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")

def remove_directory(dir_path):
    """Remove a directory and all its contents if it exists."""
    if os.path.exists(dir_path):
        try:
            # Use custom error handler for Windows readonly files
            if platform.system() == 'Windows':
                shutil.rmtree(dir_path, onerror=remove_readonly)
            else:
                shutil.rmtree(dir_path)
            print(f"Removed directory: {dir_path}")
        except Exception as e:
            print(f"Failed to remove {dir_path}: {e}")
    else:
        print(f"Directory not found: {dir_path}")

def ensure_directory(dir_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"Created directory: {dir_path}")

def main():
    print("Starting final repository cleanup...")
    
    # Clean up clients directory
    print("\nCleaning up clients directory...")
    client_files_to_remove = [
        "clients/fastmcp_client_example.py",
        "clients/simple_client.py",
        "clients/example_usage.py"
    ]
    for file_path in client_files_to_remove:
        remove_file(file_path)
    
    # If clients directory is empty except for __init__.py, we can keep it
    if len(os.listdir("clients")) <= 1:
        print("Clients directory is now empty (except for __init__.py)")
    
    # Clean up tests directory
    print("\nCleaning up tests directory...")
    test_files_to_remove = [
        "tests/test_with_mock.py",
        "tests/test_ec2_carbon_multi.py",
        "tests/test_ec2_carbon.py",
        "tests/debug_api.py",
        "tests/debug_calculator.py"
    ]
    for file_path in test_files_to_remove:
        remove_file(file_path)
    
    # Don't remove comprehensive_test.py in tests directory, it's the main test file
    
    # Clean up mock directory
    print("\nCleaning up mock directory...")
    mock_files_to_remove = [
        "mock/mock_mcp_client.py"
    ]
    for file_path in mock_files_to_remove:
        remove_file(file_path)
    
    # We keep mock_aws.py and global_aws_mocker.py as they're needed for testing
    
    # Clean up API directory
    print("\nCleaning up API directory...")
    api_files_to_remove = [
        "api/simple_wrapper.py"
    ]
    for file_path in api_files_to_remove:
        remove_file(file_path)
    
    # Move files from root to appropriate module folders
    print("\nMoving files from root to appropriate modules...")
    
    # Files that should be in core/
    core_files = [
        "aws_cost_carbon_calculator.py",
        "aws_bedrock_carbon_calculator.py",
        "aws_environmental_calculator.py",
        "embodied_carbon_calculator.py",
        "water_metrics_integration.py"
    ]
    
    # Ensure core directory exists
    ensure_directory("core")
    
    for file_name in core_files:
        if os.path.exists(file_name):
            if os.path.exists(f"core/{file_name}"):
                print(f"Removing duplicate {file_name} from root, already in core/")
                remove_file(file_name)
            else:
                print(f"Moving {file_name} to core/")
                try:
                    shutil.move(file_name, f"core/{file_name}")
                    print(f"Moved {file_name} to core/")
                except Exception as e:
                    print(f"Failed to move {file_name} to core/: {e}")
    
    # Files that should be in api/
    api_files = [
        "mcp_server.py",
        "http_api_wrapper.py"
    ]
    
    # Ensure api directory exists
    ensure_directory("api")
    
    for file_name in api_files:
        if os.path.exists(file_name):
            if os.path.exists(f"api/{file_name}"):
                print(f"Removing duplicate {file_name} from root, already in api/")
                remove_file(file_name)
            else:
                print(f"Moving {file_name} to api/")
                try:
                    shutil.move(file_name, f"api/{file_name}")
                    print(f"Moved {file_name} to api/")
                except Exception as e:
                    print(f"Failed to move {file_name} to api/: {e}")
    
    # Files that should be in mock/
    mock_files = [
        "mock_aws.py",
        "global_aws_mocker.py"
    ]
    
    # Ensure mock directory exists
    ensure_directory("mock")
    
    for file_name in mock_files:
        if os.path.exists(file_name):
            if os.path.exists(f"mock/{file_name}"):
                print(f"Removing duplicate {file_name} from root, already in mock/")
                remove_file(file_name)
            else:
                print(f"Moving {file_name} to mock/")
                try:
                    shutil.move(file_name, f"mock/{file_name}")
                    print(f"Moved {file_name} to mock/")
                except Exception as e:
                    print(f"Failed to move {file_name} to mock/: {e}")
    
    # Files that should be in tests/
    tests_files = [
        "comprehensive_test.py"
    ]
    
    # Ensure tests directory exists
    ensure_directory("tests")
    
    for file_name in tests_files:
        if os.path.exists(file_name):
            if os.path.exists(f"tests/{file_name}"):
                print(f"Removing duplicate {file_name} from root, already in tests/")
                remove_file(file_name)
            else:
                print(f"Moving {file_name} to tests/")
                try:
                    shutil.move(file_name, f"tests/{file_name}")
                    print(f"Moved {file_name} to tests/")
                except Exception as e:
                    print(f"Failed to move {file_name} to tests/: {e}")
    
    # Remove empty directories (except for __init__.py)
    print("\nChecking for empty directories...")
    for directory in ["clients", "utils"]:
        if os.path.exists(directory) and len(os.listdir(directory)) <= 1:
            print(f"Directory {directory} is empty except for __init__.py, keeping it")
    
    print("\nFinal repository cleanup completed!")

if __name__ == "__main__":
    main() 
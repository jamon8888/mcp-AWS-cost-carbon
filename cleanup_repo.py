#!/usr/bin/env python3
"""
Repository Cleanup Script

This script removes unnecessary and duplicate files from the repository
to maintain a clean and organized structure.
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

def create_gitignore():
    """Create a .gitignore file with common patterns to ignore."""
    content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Jupyter Notebooks
.ipynb_checkpoints
.notebook/

# Editor files
.vscode/
.idea/
*.swp
*.swo

# OS specific
.DS_Store
Thumbs.db

# Environment
.env
.venv
env/
venv/
ENV/

# Logs
*.log

# Temporary files
tmp/
temp/

# Generated files
*.generated.*
aws_environmental_analysis_results.json
region_comparison_results.json
"""
    with open(".gitignore", "w") as f:
        f.write(content)
    print("Created .gitignore file")

def update_start_script():
    """Update the start.py script to fix transport and port issues."""
    if not os.path.exists("start.py"):
        print("start.py not found, skipping update")
        return
    
    with open("start.py", "r") as f:
        content = f.read()
    
    # Update the transport options to only include supported ones
    content = content.replace(
        "parser.add_argument(\"--transport\", choices=[\"sse\", \"stdio\"], default=\"sse\",",
        "parser.add_argument(\"--transport\", choices=[\"sse\", \"stdio\"], default=\"stdio\","
    )
    
    # Update the MCP server command to handle the port parameter correctly
    content = content.replace(
        "command = f\"{sys.executable} mcp_server.py --transport {transport} --port {port}\"",
        "command = f\"{sys.executable} mcp_server.py --transport {transport}\""
    )
    
    with open("start.py", "w") as f:
        f.write(content)
    print("Updated start.py script with correct transport and port parameters")

def main():
    print("Starting repository cleanup...")
    
    # Remove Python cache directories
    print("\nRemoving Python cache directories...")
    for cache_dir in glob.glob("**/__pycache__", recursive=True):
        remove_directory(cache_dir)
    
    # Remove backup and temporary directories
    print("\nRemoving backup and temporary directories...")
    dirs_to_remove = [
        "backup_20250414_134527",
        ".notebook",
        "clean_setup",
        "scripts",  # Old scripts directory is no longer needed
    ]
    for dir_path in dirs_to_remove:
        remove_directory(dir_path)
    
    # Remove redundant installation files
    print("\nRemoving redundant installation files...")
    files_to_remove = [
        "INSTALL_CURSOR.md",          # Consolidate with INSTALL.md
        "README_CURSOR.md",           # Consolidate with README.md
        "cursor_install.py",          # Consolidate with easy_install.py
        "check_fastmcp.py",           # Redundant with easy_install.py
    ]
    for file_path in files_to_remove:
        remove_file(file_path)
    
    # Remove duplicate startup scripts
    print("\nRemoving duplicate startup scripts...")
    startup_files_to_remove = [
        "start_http_api.ps1",         # Consolidate into single script
        "start_server.bat",           # Replaced by install.bat
        "start_server.ps1",           # Consolidate into single script
        "start_server.sh",            # Replaced by install.sh
        "aws_cost_explorer.py",       # Replaced by start.py
    ]
    for file_path in startup_files_to_remove:
        remove_file(file_path)
    
    # Remove redundant test files
    print("\nRemoving redundant test files...")
    test_files_to_remove = [
        "test_ec2_carbon.py",         # Covered by comprehensive_test.py
        "test_ec2_carbon_multi.py",   # Covered by comprehensive_test.py
        "test_with_mock.py",          # Covered by comprehensive_test.py
        "debug_api.py",
        "debug_calculator.py"
    ]
    for file_path in test_files_to_remove:
        remove_file(file_path)
    
    # Remove duplicate client scripts
    print("\nRemoving duplicate client scripts...")
    client_files_to_remove = [
        "example_usage.py",           # Covered by comprehensive_test.py or fastmcp_client_example.py
        "fastmcp_client_example.py",  # Examples are now in the README
        "simple_client.py",           # Simple client is redundant
        "mock_mcp_client.py",         # Only needed for development/testing
    ]
    for file_path in client_files_to_remove:
        remove_file(file_path)
    
    # Remove redundant wrapper files
    print("\nRemoving redundant wrapper files...")
    wrapper_files_to_remove = [
        "simple_wrapper.py",          # Functionality integrated into main server
    ]
    for file_path in wrapper_files_to_remove:
        remove_file(file_path)
    
    # Clean up any JSON result files
    print("\nCleaning up result files...")
    result_files_to_remove = [
        "region_comparison_results.json",
        "aws_environmental_analysis_results.json"
    ]
    for file_path in result_files_to_remove:
        remove_file(file_path)
    
    # Create .gitignore file
    print("\nCreating .gitignore file...")
    create_gitignore()
    
    # Update start script
    print("\nUpdating start script...")
    update_start_script()
    
    print("\nRepository cleanup completed!")

if __name__ == "__main__":
    main() 
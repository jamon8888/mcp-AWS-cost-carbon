#!/usr/bin/env python3
"""
AWS Cost Explorer MCP Server - Comprehensive Test Script
This script tests the functionality of the AWS Cost Explorer MCP Server.
"""

import os
import sys
import time
import json
import argparse
import subprocess
import requests
from typing import Dict, Any, Optional, List, Tuple

# Default server URL
SERVER_URL = "http://localhost:8000/jsonrpc"

def ping_server(max_retries=5, delay=2):
    """Ping the server to check if it's running."""
    print(f"Pinging server at {SERVER_URL}...")
    
    for i in range(max_retries):
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "ping",
                "id": 1
            }
            response = requests.post(SERVER_URL, json=payload)
            if response.status_code == 200:
                print(f"Server is running (attempt {i+1}/{max_retries})")
                return True
        except requests.exceptions.ConnectionError:
            print(f"Server not responding (attempt {i+1}/{max_retries}), retrying in {delay} seconds...")
            time.sleep(delay)
    
    print("Failed to connect to the server after retries")
    return False

def call_mcp_method(method_name, params):
    """Call a method on the MCP server."""
    payload = {
        "jsonrpc": "2.0",
        "method": method_name,
        "params": params,
        "id": 1
    }
    
    response = requests.post(SERVER_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        if "error" in result:
            print(f"Error calling {method_name}: {result['error']['message']}")
            return None
        return result["result"]
    else:
        print(f"HTTP error: {response.status_code}")
        return None

def test_bedrock_footprint():
    """Test calculating carbon footprint for AWS Bedrock models."""
    print("\n=== Testing Bedrock Carbon Footprint ===")
    
    params = {
        "model_id": "anthropic.claude-v2",
        "region": "us-east-1",
        "input_tokens": 1000,
        "output_tokens": 500
    }
    
    result = call_mcp_method("calculate_model_carbon_footprint", params)
    
    if result and "emissions" in result:
        print(f"Success: Calculated carbon footprint for {params['model_id']}")
        print(f"Total emissions: {result['emissions']['total_emissions_kgco2e']} kgCO2e")
        return True
    else:
        print("Failed to calculate Bedrock carbon footprint")
        return False

def test_region_comparison():
    """Test comparing environmental impact across regions."""
    print("\n=== Testing Region Comparison ===")
    
    params = {
        "service_type": "ec2",
        "resource_id": "t3.micro",
        "regions": ["us-east-1", "eu-west-1", "ap-southeast-2"],
        "usage_data": {"hours": 720, "count": 1}
    }
    
    result = call_mcp_method("compare_regions", params)
    
    if result and len(result) > 0:
        print(f"Success: Compared {len(result)} regions")
        for region, data in result.items():
            if "carbon_footprint" in data:
                print(f"Region {region}: {data['carbon_footprint']['total_kgco2e']} kgCO2e")
        return True
    else:
        print("Failed to compare regions")
        return False

def test_lowest_carbon_region():
    """Test finding the lowest carbon region."""
    print("\n=== Testing Lowest Carbon Region ===")
    
    params = {
        "service_type": "ec2",
        "resource_id": "t3.micro",
        "usage_data": {"hours": 720, "count": 1}
    }
    
    result = call_mcp_method("find_lowest_carbon_region", params)
    
    if result and "region" in result:
        print(f"Success: Found lowest carbon region: {result['region']}")
        print(f"Carbon footprint: {result['carbon_footprint']['total_kgco2e']} kgCO2e")
        return True
    else:
        print("Failed to find lowest carbon region")
        return False

def test_calculate_savings():
    """Test calculating potential savings from region migration."""
    print("\n=== Testing Calculate Savings ===")
    
    params = {
        "service_type": "ec2",
        "resource_id": "t3.micro",
        "current_region": "us-east-1",
        "target_region": "us-west-2",
        "usage_data": {"hours": 720, "count": 1}
    }
    
    result = call_mcp_method("calculate_savings", params)
    
    if result and "savings" in result:
        print(f"Success: Calculated savings for migration from {params['current_region']} to {params['target_region']}")
        print(f"Carbon savings: {result['savings']['carbon_savings_kgco2e']} kgCO2e")
        print(f"Percentage reduction: {result['savings']['percentage_reduction']}%")
        return True
    else:
        print("Failed to calculate savings")
        return False

def test_supported_models():
    """Test getting supported AI models."""
    print("\n=== Testing Supported Models ===")
    
    result = call_mcp_method("get_supported_models", {})
    
    if result and "models" in result:
        print(f"Success: Found {len(result['models'])} supported models")
        for i, model in enumerate(result["models"][:3], 1):
            print(f"{i}. {model['model_id']}")
        if len(result["models"]) > 3:
            print(f"... and {len(result['models']) - 3} more")
        return True
    else:
        print("Failed to get supported models")
        return False

def test_region_emissions_data():
    """Test getting region emissions data."""
    print("\n=== Testing Region Emissions Data ===")
    
    result = call_mcp_method("get_region_emissions_data", {})
    
    if result and len(result) > 0:
        print(f"Success: Found emissions data for {len(result)} regions")
        # Print the 3 lowest carbon regions
        sorted_regions = sorted(result.items(), key=lambda x: x[1]["carbon_intensity_gco2e_kwh"])
        print("Lowest carbon regions:")
        for i, (region, data) in enumerate(sorted_regions[:3], 1):
            print(f"{i}. {region}: {data['carbon_intensity_gco2e_kwh']} gCO2e/kWh")
        return True
    else:
        print("Failed to get region emissions data")
        return False

def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="AWS Cost Explorer MCP Server Comprehensive Test")
    parser.add_argument("--url", type=str, default=SERVER_URL, help=f"Server URL (default: {SERVER_URL})")
    
    args = parser.parse_args()
    
    global SERVER_URL
    SERVER_URL = args.url
    
    print("Testing AWS Cost Explorer MCP Server")
    print(f"Server URL: {SERVER_URL}")
    
    # Wait for the server to be available
    if not ping_server():
        print("Server not available. Make sure it's running with:")
        print("python mcp_server.py --transport sse --port 8000")
        return 1
    
    # Run tests
    bedrock_result = test_bedrock_footprint()
    region_result = test_region_comparison()
    lowest_region_result = test_lowest_carbon_region()
    savings_result = test_calculate_savings()
    models_result = test_supported_models()
    emissions_result = test_region_emissions_data()
    
    # Check if tests were successful
    if (bedrock_result and region_result and 
        lowest_region_result and savings_result and
        models_result and emissions_result):
        print("\n=== All tests completed successfully ===")
        return 0
    else:
        print("\n=== Some tests failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())

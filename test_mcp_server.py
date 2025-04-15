#!/usr/bin/env python3
"""
Test script for AWS Cost Explorer MCP Server
This script tests the server with mock data
"""

import requests
import json
import sys
import os
import time
from pprint import pprint

# URL for the MCP server
SERVER_URL = "http://localhost:8000"

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
    """Test Bedrock carbon footprint calculation."""
    print("\n=== Testing Bedrock Carbon Footprint Calculation ===")
    
    # Mock data for input and output tokens
    params = {
        "service_type": "bedrock",
        "resource_id": "anthropic.claude-3-sonnet",
        "region": "us-east-1",
        "usage_data": {
            "input_tokens": 1000000,
            "output_tokens": 500000
        }
    }
    
    # Call the calculate_total_footprint method
    result = call_mcp_method("calculate_total_footprint", params)
    
    if result:
        print("Bedrock Model Carbon Footprint:")
        pprint(result)
    
    return result

def test_region_comparison():
    """Test region comparison for carbon footprint."""
    print("\n=== Testing Region Comparison ===")
    
    # Mock data for S3 storage
    params = {
        "service_type": "s3:Standard",
        "resource_id": "Standard",
        "regions": ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-2"],
        "usage_data": {
            "storage_gb": 1000,
            "get_requests": 10000,
            "put_requests": 1000
        }
    }
    
    # Call the compare_regions method
    result = call_mcp_method("compare_regions", params)
    
    if result:
        print("Region Comparison Results:")
        pprint(result)
    
    return result

def test_lowest_carbon_region():
    """Test finding the lowest carbon region."""
    print("\n=== Testing Lowest Carbon Region ===")
    
    # Mock data for EC2 instance
    params = {
        "service_type": "ec2:t3.micro",
        "resource_id": "t3.micro",
        "usage_data": {
            "hours": 720  # One month of usage
        }
    }
    
    # Call the find_lowest_carbon_region method
    result = call_mcp_method("find_lowest_carbon_region", params)
    
    if result:
        print("Lowest Carbon Region:")
        pprint(result)
    
    return result

def test_calculate_savings():
    """Test calculating potential savings from region migration."""
    print("\n=== Testing Calculate Savings ===")
    
    # Mock data for RDS instance
    params = {
        "service_type": "rds:db.t3.medium",
        "resource_id": "db.t3.medium",
        "current_region": "us-east-1",
        "target_region": "us-west-2",
        "usage_data": {
            "hours": 720  # One month of usage
        }
    }
    
    # Call the calculate_savings method
    result = call_mcp_method("calculate_savings", params)
    
    if result:
        print("Potential Savings from Region Migration:")
        pprint(result)
    
    return result

def main():
    """Run all tests."""
    print("Testing AWS Cost Explorer MCP Server with mock data")
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
    
    # Check if tests were successful
    if (bedrock_result and region_result and 
        lowest_region_result and savings_result):
        print("\n=== All tests completed successfully ===")
        return 0
    else:
        print("\n=== Some tests failed ===")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
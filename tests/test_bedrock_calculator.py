#!/usr/bin/env python3
"""
Test script for BedrockCarbonCalculator
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator
except ImportError as e:
    print(f"Error importing BedrockCarbonCalculator: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

def test_calculator():
    """Test the main functionality of BedrockCarbonCalculator"""
    
    # Initialize calculator with test data directory
    calculator = BedrockCarbonCalculator(data_dir="tests/data")
    
    # Test model IDs to check
    test_models = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-opus-20240229-v1:0",
        "amazon.titan-text-express-v1:0"
    ]
    
    # Test regions
    test_regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2"]
    
    print("\n=== Testing BedrockCarbonCalculator ===\n")
    
    # Test 1: Calculate carbon footprint for each model in different regions
    print("Test 1: Carbon Footprint Calculation")
    print("-" * 50)
    for model_id in test_models:
        print(f"\nTesting model: {model_id}")
        for region in test_regions:
            try:
                footprint = calculator.calculate_carbon_footprint(
                    model_id=model_id,
                    region=region,
                    input_tokens=1000000,  # 1M tokens
                    output_tokens=200000    # 200K tokens
                )
                print(f"Region: {region}")
                print(f"Carbon footprint: {footprint:.2f} gCO2e")
            except Exception as e:
                print(f"Error calculating footprint for {model_id} in {region}: {e}")
    
    # Test 2: Find lowest carbon regions for a model
    print("\nTest 2: Finding Lowest Carbon Regions")
    print("-" * 50)
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    try:
        lowest_carbon_regions = calculator.find_lowest_carbon_regions(
            model_id=model_id,
            input_tokens=1000000,
            output_tokens=200000,
            limit=3
        )
        print(f"\nLowest carbon regions for {model_id}:")
        for region_data in lowest_carbon_regions:
            print(f"Region: {region_data['region']}")
            print(f"Estimated emissions: {region_data['emissions']:.2f} gCO2e")
    except Exception as e:
        print(f"Error finding lowest carbon regions: {e}")
    
    # Test 3: Calculate potential savings
    print("\nTest 3: Calculate Savings")
    print("-" * 50)
    try:
        savings = calculator.calculate_savings(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            current_region="ap-southeast-2",
            target_region="us-west-2",
            monthly_input_tokens=10000000,   # 10M tokens
            monthly_output_tokens=2000000     # 2M tokens
        )
        print("\nPotential savings from region switch:")
        print(f"Monthly emissions saved: {savings['emissions_saved_kg']:.2f} kg CO2e")
        print(f"Equivalent to: {savings['tree_months']:.1f} months of tree sequestration")
    except Exception as e:
        print(f"Error calculating savings: {e}")
    
    # Test 4: Get environmental context
    print("\nTest 4: Environmental Context")
    print("-" * 50)
    try:
        context = calculator.get_environmental_context(100.0)  # 100 kg CO2e
        print("\nEnvironmental impact equivalents for 100 kg CO2e:")
        for key, value in context.items():
            print(f"{key}: {value}")
    except Exception as e:
        print(f"Error getting environmental context: {e}")

if __name__ == "__main__":
    test_calculator() 
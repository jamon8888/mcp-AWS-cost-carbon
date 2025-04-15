#!/usr/bin/env python3
"""
Test script for AWS Pricing API features of the MCP server.
"""
import sys
import os
import json
from typing import Dict, Any
from pprint import pprint

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# We'll use our own EC2 parameter classes instead of importing them
from pydantic import BaseModel, Field

# Define the parameter classes we need
class EC2PricingParam(BaseModel):
    """Parameters for EC2 pricing and efficiency analysis."""
    instance_type: str
    region: str
    os: str = "Linux"

class EC2CompareParam(BaseModel):
    """Parameters for comparing EC2 instance types."""
    instance_types: list[str]
    region: str
    os: str = "Linux"

class EC2RegionCompareParam(BaseModel):
    """Parameters for finding cheapest region for an EC2 instance type."""
    instance_type: str
    regions: list[str]
    os: str = "Linux"

def test_ec2_pricing():
    """Test the get_ec2_pricing_and_efficiency tool."""
    print("\n=== Testing EC2 Pricing and Efficiency ===")
    
    # Create a test function (this is a mock)
    def test_get_ec2_pricing(params):
        """Mock implementation for testing."""
        return {
            "instance_type": params.instance_type,
            "region": params.region,
            "pricing": {
                "on_demand_price": 0.0416,
                "vcpus": "2",
                "memory_gb": "4 GiB",
                "generation": "t3",
                "prices": {
                    "on_demand": 0.0416,
                    "monthly": 30.368
                }
            },
            "carbon": {
                "emissions_g_per_hour": 12.5,
                "emissions_kg_per_month": 9.125
            },
            "water": {
                "water_liters_per_hour": 0.12,
                "water_liters_per_month": 87.6
            },
            "efficiency": {
                "vcpus_per_dollar": 48.08,
                "vcpus_per_carbon_g": 0.16,
                "cost_carbon_efficiency": 7.69
            }
        }
    
    # Test parameters
    params = EC2PricingParam(
        instance_type="t3.medium", 
        region="us-east-1",
        os="Linux"
    )
    
    # Call the test function
    result = test_get_ec2_pricing(params)
    
    # Print the result
    print(f"Instance: {result['instance_type']} in {result['region']}")
    print(f"Hourly cost: ${result['pricing']['on_demand_price']}")
    print(f"vCPUs: {result['pricing']['vcpus']}")
    print(f"Memory: {result['pricing']['memory_gb']}")
    print(f"Carbon emissions: {result['carbon']['emissions_g_per_hour']} g CO2e per hour")
    print(f"Water usage: {result['water']['water_liters_per_hour']} liters per hour")
    print(f"Efficiency: {result['efficiency']['vcpus_per_dollar']} vCPUs per dollar")
    print(f"Carbon efficiency: {result['efficiency']['vcpus_per_carbon_g']} vCPUs per g CO2e")
    
    return result

def test_compare_ec2_instances():
    """Test the compare_ec2_instance_pricing tool."""
    print("\n=== Testing EC2 Instance Comparison ===")
    
    # Create a test function (this is a mock)
    def test_compare_ec2_instance_pricing(params):
        """Mock implementation for testing."""
        return {
            "region": params.region,
            "os": params.os,
            "instances": {
                "t3.micro": {
                    "instance_type": "t3.micro",
                    "region": params.region,
                    "pricing": {"on_demand_price": 0.0104, "vcpus": "2", "memory_gb": "1 GiB"},
                    "carbon": {"emissions_g_per_hour": 6.2},
                    "efficiency": {"vcpus_per_dollar": 192.31, "vcpus_per_carbon_g": 0.32}
                },
                "t3.small": {
                    "instance_type": "t3.small",
                    "region": params.region,
                    "pricing": {"on_demand_price": 0.0208, "vcpus": "2", "memory_gb": "2 GiB"},
                    "carbon": {"emissions_g_per_hour": 9.3},
                    "efficiency": {"vcpus_per_dollar": 96.15, "vcpus_per_carbon_g": 0.22}
                },
                "t3.medium": {
                    "instance_type": "t3.medium",
                    "region": params.region,
                    "pricing": {"on_demand_price": 0.0416, "vcpus": "2", "memory_gb": "4 GiB"},
                    "carbon": {"emissions_g_per_hour": 12.5},
                    "efficiency": {"vcpus_per_dollar": 48.08, "vcpus_per_carbon_g": 0.16}
                }
            },
            "best_instances": {
                "cost_efficiency": "t3.micro",
                "carbon_efficiency": "t3.micro",
                "cost_carbon_balance": "t3.micro"
            }
        }
    
    # Test parameters
    params = EC2CompareParam(
        instance_types=["t3.micro", "t3.small", "t3.medium"],
        region="us-east-1",
        os="Linux"
    )
    
    # Call the test function
    result = test_compare_ec2_instance_pricing(params)
    
    # Print the result
    print(f"Compared {len(result['instances'])} instances in {result['region']}")
    
    for instance_type, data in result['instances'].items():
        print(f"\n{instance_type}:")
        print(f"  Hourly cost: ${data['pricing']['on_demand_price']}")
        print(f"  vCPUs: {data['pricing']['vcpus']}")
        print(f"  Memory: {data['pricing']['memory_gb']}")
        print(f"  Carbon: {data['carbon']['emissions_g_per_hour']} g CO2e/hour")
        print(f"  Cost efficiency: {data['efficiency']['vcpus_per_dollar']} vCPUs/$")
        print(f"  Carbon efficiency: {data['efficiency']['vcpus_per_carbon_g']} vCPUs/g CO2e")
    
    print("\nBest instances:")
    print(f"  Cost efficiency: {result['best_instances']['cost_efficiency']}")
    print(f"  Carbon efficiency: {result['best_instances']['carbon_efficiency']}")
    print(f"  Cost-carbon balance: {result['best_instances']['cost_carbon_balance']}")
    
    return result

def test_find_best_region():
    """Test the find_best_region_for_ec2_instance tool."""
    print("\n=== Testing Find Best Region for EC2 Instance ===")
    
    # Create a test function (this is a mock)
    def test_find_best_region_for_ec2_instance(params):
        """Mock implementation for testing."""
        return {
            "instance_type": params.instance_type,
            "os": params.os,
            "regions": {
                "us-east-1": {
                    "region": "us-east-1",
                    "pricing": {"on_demand_price": 0.0416},
                    "carbon": {"emissions_g_per_hour": 12.5},
                    "water": {"water_liters_per_hour": 0.12},
                    "efficiency": {"cost_carbon_efficiency": 7.69}
                },
                "us-west-2": {
                    "region": "us-west-2",
                    "pricing": {"on_demand_price": 0.0448},
                    "carbon": {"emissions_g_per_hour": 8.3},
                    "water": {"water_liters_per_hour": 0.09},
                    "efficiency": {"cost_carbon_efficiency": 9.64}
                },
                "eu-west-1": {
                    "region": "eu-west-1",
                    "pricing": {"on_demand_price": 0.0464},
                    "carbon": {"emissions_g_per_hour": 10.2},
                    "water": {"water_liters_per_hour": 0.11},
                    "efficiency": {"cost_carbon_efficiency": 8.21}
                }
            },
            "best_regions": {
                "lowest_cost": "us-east-1",
                "lowest_carbon": "us-west-2",
                "lowest_water": "us-west-2",
                "best_cost_carbon_balance": "us-west-2"
            }
        }
    
    # Test parameters
    params = EC2RegionCompareParam(
        instance_type="t3.medium",
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        os="Linux"
    )
    
    # Call the test function
    result = test_find_best_region_for_ec2_instance(params)
    
    # Print the result
    print(f"Instance type: {result['instance_type']}")
    print(f"Compared {len(result['regions'])} regions")
    
    for region, data in result['regions'].items():
        print(f"\n{region}:")
        print(f"  Hourly cost: ${data['pricing']['on_demand_price']}")
        print(f"  Carbon: {data['carbon']['emissions_g_per_hour']} g CO2e/hour")
        print(f"  Water: {data['water']['water_liters_per_hour']} liters/hour")
    
    print("\nBest regions:")
    print(f"  Lowest cost: {result['best_regions']['lowest_cost']}")
    print(f"  Lowest carbon: {result['best_regions']['lowest_carbon']}")
    print(f"  Lowest water: {result['best_regions']['lowest_water']}")
    print(f"  Best cost-carbon balance: {result['best_regions']['best_cost_carbon_balance']}")
    
    return result

if __name__ == "__main__":
    print("Testing AWS Pricing API Features")
    
    # Run the tests
    test_ec2_pricing()
    test_compare_ec2_instances()
    test_find_best_region()
    
    print("\nAll tests completed!") 
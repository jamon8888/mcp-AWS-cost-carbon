#!/usr/bin/env python3
"""
Simplified test script for region comparison feature.
"""
import json
from typing import Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class EC2RegionCompareParam(BaseModel):
    """Parameters for finding cheapest region for an EC2 instance type."""
    instance_type: str
    regions: List[str]
    os: str = "Linux"

def find_best_region(params):
    """Simplified function to find the best region for an EC2 instance."""
    # Mock data for the test
    results = {
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
    
    return results

def main():
    """Test the region comparison feature."""
    print("=== Testing Region Comparison ===")
    
    # Test parameters
    params = EC2RegionCompareParam(
        instance_type="t3.medium",
        regions=["us-east-1", "us-west-2", "eu-west-1"]
    )
    
    # Get the results
    result = find_best_region(params)
    
    # Print the instance type and regions
    print(f"Instance type: {result['instance_type']}")
    print(f"Compared {len(result['regions'])} regions")
    
    # Print details for each region
    for region_name, region_data in result['regions'].items():
        print(f"\n{region_name}:")
        print(f"  Hourly cost: ${region_data['pricing']['on_demand_price']}")
        print(f"  Carbon emissions: {region_data['carbon']['emissions_g_per_hour']} g CO2e/hour")
        print(f"  Water usage: {region_data['water']['water_liters_per_hour']} liters/hour")
        print(f"  Efficiency metric: {region_data['efficiency']['cost_carbon_efficiency']}")
    
    # Print the best regions
    print("\nBest regions:")
    print(f"  Lowest cost: {result['best_regions']['lowest_cost']}")
    print(f"  Lowest carbon: {result['best_regions']['lowest_carbon']}")
    print(f"  Lowest water: {result['best_regions']['lowest_water']}")
    print(f"  Best cost-carbon balance: {result['best_regions']['best_cost_carbon_balance']}")

if __name__ == "__main__":
    main() 
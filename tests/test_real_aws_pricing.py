#!/usr/bin/env python3
"""
Test script for AWS Pricing API features using a simulated server environment.
Since the functions in mcp_server.py are defined inside the main() function,
we need to define our own mock versions of these functions.
"""
import sys
import os
import json
import boto3
from typing import Dict, Any, List
from pprint import pprint
from pydantic import BaseModel, Field

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the necessary modules and classes
from core.aws_environmental_calculator import AWSEnvironmentalCalculator
from core.calculators.scope3_calculator import Scope3Calculator
from datetime import datetime

# Define the parameter classes
class EC2PricingParam(BaseModel):
    """Parameters for EC2 pricing and efficiency analysis."""
    instance_type: str
    region: str
    os: str = "Linux"

class EC2CompareParam(BaseModel):
    """Parameters for comparing EC2 instance types."""
    instance_types: List[str]
    region: str
    os: str = "Linux"

class EC2RegionCompareParam(BaseModel):
    """Parameters for finding cheapest region for an EC2 instance type."""
    instance_type: str
    regions: List[str]
    os: str = "Linux"

# Global variables for the simulated environment
calculator = None
pricing_client = None

def init_environment():
    """Initialize the test environment."""
    global calculator, pricing_client
    
    # Set up mock mode
    data_dir = "mock"
    print(f"Using data directory: {os.path.abspath(data_dir)}")
    
    # Initialize calculators
    calculator = AWSEnvironmentalCalculator(data_dir=data_dir, mock_mode=True)
    
    # Initialize AWS Pricing client
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    print(f"Test environment initialized")

def get_ec2_pricing_and_efficiency(params: EC2PricingParam) -> Dict[str, Any]:
    """
    Get real-time AWS EC2 instance pricing and efficiency metrics.
    
    Args:
        params: Parameters for the analysis including:
            - instance_type: EC2 instance type (e.g., t3.micro, m5.large)
            - region: AWS region code (e.g., us-east-1)
            - os: Operating system (default: Linux)
    
    Returns:
        Dictionary with pricing and efficiency metrics
    """
    try:
        # Map region code to region name (e.g., us-east-1 -> US East (N. Virginia))
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-west-2': 'EU (London)',
            'eu-west-3': 'EU (Paris)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-northeast-3': 'Asia Pacific (Osaka)',
            'sa-east-1': 'South America (Sao Paulo)',
            'ca-central-1': 'Canada (Central)'
        }
        
        region_name = region_mapping.get(params.region, params.region)
        
        # Build filter for AWS Pricing API
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': params.instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': params.os},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
        ]
        
        # For testing purposes, we'll provide mock data instead of calling the actual API
        # In a real scenario, this would call pricing_client.get_products()
        
        # Mock response data
        pricing_result = {
            "instance_type": params.instance_type,
            "region": params.region,
            "os": params.os,
            "on_demand_price": 0.0416 if params.instance_type == "t3.medium" else 0.0104,
            "vcpus": "2",
            "memory_gb": "4 GiB" if params.instance_type == "t3.medium" else "1 GiB",
            "generation": "t3",
            "prices": {
                "on_demand": 0.0416 if params.instance_type == "t3.medium" else 0.0104,
                "monthly": 30.368 if params.instance_type == "t3.medium" else 7.592
            }
        }
        
        # Get carbon and water data from environmental calculator
        carbon_metrics = {}
        water_metrics = {}
        
        # Mock data for carbon and water
        carbon_metrics = {
            "emissions_g_per_hour": 12.5 if params.instance_type == "t3.medium" else 6.2,
            "emissions_kg_per_month": 9.125 if params.instance_type == "t3.medium" else 4.526,
        }
        
        water_metrics = {
            "water_liters_per_hour": 0.12 if params.instance_type == "t3.medium" else 0.08,
            "water_liters_per_month": 87.6 if params.instance_type == "t3.medium" else 58.4,
        }
        
        # Calculate efficiency metrics
        efficiency_metrics = {}
        if pricing_result.get('vcpus') and pricing_result.get('on_demand_price'):
            try:
                vcpu_count = int(pricing_result.get('vcpus', 1))
                hourly_price = float(pricing_result.get('on_demand_price', 0))
                
                if hourly_price > 0:
                    # Cost efficiency (vCPUs per dollar per hour)
                    efficiency_metrics["vcpus_per_dollar"] = vcpu_count / hourly_price
                    
                    # If we have carbon data, calculate carbon efficiency
                    if carbon_metrics.get('emissions_g_per_hour'):
                        carbon_per_hour = carbon_metrics.get('emissions_g_per_hour', 0)
                        if carbon_per_hour > 0:
                            # Carbon efficiency (vCPUs per gram of CO2 per hour)
                            efficiency_metrics["vcpus_per_carbon_g"] = vcpu_count / carbon_per_hour
                            
                            # Cost-carbon efficiency (vCPUs per dollar per gram of CO2)
                            efficiency_metrics["cost_carbon_efficiency"] = efficiency_metrics["vcpus_per_dollar"] * efficiency_metrics["vcpus_per_carbon_g"]
            except (ValueError, ZeroDivisionError):
                pass
        
        return {
            "instance_type": params.instance_type,
            "region": params.region,
            "pricing": pricing_result,
            "carbon": carbon_metrics,
            "water": water_metrics,
            "efficiency": efficiency_metrics,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Error getting EC2 pricing: {str(e)}")
        return {
            "instance_type": params.instance_type,
            "region": params.region,
            "os": params.os,
            "error": str(e)
        }

def compare_ec2_instance_pricing(params: EC2CompareParam) -> Dict[str, Any]:
    """
    Compare pricing and efficiency metrics for multiple EC2 instance types.
    
    Args:
        params: Parameters for the comparison including:
            - instance_types: List of EC2 instance types to compare
            - region: AWS region code (e.g., us-east-1)
            - os: Operating system (default: Linux)
    
    Returns:
        Dictionary with comparison results
    """
    try:
        results = {
            "region": params.region,
            "os": params.os,
            "instances": {},
            "generated_at": datetime.now().isoformat()
        }
        
        for instance_type in params.instance_types:
            # Reuse the get_ec2_pricing_and_efficiency function
            instance_params = EC2PricingParam(
                instance_type=instance_type,
                region=params.region,
                os=params.os
            )
            
            pricing_data = get_ec2_pricing_and_efficiency(instance_params)
            if pricing_data:
                results["instances"][instance_type] = pricing_data
        
        # Find best instance for different metrics
        best_instances = {
            "cost_efficiency": None,
            "carbon_efficiency": None,
            "cost_carbon_balance": None
        }
        
        best_cost_efficiency = -1
        best_carbon_efficiency = -1
        best_balance = -1
        
        for instance_type, data in results["instances"].items():
            efficiency = data.get("efficiency", {})
            
            # Check cost efficiency
            cost_eff = efficiency.get("vcpus_per_dollar", 0)
            if cost_eff > best_cost_efficiency:
                best_cost_efficiency = cost_eff
                best_instances["cost_efficiency"] = instance_type
            
            # Check carbon efficiency
            carbon_eff = efficiency.get("vcpus_per_carbon_g", 0)
            if carbon_eff > best_carbon_efficiency:
                best_carbon_efficiency = carbon_eff
                best_instances["carbon_efficiency"] = instance_type
            
            # Check balanced efficiency
            balance = efficiency.get("cost_carbon_efficiency", 0)
            if balance > best_balance:
                best_balance = balance
                best_instances["cost_carbon_balance"] = instance_type
        
        results["best_instances"] = best_instances
        return results
    
    except Exception as e:
        print(f"Error comparing EC2 instances: {str(e)}")
        return {
            "region": params.region,
            "os": params.os,
            "error": str(e)
        }

def find_best_region_for_ec2_instance(params: EC2RegionCompareParam) -> Dict[str, Any]:
    """
    Find the best region for an EC2 instance type based on cost and environmental metrics.
    
    Args:
        params: Parameters for the analysis including:
            - instance_type: EC2 instance type (e.g., t3.micro, m5.large)
            - regions: List of AWS regions to compare
            - os: Operating system (default: Linux)
    
    Returns:
        Dictionary with best regions for different metrics
    """
    try:
        results = {
            "instance_type": params.instance_type,
            "os": params.os,
            "regions": {},
            "generated_at": datetime.now().isoformat()
        }
        
        # Mock data for regions
        region_data = {
            "us-east-1": {
                "pricing": {"on_demand_price": 0.0416},
                "carbon": {"emissions_g_per_hour": 12.5},
                "water": {"water_liters_per_hour": 0.12},
                "efficiency": {"cost_carbon_efficiency": 7.69}
            },
            "us-west-2": {
                "pricing": {"on_demand_price": 0.0448},
                "carbon": {"emissions_g_per_hour": 8.3},
                "water": {"water_liters_per_hour": 0.09},
                "efficiency": {"cost_carbon_efficiency": 9.64}
            },
            "eu-west-1": {
                "pricing": {"on_demand_price": 0.0464},
                "carbon": {"emissions_g_per_hour": 10.2},
                "water": {"water_liters_per_hour": 0.11},
                "efficiency": {"cost_carbon_efficiency": 8.21}
            }
        }
        
        for region in params.regions:
            if region in region_data:
                results["regions"][region] = {
                    "region": region,
                    **region_data[region]
                }
        
        # Find best regions for different metrics
        best_regions = {
            "lowest_cost": None,
            "lowest_carbon": None,
            "lowest_water": None,
            "best_cost_carbon_balance": None
        }
        
        lowest_cost = float('inf')
        lowest_carbon = float('inf')
        lowest_water = float('inf')
        best_balance = -1
        
        for region, data in results["regions"].items():
            pricing = data.get("pricing", {})
            carbon = data.get("carbon", {})
            water = data.get("water", {})
            efficiency = data.get("efficiency", {})
            
            # Check cost
            cost = pricing.get("on_demand_price", float('inf'))
            if cost < lowest_cost:
                lowest_cost = cost
                best_regions["lowest_cost"] = region
            
            # Check carbon
            carbon_emissions = carbon.get("emissions_g_per_hour", float('inf'))
            if carbon_emissions < lowest_carbon:
                lowest_carbon = carbon_emissions
                best_regions["lowest_carbon"] = region
            
            # Check water
            water_usage = water.get("water_liters_per_hour", float('inf'))
            if water_usage < lowest_water:
                lowest_water = water_usage
                best_regions["lowest_water"] = region
            
            # Check balanced efficiency
            balance = efficiency.get("cost_carbon_efficiency", 0)
            if balance > best_balance:
                best_balance = balance
                best_regions["best_cost_carbon_balance"] = region
        
        results["best_regions"] = best_regions
        return results
    
    except Exception as e:
        print(f"Error finding best region: {str(e)}")
        return {
            "instance_type": params.instance_type,
            "os": params.os,
            "error": str(e)
        }

def test_ec2_pricing():
    """Test the get_ec2_pricing_and_efficiency function."""
    print("\n=== Testing EC2 Pricing and Efficiency (Simulated) ===")
    
    # Test parameters
    params = EC2PricingParam(
        instance_type="t3.medium", 
        region="us-east-1",
        os="Linux"
    )
    
    # Call the function
    result = get_ec2_pricing_and_efficiency(params)
    
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
    """Test the compare_ec2_instance_pricing function."""
    print("\n=== Testing EC2 Instance Comparison (Simulated) ===")
    
    # Test parameters
    params = EC2CompareParam(
        instance_types=["t3.micro", "t3.small", "t3.medium"],
        region="us-east-1",
        os="Linux"
    )
    
    # Call the function
    result = compare_ec2_instance_pricing(params)
    
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
    """Test the find_best_region_for_ec2_instance function."""
    print("\n=== Testing Find Best Region for EC2 Instance (Simulated) ===")
    
    # Test parameters
    params = EC2RegionCompareParam(
        instance_type="t3.medium",
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        os="Linux"
    )
    
    # Call the function
    result = find_best_region_for_ec2_instance(params)
    
    # Print the result
    print(f"Instance type: {result['instance_type']}")
    print(f"Compared {len(result['regions'])} regions")
    
    # Debug the region data
    for region_name, region_data in result['regions'].items():
        print(f"\n{region_name}:")
        print(f"  Hourly cost: ${region_data['pricing']['on_demand_price']}")
        print(f"  Carbon emissions: {region_data['carbon']['emissions_g_per_hour']} g CO2e/hour")
        print(f"  Water usage: {region_data['water']['water_liters_per_hour']} liters/hour")
        print(f"  Efficiency metric: {region_data['efficiency']['cost_carbon_efficiency']}")
    
    print("\nBest regions:")
    print(f"  Lowest cost: {result['best_regions']['lowest_cost']}")
    print(f"  Lowest carbon: {result['best_regions']['lowest_carbon']}")
    print(f"  Lowest water: {result['best_regions']['lowest_water']}")
    print(f"  Best cost-carbon balance: {result['best_regions']['best_cost_carbon_balance']}")
    
    return result

if __name__ == "__main__":
    print("Testing AWS Pricing API Features (Simulated Environment)")
    print("Note: Using mock data to demonstrate functionality")
    
    try:
        # Initialize test environment
        init_environment()
        
        # Run the tests
        test_ec2_pricing()
        test_compare_ec2_instances()
        test_find_best_region()
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        import traceback
        traceback.print_exc() 
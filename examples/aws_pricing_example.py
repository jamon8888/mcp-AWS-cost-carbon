#!/usr/bin/env python3
"""
Example script showing how to use the AWS Pricing API features.
"""
import sys
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse
import pandas as pd
import matplotlib.pyplot as plt

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the MCP server module
# Note: In a real application, you would import the functions you need
# from the appropriate modules
from pydantic import BaseModel, Field

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

def get_ec2_pricing(instance_type: str, region: str, os: str = "Linux") -> Dict[str, Any]:
    """
    Get EC2 pricing and efficiency metrics for a specific instance type.
    
    In a real application, this would call the actual AWS Pricing API.
    For this example, we're using mock data.
    """
    # Create parameter object
    params = EC2PricingParam(
        instance_type=instance_type,
        region=region,
        os=os
    )
    
    # Mock data for different instance types
    instance_data = {
        "t3.micro": {
            "pricing": {
                "on_demand_price": 0.0104,
                "vcpus": "2",
                "memory_gb": "1 GiB",
                "generation": "t3",
            },
            "carbon": {
                "emissions_g_per_hour": 6.2,
                "emissions_kg_per_month": 4.526,
            },
            "water": {
                "water_liters_per_hour": 0.08,
                "water_liters_per_month": 58.4,
            },
            "efficiency": {
                "vcpus_per_dollar": 192.31,
                "vcpus_per_carbon_g": 0.32,
                "cost_carbon_efficiency": 61.54,
            }
        },
        "t3.small": {
            "pricing": {
                "on_demand_price": 0.0208,
                "vcpus": "2",
                "memory_gb": "2 GiB",
                "generation": "t3",
            },
            "carbon": {
                "emissions_g_per_hour": 9.3,
                "emissions_kg_per_month": 6.789,
            },
            "water": {
                "water_liters_per_hour": 0.10,
                "water_liters_per_month": 73.0,
            },
            "efficiency": {
                "vcpus_per_dollar": 96.15,
                "vcpus_per_carbon_g": 0.22,
                "cost_carbon_efficiency": 21.15,
            }
        },
        "t3.medium": {
            "pricing": {
                "on_demand_price": 0.0416,
                "vcpus": "2",
                "memory_gb": "4 GiB",
                "generation": "t3",
            },
            "carbon": {
                "emissions_g_per_hour": 12.5,
                "emissions_kg_per_month": 9.125,
            },
            "water": {
                "water_liters_per_hour": 0.12,
                "water_liters_per_month": 87.6,
            },
            "efficiency": {
                "vcpus_per_dollar": 48.08,
                "vcpus_per_carbon_g": 0.16,
                "cost_carbon_efficiency": 7.69,
            }
        }
    }
    
    # Get the data for the requested instance type
    if instance_type in instance_data:
        result = {
            "instance_type": instance_type,
            "region": region,
            "os": os,
            **instance_data[instance_type],
            "generated_at": datetime.now().isoformat()
        }
    else:
        # Default data if the instance type is not found
        result = {
            "instance_type": instance_type,
            "region": region,
            "os": os,
            "pricing": {
                "on_demand_price": 0.05,
                "vcpus": "2",
                "memory_gb": "4 GiB",
                "generation": "unknown",
            },
            "carbon": {
                "emissions_g_per_hour": 10.0,
                "emissions_kg_per_month": 7.3,
            },
            "water": {
                "water_liters_per_hour": 0.1,
                "water_liters_per_month": 73.0,
            },
            "efficiency": {
                "vcpus_per_dollar": 40.0,
                "vcpus_per_carbon_g": 0.2,
                "cost_carbon_efficiency": 8.0,
            },
            "generated_at": datetime.now().isoformat()
        }
    
    return result

def compare_ec2_instances(instance_types: List[str], region: str, os: str = "Linux") -> Dict[str, Any]:
    """
    Compare EC2 pricing and efficiency metrics for multiple instance types.
    
    In a real application, this would call the actual AWS Pricing API.
    For this example, we're using mock data.
    """
    # Create parameter object
    params = EC2CompareParam(
        instance_types=instance_types,
        region=region,
        os=os
    )
    
    # Get pricing data for each instance type
    results = {
        "region": region,
        "os": os,
        "instances": {},
        "generated_at": datetime.now().isoformat()
    }
    
    for instance_type in instance_types:
        pricing_data = get_ec2_pricing(instance_type, region, os)
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

def find_best_regions(instance_type: str, regions: List[str], os: str = "Linux") -> Dict[str, Any]:
    """
    Find the best regions for an EC2 instance type based on cost and environmental metrics.
    
    In a real application, this would call the actual AWS Pricing API.
    For this example, we're using mock data.
    """
    # Create parameter object
    params = EC2RegionCompareParam(
        instance_type=instance_type,
        regions=regions,
        os=os
    )
    
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
        },
        "ap-southeast-1": {
            "pricing": {"on_demand_price": 0.0512},
            "carbon": {"emissions_g_per_hour": 14.8},
            "water": {"water_liters_per_hour": 0.14},
            "efficiency": {"cost_carbon_efficiency": 6.45}
        },
        "ap-northeast-1": {
            "pricing": {"on_demand_price": 0.0528},
            "carbon": {"emissions_g_per_hour": 11.7},
            "water": {"water_liters_per_hour": 0.13},
            "efficiency": {"cost_carbon_efficiency": 7.25}
        }
    }
    
    results = {
        "instance_type": instance_type,
        "os": os,
        "regions": {},
        "generated_at": datetime.now().isoformat()
    }
    
    for region in regions:
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

def create_instance_comparison_chart(data: Dict[str, Any], metric: str = "cost") -> None:
    """Create a chart comparing EC2 instances based on the specified metric."""
    # Extract the data for the chart
    instances = list(data["instances"].keys())
    
    if metric == "cost":
        values = [data["instances"][instance]["pricing"]["on_demand_price"] for instance in instances]
        title = "Hourly Cost Comparison"
        ylabel = "Hourly Cost ($)"
    elif metric == "carbon":
        values = [data["instances"][instance]["carbon"]["emissions_g_per_hour"] for instance in instances]
        title = "Carbon Emissions Comparison"
        ylabel = "Carbon Emissions (g CO2e/hour)"
    elif metric == "water":
        values = [data["instances"][instance]["water"]["water_liters_per_hour"] for instance in instances]
        title = "Water Usage Comparison"
        ylabel = "Water Usage (liters/hour)"
    elif metric == "efficiency":
        values = [data["instances"][instance]["efficiency"]["vcpus_per_dollar"] for instance in instances]
        title = "Cost Efficiency Comparison"
        ylabel = "vCPUs per Dollar"
    else:
        print(f"Unknown metric: {metric}")
        return
    
    # Create the chart
    plt.figure(figsize=(10, 6))
    plt.bar(instances, values)
    plt.title(title)
    plt.xlabel("Instance Type")
    plt.ylabel(ylabel)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Add value labels on top of the bars
    for i, v in enumerate(values):
        plt.text(i, v, f"{v:.4f}", ha="center", va="bottom")
    
    # Save the chart
    filename = f"ec2_{metric}_comparison.png"
    plt.savefig(filename)
    print(f"Chart saved as {filename}")

def create_region_comparison_chart(data: Dict[str, Any], metric: str = "cost") -> None:
    """Create a chart comparing AWS regions based on the specified metric."""
    # Extract the data for the chart
    regions = list(data["regions"].keys())
    
    if metric == "cost":
        values = [data["regions"][region]["pricing"]["on_demand_price"] for region in regions]
        title = "Hourly Cost Comparison by Region"
        ylabel = "Hourly Cost ($)"
    elif metric == "carbon":
        values = [data["regions"][region]["carbon"]["emissions_g_per_hour"] for region in regions]
        title = "Carbon Emissions Comparison by Region"
        ylabel = "Carbon Emissions (g CO2e/hour)"
    elif metric == "water":
        values = [data["regions"][region]["water"]["water_liters_per_hour"] for region in regions]
        title = "Water Usage Comparison by Region"
        ylabel = "Water Usage (liters/hour)"
    else:
        print(f"Unknown metric: {metric}")
        return
    
    # Create the chart
    plt.figure(figsize=(12, 6))
    plt.bar(regions, values)
    plt.title(title)
    plt.xlabel("AWS Region")
    plt.ylabel(ylabel)
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Add value labels on top of the bars
    for i, v in enumerate(values):
        plt.text(i, v, f"{v:.4f}", ha="center", va="bottom")
    
    # Save the chart
    filename = f"region_{metric}_comparison.png"
    plt.savefig(filename)
    print(f"Chart saved as {filename}")

def main():
    """Run the example application."""
    parser = argparse.ArgumentParser(description="AWS Pricing API Example")
    parser.add_argument("--action", type=str, required=True,
                      choices=["pricing", "compare-instances", "compare-regions"],
                      help="Action to perform")
    parser.add_argument("--instance-type", type=str, help="EC2 instance type")
    parser.add_argument("--instance-types", type=str, help="Comma-separated list of EC2 instance types")
    parser.add_argument("--region", type=str, default="us-east-1", help="AWS region")
    parser.add_argument("--regions", type=str, help="Comma-separated list of AWS regions")
    parser.add_argument("--os", type=str, default="Linux", help="Operating system")
    parser.add_argument("--chart", action="store_true", help="Generate a chart")
    parser.add_argument("--metric", type=str, default="cost",
                      choices=["cost", "carbon", "water", "efficiency"],
                      help="Metric to show in the chart")
    
    args = parser.parse_args()
    
    if args.action == "pricing":
        if not args.instance_type:
            parser.error("--instance-type is required for 'pricing' action")
        
        result = get_ec2_pricing(args.instance_type, args.region, args.os)
        
        print(f"\nEC2 Pricing for {args.instance_type} in {args.region}:")
        print(f"Hourly cost: ${result['pricing']['on_demand_price']}")
        print(f"vCPUs: {result['pricing']['vcpus']}")
        print(f"Memory: {result['pricing']['memory_gb']}")
        print(f"Carbon emissions: {result['carbon']['emissions_g_per_hour']} g CO2e per hour")
        print(f"Water usage: {result['water']['water_liters_per_hour']} liters per hour")
        print(f"Cost efficiency: {result['efficiency']['vcpus_per_dollar']} vCPUs per dollar")
        print(f"Carbon efficiency: {result['efficiency']['vcpus_per_carbon_g']} vCPUs per g CO2e")
    
    elif args.action == "compare-instances":
        if not args.instance_types:
            parser.error("--instance-types is required for 'compare-instances' action")
        
        instance_types = args.instance_types.split(",")
        result = compare_ec2_instances(instance_types, args.region, args.os)
        
        print(f"\nEC2 Instance Comparison in {args.region}:")
        
        for instance_type, data in result["instances"].items():
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
        
        if args.chart:
            create_instance_comparison_chart(result, args.metric)
    
    elif args.action == "compare-regions":
        if not args.instance_type:
            parser.error("--instance-type is required for 'compare-regions' action")
        
        if not args.regions:
            # Default to comparing major regions
            regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"]
        else:
            regions = args.regions.split(",")
        
        result = find_best_regions(args.instance_type, regions, args.os)
        
        print(f"\nRegion Comparison for {args.instance_type}:")
        
        for region, data in result["regions"].items():
            print(f"\n{region}:")
            print(f"  Hourly cost: ${data['pricing']['on_demand_price']}")
            print(f"  Carbon: {data['carbon']['emissions_g_per_hour']} g CO2e/hour")
            print(f"  Water: {data['water']['water_liters_per_hour']} liters/hour")
        
        print("\nBest regions:")
        print(f"  Lowest cost: {result['best_regions']['lowest_cost']}")
        print(f"  Lowest carbon: {result['best_regions']['lowest_carbon']}")
        print(f"  Lowest water: {result['best_regions']['lowest_water']}")
        print(f"  Best cost-carbon balance: {result['best_regions']['best_cost_carbon_balance']}")
        
        if args.chart:
            create_region_comparison_chart(result, args.metric)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc() 
#!/usr/bin/env python3
"""
AWS Cost Explorer MCP Server
A server for analyzing AWS costs and environmental impact
"""

import argparse
import os
import json
import logging
from core.aws_environmental_calculator import AWSEnvironmentalCalculator
from core.calculators.scope3_calculator import Scope3Calculator
import fastmcp
from typing import Dict, List, Any, Optional, Literal, Union
from datetime import datetime, timedelta

import boto3
import pandas as pd
from fastmcp import FastMCP
from pydantic import BaseModel, Field, conint, confloat, UUID4

def main():
    """Run the MCP server."""
    
    parser = argparse.ArgumentParser(description="AWS Cost and Environmental Impact Analyzer")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--transport", type=str, default="stdio", 
                        choices=["stdio", "sse"], 
                        help="Transport type (stdio, sse)")
    parser.add_argument("--host", type=str, default="0.0.0.0", 
                        help="Host to bind to (for sse transport)")
    parser.add_argument("--data-dir", type=str, default="data",
                        help="Directory containing data files (default: data)")
    parser.add_argument("--mock", action="store_true",
                        help="Use mock data from 'mock/' directory instead of 'data/'")
    
    args = parser.parse_args()
    
    # Determine data directory based on mock flag
    data_dir = "mock" if args.mock else args.data_dir
    print(f"Using data directory: {os.path.abspath(data_dir)}")

    # Initialize the core calculators with mock mode flag
    calculator = AWSEnvironmentalCalculator(data_dir=data_dir, mock_mode=args.mock)
    scope3_calculator = Scope3Calculator(data_dir=data_dir, mock_mode=args.mock)

    # Initialize AWS Pricing API client
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    # Create the MCP server
    app = fastmcp.FastMCP("aws-cost-explorer")

    # Register EC2 pricing API tools
    class EC2PricingParam(BaseModel):
        """Parameters for EC2 pricing and efficiency analysis."""
        instance_type: str = Field(
            ..., 
            description="EC2 instance type (e.g., t3.micro, m5.large)",
            examples=["t3.micro", "m5.large", "c5.xlarge"]
        )
        region: str = Field(
            ..., 
            description="AWS region code (e.g., us-east-1, eu-west-1)",
            examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
        )
        os: str = Field(
            "Linux", 
            description="Operating system (e.g., Linux, Windows)",
            examples=["Linux", "Windows"]
        )

    class EC2CompareParam(BaseModel):
        """Parameters for comparing EC2 instance types."""
        instance_types: List[str] = Field(
            ..., 
            description="List of EC2 instance types to compare",
            min_items=1,
            examples=[["t3.micro", "t3.small", "t3.medium"]]
        )
        region: str = Field(
            ..., 
            description="AWS region code (e.g., us-east-1, eu-west-1)",
            examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
        )
        os: str = Field(
            "Linux", 
            description="Operating system (e.g., Linux, Windows)",
            examples=["Linux", "Windows"]
        )

    class EC2RegionCompareParam(BaseModel):
        """Parameters for finding cheapest region for an EC2 instance type."""
        instance_type: str = Field(
            ..., 
            description="EC2 instance type (e.g., t3.micro, m5.large)",
            examples=["t3.micro", "m5.large", "c5.xlarge"]
        )
        regions: List[str] = Field(
            ..., 
            description="List of AWS regions to compare",
            min_items=1,
            examples=[["us-east-1", "us-east-2", "us-west-1", "us-west-2"]]
        )
        os: str = Field(
            "Linux", 
            description="Operating system (e.g., Linux, Windows)",
            examples=["Linux", "Windows"]
        )

    @app.tool("get_ec2_pricing_and_efficiency")
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
            
            # Query pricing API
            response = pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters,
                MaxResults=100
            )
            
            # Process response
            pricing_result = {
                "instance_type": params.instance_type,
                "region": params.region,
                "os": params.os,
                "on_demand_price": None,
                "vcpus": None,
                "memory_gb": None,
                "generation": None,
                "prices": {}
            }
            
            # Extract pricing from response
            for price_str in response.get('PriceList', []):
                price_data = json.loads(price_str)
                product = price_data.get('product', {})
                attributes = product.get('attributes', {})
                
                # Get instance attributes
                pricing_result["vcpus"] = attributes.get('vcpu')
                pricing_result["memory_gb"] = attributes.get('memory')
                pricing_result["generation"] = attributes.get('instanceFamily')
                
                # Get pricing details
                for term_key, term_value in price_data.get('terms', {}).get('OnDemand', {}).items():
                    for price_key, price_value in term_value.get('priceDimensions', {}).items():
                        price_unit = price_value.get('unit')
                        price_per_unit = price_value.get('pricePerUnit', {}).get('USD')
                        if price_per_unit:
                            # Convert to float
                            try:
                                price = float(price_per_unit)
                                pricing_result["on_demand_price"] = price
                                pricing_result["prices"]["on_demand"] = price
                                
                                # Calculate monthly price (730 hours)
                                pricing_result["prices"]["monthly"] = price * 730
                            except ValueError:
                                pass
            
            # Get carbon and water data from environmental calculator
            carbon_metrics = {}
            water_metrics = {}
            
            # Use the AWSEnvironmentalCalculator to get carbon and water data
            carbon_data = calculator.get_ec2_carbon_emissions(params.instance_type, params.region)
            water_data = calculator.get_ec2_water_usage(params.instance_type, params.region)
            
            carbon_metrics = {
                "emissions_g_per_hour": carbon_data.get('carbon_per_hour_g', 0),
                "emissions_kg_per_month": carbon_data.get('carbon_per_hour_g', 0) * 730 / 1000,
            }
            
            water_metrics = {
                "water_liters_per_hour": water_data.get('water_per_hour_liters', 0),
                "water_liters_per_month": water_data.get('water_per_hour_liters', 0) * 730,
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

    @app.tool("compare_ec2_instance_pricing")
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

    @app.tool("find_best_region_for_ec2_instance")
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
            
            for region in params.regions:
                # Reuse the get_ec2_pricing_and_efficiency function
                region_params = EC2PricingParam(
                    instance_type=params.instance_type,
                    region=region,
                    os=params.os
                )
                
                region_data = get_ec2_pricing_and_efficiency(region_params)
                if region_data:
                    results["regions"][region] = region_data
            
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
    
    # Register original calculator methods as tools
    # (Keep existing @app.tool definitions below this point)
    
    # Environmental calculator methods
    @app.tool("calculate_total_footprint")
    def calculate_total_footprint(service_type: str, resource_id: str, region: str, usage_data: dict):
        """Calculate the total carbon footprint for a service."""
        return calculator.calculate_total_footprint(service_type, resource_id, region, usage_data)
    
    @app.tool("compare_regions")
    def compare_regions(service_type: str, resource_id: str, regions: list, usage_data: dict):
        """Compare environmental impact across regions."""
        return calculator.compare_regions(service_type, resource_id, regions, usage_data)
    
    @app.tool("find_lowest_carbon_region")
    def find_lowest_carbon_region(service_type: str, resource_id: str, usage_data: dict):
        """Find the region with the lowest carbon footprint."""
        return calculator.find_lowest_carbon_region(service_type, resource_id, usage_data)
    
    @app.tool("calculate_savings")
    def calculate_savings(service_type: str, resource_id: str, 
                         current_region: str, target_region: str, usage_data: dict):
        """Calculate potential savings from region migration."""
        return calculator.calculate_savings(service_type, resource_id, 
                                          current_region, target_region, usage_data)
    
    # Scope3 calculator methods
    @app.tool("calculate_upstream_emissions")
    def calculate_upstream_emissions(service_type: str, usage_data: dict):
        """Calculate upstream emissions (Scope 3) for a service."""
        return scope3_calculator.calculate_upstream_emissions(service_type, usage_data)
    
    @app.tool("calculate_downstream_emissions")
    def calculate_downstream_emissions(service_type: str, usage_data: dict):
        """Calculate downstream emissions (Scope 3) for a service."""
        return scope3_calculator.calculate_downstream_emissions(service_type, usage_data)
    
    @app.tool("get_supply_chain_emissions")
    def get_supply_chain_emissions(service_type: str):
        """Get supply chain emissions factors for a service."""
        return scope3_calculator.get_supply_chain_emissions(service_type)
    
    print(f"Starting AWS Cost and Environmental Impact Analyzer")
    print(f"Transport: {args.transport}")
    print(f"Data directory: {data_dir} {'(Mock Mode)' if args.mock else ''}")
    print(f"Loaded {len(calculator.region_carbon_intensity)} regions with carbon intensity data")
    print(f"Loaded {len(calculator.model_energy_consumption)} AI models with energy consumption data")
    print(f"AWS Pricing API integration enabled!")
    
    # Run the server with the specified transport
    if args.transport == "sse":
        app.run(transport=args.transport, port=args.port)
    else:
        app.run(transport=args.transport)

if __name__ == "__main__":
    main() 
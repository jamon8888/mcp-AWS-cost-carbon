#!/usr/bin/env python3
"""
AWS Cost Explorer Server Starter

A unified script to start different server types with the AWS Cost Explorer.
Replaces multiple separate scripts.
"""

import argparse
import os
import sys
import subprocess
import platform
import socket
import logging
from flask import Flask, render_template, jsonify, request
import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Ensure correct path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import MCP server components
from mcp_server import start_mcp_server

# Try to import the AWS Environmental Calculator
try:
    from core.aws_environmental_calculator import AWSEnvironmentalCalculator
    HAS_ENV_CALCULATOR = True
except ImportError:
    print("Warning: AWSEnvironmentalCalculator not found. Environmental impact analysis will be disabled.")
    HAS_ENV_CALCULATOR = False

# Create AWS pricing client (global)
pricing_client = None

class AWSPricingService:
    """Service for fetching and analyzing AWS pricing using the boto3 pricing API."""
    
    def __init__(self, region="us-east-1"):
        """Initialize AWS pricing service.
        
        Note: The pricing API is only available in us-east-1 and ap-south-1.
        """
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.cached_pricing = {}
        self.cache_expiry = {}
        self.cache_duration = timedelta(hours=6)  # Cache pricing data for 6 hours
        
    def get_ec2_pricing(self, instance_type: str, region: str, os: str = 'Linux') -> Dict[str, Any]:
        """Get pricing for EC2 instance type in a specific region."""
        cache_key = f"ec2_{instance_type}_{region}_{os}"
        
        # Check cache
        if cache_key in self.cached_pricing and datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
            return self.cached_pricing[cache_key]
        
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
        
        region_name = region_mapping.get(region, region)
        
        # Build filter for AWS Pricing API
        filters = [
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': os},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
        ]
        
        try:
            # Query pricing API
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=filters,
                MaxResults=100
            )
            
            # Process response
            result = {
                "instance_type": instance_type,
                "region": region,
                "os": os,
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
                result["vcpus"] = attributes.get('vcpu')
                result["memory_gb"] = attributes.get('memory')
                result["generation"] = attributes.get('instanceFamily')
                
                # Get pricing details
                for term_key, term_value in price_data.get('terms', {}).get('OnDemand', {}).items():
                    for price_key, price_value in term_value.get('priceDimensions', {}).items():
                        price_unit = price_value.get('unit')
                        price_per_unit = price_value.get('pricePerUnit', {}).get('USD')
                        if price_per_unit:
                            # Convert to float
                            try:
                                price = float(price_per_unit)
                                result["on_demand_price"] = price
                                result["prices"]["on_demand"] = price
                                
                                # Calculate monthly price (730 hours)
                                result["prices"]["monthly"] = price * 730
                            except ValueError:
                                pass
            
            # Cache the result
            self.cached_pricing[cache_key] = result
            self.cache_expiry[cache_key] = datetime.now() + self.cache_duration
            
            return result
        
        except Exception as e:
            logging.error(f"Error getting EC2 pricing: {str(e)}")
            return {
                "instance_type": instance_type,
                "region": region,
                "os": os,
                "error": str(e)
            }
    
    def compare_instance_types(self, instance_types: List[str], region: str, os: str = 'Linux') -> Dict[str, Any]:
        """Compare pricing for multiple instance types in a region."""
        results = {
            "region": region,
            "os": os,
            "instances": {},
            "generated_at": datetime.now().isoformat()
        }
        
        for instance_type in instance_types:
            pricing = self.get_ec2_pricing(instance_type, region, os)
            if pricing:
                results["instances"][instance_type] = pricing
        
        return results
    
    def find_cheapest_region(self, instance_type: str, regions: List[str], os: str = 'Linux') -> Dict[str, Any]:
        """Find the cheapest region for an instance type."""
        results = {
            "instance_type": instance_type,
            "os": os,
            "regions": {},
            "cheapest_region": None,
            "cheapest_price": None,
            "generated_at": datetime.now().isoformat()
        }
        
        for region in regions:
            pricing = self.get_ec2_pricing(instance_type, region, os)
            if pricing and pricing.get('on_demand_price'):
                results["regions"][region] = pricing
                
                # Update cheapest if applicable
                if (results["cheapest_price"] is None or 
                    pricing.get('on_demand_price') < results["cheapest_price"]):
                    results["cheapest_region"] = region
                    results["cheapest_price"] = pricing.get('on_demand_price')
        
        return results
    
    def get_cost_and_carbon_efficiency(self, instance_type: str, region: str, os: str = 'Linux',
                                      workload_type: str = 'general') -> Dict[str, Any]:
        """Get cost and carbon efficiency metrics for an instance."""
        pricing = self.get_ec2_pricing(instance_type, region, os)
        
        # Get carbon and water data if environmental calculator is available
        carbon_metrics = {}
        water_metrics = {}
        
        if HAS_ENV_CALCULATOR:
            env_calculator = AWSEnvironmentalCalculator()
            carbon_data = env_calculator.get_ec2_carbon_emissions(instance_type, region)
            water_data = env_calculator.get_ec2_water_usage(instance_type, region)
            
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
        if pricing.get('vcpus') and pricing.get('on_demand_price'):
            try:
                vcpu_count = int(pricing.get('vcpus', 1))
                hourly_price = float(pricing.get('on_demand_price', 0))
                
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
            "instance_type": instance_type,
            "region": region,
            "pricing": pricing,
            "carbon": carbon_metrics,
            "water": water_metrics,
            "efficiency": efficiency_metrics,
            "generated_at": datetime.now().isoformat()
        }


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Start the AWS Cost & Environmental Impact MCP Server')
    
    # MCP server arguments
    parser.add_argument('--data-file', type=str, default='data/mcp_cost_data.json',
                      help='Path to MCP data file')
    parser.add_argument('--port', type=int, default=8080,
                      help='Port to run server on')
    
    # AWS Pricing API arguments
    parser.add_argument('--cache-duration', type=int, default=6,
                      help='Duration in hours to cache pricing data')
    
    return parser.parse_args()


def setup_aws_pricing_api(app):
    """Setup AWS Pricing API integration."""
    global pricing_client
    pricing_client = AWSPricingService()
    
    # Register API routes for AWS pricing
    @app.route('/api/pricing/ec2')
    def get_ec2_pricing():
        instance_type = request.args.get('instance_type', 't3.micro')
        region = request.args.get('region', 'us-east-1')
        os = request.args.get('os', 'Linux')
        
        result = pricing_client.get_ec2_pricing(instance_type, region, os)
        return jsonify(result)
    
    @app.route('/api/pricing/ec2/compare')
    def compare_ec2_instances():
        instance_types = request.args.get('instance_types', 't3.micro,t3.small,t3.medium').split(',')
        region = request.args.get('region', 'us-east-1')
        os = request.args.get('os', 'Linux')
        
        result = pricing_client.compare_instance_types(instance_types, region, os)
        return jsonify(result)
    
    @app.route('/api/pricing/ec2/cheapest-region')
    def find_cheapest_region():
        instance_type = request.args.get('instance_type', 't3.micro')
        regions = request.args.get('regions', 'us-east-1,us-east-2,us-west-1,us-west-2').split(',')
        os = request.args.get('os', 'Linux')
        
        result = pricing_client.find_cheapest_region(instance_type, regions, os)
        return jsonify(result)
    
    @app.route('/api/pricing/ec2/efficiency')
    def get_efficiency_metrics():
        instance_type = request.args.get('instance_type', 't3.micro')
        region = request.args.get('region', 'us-east-1')
        os = request.args.get('os', 'Linux')
        workload_type = request.args.get('workload_type', 'general')
        
        result = pricing_client.get_cost_and_carbon_efficiency(instance_type, region, os, workload_type)
        return jsonify(result)
    
    @app.route('/aws-pricing')
    def aws_pricing_dashboard():
        return render_template('aws_pricing_dashboard.html')
    
    print("AWS Pricing API integration enabled!")


def main():
    """Main entry point."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Setup AWS Pricing API integration
    setup_aws_pricing_api(app)
    
    # Start the MCP server
    start_mcp_server(app, args.data_file, args.port)


if __name__ == "__main__":
    main() 
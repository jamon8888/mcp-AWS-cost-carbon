#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AWS Region Environmental Impact Comparison

This script compares the environmental impact (carbon emissions, water usage, etc.) 
of running the same workload across different AWS regions.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.aws_environmental_calculator import AWSEnvironmentalCalculator
from core.scope3_carbon_calculator import Scope3Calculator
from core.region_comparison import compare_regions_impact

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Compare environmental impact across AWS regions')
    
    parser.add_argument('--output', '-o', type=str, default='region_comparison_results.json',
                        help='Path to save comparison results (default: region_comparison_results.json)')
    parser.add_argument('--regions', '-r', type=str, nargs='+',
                        default=['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-2'],
                        help='AWS regions to compare (default: us-east-1 us-west-2 eu-west-1 eu-central-1 ap-southeast-2)')
    parser.add_argument('--services', '-s', type=str, nargs='+',
                        default=['ec2', 'lambda', 'dynamodb'],
                        help='AWS services to analyze (default: ec2 lambda dynamodb)')
    parser.add_argument('--data-dir', '-d', type=str, default='data',
                        help='Directory containing environmental data files (default: data)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    return parser.parse_args()

def setup_logging(verbose=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def define_test_services(selected_services):
    """Define test services based on service selection."""
    test_services = {}
    
    service_definitions = {
        'ec2': {
            'service_type': 'ec2',
            'resource_id': 't3.xlarge',
            'usage_data': {'hours': 720, 'vcpu': 4, 'memory_gb': 16}
        },
        'lambda': {
            'service_type': 'lambda',
            'resource_id': 'function-1',
            'usage_data': {'invocations': 1000000, 'avg_duration_ms': 500, 'memory_mb': 512}
        },
        'dynamodb': {
            'service_type': 'dynamodb',
            'resource_id': 'table-1',
            'usage_data': {'read_request_units': 5000000, 'write_request_units': 1000000, 'storage_gb': 50}
        },
        'bedrock': {
            'service_type': 'bedrock',
            'resource_id': 'Claude-3-Sonnet',
            'usage_data': {'input_tokens': 10000000, 'output_tokens': 5000000}
        },
        's3': {
            'service_type': 's3',
            'resource_id': 'bucket-1',
            'usage_data': {'storage_gb': 1000, 'get_requests': 10000000, 'put_requests': 1000000}
        },
        'rds': {
            'service_type': 'rds',
            'resource_id': 'db.t3.large',
            'usage_data': {'hours': 720, 'storage_gb': 100}
        }
    }
    
    for service in selected_services:
        if service in service_definitions:
            test_services[service] = service_definitions[service]
        else:
            logging.warning(f"Service '{service}' is not defined. Skipping.")
    
    return test_services

def main():
    args = parse_arguments()
    setup_logging(args.verbose)
    
    # Ensure data directory exists
    if not os.path.exists(args.data_dir):
        logging.error(f"Data directory '{args.data_dir}' does not exist.")
        sys.exit(1)
    
    logging.info("Starting region environmental impact comparison")
    logging.info(f"Comparing regions: {', '.join(args.regions)}")
    logging.info(f"Analyzing services: {', '.join(args.services)}")
    
    # Define services to test
    test_services = define_test_services(args.services)
    if not test_services:
        logging.error("No valid services selected for analysis.")
        sys.exit(1)
    
    try:
        # Perform region comparison
        results = compare_regions_impact(
            regions=args.regions,
            services=test_services,
            data_dir=args.data_dir
        )
        
        # Save results to file
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Comparison results saved to {args.output}")
        
        # Print summary of findings
        print("\n==== REGION COMPARISON SUMMARY ====")
        
        # Best region for carbon footprint
        best_carbon_region = min(results['carbon_emissions_by_region'], 
                                key=lambda r: results['carbon_emissions_by_region'][r]['total_emissions'])
        print(f"Best region for carbon footprint: {best_carbon_region}")
        
        # Best region for water usage
        best_water_region = min(results['water_usage_by_region'], 
                              key=lambda r: results['water_usage_by_region'][r]['total_water_usage'])
        print(f"Best region for water usage: {best_water_region}")
        
        # Potential carbon savings
        carbon_savings = results['potential_savings']['carbon_emissions_savings']
        print(f"Potential carbon savings by selecting the best region: {carbon_savings:.2f} kg CO2e")
        
        # Potential water savings
        water_savings = results['potential_savings']['water_usage_savings']
        print(f"Potential water savings by selecting the best region: {water_savings:.2f} liters")
        
        # Efficiency information
        print("\nRegion PUE (Power Usage Effectiveness):")
        for region, data in results['region_characteristics'].items():
            print(f"  {region}: {data['pue']:.2f}")
        
        print("\nRegion Water Stress Levels (1-5, 5 being highest):")
        for region, data in results['region_characteristics'].items():
            print(f"  {region}: {data['water_stress']:.1f}")
            
    except Exception as e:
        logging.error(f"An error occurred during comparison: {e}")
        sys.exit(1)
        
    logging.info("Region comparison completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
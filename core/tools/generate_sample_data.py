#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate sample data files for AWS Cost Explorer MCP Server.

This module provides functions to generate sample data files for various metrics:
- Region carbon intensity
- Region Power Usage Effectiveness (PUE)
- Region water usage
- Region water stress
- Model energy consumption
- Model training footprint

These generated files can be used for testing and development purposes.
"""

import os
import argparse
import pandas as pd
import numpy as np
from typing import Dict, List


def generate_region_carbon_intensity(output_dir: str) -> str:
    """
    Generate a sample region carbon intensity CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AWS regions and their carbon intensity values (gCO2e/kWh)
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1", "ap-south-1"
    ]
    
    # Sample carbon intensity values (gCO2e/kWh)
    carbon_intensities = [
        389.2, 429.0, 210.5, 136.5,
        275.8, 231.0, 51.2, 345.6,
        408.1, 700.3, 463.8,
        142.9, 128.9, 708.2
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'region': regions,
        'carbon_intensity': carbon_intensities
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "region_carbon_intensity.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated region carbon intensity data: {file_path}")
    return file_path


def generate_region_pue(output_dir: str) -> str:
    """
    Generate a sample region PUE (Power Usage Effectiveness) CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AWS regions and their PUE values
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1", "ap-south-1"
    ]
    
    # Sample PUE values
    pue_values = [
        1.21, 1.20, 1.18, 1.16,
        1.19, 1.22, 1.17, 1.23,
        1.25, 1.24, 1.20,
        1.28, 1.19, 1.26
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'region': regions,
        'pue': pue_values
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "region_pue.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated region PUE data: {file_path}")
    return file_path


def generate_region_water_usage(output_dir: str) -> str:
    """
    Generate a sample region water usage CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AWS regions and their water usage values (L/kWh)
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1", "ap-south-1"
    ]
    
    # Sample water usage values (L/kWh)
    water_usage_values = [
        1.8, 2.1, 3.2, 1.5,
        1.7, 1.9, 1.6, 2.3,
        2.5, 2.2, 1.8,
        1.9, 1.4, 2.7
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'region': regions,
        'water_usage': water_usage_values
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "region_water_usage.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated region water usage data: {file_path}")
    return file_path


def generate_region_water_stress(output_dir: str) -> str:
    """
    Generate a sample region water stress CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AWS regions and their water stress values (0-5 scale)
    regions = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1", "ap-south-1"
    ]
    
    # Sample water stress values (0-5 scale, 5 being highest stress)
    water_stress_values = [
        2.3, 1.8, 4.2, 3.7,
        1.2, 2.1, 1.5, 2.5,
        1.9, 2.7, 3.1,
        1.1, 1.3, 4.3
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'region': regions,
        'water_stress': water_stress_values
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "region_water_stress.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated region water stress data: {file_path}")
    return file_path


def generate_model_energy_consumption(output_dir: str) -> str:
    """
    Generate a sample model energy consumption CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AI models and their energy consumption values
    models = [
        "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo",
        "claude-instant-1", "claude-2", "claude-3-opus",
        "claude-3-sonnet", "claude-3-haiku",
        "llama-2-7b", "llama-2-13b", "llama-2-70b",
        "falcon-7b", "falcon-40b",
        "mistral-7b", "mixtral-8x7b"
    ]
    
    # Sample input energy values (kWh per 1M tokens)
    input_energy_values = [
        0.0003, 0.0015, 0.0012,
        0.0002, 0.0008, 0.0018,
        0.0010, 0.0005,
        0.0004, 0.0008, 0.0025,
        0.0004, 0.0020,
        0.0004, 0.0015
    ]
    
    # Sample output energy values (kWh per 1M tokens)
    output_energy_values = [
        0.0015, 0.0080, 0.0060,
        0.0010, 0.0040, 0.0090,
        0.0050, 0.0025,
        0.0020, 0.0040, 0.0120,
        0.0020, 0.0100,
        0.0020, 0.0075
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'model_id': models,
        'input_energy': input_energy_values,
        'output_energy': output_energy_values
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "model_energy_consumption.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated model energy consumption data: {file_path}")
    return file_path


def generate_model_training_footprint(output_dir: str) -> str:
    """
    Generate a sample model training footprint CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define AI models and their training footprint values
    models = [
        "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo",
        "claude-instant-1", "claude-2", "claude-3-opus",
        "claude-3-sonnet", "claude-3-haiku",
        "llama-2-7b", "llama-2-13b", "llama-2-70b",
        "falcon-7b", "falcon-40b",
        "mistral-7b", "mixtral-8x7b"
    ]
    
    # Sample energy consumption during training (MWh)
    training_energy_values = [
        250, 1000, 850,
        180, 600, 1200,
        750, 350,
        90, 180, 950,
        95, 600,
        100, 500
    ]
    
    # Sample carbon emissions during training (tCO2e)
    emissions_values = [
        125, 500, 425,
        90, 300, 600,
        375, 175,
        45, 90, 475,
        47, 300,
        50, 250
    ]
    
    # Sample parameters count (billions)
    params_count = [
        6, 175, 165,
        8, 70, 190,
        90, 20,
        7, 13, 70,
        7, 40,
        7, 45
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'model_id': models,
        'training_energy_mwh': training_energy_values,
        'emissions_tco2e': emissions_values,
        'params_b': params_count
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "model_training_footprint.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated model training footprint data: {file_path}")
    return file_path


def generate_ec2_instance_power(output_dir: str) -> str:
    """
    Generate a sample EC2 instance power consumption CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Define EC2 instance types and their power consumption values
    instance_types = [
        "t2.micro", "t2.small", "t2.medium", "t2.large",
        "m5.large", "m5.xlarge", "m5.2xlarge", "m5.4xlarge",
        "c5.large", "c5.xlarge", "c5.2xlarge", "c5.4xlarge",
        "r5.large", "r5.xlarge", "r5.2xlarge", "r5.4xlarge",
        "p3.2xlarge", "p3.8xlarge", "p3.16xlarge",
        "g4dn.xlarge", "g4dn.2xlarge", "g4dn.4xlarge"
    ]
    
    # Sample average power consumption (W)
    avg_power_values = [
        15, 20, 40, 60,
        75, 150, 300, 600,
        80, 160, 320, 640,
        90, 180, 360, 720,
        350, 1400, 2800,
        250, 500, 1000
    ]
    
    # Sample idle power consumption (W)
    idle_power_values = [
        8, 10, 20, 30,
        40, 80, 160, 320,
        45, 90, 180, 360,
        50, 100, 200, 400,
        200, 800, 1600,
        150, 300, 600
    ]
    
    # Sample max power consumption (W)
    max_power_values = [
        25, 35, 70, 100,
        120, 240, 480, 960,
        140, 280, 560, 1120,
        150, 300, 600, 1200,
        500, 2000, 4000,
        400, 800, 1600
    ]
    
    # Create DataFrame
    df = pd.DataFrame({
        'instance_type': instance_types,
        'avg_power_watts': avg_power_values,
        'idle_power_watts': idle_power_values,
        'max_power_watts': max_power_values
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "ec2_instance_power.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated EC2 instance power data: {file_path}")
    return file_path


def generate_cost_data(output_dir: str) -> str:
    """
    Generate a sample AWS cost data CSV file.
    
    Args:
        output_dir: Directory where the CSV file will be saved
        
    Returns:
        Path to the generated file
    """
    # Create date range for the last 3 months
    import datetime
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=90)
    date_range = pd.date_range(start=start_date, end=end_date)
    
    # Define AWS services
    services = [
        "AmazonEC2", "AmazonRDS", "AmazonS3", 
        "AmazonDynamoDB", "AWSLambda", "AmazonBedrockInference",
        "AmazonCloudWatch", "AmazonRoute53"
    ]
    
    # Define AWS regions
    regions = [
        "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"
    ]
    
    # Create empty lists to store the data
    dates = []
    service_names = []
    region_names = []
    costs = []
    usage_amounts = []
    usage_types = []
    
    # Generate random data
    np.random.seed(42)  # For reproducibility
    
    for date in date_range:
        for service in services:
            for region in regions:
                # Add 1-3 entries per service/region/day
                entries = np.random.randint(1, 4)
                
                for _ in range(entries):
                    dates.append(date.strftime('%Y-%m-%d'))
                    service_names.append(service)
                    region_names.append(region)
                    
                    # Generate random cost
                    if service == "AmazonEC2":
                        cost = np.random.uniform(5, 100)
                        usage_type = np.random.choice(["BoxUsage", "DataTransfer"])
                        usage_amount = np.random.uniform(10, 1000) if usage_type == "BoxUsage" else np.random.uniform(1, 100)
                    elif service == "AmazonRDS":
                        cost = np.random.uniform(10, 200)
                        usage_type = "InstanceUsage"
                        usage_amount = np.random.uniform(100, 500)
                    elif service == "AmazonS3":
                        cost = np.random.uniform(1, 50)
                        usage_type = np.random.choice(["StorageUsage", "Requests", "DataTransfer"])
                        usage_amount = np.random.uniform(5, 5000)
                    elif service == "AmazonDynamoDB":
                        cost = np.random.uniform(1, 30)
                        usage_type = np.random.choice(["ReadCapacityUnits", "WriteCapacityUnits", "Storage"])
                        usage_amount = np.random.uniform(100, 10000)
                    elif service == "AWSLambda":
                        cost = np.random.uniform(0.5, 20)
                        usage_type = "Requests"
                        usage_amount = np.random.uniform(10000, 1000000)
                    elif service == "AmazonBedrockInference":
                        cost = np.random.uniform(5, 150)
                        usage_type = "InferenceRequests"
                        usage_amount = np.random.uniform(1000, 100000)
                    elif service == "AmazonCloudWatch":
                        cost = np.random.uniform(0.5, 15)
                        usage_type = np.random.choice(["Metrics", "Logs", "Alarms"])
                        usage_amount = np.random.uniform(100, 5000)
                    else:  # Route53
                        cost = np.random.uniform(0.1, 5)
                        usage_type = np.random.choice(["HostedZone", "Queries"])
                        usage_amount = np.random.uniform(10, 1000)
                    
                    costs.append(round(cost, 2))
                    usage_types.append(usage_type)
                    usage_amounts.append(round(usage_amount, 2))
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'service': service_names,
        'region': region_names,
        'cost': costs,
        'usage_type': usage_types,
        'usage_amount': usage_amounts
    })
    
    # Save to CSV
    file_path = os.path.join(output_dir, "aws_cost_data.csv")
    df.to_csv(file_path, index=False)
    
    print(f"Generated AWS cost data: {file_path}")
    return file_path


def generate_all_data(output_dir: str) -> Dict[str, str]:
    """
    Generate all sample data files.
    
    Args:
        output_dir: Directory where the CSV files will be saved
        
    Returns:
        Dictionary mapping data type to file path
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate all sample data files
    files = {}
    
    files['carbon_intensity'] = generate_region_carbon_intensity(output_dir)
    files['pue'] = generate_region_pue(output_dir)
    files['water_usage'] = generate_region_water_usage(output_dir)
    files['water_stress'] = generate_region_water_stress(output_dir)
    files['model_energy'] = generate_model_energy_consumption(output_dir)
    files['model_training'] = generate_model_training_footprint(output_dir)
    files['ec2_power'] = generate_ec2_instance_power(output_dir)
    files['cost_data'] = generate_cost_data(output_dir)
    
    print(f"\nSuccessfully generated {len(files)} sample data files in {output_dir}")
    return files


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Generate sample data files for AWS Cost Explorer MCP Server")
    parser.add_argument("--output", "-o", default="data", help="Output directory for generated files")
    args = parser.parse_args()
    
    generate_all_data(args.output)


if __name__ == "__main__":
    main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Convert AWS Cost Explorer data to MCP format.

This module provides functions to convert AWS Cost Explorer CSV data
to the format expected by the MCP server for analysis and visualization.
"""

import os
import argparse
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json
import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_aws_cost_data(file_path: str) -> pd.DataFrame:
    """
    Load AWS Cost Explorer data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing AWS cost data
        
    Returns:
        DataFrame containing the AWS cost data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded AWS cost data from {file_path}: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error loading AWS cost data: {e}")
        raise


def convert_to_mcp_format(cost_data: pd.DataFrame) -> Dict:
    """
    Convert AWS cost data to MCP format.
    
    Args:
        cost_data: DataFrame containing AWS cost data
        
    Returns:
        Dictionary in MCP format
    """
    # Validate required columns
    required_columns = ['date', 'service', 'region', 'cost', 'usage_type', 'usage_amount']
    missing_columns = [col for col in required_columns if col not in cost_data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Create the base MCP structure
    mcp_data = {
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.datetime.now().isoformat(),
            "source": "AWS Cost Explorer",
            "row_count": len(cost_data)
        },
        "time_period": {
            "start": cost_data['date'].min(),
            "end": cost_data['date'].max()
        },
        "summary": {
            "total_cost": round(cost_data['cost'].sum(), 2),
            "service_count": cost_data['service'].nunique(),
            "region_count": cost_data['region'].nunique()
        },
        "services": {},
        "regions": {},
        "daily_costs": []
    }
    
    # Process services
    for service, group in cost_data.groupby('service'):
        mcp_data["services"][service] = {
            "total_cost": round(group['cost'].sum(), 2),
            "usage_types": group['usage_type'].unique().tolist()
        }
    
    # Process regions
    for region, group in cost_data.groupby('region'):
        mcp_data["regions"][region] = {
            "total_cost": round(group['cost'].sum(), 2),
            "services": group['service'].unique().tolist()
        }
    
    # Process daily costs
    for date, group in cost_data.groupby('date'):
        daily_data = {
            "date": date,
            "total_cost": round(group['cost'].sum(), 2),
            "services": {}
        }
        
        # Add service breakdown for each day
        for service, service_group in group.groupby('service'):
            daily_data["services"][service] = {
                "cost": round(service_group['cost'].sum(), 2),
                "regions": {}
            }
            
            # Add region breakdown for each service
            for region, region_group in service_group.groupby('region'):
                daily_data["services"][service]["regions"][region] = round(region_group['cost'].sum(), 2)
        
        mcp_data["daily_costs"].append(daily_data)
    
    # Sort daily costs by date
    mcp_data["daily_costs"] = sorted(mcp_data["daily_costs"], key=lambda x: x["date"])
    
    logger.info(f"Converted AWS cost data to MCP format: {len(mcp_data['daily_costs'])} days")
    return mcp_data


def save_mcp_data(mcp_data: Dict, output_path: str) -> str:
    """
    Save MCP data to a JSON file.
    
    Args:
        mcp_data: Dictionary containing MCP data
        output_path: Path where the JSON file will be saved
        
    Returns:
        Path to the saved file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(mcp_data, f, indent=2)
        
        logger.info(f"Saved MCP data to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error saving MCP data: {e}")
        raise


def add_environmental_metrics(mcp_data: Dict, env_metrics: Dict) -> Dict:
    """
    Add environmental metrics to MCP data.
    
    Args:
        mcp_data: Dictionary containing MCP data
        env_metrics: Dictionary containing environmental metrics by service and region
        
    Returns:
        Updated MCP data with environmental metrics
    """
    # Add environmental metrics to metadata
    mcp_data["metadata"]["includes_environmental_metrics"] = True
    
    # Add environmental metrics summary
    mcp_data["environmental_summary"] = {
        "total_carbon_emissions": 0,
        "total_energy_consumption": 0,
        "total_water_usage": 0
    }
    
    # Add environmental metrics to services
    for service_name, service_data in mcp_data["services"].items():
        if service_name in env_metrics.get("services", {}):
            service_data["environmental_metrics"] = env_metrics["services"][service_name]
            
            # Add to summary
            mcp_data["environmental_summary"]["total_carbon_emissions"] += service_data["environmental_metrics"].get("carbon_emissions", 0)
            mcp_data["environmental_summary"]["total_energy_consumption"] += service_data["environmental_metrics"].get("energy_consumption", 0)
            mcp_data["environmental_summary"]["total_water_usage"] += service_data["environmental_metrics"].get("water_usage", 0)
    
    # Add environmental metrics to regions
    for region_name, region_data in mcp_data["regions"].items():
        if region_name in env_metrics.get("regions", {}):
            region_data["environmental_metrics"] = env_metrics["regions"][region_name]
    
    # Round the summary values
    for key in mcp_data["environmental_summary"]:
        mcp_data["environmental_summary"][key] = round(mcp_data["environmental_summary"][key], 2)
    
    logger.info("Added environmental metrics to MCP data")
    return mcp_data


def process_aws_cost_data(input_file: str, output_file: str, env_metrics_file: Optional[str] = None) -> str:
    """
    Process AWS cost data and convert it to MCP format.
    
    Args:
        input_file: Path to the CSV file containing AWS cost data
        output_file: Path where the MCP JSON file will be saved
        env_metrics_file: Optional path to a JSON file containing environmental metrics
        
    Returns:
        Path to the saved MCP file
    """
    # Load AWS cost data
    cost_data = load_aws_cost_data(input_file)
    
    # Convert to MCP format
    mcp_data = convert_to_mcp_format(cost_data)
    
    # Add environmental metrics if provided
    if env_metrics_file:
        try:
            with open(env_metrics_file, 'r') as f:
                env_metrics = json.load(f)
            
            mcp_data = add_environmental_metrics(mcp_data, env_metrics)
        except Exception as e:
            logger.warning(f"Could not add environmental metrics: {e}")
    
    # Save MCP data
    return save_mcp_data(mcp_data, output_file)


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Convert AWS Cost Explorer data to MCP format")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file with AWS cost data")
    parser.add_argument("--output", "-o", required=True, help="Output JSON file for MCP data")
    parser.add_argument("--env-metrics", "-e", help="Optional JSON file with environmental metrics")
    args = parser.parse_args()
    
    try:
        output_path = process_aws_cost_data(args.input, args.output, args.env_metrics)
        print(f"Successfully converted AWS cost data to MCP format: {output_path}")
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 
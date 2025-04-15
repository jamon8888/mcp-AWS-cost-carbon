#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AWS Cost and Environmental Impact MCP Server

MCP server for analyzing AWS cost, carbon emissions, and water usage.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Literal, Union
from datetime import datetime, timedelta

import boto3
import pandas as pd
from fastmcp import FastMCP
from pydantic import BaseModel, Field, conint, confloat, UUID4

# Add parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the calculators
from core.aws_cost_carbon_calculator import AWSEnvironmentalCalculator
from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("AWS Cost & Environmental Impact Analysis Assistant")

# Initialize the calculator
calculator = AWSEnvironmentalCalculator()
bedrock_calculator = BedrockCarbonCalculator()

# Parameter models for the MCP tools
class RegionParam(BaseModel):
    """Parameters for specifying an AWS region."""
    region: str = Field(
        ..., 
        description="AWS region code (e.g., us-east-1, eu-west-1)",
        examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
    )

class DaysParam(BaseModel):
    """Parameters for specifying the number of days to look back."""
    days: int = Field(
        30, 
        description="Number of days for the analysis period",
        ge=1,
        le=365,
        examples=[7, 30, 90]
    )

class EC2Param(BaseModel):
    """Parameters for EC2 carbon footprint calculation."""
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
    hours: float = Field(
        730.0, 
        description="Number of hours the instance will run",
        ge=1,
        examples=[24, 168, 730]
    )
    count: int = Field(
        1, 
        description="Number of instances",
        ge=1,
        examples=[1, 5, 10]
    )

class ModelCarbonParam(BaseModel):
    """Parameters for AI model carbon footprint calculation."""
    model_id: str = Field(
        ..., 
        description="Bedrock model ID (e.g., anthropic.claude-v2:1)",
        examples=["anthropic.claude-v2:1", "anthropic.claude-3-sonnet-20240229-v1:0", "amazon.titan-text-express-v1"]
    )
    input_tokens: int = Field(
        1000, 
        description="Number of input tokens",
        ge=1,
        examples=[100, 1000, 10000]
    )
    output_tokens: int = Field(
        1000, 
        description="Number of output tokens",
        ge=0,
        examples=[100, 1000, 10000]
    )
    region: str = Field(
        "us-east-1", 
        description="AWS region code (e.g., us-east-1, eu-west-1)",
        examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
    )

class TotalImpactParam(BaseModel):
    """Parameters for total environmental impact calculation."""
    model_id: str = Field(
        ..., 
        description="Bedrock model ID (e.g., anthropic.claude-v2:1)",
        examples=["anthropic.claude-v2:1", "anthropic.claude-3-sonnet-20240229-v1:0", "amazon.titan-text-express-v1"]
    )
    input_tokens: int = Field(
        1000, 
        description="Number of input tokens",
        ge=1,
        examples=[100, 1000, 10000]
    )
    output_tokens: int = Field(
        1000, 
        description="Number of output tokens",
        ge=0,
        examples=[100, 1000, 10000]
    )
    region: str = Field(
        "us-east-1", 
        description="AWS region code (e.g., us-east-1, eu-west-1)",
        examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
    )
    duration_hours: float = Field(
        1.0, 
        description="Duration of usage in hours",
        ge=0.1,
        examples=[1.0, 24.0, 730.0]
    )
    utilization: float = Field(
        0.05, 
        description="Utilization factor (0-1)",
        ge=0.01,
        le=1.0,
        examples=[0.05, 0.25, 0.75]
    )

class CompareModelsParam(BaseModel):
    """Parameters for comparing models."""
    model_ids: List[str] = Field(
        ..., 
        description="List of Bedrock model IDs to compare",
        examples=[["anthropic.claude-v2:1", "amazon.titan-text-express-v1"]]
    )
    input_tokens: int = Field(
        1000, 
        description="Number of input tokens",
        ge=1,
        examples=[100, 1000, 10000]
    )
    output_tokens: int = Field(
        1000, 
        description="Number of output tokens",
        ge=0,
        examples=[100, 1000, 10000]
    )
    region: str = Field(
        "us-east-1", 
        description="AWS region code (e.g., us-east-1, eu-west-1)",
        examples=["us-east-1", "eu-west-1", "ap-southeast-2"]
    )
    duration_hours: float = Field(
        1.0, 
        description="Duration of usage in hours",
        ge=0.1,
        examples=[1.0, 24.0, 730.0]
    )
    utilization: float = Field(
        0.05, 
        description="Utilization factor (0-1)",
        ge=0.01,
        le=1.0,
        examples=[0.05, 0.25, 0.75]
    )

class FindRegionsParam(BaseModel):
    """Parameters for finding lowest impact regions."""
    model_id: str = Field(
        ..., 
        description="Bedrock model ID (e.g., anthropic.claude-v2:1)",
        examples=["anthropic.claude-v2:1", "anthropic.claude-3-sonnet-20240229-v1:0", "amazon.titan-text-express-v1"]
    )
    input_tokens: int = Field(
        1000, 
        description="Number of input tokens",
        ge=1,
        examples=[100, 1000, 10000]
    )
    output_tokens: int = Field(
        1000, 
        description="Number of output tokens",
        ge=0,
        examples=[100, 1000, 10000]
    )
    limit: int = Field(
        5, 
        description="Maximum number of regions to return",
        ge=1,
        le=50,
        examples=[3, 5, 10]
    )

class AWSCostParam(BaseModel):
    """Parameters for AWS cost analysis."""
    resources: Dict[str, Any] = Field(
        ..., 
        description="Dictionary of AWS resources to calculate the cost for"
    )
    usage_data: Dict[str, Any] = Field(
        ..., 
        description="Dictionary of AWS usage data"
    )
    days: int = Field(
        30, 
        description="Number of days for the analysis period",
        ge=1,
        le=365,
        examples=[7, 30, 90]
    )
    resource_id: Optional[str] = Field(
        None,
        description="Specific resource ID to filter results (optional)"
    )

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

# REGION COMPARISON TOOLS

class RegionComparisonInput(BaseModel):
    """
    Input parameters for region comparison.
    """
    regions: List[str] = Field(
        ...,
        description="List of AWS regions to compare",
        min_items=2,
        examples=[["us-east-1", "eu-west-1", "ap-southeast-2"]]
    )
    workload_type: Optional[str] = Field(
        None,
        description="Type of workload for more accurate recommendations",
        examples=["general", "compute-intensive", "memory-intensive"]
    )
    metrics: List[str] = Field(
        ["carbon", "water", "pue"],
        description="Environmental metrics to compare",
        examples=[["carbon", "water", "pue"]]
    )

@mcp.resource("config://app")
def get_config() -> str:
    """Return the server configuration."""
    return json.dumps({
        "name": "AWS Cost and Environmental Impact Server",
        "version": "1.0.0",
        "description": "MCP server for analyzing AWS cost, carbon emissions, and water usage"
    })

@mcp.prompt()
def system_prompt_for_agent(aws_account_id: Optional[str] = None) -> str:
    """
    Generate a system prompt for an AWS cost and environmental impact analysis agent.
    
    Args:
        aws_account_id: The AWS account ID to analyze (optional)
    
    Returns:
        System prompt for the agent
    """
    account_context = f"for AWS account {aws_account_id}" if aws_account_id else ""
    
    return f"""You are an AWS Cost and Environmental Impact analysis assistant {account_context}.

Your role is to help the user understand their AWS cloud spending and environmental impact, and to provide actionable recommendations for optimization.

You can:
1. Analyze AWS cost data across services, regions, and time periods
2. Calculate carbon footprints for EC2 instance usage
3. Calculate carbon and water footprints for AWS Bedrock model usage
4. Find AWS regions with the lowest carbon footprint or water usage
5. Compare environmental impact across different models or instance types
6. Provide recommendations for reducing costs and environmental impact

When answering questions, be specific and data-driven. Provide clear comparisons and recommendations based on the analysis results.

When discussing environmental impact, consider both carbon emissions and water usage, as well as regional factors like carbon intensity and water stress levels.

Remember to suggest optimization strategies like:
- Moving workloads to regions with lower carbon intensity or water usage
- Choosing more efficient instance types or models
- Optimizing token usage for AI models
- Implementing auto-scaling to reduce idle resources
- Considering both operational and embodied emissions in hardware selection

Always provide context to help users understand the environmental metrics (e.g., what the carbon emissions are equivalent to in everyday terms).
"""

# EC2 CARBON FOOTPRINT TOOLS

@mcp.tool()
async def calculate_ec2_carbon_footprint(params: EC2Param) -> Dict[str, Any]:
    """
    Calculate carbon footprint for EC2 instance usage.
    
    Args:
        params: Parameters for the calculation including:
            - instance_type: EC2 instance type (e.g., 't2.micro')
            - region: AWS region (default: 'us-east-1')
            - usage_hours: Hours of instance usage
    
    Returns:
        Dictionary with carbon footprint results
    """
    try:
        result = calculator.calculate_ec2_carbon(
            params.instance_type,
            params.region,
            params.hours,
            params.count
        )
        
        # Add environmental equivalents
        carbon_kg = result["carbon_emissions"]["emissions_kgco2e"]
        result["environmental_equivalents"] = calculator.get_environmental_equivalents(carbon_kg)
        
        return result
    except Exception as e:
        logger.error(f"Error calculating EC2 carbon footprint: {e}")
        return {"error": str(e)}

@mcp.tool()
async def find_lowest_carbon_ec2_regions(params: EC2Param) -> Dict[str, Any]:
    """
    Find AWS regions with the lowest carbon footprint for a specific EC2 instance type.
    
    Args:
        params: Parameters for the calculation including:
            - instance_type: EC2 instance type
            - usage_hours: Hours of instance usage
    
    Returns:
        Dictionary with regions ranked by carbon emissions
    """
    try:
        results = []
        count = params.count
        
        # Calculate carbon footprint for all regions
        for region in calculator.region_carbon_intensity.keys():
            try:
                # Call with just 3 parameters
                result = calculator.calculate_ec2_carbon(
                    params.instance_type, 
                    region, 
                    params.hours
                )
                
                # Scale for instance count if needed
                if count > 1:
                    result["count"] = count
                    
                    # Scale energy consumption
                    for key in ["energy_kwh", "total_facility_energy_kwh"]:
                        if key in result["energy_consumption"]:
                            result["energy_consumption"][key] *= count
                    
                    # Scale emissions
                    for key in ["emissions_gco2e", "emissions_kgco2e"]:
                        if key in result["carbon_emissions"]:
                            result["carbon_emissions"][key] *= count
                    
                    # Scale water usage
                    if "water_usage_liters" in result["water_usage"]:
                        result["water_usage"]["water_usage_liters"] *= count
                
                results.append(result)
            except Exception as e:
                logger.warning(f"Error calculating carbon footprint for region {region}: {e}")
        
        # Sort by emissions (lowest first)
        results.sort(key=lambda x: x["carbon_emissions"]["emissions_gco2e"])
        
        # Add savings percentage
        if results:
            highest_emissions = max(r["carbon_emissions"]["emissions_gco2e"] for r in results)
            
            for result in results:
                emissions = result["carbon_emissions"]["emissions_gco2e"]
                savings_percentage = ((highest_emissions - emissions) / highest_emissions) * 100 if highest_emissions > 0 else 0
                result["savings_percentage"] = savings_percentage
        
        return {
            "instance_type": params.instance_type,
            "usage_hours": params.hours,
            "count": count,
            "regions": results
        }
    except Exception as e:
        logger.error(f"Error finding lowest carbon EC2 regions: {e}")
        return {"error": str(e)}

# AI MODEL CARBON FOOTPRINT TOOLS

@mcp.tool()
async def calculate_model_carbon_footprint(params: ModelCarbonParam) -> Dict[str, Any]:
    """
    Calculate carbon footprint for AI model usage.
    
    Args:
        params: Parameters for the calculation including:
            - model_id: AI model identifier
            - region: AWS region (default: 'us-east-1')
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
    
    Returns:
        Dictionary with carbon footprint results
    """
    try:
        result = calculator.calculate_model_carbon(
            params.model_id,
            params.region,
            params.input_tokens,
            params.output_tokens
        )
        
        # Add environmental equivalents
        carbon_kg = result["emissions"]["total_emissions_kgco2e"]
        result["environmental_equivalents"] = calculator.get_environmental_equivalents(carbon_kg)
        
        return result
    except Exception as e:
        logger.error(f"Error calculating model carbon footprint: {e}")
        return {"error": str(e)}

@mcp.tool()
async def calculate_total_environmental_impact(params: TotalImpactParam) -> Dict[str, Any]:
    """
    Calculate total environmental impact (carbon, water, embodied) for AI model usage.
    
    Args:
        params: Parameters for the calculation including:
            - model_id: AI model identifier
            - region: AWS region (default: 'us-east-1')
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - duration_hours: Duration of usage in hours (default: 1.0)
            - utilization: Utilization factor 0-1 (default: 0.05)
    
    Returns:
        Dictionary with total impact results
    """
    try:
        result = calculator.calculate_total_impact(
            params.model_id,
            params.region,
            params.input_tokens,
            params.output_tokens,
            params.duration_hours,
            params.utilization
        )
        
        return result
    except Exception as e:
        logger.error(f"Error calculating total environmental impact: {e}")
        return {"error": str(e)}

@mcp.tool()
async def compare_model_environmental_impact(params: CompareModelsParam) -> Dict[str, Any]:
    """
    Compare environmental impact across multiple AI models.
    
    Args:
        params: Parameters for the comparison including:
            - model_ids: List of model identifiers to compare
            - region: AWS region (default: 'us-east-1')
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - duration_hours: Duration of usage in hours (default: 1.0)
            - utilization: Utilization factor 0-1 (default: 0.05)
    
    Returns:
        Dictionary with comparison results
    """
    try:
        result = calculator.compare_models(
            params.model_ids,
            params.region,
            params.input_tokens,
            params.output_tokens,
            params.duration_hours,
            params.utilization
        )
        
        return result
    except Exception as e:
        logger.error(f"Error comparing model environmental impact: {e}")
        return {"error": str(e)}

@mcp.tool()
async def find_lowest_carbon_regions(params: FindRegionsParam) -> Dict[str, Any]:
    """
    Find AWS regions with the lowest carbon footprint for a specific AI model.
    
    Args:
        params: Parameters for the search including:
            - model_id: AI model identifier
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - limit: Maximum number of regions to return (default: 5)
    
    Returns:
        Dictionary with regions ranked by carbon emissions
    """
    try:
        results = calculator.find_lowest_carbon_regions(
            params.model_id,
            params.input_tokens,
            params.output_tokens,
            params.limit
        )
        
        return {
            "model_id": params.model_id,
            "input_tokens": params.input_tokens,
            "output_tokens": params.output_tokens,
            "regions": results
        }
    except Exception as e:
        logger.error(f"Error finding lowest carbon regions: {e}")
        return {"error": str(e)}

@mcp.tool()
async def find_lowest_water_regions(params: FindRegionsParam) -> Dict[str, Any]:
    """
    Find AWS regions with the lowest water footprint for a specific AI model.
    
    Args:
        params: Parameters for the search including:
            - model_id: AI model identifier
            - input_tokens: Number of input tokens
            - output_tokens: Number of output tokens
            - limit: Maximum number of regions to return (default: 5)
    
    Returns:
        Dictionary with regions ranked by water usage
    """
    try:
        results = calculator.find_lowest_water_regions(
            params.model_id,
            params.input_tokens,
            params.output_tokens,
            params.limit
        )
        
        return {
            "model_id": params.model_id,
            "input_tokens": params.input_tokens,
            "output_tokens": params.output_tokens,
            "regions": results
        }
    except Exception as e:
        logger.error(f"Error finding lowest water regions: {e}")
        return {"error": str(e)}

# METADATA TOOLS

@mcp.tool()
async def get_supported_models() -> Dict[str, Any]:
    """
    Get a list of supported AI models.
    
    Returns:
        Dictionary with the list of supported model IDs
    """
    try:
        models = calculator.get_supported_models()
        return {"models": models, "count": len(models)}
    except Exception as e:
        logger.error(f"Error getting supported models: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_region_emissions_data() -> Dict[str, Any]:
    """
    Get carbon intensity data for all AWS regions.
    
    Returns:
        Dictionary with region carbon intensity data
    """
    try:
        regions = calculator.get_regions_with_intensity()
        
        # Sort by carbon intensity (lowest first)
        sorted_regions = dict(sorted(regions.items(), key=lambda item: item[1]))
        
        # Add carbon intensity category
        categorized_regions = {}
        for region, intensity in sorted_regions.items():
            if intensity < 50:
                category = "low"
            elif intensity < 200:
                category = "medium"
            elif intensity < 500:
                category = "high"
            else:
                category = "very_high"
            
            categorized_regions[region] = {
                "carbon_intensity_gco2e_kwh": intensity,
                "category": category
            }
        
        return {"regions": categorized_regions, "count": len(categorized_regions)}
    except Exception as e:
        logger.error(f"Error getting region emissions data: {e}")
        return {"error": str(e)}

@mcp.tool()
async def get_region_water_data() -> Dict[str, Any]:
    """
    Get water usage data for all AWS regions.
    
    Returns:
        Dictionary with region water usage data
    """
    try:
        water_usage = calculator.get_regions_with_water_usage()
        water_stress = calculator.region_water_stress
        
        # Combine data
        region_data = {}
        for region, wue in water_usage.items():
            region_data[region] = {
                "water_usage_effectiveness": wue,
                "water_stress_level": water_stress.get(region, "Unknown")
            }
        
        # Sort by water usage effectiveness (lowest first)
        sorted_regions = dict(sorted(region_data.items(), key=lambda item: item[1]["water_usage_effectiveness"]))
        
        return {"regions": sorted_regions, "count": len(sorted_regions)}
    except Exception as e:
        logger.error(f"Error getting region water data: {e}")
        return {"error": str(e)}

# REGION COMPARISON TOOLS

@mcp.tool()
async def compare_regions(params: RegionComparisonInput) -> Dict[str, Any]:
    """
    Compare environmental impact across different AWS regions.
    
    Args:
        params: Parameters for the comparison including:
            - baseline_region: The reference region to compare against (default: 'us-east-1')
            - target_regions: List of regions to compare (if empty, all regions will be compared)
            - workload_types: Types of workloads to consider ('ec2', 'bedrock')
            - compare_metrics: Metrics to compare ('carbon', 'water', 'pue')
    
    Returns:
        Dictionary with comparison results for regions
    """
    try:
        # If no target regions specified, use all regions
        if not params.target_regions:
            params.target_regions = list(calculator.region_carbon_intensity.keys())
        
        # Results containers
        results = {
            "baseline_region": params.baseline_region,
            "compared_regions": [],
            "metrics_compared": params.compare_metrics
        }
        
        # Get baseline metrics
        baseline_carbon = calculator.region_carbon_intensity.get(params.baseline_region, 0)
        baseline_pue = calculator.get_pue(params.baseline_region)
        baseline_water = calculator.get_water_usage(params.baseline_region)
        baseline_water_stress = calculator.get_water_stress(params.baseline_region)
        
        # Compare each region
        for region in params.target_regions:
            if region == params.baseline_region:
                continue
                
            try:
                # Get region metrics
                carbon = calculator.region_carbon_intensity.get(region, 0)
                pue = calculator.get_pue(region)
                water = calculator.get_water_usage(region)
                water_stress = calculator.get_water_stress(region)
                
                # Calculate differences
                carbon_diff = carbon - baseline_carbon
                carbon_pct = (carbon_diff / baseline_carbon) * 100 if baseline_carbon > 0 else 0
                
                pue_diff = pue - baseline_pue
                pue_pct = (pue_diff / baseline_pue) * 100 if baseline_pue > 0 else 0
                
                water_diff = water - baseline_water
                water_pct = (water_diff / baseline_water) * 100 if baseline_water > 0 else 0
                
                # Potential savings
                carbon_savings = -carbon_diff if carbon_diff < 0 else 0
                water_savings = -water_diff if water_diff < 0 else 0
                
                region_result = {
                    "region": region,
                    "metrics": {
                        "carbon_intensity": {
                            "value": carbon,
                            "unit": "gCO2e/kWh",
                            "difference": carbon_diff,
                            "percent_difference": carbon_pct,
                            "is_better": carbon < baseline_carbon
                        },
                        "pue": {
                            "value": pue,
                            "difference": pue_diff,
                            "percent_difference": pue_pct,
                            "is_better": pue < baseline_pue
                        },
                        "water_usage": {
                            "value": water,
                            "unit": "liters/kWh",
                            "difference": water_diff,
                            "percent_difference": water_pct,
                            "is_better": water < baseline_water
                        },
                        "water_stress": {
                            "value": water_stress,
                            "is_better": (water_stress == "Low" and baseline_water_stress != "Low") or
                                       (water_stress == "Medium" and baseline_water_stress in ["High", "Very High"]) or
                                       (water_stress == "High" and baseline_water_stress == "Very High")
                        }
                    },
                    "potential_savings": {
                        "carbon": carbon_savings,
                        "water": water_savings
                    }
                }
                
                results["compared_regions"].append(region_result)
            except Exception as e:
                logger.warning(f"Error comparing region {region}: {e}")
        
        # Sort by carbon savings (highest first)
        results["compared_regions"].sort(key=lambda x: x["potential_savings"]["carbon"], reverse=True)
        
        return results
    except Exception as e:
        logger.error(f"Error comparing regions: {e}")
        return {"error": str(e)}

# AWS COST ANALYSIS TOOLS

@mcp.tool()
async def get_aws_cost_summary(params: AWSCostParam) -> Dict[str, Any]:
    """
    Get a summary of AWS costs for the specified time period.
    
    Args:
        params: Parameters for the cost analysis including:
            - days: Number of days to analyze (default: 30)
            - region: Filter by AWS region (optional)
            - service: Filter by AWS service (optional)
    
    Returns:
        Dictionary with cost summary data
    """
    try:
        # Create AWS Cost Explorer client
        ce_client = boto3.client('ce')
        
        # Calculate time period
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=params.days)
        
        # Format dates for Cost Explorer API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Define filters
        filters = {"Dimensions": {"Key": "RECORD_TYPE", "Values": ["Usage"]}}
        
        # Add region filter if specified
        if params.region:
            filters["Dimensions"]["Key"] = "REGION"
            filters["Dimensions"]["Values"] = [params.region]
        
        # Add service filter if specified
        if params.service:
            filters["Dimensions"]["Key"] = "SERVICE"
            filters["Dimensions"]["Values"] = [params.service]
        
        # Get cost and usage data
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date_str,
                'End': end_date_str
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost', 'UsageQuantity'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Filter=filters
        )
        
        # Process results
        results = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                currency = group['Metrics']['UnblendedCost']['Unit']
                
                results.append({
                    'date': date,
                    'service': service,
                    'cost': cost,
                    'currency': currency
                })
        
        # Create a DataFrame for analysis
        df = pd.DataFrame(results)
        
        # Calculate total cost by service
        service_totals = df.groupby('service')['cost'].sum().reset_index()
        service_totals = service_totals.sort_values('cost', ascending=False)
        
        # Calculate daily totals
        daily_totals = df.groupby('date')['cost'].sum().reset_index()
        
        # Calculate overall total
        total_cost = df['cost'].sum()
        
        return {
            'total_cost': total_cost,
            'currency': results[0]['currency'] if results else 'USD',
            'time_period': {
                'start_date': start_date_str,
                'end_date': end_date_str,
                'days': params.days
            },
            'service_totals': service_totals.to_dict('records'),
            'daily_totals': daily_totals.to_dict('records'),
            'filters': {
                'region': params.region,
                'service': params.service
            }
        }
    except Exception as e:
        logger.error(f"Error getting AWS cost summary: {e}")
        return {"error": str(e)}

# EC2 PRICING AND EFFICIENCY TOOLS

@mcp.tool()
async def get_ec2_pricing_and_efficiency(params: EC2PricingParam) -> Dict[str, Any]:
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
        # Create AWS Pricing client (only available in us-east-1 and ap-south-1)
        pricing_client = boto3.client('pricing', region_name='us-east-1')
        
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
        logger.error(f"Error getting EC2 pricing: {str(e)}")
        return {
            "instance_type": params.instance_type,
            "region": params.region,
            "os": params.os,
            "error": str(e)
        }

@mcp.tool()
async def compare_ec2_instance_pricing(params: EC2CompareParam) -> Dict[str, Any]:
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
            
            pricing_data = await get_ec2_pricing_and_efficiency(instance_params)
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
        logger.error(f"Error comparing EC2 instances: {str(e)}")
        return {
            "region": params.region,
            "os": params.os,
            "error": str(e)
        }

@mcp.tool()
async def find_best_region_for_ec2_instance(params: EC2RegionCompareParam) -> Dict[str, Any]:
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
            
            region_data = await get_ec2_pricing_and_efficiency(region_params)
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
        logger.error(f"Error finding best region: {str(e)}")
        return {
            "instance_type": params.instance_type,
            "os": params.os,
            "error": str(e)
        }

def main():
    """Run the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AWS Cost and Environmental Impact Analyzer")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--transport", type=str, default="stdio", 
                        choices=["stdio", "sse"], 
                        help="Transport type (stdio, sse)")
    parser.add_argument("--host", type=str, default="0.0.0.0", 
                        help="Host to bind to (for sse transport)")
    
    args = parser.parse_args()
    
    print(f"Starting AWS Cost and Environmental Impact Analyzer")
    print(f"Transport: {args.transport}")
    print(f"Data directory: {calculator.data_dir}")
    print(f"Loaded {len(calculator.region_carbon_intensity)} regions with carbon intensity data")
    print(f"Loaded {len(calculator.model_energy_consumption)} AI models with energy consumption data")
    
    # Run the server with the specified transport - port parameter is not supported in FastMCP.run()
    mcp.run(transport=args.transport)

if __name__ == "__main__":
    main() 
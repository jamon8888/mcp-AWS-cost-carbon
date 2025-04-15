#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
HTTP API Wrapper for AWS Cost and Environmental Impact Analyzer

This script creates a FastAPI wrapper around the AWS environmental calculators to expose HTTP endpoints.
"""

import os
import json
import asyncio
import traceback
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys

# Create FastAPI app
app = FastAPI(title="AWS Cost & Environmental Impact Analysis API")

# Add parent directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the calculators
from core.aws_cost_carbon_calculator import AWSEnvironmentalCalculator
from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator

# Initialize fresh calculator instances
calculator = AWSEnvironmentalCalculator()
bedrock_calculator = BedrockCarbonCalculator()

class EC2Request(BaseModel):
    instance_type: str
    region: str
    hours: float = 720.0
    count: int = 1

class ModelRequest(BaseModel):
    model_id: str
    region: str = "us-east-1"
    input_tokens: int = 1000
    output_tokens: int = 1000

@app.get("/")
async def root():
    return {
        "name": "AWS Cost and Environmental Impact API",
        "version": "1.0.0",
        "description": "HTTP API for analyzing AWS cost, carbon emissions, and water usage"
    }

@app.post("/api/ec2/carbon")
async def calculate_ec2_carbon(request: EC2Request):
    """Calculate carbon footprint for EC2 instance usage."""
    try:
        # Get the request parameters
        instance_type = request.instance_type
        region = request.region
        usage_hours = request.hours
        count = request.count
        
        # Call the calculator with just the 3 required parameters
        result = calculator.calculate_ec2_carbon(instance_type, region, usage_hours)
        
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
        
        # Add environmental equivalents
        carbon_kg = result["carbon_emissions"]["emissions_kgco2e"]
        result["environmental_equivalents"] = calculator.get_environmental_equivalents(carbon_kg)
        
        return result
    except Exception as e:
        # Get the full traceback for better error diagnosis
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\nTraceback: {tb}")

@app.post("/api/models/carbon")
async def calculate_model_carbon(request: ModelRequest):
    """Calculate carbon footprint for AI model usage."""
    try:
        result = calculator.calculate_model_carbon(
            request.model_id,
            request.region,
            request.input_tokens,
            request.output_tokens
        )
        
        # Add environmental equivalents
        carbon_kg = result["emissions"]["total_emissions_kgco2e"]
        result["environmental_equivalents"] = calculator.get_environmental_equivalents(carbon_kg)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
async def get_supported_models():
    """Get a list of supported AI models."""
    try:
        models = calculator.get_supported_models()
        return {"models": models, "count": len(models)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/regions/emissions")
async def get_region_emissions_data():
    """Get carbon intensity data for all AWS regions."""
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/regions/water")
async def get_region_water_data():
    """Get water usage data for all AWS regions."""
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
        raise HTTPException(status_code=500, detail=str(e))

# Add main function for entry point
def main():
    import uvicorn
    import argparse
    import socket
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="AWS Cost and Environmental Impact HTTP API")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    
    args = parser.parse_args()
    
    # Check if port is available
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    # Find an available port if the specified one is in use
    port = args.port
    if is_port_in_use(port):
        print(f"Port {port} is already in use.")
        for new_port in range(port + 1, port + 10):
            if not is_port_in_use(new_port):
                port = new_port
                print(f"Using port {port} instead.")
                break
        else:
            print(f"Could not find an available port. Will try with port {port} anyway.")
    
    # Run the server with uvicorn
    try:
        print(f"Starting uvicorn server on host 0.0.0.0 and port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print(f"Failed to start server: {e}")
        # Try another port
        try:
            new_port = port + 1
            print(f"Trying port {new_port} instead...")
            uvicorn.run(app, host="0.0.0.0", port=new_port)
        except Exception as e2:
            print(f"Still failed to start server: {e2}")
            sys.exit(1)

if __name__ == "__main__":
    main() 
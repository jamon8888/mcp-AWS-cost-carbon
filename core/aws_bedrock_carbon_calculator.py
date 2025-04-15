#!/usr/bin/env python3
"""
AWS Bedrock Carbon Calculator
--------------------------
A calculator for AWS Bedrock models energy consumption and carbon footprints.
"""

import os
import json
import math
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from .data_providers.data_loader import DataLoader # Import DataLoader

class BedrockCarbonCalculator:
    """Calculator for AWS Bedrock models energy consumption and carbon footprints."""
    
    def __init__(self, data_dir: str = "data", mock_mode: bool = False):
        """
        Initialize the calculator with data directory.
        
        Args:
            data_dir: Directory containing data files
            mock_mode: Whether to use mock data
        """
        self.data_dir = data_dir
        self.mock_mode = mock_mode
        # Use DataLoader for consistent data loading
        self.data_loader = DataLoader(data_dir=self.data_dir, mock_mode=self.mock_mode)

        # Load data using DataLoader
        self.region_carbon_intensity = self.data_loader.load_region_data("carbon_intensity")
        self.region_pue = self.data_loader.load_region_data("pue")
        self.region_water_usage = self.data_loader.load_region_data("water_usage")
        self.region_water_stress = self.data_loader.load_region_data("water_stress")
        self.model_energy_consumption = self.data_loader.load_model_data("energy_consumption")
        
        # Default values
        self.default_carbon_intensity = 500.0  # gCO2e/kWh
        self.default_pue = 1.5
        self.default_water_usage = 1.8  # liters/kWh
        self.default_water_stress = "Medium"
        
        # Define BEDROCK_MODEL_ENERGY mapping for model energy profiles
        self.BEDROCK_MODEL_ENERGY = {
            # Anthropic models
            "anthropic.claude-3-opus-20240229-v1:0": {
                "input_kwh_per_million_tokens": 0.08,
                "output_kwh_per_million_tokens": 0.24
            },
            "anthropic.claude-3-sonnet-20240229-v1:0": {
                "input_kwh_per_million_tokens": 0.05,
                "output_kwh_per_million_tokens": 0.15
            },
            "anthropic.claude-3-haiku-20240307-v1:0": {
                "input_kwh_per_million_tokens": 0.03,
                "output_kwh_per_million_tokens": 0.09
            },
            "anthropic.claude-2.1": {
                "input_kwh_per_million_tokens": 0.06,
                "output_kwh_per_million_tokens": 0.18
            },
            "anthropic.claude-2.0": {
                "input_kwh_per_million_tokens": 0.06,
                "output_kwh_per_million_tokens": 0.18
            },
            "anthropic.claude-instant-1.2": {
                "input_kwh_per_million_tokens": 0.03,
                "output_kwh_per_million_tokens": 0.09
            },
            # Amazon models
            "amazon.titan-text-express-v1:0": {
                "input_kwh_per_million_tokens": 0.04,
                "output_kwh_per_million_tokens": 0.12
            },
            "amazon.titan-text-lite-v1:0": {
                "input_kwh_per_million_tokens": 0.02,
                "output_kwh_per_million_tokens": 0.06
            },
            # Meta models
            "meta.llama3-70b-instruct-v1:0": {
                "input_kwh_per_million_tokens": 0.05,
                "output_kwh_per_million_tokens": 0.15
            },
            # Default for unknown models
            "default": {
                "input_kwh_per_million_tokens": 0.05,
                "output_kwh_per_million_tokens": 0.15
            }
        }
    
    def get_carbon_intensity(self, region: str) -> float:
        """Get carbon intensity for a region (gCO2e/kWh)."""
        return self.region_carbon_intensity.get(region, self.default_carbon_intensity)
    
    def get_pue(self, region: str) -> float:
        """Get PUE (Power Usage Effectiveness) for a region."""
        return self.region_pue.get(region, self.default_pue)
    
    def get_water_usage(self, region: str) -> float:
        """Get water usage for a region (liters/kWh)."""
        return self.region_water_usage.get(region, self.default_water_usage)
    
    def get_water_stress(self, region: str) -> str:
        """Get water stress level for a region."""
        return self.region_water_stress.get(region, self.default_water_stress)

    def calculate_energy_consumption(self, model_id: str, usage_data: Dict[str, Any]) -> float:
        """Calculate energy consumption for a model (kWh)."""
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        
        # Get energy consumption data for this model
        model_data = self.model_energy_consumption.get(model_id, self.model_energy_consumption.get('default', {}))
        
        # Get energy consumption per million tokens
        input_kwh_per_million = model_data.get("input_kwh_per_million_tokens", 0.05)
        output_kwh_per_million = model_data.get("output_kwh_per_million_tokens", 0.15)
        
        # Calculate energy consumption
        input_energy = (input_tokens / 1_000_000) * input_kwh_per_million
        output_energy = (output_tokens / 1_000_000) * output_kwh_per_million
        
        return input_energy + output_energy

    def calculate_carbon_footprint(
        self, 
        model_id: str, 
        region: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Calculate the carbon footprint for a specific model usage.
        
        Args:
            model_id: The AWS Bedrock model identifier
            region: The AWS region where the model is used
            input_tokens: Number of input tokens processed
            output_tokens: Number of output tokens generated
            
        Returns:
            Dictionary with carbon footprint information
        """
        # Validate inputs
        if model_id not in self.BEDROCK_MODEL_ENERGY:
            raise ValueError(f"Unknown model: {model_id}")
        
        if region not in self.region_carbon_intensity:
            raise ValueError(f"Unknown region: {region}")
        
        if input_tokens < 0 or output_tokens < 0:
            raise ValueError("Token counts must be non-negative")
        
        # Get energy consumption per token
        energy_profile = self.BEDROCK_MODEL_ENERGY[model_id]
        
        # Calculate operational energy consumption in watt-hours (Wh)
        input_energy_wh = energy_profile["input_kwh_per_million_tokens"] * input_tokens * 1000
        output_energy_wh = energy_profile["output_kwh_per_million_tokens"] * output_tokens * 1000
        total_energy_wh = input_energy_wh + output_energy_wh
        
        # Convert to kilowatt-hours (kWh)
        total_energy_kwh = total_energy_wh / 1000
        
        # Get carbon intensity for the region in gCO2e/kWh
        carbon_intensity = self.region_carbon_intensity[region]
        
        # Calculate operational emissions in gCO2e
        operational_emissions = total_energy_kwh * carbon_intensity
        
        # Calculate percentages
        operational_percentage = 0
        training_percentage = 0
        if operational_emissions > 0:
            operational_percentage = (operational_emissions / operational_emissions) * 100
        
        # Prepare the result
        result = {
            "model_id": model_id,
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "energy_consumption": {
                "input_energy_wh": input_energy_wh,
                "output_energy_wh": output_energy_wh,
                "total_energy_wh": total_energy_wh,
                "total_energy_kwh": total_energy_kwh
            },
            "emissions": {
                "operational_emissions_gco2e": operational_emissions,
                "operational_percentage": operational_percentage
            },
            "carbon_intensity_gco2e_kwh": carbon_intensity
        }
        
        return result
    
    def compare_models(
        self, 
        model_ids: List[str], 
        region: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        Compare carbon footprints across different models.
        
        Args:
            model_ids: List of AWS Bedrock model identifiers
            region: The AWS region where the models are used
            input_tokens: Number of input tokens processed
            output_tokens: Number of output tokens generated
            
        Returns:
            Dictionary with comparison results
        """
        if not model_ids:
            raise ValueError("Model IDs list cannot be empty")
        
        # Calculate carbon footprint for each model
        results = []
        for model_id in model_ids:
            try:
                result = self.calculate_carbon_footprint(
                    model_id, region, input_tokens, output_tokens
                )
                results.append(result)
            except ValueError as e:
                # Skip invalid models but provide an error message
                results.append({
                    "model_id": model_id,
                    "error": str(e)
                })
        
        # Sort results by total emissions (lowest first)
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            valid_results.sort(key=lambda x: x["emissions"]["operational_emissions_gco2e"])
            
            # Find the model with the lowest emissions
            lowest_emissions_model = valid_results[0]
            
            # Calculate relative emissions compared to the lowest
            for result in valid_results:
                if result != lowest_emissions_model:
                    relative_emissions = (
                        result["emissions"]["operational_emissions_gco2e"] / 
                        lowest_emissions_model["emissions"]["operational_emissions_gco2e"]
                    )
                    result["relative_emissions"] = relative_emissions
                else:
                    result["relative_emissions"] = 1.0
        
        # Prepare the comparison result
        comparison = {
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "results": results
        }
        
        return comparison
    
    def find_lowest_carbon_regions(
        self, 
        model_id: str, 
        input_tokens: int, 
        output_tokens: int, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find AWS regions with the lowest carbon footprint for a specific model.
        
        Args:
            model_id: The AWS Bedrock model identifier
            input_tokens: Number of input tokens processed
            output_tokens: Number of output tokens generated
            limit: Maximum number of regions to return
            
        Returns:
            List of regions with the lowest carbon footprint
        """
        if model_id not in self.model_energy_consumption:
            raise ValueError(f"Unknown model: {model_id}")
        
        if limit <= 0:
            raise ValueError("Limit must be positive")
        
        # Calculate carbon footprint for each region
        results = []
        for region in self.region_carbon_intensity:
            result = self.calculate_carbon_footprint(
                model_id, region, input_tokens, output_tokens
            )
            results.append(result)
        
        # Sort results by total emissions (lowest first)
        results.sort(key=lambda x: x["emissions"]["operational_emissions_gco2e"])
        
        # Return the top N regions with the lowest carbon footprint
        return results[:limit]
    
    def calculate_savings(
        self, 
        model_id: str, 
        current_region: str, 
        target_region: str, 
        monthly_input_tokens: int, 
        monthly_output_tokens: int
    ) -> Dict[str, Any]:
        """
        Calculate potential carbon savings by switching regions.
        
        Args:
            model_id: The AWS Bedrock model identifier
            current_region: Current AWS region
            target_region: Target AWS region to compare against
            monthly_input_tokens: Monthly input token volume
            monthly_output_tokens: Monthly output token volume
            
        Returns:
            Dictionary with savings information
        """
        # Calculate current carbon footprint
        current_footprint = self.calculate_carbon_footprint(
            model_id, current_region, monthly_input_tokens, monthly_output_tokens
        )
        
        # Calculate target carbon footprint
        target_footprint = self.calculate_carbon_footprint(
            model_id, target_region, monthly_input_tokens, monthly_output_tokens
        )
        
        # Calculate savings
        emissions_saved = (
            current_footprint["emissions"]["operational_emissions_gco2e"] - 
            target_footprint["emissions"]["operational_emissions_gco2e"]
        )
        
        savings_percentage = (
            emissions_saved / current_footprint["emissions"]["operational_emissions_gco2e"]
        ) * 100 if current_footprint["emissions"]["operational_emissions_gco2e"] > 0 else 0
        
        # Convert to kg and tonnes for more readable values
        emissions_saved_kg = emissions_saved / 1000
        emissions_saved_tonnes = emissions_saved / 1000000
        
        # Prepare the result
        result = {
            "model_id": model_id,
            "current_region": current_region,
            "target_region": target_region,
            "monthly_input_tokens": monthly_input_tokens,
            "monthly_output_tokens": monthly_output_tokens,
            "current_emissions_gco2e": current_footprint["emissions"]["operational_emissions_gco2e"],
            "target_emissions_gco2e": target_footprint["emissions"]["operational_emissions_gco2e"],
            "emissions_saved_gco2e": emissions_saved,
            "emissions_saved_kg": emissions_saved_kg,
            "emissions_saved_tonnes": emissions_saved_tonnes,
            "savings_percentage": savings_percentage,
            "current_carbon_intensity": current_footprint["carbon_intensity_gco2e_kwh"],
            "target_carbon_intensity": target_footprint["carbon_intensity_gco2e_kwh"]
        }
        
        return result

    def get_environmental_context(self, total_emissions_kg: float) -> Dict[str, Any]:
        """
        Get environmental impact equivalents to provide context.
        
        Args:
            total_emissions_kg: Total carbon emissions in kg CO2e
            
        Returns:
            Dictionary of environmental equivalents
        """
        # Environmental equivalents
        # Source: EPA Greenhouse Gas Equivalencies Calculator
        equivalents = {
            "miles_driven": total_emissions_kg * 2.5,  # 0.4 kg CO2e per mile
            "smartphone_charges": total_emissions_kg * 112.5,  # 0.008 kg CO2e per full charge
            "trees_month": total_emissions_kg / 20,  # ~20 kg CO2 sequestered by a tree per month
            "flight_miles": total_emissions_kg * 2.2,  # 0.45 kg CO2e per passenger mile
        }
        
        # Calculate equivalents for more relatable context
        return {
            "car_miles_equivalent": round(equivalents["miles_driven"], 1),
            "smartphone_charges_equivalent": round(equivalents["smartphone_charges"], 0),
            "tree_months_sequestration": round(equivalents["trees_month"], 2),
            "flight_miles_equivalent": round(equivalents["flight_miles"], 1)
        }

# Example usage
if __name__ == "__main__":
    calculator = BedrockCarbonCalculator()
    
    # Example 1: Calculate carbon footprint for Claude 3 Sonnet
    result = calculator.calculate_carbon_footprint(
        "claude-3-sonnet",
        "us-east-1",
        1000,  # 1000 input tokens
        500    # 500 output tokens
    )
    print("Carbon footprint for Claude 3 Sonnet in us-east-1:")
    print(f"  Total emissions: {result['emissions']['operational_emissions_gco2e']:.6f} gCO2e")
    print(f"  Energy consumption: {result['energy_consumption']['total_energy_wh']:.6f} Wh")
    
    # Example 2: Find regions with the lowest carbon footprint
    lowest_regions = calculator.find_lowest_carbon_regions(
        "claude-3-sonnet",
        1000,
        500,
        3  # Top 3 regions
    )
    print("\nTop 3 regions with lowest carbon footprint:")
    for i, region in enumerate(lowest_regions):
        print(f"  {i+1}. {region['region']}: {region['emissions']['operational_emissions_gco2e']:.6f} gCO2e")
    
    # Example 3: Compare models
    comparison = calculator.compare_models(
        [
            "claude-3-sonnet",
            "claude-3-opus",
            "gpt-4-turbo"
        ],
        "us-east-1",
        1000,
        500
    )
    print("\nModel comparison in us-east-1:")
    for result in comparison["results"]:
        print(f"  {result['model_id']}: {result['emissions']['operational_emissions_gco2e']:.6f} gCO2e") 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AWS Cost and Environmental Impact Calculator

A unified calculator for analyzing AWS cost data, carbon emissions,
and water usage across all AWS services including EC2, Bedrock, and more.
"""

import os
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AWSEnvironmentalCalculator:
    """Unified calculator for AWS cost, carbon emissions, and water usage."""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the calculator with data from files.
        
        Args:
            data_dir: Directory containing data files
        """
        # Set default data directory if not provided
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        
        self.data_dir = data_dir
        
        # Load region-specific data
        self.region_carbon_intensity = self._load_region_carbon_intensity()
        self.region_water_usage = self._load_region_water_usage()  
        self.region_pue = self._load_region_pue_data()
        self.region_water_stress = self._load_region_water_stress_data()
        
        # Default values if region not found
        self.DEFAULT_CARBON_INTENSITY = 380.0  # gCO2e/kWh
        self.DEFAULT_WUE = 1.8  # L/kWh
        self.DEFAULT_PUE = 1.2  # ratio
        
        # Load AWS service-specific data
        self.model_energy_consumption = self._load_model_energy_data()
        self.model_training_emissions = self._load_training_emissions_data()
        self.instance_power_consumption = self._load_instance_power_data()
        self.hardware_embodied_emissions = self._load_hardware_emissions_data()
        
        # Mapping of model IDs to hardware requirements
        self.model_hardware_map = self._load_hardware_mapping()
        
        # Default hardware lifecycle (years)
        self.hardware_lifecycle = 4.0
    
    def _load_region_carbon_intensity(self) -> Dict[str, float]:
        """Load carbon intensity data for AWS regions (gCO2e/kWh)."""
        intensity_data = {}
        csv_path = os.path.join(self.data_dir, "region_carbon_intensity.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        region, intensity = row[0], float(row[1])
                        intensity_data[region] = intensity
            
            logger.info(f"Loaded carbon intensity data for {len(intensity_data)} regions")
        except Exception as e:
            logger.warning(f"Could not load region carbon intensity data: {e}")
            # Fallback to basic values for major regions
            intensity_data = {
                "us-east-1": 379.1,
                "us-east-2": 429.0, 
                "us-west-1": 204.0,
                "us-west-2": 136.3,
                "eu-west-1": 316.0,
                "eu-north-1": 8.6,
                "eu-central-1": 311.0,
                "ap-northeast-1": 506.0,
                "ap-southeast-1": 408.0,
                "ap-south-1": 708.0
            }
        
        return intensity_data
    
    def _load_region_water_usage(self) -> Dict[str, float]:
        """Load water usage effectiveness data for AWS regions (L/kWh)."""
        water_data = {}
        csv_path = os.path.join(self.data_dir, "region_water_usage.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        region, wue = row[0], float(row[1])
                        water_data[region] = wue
            
            logger.info(f"Loaded water usage data for {len(water_data)} regions")
        except Exception as e:
            logger.warning(f"Could not load region water usage data: {e}")
            # Fallback to basic values for major regions
            water_data = {
                "us-east-1": 1.8,
                "us-east-2": 1.9,
                "us-west-1": 2.1,
                "us-west-2": 1.7,
                "eu-west-1": 1.5,
                "eu-central-1": 1.6,
                "eu-north-1": 1.1
            }
        
        return water_data
    
    def _load_region_pue_data(self) -> Dict[str, float]:
        """Load power usage effectiveness data for AWS regions."""
        pue_data = {}
        csv_path = os.path.join(self.data_dir, "region_pue.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        region, pue = row[0], float(row[1])
                        pue_data[region] = pue
            
            logger.info(f"Loaded PUE data for {len(pue_data)} regions")
        except Exception as e:
            logger.warning(f"Could not load region PUE data: {e}")
            # Fallback to basic values for major regions
            pue_data = {
                "us-east-1": 1.2,
                "us-east-2": 1.15,
                "us-west-1": 1.25,
                "us-west-2": 1.18,
                "eu-west-1": 1.15,
                "eu-north-1": 1.07,
                "eu-central-1": 1.2
            }
        
        return pue_data
    
    def _load_region_water_stress_data(self) -> Dict[str, str]:
        """Load water stress level data for AWS regions."""
        water_stress_data = {}
        csv_path = os.path.join(self.data_dir, "region_water_stress.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 2:
                        region, stress_level = row[0], row[1]
                        water_stress_data[region] = stress_level
            
            logger.info(f"Loaded water stress data for {len(water_stress_data)} regions")
        except Exception as e:
            logger.warning(f"Could not load region water stress data: {e}")
            # Fallback to estimated values for major regions
            water_stress_data = {
                "us-east-1": "Medium",
                "us-east-2": "Medium",
                "us-west-1": "High",
                "us-west-2": "Medium",
                "eu-west-1": "Low",
                "eu-north-1": "Low"
            }
        
        return water_stress_data
    
    def _load_model_energy_data(self) -> Dict[str, Dict[str, float]]:
        """Load energy consumption data for AI models."""
        energy_data = {}
        csv_path = os.path.join(self.data_dir, "model_energy_consumption.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:
                        model_id, input_energy, output_energy = row[0], float(row[1]), float(row[2])
                        energy_data[model_id] = {
                            "input_kwh_per_token": input_energy / 1000,  # Convert Wh to kWh
                            "output_kwh_per_token": output_energy / 1000
                        }
            
            logger.info(f"Loaded energy data for {len(energy_data)} models")
        except Exception as e:
            logger.warning(f"Could not load model energy data: {e}")
            # Fallback to basic values for common models
            energy_data = {
                "anthropic.claude-3-sonnet-20240229-v1:0": {
                    "input_kwh_per_token": 2.05e-7,
                    "output_kwh_per_token": 2.05e-7
                },
                "anthropic.claude-3-haiku-20240307-v1:0": {
                    "input_kwh_per_token": 1.25e-7,
                    "output_kwh_per_token": 1.25e-7
                }
            }
        
        return energy_data
    
    def _load_training_emissions_data(self) -> Dict[str, Dict[str, float]]:
        """Load training emissions data for models."""
        training_data = {}
        csv_path = os.path.join(self.data_dir, "model_training_footprint.csv")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    if len(row) >= 3:
                        model_id = row[0]
                        total_emissions = float(row[1])
                        expected_inferences = float(row[2])
                        training_data[model_id] = {
                            "total_emissions_gco2e": total_emissions,
                            "expected_inferences": expected_inferences
                        }
            
            logger.info(f"Loaded training emissions data for {len(training_data)} models")
        except Exception as e:
            logger.warning(f"Could not load training emissions data: {e}")
            # Basic fallback values
            training_data = {
                "anthropic.claude-3-sonnet-20240229-v1:0": {
                    "total_emissions_gco2e": 650000000,
                    "expected_inferences": 18000000000
                },
                "anthropic.claude-3-haiku-20240307-v1:0": {
                    "total_emissions_gco2e": 260000000,
                    "expected_inferences": 20000000000
                }
            }
        
        return training_data
    
    def _load_instance_power_data(self) -> Dict[str, float]:
        """Load power consumption data for EC2 instance types (in watts)."""
        # For simplicity, using hardcoded values as defaults
        # In a real implementation, this would load from a CSV file
        return {
            't2.micro': 2.5,
            't2.small': 5,
            't2.medium': 10,
            't2.large': 20,
            'm5.large': 40,
            'm5.xlarge': 80,
            'm5.2xlarge': 160,
            'c5.large': 50,
            'c5.xlarge': 100,
            'r5.large': 55,
            'r5.xlarge': 110,
            'p3.2xlarge': 650,
            'p3.8xlarge': 2600,
            'p4d.24xlarge': 8000
        }
    
    def _load_hardware_emissions_data(self) -> Dict[str, float]:
        """Load embodied carbon emissions data for hardware components."""
        # For simplicity, using hardcoded values as defaults
        return {
            "cpu": {
                "small": 320,     # Small CPU (kgCO2e)
                "medium": 720,    # Medium CPU
                "large": 1250     # Large CPU
            },
            "gpu": {
                "a10g": 1450,      # NVIDIA A10G (kgCO2e)
                "a100": 2850,      # NVIDIA A100
                "h100": 3750       # NVIDIA H100
            },
            "memory": 7.5,        # Per 16GB module (kgCO2e)
            "ssd": 85,            # Per 1TB SSD (kgCO2e)
            "hdd": 35,            # Per 1TB HDD (kgCO2e)
            "server_chassis": 650  # Server chassis and other components (kgCO2e)
        }
    
    def _load_hardware_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Load mapping of model IDs to hardware requirements."""
        # Default hardware profile for common models
        hardware_map = {
            "anthropic.claude-3-opus-20240229-v1:0": {
                "gpu_type": "a100",
                "gpu_count": 8,
                "cpu_type": "large",
                "memory_gb": 1024,
                "storage_tb": 4.0,
                "server_count": 1.0
            },
            "anthropic.claude-3-sonnet-20240229-v1:0": {
                "gpu_type": "a100",
                "gpu_count": 4,
                "cpu_type": "medium",
                "memory_gb": 512,
                "storage_tb": 2.0,
                "server_count": 0.5
            },
            "anthropic.claude-3-haiku-20240307-v1:0": {
                "gpu_type": "a10g",
                "gpu_count": 2,
                "cpu_type": "medium",
                "memory_gb": 256,
                "storage_tb": 1.0,
                "server_count": 0.2
            },
            "default": {
                "gpu_type": "a10g",
                "gpu_count": 2,
                "cpu_type": "medium",
                "memory_gb": 256,
                "storage_tb": 1.0,
                "server_count": 0.2
            }
        }
        
        return hardware_map
    
    # EC2 CARBON FOOTPRINT CALCULATIONS
    
    def calculate_ec2_carbon(self, instance_type: str, region: str, 
                            usage_hours: float) -> Dict[str, Any]:
        """
        Calculate carbon footprint for EC2 instance usage.
        
        Args:
            instance_type: EC2 instance type (e.g., 't2.micro')
            region: AWS region (e.g., 'us-east-1')
            usage_hours: Hours of instance usage
            
        Returns:
            Dictionary with carbon footprint results
        """
        # Get power consumption for instance type (watts)
        power_watts = self.instance_power_consumption.get(instance_type, 10)
        
        # Convert watts to kilowatts and multiply by hours to get kWh
        energy_kwh = (power_watts / 1000) * usage_hours
        
        # Get PUE for the region
        pue = self.region_pue.get(region, self.DEFAULT_PUE)
        
        # Apply PUE to get total data center energy
        total_energy_kwh = energy_kwh * pue
        
        # Get carbon intensity for the region (gCO2e/kWh)
        carbon_intensity = self.region_carbon_intensity.get(region, self.DEFAULT_CARBON_INTENSITY)
        
        # Calculate carbon emissions in grams CO2e
        carbon_emissions_grams = total_energy_kwh * carbon_intensity
        
        # Calculate water usage
        wue = self.region_water_usage.get(region, self.DEFAULT_WUE)
        water_usage_liters = total_energy_kwh * wue
        
        # Get water stress level
        water_stress_level = self.region_water_stress.get(region, "Unknown")
        
        # Format result
        result = {
            "instance_type": instance_type,
            "region": region,
            "usage_hours": usage_hours,
            "energy_consumption": {
                "instance_power_watts": power_watts,
                "energy_kwh": energy_kwh,
                "pue": pue,
                "total_facility_energy_kwh": total_energy_kwh
            },
            "carbon_emissions": {
                "carbon_intensity_gco2e_kwh": carbon_intensity,
                "emissions_gco2e": carbon_emissions_grams,
                "emissions_kgco2e": carbon_emissions_grams / 1000
            },
            "water_usage": {
                "water_usage_effectiveness": wue,
                "water_usage_liters": water_usage_liters,
                "water_stress_level": water_stress_level
            }
        }
        
        return result
    
    # AI MODEL CARBON FOOTPRINT CALCULATIONS
    
    def calculate_model_carbon(self, model_id: str, region: str, 
                              input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """
        Calculate carbon footprint for AI model usage.
        
        Args:
            model_id: Model identifier (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')
            region: AWS region (e.g., 'us-east-1')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary with carbon footprint results
        """
        # Validate model
        if model_id not in self.model_energy_consumption:
            model_id = "default"
            if model_id not in self.model_energy_consumption:
                raise ValueError(f"Model {model_id} not found and no default available")
        
        # Get energy consumption per token
        energy_per_token = self.model_energy_consumption[model_id]
        
        # Calculate energy consumption
        input_energy_kwh = energy_per_token["input_kwh_per_token"] * input_tokens
        output_energy_kwh = energy_per_token["output_kwh_per_token"] * output_tokens
        total_energy_kwh = input_energy_kwh + output_energy_kwh
        
        # Get PUE for the region
        pue = self.region_pue.get(region, self.DEFAULT_PUE)
        
        # Apply PUE to get total data center energy
        total_facility_energy_kwh = total_energy_kwh * pue
        
        # Get carbon intensity for the region (gCO2e/kWh)
        carbon_intensity = self.region_carbon_intensity.get(region, self.DEFAULT_CARBON_INTENSITY)
        
        # Calculate operational carbon emissions (gCO2e)
        operational_emissions_gco2e = total_facility_energy_kwh * carbon_intensity
        
        # Calculate amortized training emissions
        amortized_training_emissions_gco2e = 0
        if model_id in self.model_training_emissions:
            training_data = self.model_training_emissions[model_id]
            total_tokens = input_tokens + output_tokens
            # Calculate training emissions per token and multiply by tokens used
            training_emissions_per_token = training_data["total_emissions_gco2e"] / training_data["expected_inferences"]
            amortized_training_emissions_gco2e = training_emissions_per_token * total_tokens
        
        # Calculate total emissions
        total_emissions_gco2e = operational_emissions_gco2e + amortized_training_emissions_gco2e
        
        # Calculate water usage
        wue = self.region_water_usage.get(region, self.DEFAULT_WUE)
        water_usage_liters = total_facility_energy_kwh * wue
        
        # Get water stress level
        water_stress_level = self.region_water_stress.get(region, "Unknown")
        
        # Calculate percentages
        if total_emissions_gco2e > 0:
            operational_percentage = (operational_emissions_gco2e / total_emissions_gco2e) * 100
            training_percentage = (amortized_training_emissions_gco2e / total_emissions_gco2e) * 100
        else:
            operational_percentage = 0
            training_percentage = 0
        
        # Format result
        result = {
            "model_id": model_id,
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "energy_consumption": {
                "input_energy_kwh": input_energy_kwh,
                "output_energy_kwh": output_energy_kwh,
                "total_energy_kwh": total_energy_kwh,
                "pue": pue,
                "total_facility_energy_kwh": total_facility_energy_kwh
            },
            "emissions": {
                "carbon_intensity_gco2e_kwh": carbon_intensity,
                "operational_emissions_gco2e": operational_emissions_gco2e,
                "operational_percentage": operational_percentage,
                "amortized_training_emissions_gco2e": amortized_training_emissions_gco2e,
                "training_percentage": training_percentage,
                "total_emissions_gco2e": total_emissions_gco2e,
                "total_emissions_kgco2e": total_emissions_gco2e / 1000
            },
            "water_usage": {
                "water_usage_effectiveness": wue,
                "water_usage_liters": water_usage_liters,
                "water_stress_level": water_stress_level
            }
        }
        
        return result
    
    # HARDWARE EMBODIED CARBON CALCULATIONS
    
    def calculate_hardware_embodied_carbon(self, model_id: str, region: str, 
                                         duration_hours: float = 1.0,
                                         utilization: float = 0.05) -> Dict[str, Any]:
        """
        Calculate hardware embodied carbon for AI model usage.
        
        Args:
            model_id: Model identifier
            region: AWS region
            duration_hours: Duration of usage in hours
            utilization: Utilization factor (0-1)
            
        Returns:
            Dictionary with embodied carbon results
        """
        # Get hardware profile for the model
        hardware = self.model_hardware_map.get(model_id, self.model_hardware_map["default"])
        
        # Calculate amortized hourly emissions
        # Total lifecycle hours = years * 365 days * 24 hours
        lifecycle_hours = self.hardware_lifecycle * 365 * 24
        
        # Get component emissions
        gpu_emissions = self.hardware_embodied_emissions["gpu"][hardware["gpu_type"]] * hardware["gpu_count"]
        cpu_emissions = self.hardware_embodied_emissions["cpu"][hardware["cpu_type"]]
        memory_modules = hardware["memory_gb"] / 16  # Convert GB to 16GB modules
        memory_emissions = self.hardware_embodied_emissions["memory"] * memory_modules
        storage_emissions = self.hardware_embodied_emissions["ssd"] * hardware["storage_tb"]
        chassis_emissions = self.hardware_embodied_emissions["server_chassis"]
        
        # Total embodied emissions for the server (kgCO2e)
        total_embodied_kgco2e = gpu_emissions + cpu_emissions + memory_emissions + storage_emissions + chassis_emissions
        
        # Amortized hourly emissions (kgCO2e/hour)
        hourly_embodied_kgco2e = total_embodied_kgco2e / lifecycle_hours
        
        # Adjust for server utilization and duration
        adjusted_embodied_kgco2e = hourly_embodied_kgco2e * duration_hours * utilization * hardware["server_count"]
        
        # Format result
        result = {
            "model_id": model_id,
            "region": region,
            "hardware_profile": hardware,
            "utilization": utilization,
            "duration_hours": duration_hours,
            "embodied_emissions": {
                "gpu_emissions_kgco2e": gpu_emissions,
                "cpu_emissions_kgco2e": cpu_emissions,
                "memory_emissions_kgco2e": memory_emissions,
                "storage_emissions_kgco2e": storage_emissions,
                "chassis_emissions_kgco2e": chassis_emissions,
                "total_embodied_kgco2e": total_embodied_kgco2e,
                "hourly_embodied_kgco2e": hourly_embodied_kgco2e,
                "adjusted_embodied_kgco2e": adjusted_embodied_kgco2e
            },
            "hardware_lifecycle_years": self.hardware_lifecycle
        }
        
        return result
    
    # COMBINED CALCULATIONS AND HELPER METHODS
    
    def calculate_total_impact(self, model_id: str, region: str,
                             input_tokens: int, output_tokens: int,
                             duration_hours: float = 1.0,
                             utilization: float = 0.05) -> Dict[str, Any]:
        """
        Calculate combined carbon, water, and embodied emissions for AI model usage.
        
        Args:
            model_id: Model identifier
            region: AWS region
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_hours: Duration of usage in hours
            utilization: Utilization factor (0-1)
            
        Returns:
            Dictionary with combined impact results
        """
        # Calculate operational and training emissions
        operational_result = self.calculate_model_carbon(model_id, region, input_tokens, output_tokens)
        
        # Calculate embodied hardware emissions
        embodied_result = self.calculate_hardware_embodied_carbon(model_id, region, duration_hours, utilization)
        
        # Combine results
        result = {
            "model_id": model_id,
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_hours": duration_hours,
            "utilization": utilization,
            "operational_emissions_gco2e": operational_result["emissions"]["operational_emissions_gco2e"],
            "training_emissions_gco2e": operational_result["emissions"]["amortized_training_emissions_gco2e"],
            "embodied_emissions_gco2e": embodied_result["embodied_emissions"]["adjusted_embodied_kgco2e"] * 1000,  # Convert kg to g
            "total_emissions_gco2e": (
                operational_result["emissions"]["operational_emissions_gco2e"] +
                operational_result["emissions"]["amortized_training_emissions_gco2e"] +
                embodied_result["embodied_emissions"]["adjusted_embodied_kgco2e"] * 1000  # Convert kg to g
            ),
            "water_usage_liters": operational_result["water_usage"]["water_usage_liters"],
            "water_stress_level": operational_result["water_usage"]["water_stress_level"],
            "energy_kwh": operational_result["energy_consumption"]["total_facility_energy_kwh"]
        }
        
        # Add environmental equivalents
        result["environmental_equivalents"] = self.get_environmental_equivalents(result["total_emissions_gco2e"] / 1000)  # Convert g to kg
        
        return result
    
    def compare_models(self, model_ids: List[str], region: str,
                     input_tokens: int, output_tokens: int,
                     duration_hours: float = 1.0,
                     utilization: float = 0.05) -> Dict[str, Any]:
        """
        Compare environmental impact across multiple models.
        
        Args:
            model_ids: List of model identifiers
            region: AWS region
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_hours: Duration of usage in hours
            utilization: Utilization factor (0-1)
            
        Returns:
            Dictionary with comparison results
        """
        results = []
        
        for model_id in model_ids:
            try:
                result = self.calculate_total_impact(
                    model_id, region, input_tokens, output_tokens, duration_hours, utilization
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Error calculating impact for model {model_id}: {e}")
                results.append({
                    "model_id": model_id,
                    "error": str(e)
                })
        
        # Sort by total emissions (lowest first)
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            valid_results.sort(key=lambda x: x["total_emissions_gco2e"])
            
            # Calculate potential savings percentage
            if len(valid_results) > 1:
                lowest_emissions = valid_results[0]["total_emissions_gco2e"]
                highest_emissions = valid_results[-1]["total_emissions_gco2e"]
                
                if highest_emissions > 0:
                    potential_savings_percentage = ((highest_emissions - lowest_emissions) / highest_emissions) * 100
                else:
                    potential_savings_percentage = 0
            else:
                potential_savings_percentage = 0
        else:
            potential_savings_percentage = 0
        
        return {
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_hours": duration_hours,
            "utilization": utilization,
            "results": results,
            "potential_savings_percentage": potential_savings_percentage
        }
    
    def find_lowest_carbon_regions(self, model_id: str, input_tokens: int, 
                                output_tokens: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find AWS regions with the lowest carbon footprint for a specific model.
        
        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            limit: Maximum number of regions to return
            
        Returns:
            List of dictionaries with region carbon footprint results, sorted by lowest emissions
        """
        results = []
        
        # Calculate carbon footprint for all regions
        for region in self.region_carbon_intensity.keys():
            try:
                result = self.calculate_model_carbon(model_id, region, input_tokens, output_tokens)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error calculating carbon footprint for region {region}: {e}")
        
        # Sort by total emissions (lowest first)
        results.sort(key=lambda x: x["emissions"]["total_emissions_gco2e"])
        
        # Limit the number of results
        top_results = results[:limit]
        
        # Calculate savings percentage compared to highest carbon region
        if results:
            highest_emissions = max(r["emissions"]["total_emissions_gco2e"] for r in results)
            
            for result in top_results:
                emissions = result["emissions"]["total_emissions_gco2e"]
                savings_percentage = ((highest_emissions - emissions) / highest_emissions) * 100 if highest_emissions > 0 else 0
                result["savings_percentage"] = savings_percentage
        
        return top_results
    
    def find_lowest_water_regions(self, model_id: str, input_tokens: int, 
                              output_tokens: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find AWS regions with the lowest water footprint for a specific model.
        
        Args:
            model_id: Model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            limit: Maximum number of regions to return
            
        Returns:
            List of dictionaries with region water footprint results, sorted by lowest usage
        """
        results = []
        
        # Calculate water footprint for all regions
        for region in self.region_water_usage.keys():
            try:
                result = self.calculate_model_carbon(model_id, region, input_tokens, output_tokens)
                results.append(result)
            except Exception as e:
                logger.warning(f"Error calculating water footprint for region {region}: {e}")
        
        # Sort by water usage (lowest first)
        results.sort(key=lambda x: x["water_usage"]["water_usage_liters"])
        
        # Limit the number of results
        top_results = results[:limit]
        
        # Calculate savings percentage compared to highest water usage
        if results:
            highest_usage = max(r["water_usage"]["water_usage_liters"] for r in results)
            
            for result in top_results:
                usage = result["water_usage"]["water_usage_liters"]
                savings_percentage = ((highest_usage - usage) / highest_usage) * 100 if highest_usage > 0 else 0
                result["savings_percentage"] = savings_percentage
        
        return top_results
    
    def get_environmental_equivalents(self, carbon_kg: float) -> Dict[str, Any]:
        """
        Get environmental equivalents for a given amount of carbon emissions.
        
        Args:
            carbon_kg: Carbon emissions in kilograms
            
        Returns:
            Dictionary with environmental equivalents
        """
        # Car travel: 0.192 kg CO2e per mile (average passenger car)
        car_miles = carbon_kg / 0.192
        
        # Smartphone charging: 0.005 kg CO2e per full charge
        smartphone_charges = carbon_kg / 0.005
        
        # Home electricity: 0.92 kg CO2e per kWh (global average)
        home_electricity_kwh = carbon_kg / 0.92
        
        # Tree absorption: 21 kg CO2 per tree per year
        tree_days = (carbon_kg / 21) * 365
        
        return {
            "car_miles": car_miles,
            "smartphone_charges": smartphone_charges,
            "home_electricity_kwh": home_electricity_kwh,
            "tree_absorption_days": tree_days
        }

    def get_supported_models(self) -> List[str]:
        """Get a list of supported model IDs."""
        return list(self.model_energy_consumption.keys())
    
    def get_regions_with_intensity(self) -> Dict[str, float]:
        """Get all AWS regions with their carbon intensity."""
        return self.region_carbon_intensity
    
    def get_regions_with_water_usage(self) -> Dict[str, float]:
        """Get all AWS regions with their water usage effectiveness."""
        return self.region_water_usage


# Example usage
if __name__ == "__main__":
    calculator = AWSEnvironmentalCalculator()
    
    # Example 1: Calculate EC2 carbon footprint
    ec2_result = calculator.calculate_ec2_carbon('m5.xlarge', 'us-east-1', 24)
    print("\nEC2 Carbon Footprint:")
    print(f"Emissions: {ec2_result['carbon_emissions']['emissions_kgco2e']:.4f} kgCO2e")
    print(f"Water Usage: {ec2_result['water_usage']['water_usage_liters']:.2f} liters")
    
    # Example 2: Calculate AI model carbon footprint
    model_result = calculator.calculate_model_carbon(
        'anthropic.claude-3-sonnet-20240229-v1:0', 'us-east-1', 1000, 500
    )
    print("\nAI Model Carbon Footprint:")
    print(f"Operational Emissions: {model_result['emissions']['operational_emissions_gco2e']:.6f} gCO2e")
    print(f"Training Emissions: {model_result['emissions']['amortized_training_emissions_gco2e']:.6f} gCO2e")
    print(f"Total Emissions: {model_result['emissions']['total_emissions_gco2e']:.6f} gCO2e")
    print(f"Water Usage: {model_result['water_usage']['water_usage_liters']:.4f} liters")
    
    # Example 3: Calculate total impact with embodied emissions
    impact_result = calculator.calculate_total_impact(
        'anthropic.claude-3-sonnet-20240229-v1:0', 'us-east-1', 1000, 500, 1.0, 0.05
    )
    print("\nTotal Environmental Impact:")
    print(f"Operational Emissions: {impact_result['operational_emissions_gco2e']:.6f} gCO2e")
    print(f"Training Emissions: {impact_result['training_emissions_gco2e']:.6f} gCO2e")
    print(f"Embodied Emissions: {impact_result['embodied_emissions_gco2e']:.6f} gCO2e")
    print(f"Total Emissions: {impact_result['total_emissions_gco2e']:.6f} gCO2e")
    print(f"Water Usage: {impact_result['water_usage_liters']:.4f} liters")
    
    # Example 4: Compare models
    comparison_result = calculator.compare_models(
        ['anthropic.claude-3-sonnet-20240229-v1:0', 'anthropic.claude-3-haiku-20240307-v1:0'], 
        'us-east-1', 1000, 500
    )
    print("\nModel Comparison:")
    print(f"Potential Savings: {comparison_result['potential_savings_percentage']:.1f}%")
    for result in comparison_result['results']:
        print(f"{result['model_id']}: {result['total_emissions_gco2e']:.6f} gCO2e") 
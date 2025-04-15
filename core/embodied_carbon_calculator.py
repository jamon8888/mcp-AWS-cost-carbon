#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Embodied Carbon Calculator
-------------------------
Calculator for embodied carbon emissions in hardware resources.
"""

import os
import json
import csv
from typing import Dict, Any, List, Tuple, Optional
from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator
from .data_providers.data_loader import DataLoader


class EmbodiedCarbonCalculator:
    """Calculator for embodied carbon emissions in hardware resources."""
    
    def __init__(self, data_dir: str = "data", mock_mode: bool = False):
        """
        Initialize the calculator with data directory.
        
        Args:
            data_dir: Directory containing data files
            mock_mode: Whether to use mock data
        """
        self.data_dir = data_dir
        self.mock_mode = mock_mode
        self.data_loader = DataLoader(data_dir=self.data_dir, mock_mode=self.mock_mode)
        self.carbon_calculator = BedrockCarbonCalculator(data_dir=self.data_dir, mock_mode=self.mock_mode)
        
        # Hardware profiles with embodied carbon data
        # Values in kgCO2e for full lifecycle
        self.HARDWARE_PROFILES = {
            # EC2 instances
            't2.micro': {'carbon': 150, 'lifespan_years': 4},
            't3.medium': {'carbon': 250, 'lifespan_years': 4},
            'm5.large': {'carbon': 400, 'lifespan_years': 4},
            'c5.xlarge': {'carbon': 600, 'lifespan_years': 4},
            'r5.large': {'carbon': 450, 'lifespan_years': 4},
            'p3.2xlarge': {'carbon': 2500, 'lifespan_years': 3},
            
            # RDS instances
            'db.t3.micro': {'carbon': 200, 'lifespan_years': 4},
            'db.t3.small': {'carbon': 300, 'lifespan_years': 4},
            'db.r5.large': {'carbon': 600, 'lifespan_years': 4},
            'db.r5.xlarge': {'carbon': 900, 'lifespan_years': 4},
            
            # SageMaker instances
            'ml.t3.medium': {'carbon': 300, 'lifespan_years': 4},
            'ml.c5.xlarge': {'carbon': 700, 'lifespan_years': 4},
            'ml.p3.2xlarge': {'carbon': 3000, 'lifespan_years': 3}
        }
        
        # Default lifecycle for hardware (in years)
        self.hardware_lifecycle = 4.0  # 4 years
        
        # Load model-to-hardware mapping data
        self.model_hardware_map = self._load_hardware_mapping()
        
        # Define embodied carbon for typical hardware components (kgCO2e)
        self.component_emissions = {
            # Data from various LCA studies on server hardware
            "cpu": {
                "small": 320,     # Small CPU (e.g., for lightweight models)
                "medium": 720,    # Medium CPU (e.g., for medium-sized models)
                "large": 1250     # Large CPU (e.g., for large language models)
            },
            "gpu": {
                "a10g": 1450,      # NVIDIA A10G
                "a100": 2850,      # NVIDIA A100
                "h100": 3750       # NVIDIA H100
            },
            "memory": 7.5,        # Per 16GB module
            "ssd": 85,            # Per 1TB SSD
            "hdd": 35,            # Per 1TB HDD
            "server_chassis": 650  # Server chassis and other components
        }
        
        # Manufacturing emissions factor by region (multiplier)
        # Source: Estimates based on grid intensity of manufacturing regions
        self.manufacturing_factors = {
            "us-east-1": 1.0,      # Baseline
            "us-east-2": 1.05,
            "us-west-1": 0.85,
            "us-west-2": 0.8,
            "ca-central-1": 0.6,
            "eu-west-1": 0.95,
            "eu-west-2": 0.9,
            "eu-west-3": 0.6,
            "eu-central-1": 0.9,
            "eu-north-1": 0.5,     # Low carbon intensity in Sweden
            "ap-northeast-1": 1.2, # Higher carbon intensity in Japan
            "ap-northeast-2": 1.3, # Higher carbon intensity in South Korea
            "ap-southeast-1": 1.1,
            "ap-southeast-2": 1.0,
            "ap-south-1": 1.4,     # Higher carbon intensity in India
            "sa-east-1": 0.7       # Brazil uses more hydropower
        }
        
        # Default manufacturing factor for regions not in the list
        self.default_manufacturing_factor = 1.0
        
        # Load model training emissions using DataLoader
        self.model_training_emissions = self._load_training_emissions_from_loader()
        
        # Default embodied emissions estimates (gCO2e per hour)
        self.default_emissions = {
            "ec2": {
                "t3": 10,  # Low for shared instances
                "m5": 25,  # Medium for general purpose
                "c5": 30,  # Higher for compute optimized
                "r5": 35,  # Higher for memory optimized
                "p3": 100, # Much higher for GPU instances
                "default": 20
            },
            "storage": {
                "s3": 0.05,  # Per GB per month
                "ebs": 0.1,  # Per GB per month
                "default": 0.08
            },
            "network": 0.05,  # Per GB transferred
            "default": 10.0  # Default hourly embodied emissions
        }
    
    def _load_hardware_mapping(self) -> Dict[str, Dict[str, Any]]:
        """
        Load the mapping between model types and hardware requirements.
        
        This is based on estimates and public information about
        infrastructure requirements for different model sizes.
        """
        # Create hardware profiles for different model types
        hardware_map = {
            # Large language models
            "anthropic.claude-3-opus-20240229-v1:0": {
                "gpu_type": "a100",
                "gpu_count": 8,
                "cpu_type": "large",
                "memory_gb": 1024,
                "storage_tb": 4.0,
                "server_count": 1.0,  # Fractional because one server serves many requests
                "manufacturing_multiplier": 1.1  # Higher for cutting-edge hardware
            },
            "anthropic.claude-3-sonnet-20240229-v1:0": {
                "gpu_type": "a100",
                "gpu_count": 4,
                "cpu_type": "medium",
                "memory_gb": 512,
                "storage_tb": 2.0,
                "server_count": 0.5,
                "manufacturing_multiplier": 1.05
            },
            "anthropic.claude-3-haiku-20240307-v1:0": {
                "gpu_type": "a10g",
                "gpu_count": 2,
                "cpu_type": "medium",
                "memory_gb": 256,
                "storage_tb": 1.0,
                "server_count": 0.2,
                "manufacturing_multiplier": 1.0
            },
            "anthropic.claude-2.1": {
                "gpu_type": "a10g", 
                "gpu_count": 3,
                "cpu_type": "medium",
                "memory_gb": 384,
                "storage_tb": 1.5,
                "server_count": 0.3,
                "manufacturing_multiplier": 1.0
            },
            "anthropic.claude-2.0": {
                "gpu_type": "a10g",
                "gpu_count": 2,
                "cpu_type": "medium",
                "memory_gb": 256,
                "storage_tb": 1.0,
                "server_count": 0.25,
                "manufacturing_multiplier": 1.0
            },
            "anthropic.claude-instant-1.2": {
                "gpu_type": "a10g",
                "gpu_count": 1,
                "cpu_type": "medium",
                "memory_gb": 128,
                "storage_tb": 0.5,
                "server_count": 0.1,
                "manufacturing_multiplier": 1.0
            },
            # Amazon models
            "amazon.titan-text-express-v1:0": {
                "gpu_type": "a10g",
                "gpu_count": 1,
                "cpu_type": "medium",
                "memory_gb": 128,
                "storage_tb": 0.5,
                "server_count": 0.1,
                "manufacturing_multiplier": 1.0
            },
            "amazon.titan-text-lite-v1:0": {
                "gpu_type": "a10g",
                "gpu_count": 0.5,  # Fractional because models are often deployed on shared GPUs
                "cpu_type": "small",
                "memory_gb": 64,
                "storage_tb": 0.25,
                "server_count": 0.05,
                "manufacturing_multiplier": 0.95
            },
            # Meta models
            "meta.llama3-70b-instruct-v1:0": {
                "gpu_type": "a100",
                "gpu_count": 4,
                "cpu_type": "medium",
                "memory_gb": 384,
                "storage_tb": 2.0,
                "server_count": 0.4,
                "manufacturing_multiplier": 1.05
            },
            # Default profile for unknown models
            "default": {
                "gpu_type": "a10g",
                "gpu_count": 2,
                "cpu_type": "medium",
                "memory_gb": 256,
                "storage_tb": 1.0,
                "server_count": 0.2,
                "manufacturing_multiplier": 1.0
            }
        }
        
        # Add other models with similar profiles
        for model in self.carbon_calculator.BEDROCK_MODEL_ENERGY.keys():
            if model not in hardware_map:
                # Use default profile for unknown models
                hardware_map[model] = hardware_map["default"].copy()
        
        return hardware_map
    
    def _load_training_emissions_from_loader(self) -> Dict[str, Dict[str, float]]:
        """Load training emissions using DataLoader."""
        # DataLoader returns a dict {model_id: {col: val, ...}}
        # Convert total_emissions_gco2e to a numeric type if needed
        loaded_data = self.data_loader.load_model_data("training_footprint")
        for model_id, data in loaded_data.items():
            if "total_emissions_gco2e" in data:
                try:
                    data["total_emissions_gco2e"] = float(data["total_emissions_gco2e"])
                except (ValueError, TypeError):
                    print(f"Warning: Could not convert training emissions for {model_id} to float.")
                    data["total_emissions_gco2e"] = 0.0 # Or handle as needed
            if "expected_inferences" in data:
                 try:
                     data["expected_inferences"] = float(data["expected_inferences"])
                 except (ValueError, TypeError):
                     print(f"Warning: Could not convert expected inferences for {model_id} to float.")
                     data["expected_inferences"] = 1e9 # Default

        return loaded_data
    
    def _calculate_hardware_embodied_carbon(
        self,
        instance_type: str,
        usage_fraction: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate embodied carbon emissions for hardware resources.
        
        Args:
            instance_type: AWS instance type identifier
            usage_fraction: Fraction of hardware resources used (0-1)
            
        Returns:
            Dictionary with embodied carbon metrics
            
        Raises:
            ValueError: If instance type is not found
        """
        if instance_type not in self.HARDWARE_PROFILES:
            raise ValueError(f"Unknown instance type: {instance_type}")
        
        profile = self.HARDWARE_PROFILES[instance_type]
        total_carbon = profile['carbon']  # kgCO2e
        lifespan_hours = profile['lifespan_years'] * 365 * 24
        
        # Calculate hourly embodied carbon
        hourly_carbon = (total_carbon / lifespan_hours) * usage_fraction
        
        return {
            'total_embodied_kgco2e': total_carbon,
            'hourly_embodied_kgco2e': hourly_carbon,
            'lifespan_hours': lifespan_hours
        }
    
    def get_supported_instance_types(self) -> list:
        """Get list of supported instance types."""
        return list(self.HARDWARE_PROFILES.keys())
    
    def get_instance_profile(self, instance_type: str) -> Dict[str, Any]:
        """Get hardware profile for an instance type."""
        if instance_type not in self.HARDWARE_PROFILES:
            raise ValueError(f"Unknown instance type: {instance_type}")
        return self.HARDWARE_PROFILES[instance_type].copy()
    
    def calculate_total_carbon_footprint(
        self, 
        model_id: str, 
        region: str, 
        input_tokens: int, 
        output_tokens: int,
        duration_hours: float = 1.0,
        utilization: float = 0.05  # Default to 5% utilization of allocated resources
    ) -> Dict[str, Any]:
        """
        Calculate the total carbon footprint, including both operational
        and embodied emissions.
        
        Args:
            model_id: The AWS Bedrock model identifier
            region: AWS region where the model is running
            input_tokens: Number of input tokens processed
            output_tokens: Number of output tokens generated
            duration_hours: Duration of usage in hours
            utilization: Fraction of allocated resources utilized
            
        Returns:
            Dictionary with carbon footprint information
        """
        # Calculate operational emissions using the standard calculator
        operational_result = self.carbon_calculator.calculate_carbon_footprint(
            model_id, region, input_tokens, output_tokens
        )
        
        # Calculate embodied emissions from hardware
        embodied_emissions = self._calculate_hardware_embodied_carbon(
            model_id, utilization
        )
        
        # Scale embodied emissions by duration
        embodied_emissions_total = embodied_emissions["hourly_embodied_kgco2e"] * duration_hours
        
        # Get training emissions if available
        model_training_data = self.model_training_emissions.get(model_id, {})
        if model_training_data:
            total_training_emissions = model_training_data.get('total_emissions_gco2e', 0) / 1000  # Convert to kg
            expected_inferences = model_training_data.get('expected_inferences', 1)
            amortized_training = (total_training_emissions / expected_inferences) * (input_tokens + output_tokens)
        else:
            # Fallback to the existing approach
            amortized_training = operational_result["emissions"]["amortized_training_emissions_gco2e"] / 1000
        
        # Convert operational emissions from g to kg
        operational_emissions = operational_result["emissions"]["operational_emissions_gco2e"] / 1000
        
        # Calculate total carbon footprint
        total_carbon = operational_emissions + embodied_emissions_total + amortized_training
        
        # Create detailed breakdown
        result = {
            "model_id": model_id,
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_hours": duration_hours,
            "utilization": utilization,
            "emissions": {
                "operational_kgco2e": operational_emissions,
                "operational_percentage": (operational_emissions / total_carbon) * 100 if total_carbon > 0 else 0,
                
                "embodied_kgco2e": embodied_emissions_total,
                "embodied_percentage": (embodied_emissions_total / total_carbon) * 100 if total_carbon > 0 else 0,
                "embodied_breakdown": embodied_emissions,
                
                "training_kgco2e": amortized_training,
                "training_percentage": (amortized_training / total_carbon) * 100 if total_carbon > 0 else 0,
                
                "total_kgco2e": total_carbon
            },
            "environmental_equivalents": {
                "miles_driven": total_carbon / 0.2,  # kg CO2 per mile driven in average car
                "smartphone_charges": total_carbon / 0.005,  # kg CO2 per smartphone charge
                "hours_of_tv": total_carbon / 0.1  # kg CO2 per hour of TV watching
            }
        }
        
        return result
    
    def compare_models_emissions(
        self,
        model_ids: List[str],
        region: str,
        input_tokens: int,
        output_tokens: int,
        duration_hours: float = 1.0
    ) -> Dict[str, Any]:
        """
        Compare the carbon footprint of multiple models.
        
        Args:
            model_ids: List of AWS Bedrock model identifiers
            region: AWS region where the models are running
            input_tokens: Number of input tokens processed
            output_tokens: Number of output tokens generated
            duration_hours: Duration of usage in hours
            
        Returns:
            Dictionary with comparison results
        """
        results = []
        for model_id in model_ids:
            try:
                result = self.calculate_total_carbon_footprint(
                    model_id, region, input_tokens, output_tokens, duration_hours
                )
                results.append(result)
            except Exception as e:
                print(f"Error calculating emissions for {model_id}: {str(e)}")
                results.append({
                    "model_id": model_id,
                    "error": str(e)
                })
        
        # Sort results by total emissions
        valid_results = [r for r in results if "error" not in r]
        if valid_results:
            valid_results.sort(key=lambda x: x["emissions"]["total_kgco2e"])
            
            # Calculate relative emissions compared to the lowest
            lowest_emissions = valid_results[0]["emissions"]["total_kgco2e"]
            for result in valid_results:
                if result["emissions"]["total_kgco2e"] > 0:
                    result["relative_emissions"] = result["emissions"]["total_kgco2e"] / lowest_emissions
                else:
                    result["relative_emissions"] = 1.0
        
        # Prepare comparison result
        comparison = {
            "region": region,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_hours": duration_hours,
            "results": results,
            "lowest_carbon_model": valid_results[0]["model_id"] if valid_results else None,
            "highest_carbon_model": valid_results[-1]["model_id"] if valid_results else None,
            "potential_savings_percentage": ((valid_results[-1]["emissions"]["total_kgco2e"] - 
                                           valid_results[0]["emissions"]["total_kgco2e"]) / 
                                          valid_results[-1]["emissions"]["total_kgco2e"] * 100)
                                         if valid_results and valid_results[-1]["emissions"]["total_kgco2e"] > 0 else 0
        }
        
        return comparison
    
    def calculate_embodied_emissions(self, service_type: str, resource_id: str, 
                                     usage_data: Dict[str, Any]) -> float:
        """
        Calculate embodied emissions for a resource.
        
        Args:
            service_type: Type of service (EC2, S3, etc.)
            resource_id: Resource identifier
            usage_data: Usage metrics for the resource
            
        Returns:
            Embodied emissions in gCO2e
        """
        service_type = service_type.lower()
        
        if "ec2" in service_type or "compute" in service_type:
            return self._calculate_compute_embodied_emissions(resource_id, usage_data)
        elif "s3" in service_type or "storage" in service_type:
            return self._calculate_storage_embodied_emissions(resource_id, usage_data)
        else:
            # Default calculation for other service types
            hours = usage_data.get("hours", 1)
            return self.default_emissions["default"] * hours
    
    def _calculate_compute_embodied_emissions(self, resource_id: str, 
                                             usage_data: Dict[str, Any]) -> float:
        """Calculate embodied emissions for compute resources."""
        hours = usage_data.get("hours", 1)
        
        # Get instance family
        instance_family = resource_id.split('.')[0] if '.' in resource_id else "default"
        
        # Get embodied emissions for this instance family
        hourly_emissions = self.default_emissions["ec2"].get(
            instance_family, self.default_emissions["ec2"]["default"]
        )
        
        return hourly_emissions * hours
    
    def _calculate_storage_embodied_emissions(self, resource_id: str, 
                                             usage_data: Dict[str, Any]) -> float:
        """Calculate embodied emissions for storage resources."""
        storage_gb = usage_data.get("storage_gb", 1)
        storage_type = resource_id.lower()
        
        # Get embodied emissions for this storage type
        if "s3" in storage_type:
            emissions_per_gb = self.default_emissions["storage"]["s3"]
        elif "ebs" in storage_type:
            emissions_per_gb = self.default_emissions["storage"]["ebs"]
        else:
            emissions_per_gb = self.default_emissions["storage"]["default"]
        
        return emissions_per_gb * storage_gb

# Example usage
if __name__ == "__main__":
    calculator = EmbodiedCarbonCalculator()
    
    # Example 1: Calculate total carbon footprint for a single model
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    region = "us-east-1"
    input_tokens = 1000
    output_tokens = 500
    
    result = calculator.calculate_total_carbon_footprint(
        model_id, region, input_tokens, output_tokens
    )
    
    print(f"Total carbon footprint for {model_id} in {region}:")
    print(f"  Operational: {result['emissions']['operational_kgco2e']:.6f} kgCO2e ({result['emissions']['operational_percentage']:.2f}%)")
    print(f"  Embodied: {result['emissions']['embodied_kgco2e']:.6f} kgCO2e ({result['emissions']['embodied_percentage']:.2f}%)")
    print(f"  Training: {result['emissions']['training_kgco2e']:.6f} kgCO2e ({result['emissions']['training_percentage']:.2f}%)")
    print(f"  Total: {result['emissions']['total_kgco2e']:.6f} kgCO2e")
    print(f"  Equivalent to driving {result['environmental_equivalents']['miles_driven']:.2f} miles")
    
    # Example 2: Compare multiple models
    models_to_compare = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-opus-20240229-v1:0"
    ]
    
    comparison = calculator.compare_models_emissions(
        models_to_compare, region, input_tokens, output_tokens
    )
    
    print("\nModel comparison:")
    for result in comparison["results"]:
        if "error" in result:
            print(f"  {result['model_id']}: Error - {result['error']}")
        else:
            relative = result.get("relative_emissions", 1.0)
            print(f"  {result['model_id']}:")
            print(f"    Total emissions: {result['emissions']['total_kgco2e']:.6f} kgCO2e")
            print(f"    Operational: {result['emissions']['operational_percentage']:.1f}%, "
                  f"Embodied: {result['emissions']['embodied_percentage']:.1f}%, "
                  f"Training: {result['emissions']['training_percentage']:.1f}%")
            if relative > 1.0:
                print(f"    {(relative - 1.0) * 100:.1f}% higher emissions than the lowest model")
            else:
                print(f"    Lowest emissions model in comparison")
    
    print(f"\nPotential savings: {comparison['potential_savings_percentage']:.1f}% by choosing the most efficient model") 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AWS Environmental Calculator
--------------------------
A comprehensive calculator for assessing environmental impact of AWS services,
particularly focusing on AWS Bedrock models. Combines carbon footprint,
embodied emissions, and water usage metrics.
"""

import os
import json
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass

from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator
from core.embodied_carbon_calculator import EmbodiedCarbonCalculator
from core.water_metrics_integration import BedrockWaterCalculator as WaterMetricsCalculator
from .data_providers.data_loader import DataLoader

@dataclass
class EnvironmentalMetrics:
    """Container for environmental impact metrics"""
    carbon_footprint: float  # gCO2e
    embodied_emissions: float  # gCO2e
    water_usage: float  # liters
    water_stress_level: str
    total_impact_score: float
    environmental_equivalents: Dict[str, float]
    energy_kwh: float  # kilowatt-hours

class AWSEnvironmentalCalculator:
    """
    Unified calculator for assessing environmental impact of AWS services.
    Combines carbon footprint, embodied emissions, and water usage metrics.
    """
    
    def __init__(self, data_dir: str = "data", mock_mode: bool = False):
        """
        Initialize the environmental calculator with component calculators.
        
        Args:
            data_dir: Directory containing data files for metrics calculations
            mock_mode: Whether to use mock data from the 'mock/' directory
        """
        self.data_dir = data_dir
        self.mock_mode = mock_mode
        self.data_loader = DataLoader(data_dir=self.data_dir, mock_mode=self.mock_mode)
        
        # Initialize calculators with the same mode
        self.bedrock_calculator = BedrockCarbonCalculator(data_dir=self.data_dir, mock_mode=self.mock_mode)
        self.embodied_calculator = EmbodiedCarbonCalculator(data_dir=self.data_dir, mock_mode=self.mock_mode)
        self.water_calculator = WaterMetricsCalculator(data_dir=self.data_dir, mock_mode=self.mock_mode)
        
        # Environmental equivalents conversion factors
        self.environmental_equivalents = {
            "miles_driven": 404.0,  # gCO2e per mile
            "smartphone_charges": 2.3,  # gCO2e per charge
            "trees_month_offset": 500.0,  # gCO2e per tree per month
            "liters_bottled_water": 0.08,  # kgCO2e per liter
            "laptop_hours": 50.0,  # gCO2e per hour
        }
        
        # Service-specific energy factors (kWh per unit)
        self.service_energy_factors = {
            'EC2': {
                't2.micro': 0.0116,
                't3.medium': 0.0416,
                'm5.large': 0.096,
                'c5.xlarge': 0.17,
                'r5.large': 0.126,
                'p3.2xlarge': 3.06
            },
            'RDS': {
                'db.t3.micro': 0.017,
                'db.t3.small': 0.034,
                'db.r5.large': 0.29,
                'db.r5.xlarge': 0.58
            },
            'Lambda': 0.0000167,  # kWh per GB-second
            'DynamoDB': 0.0002,   # kWh per million requests
            'ECS': 0.04048,       # kWh per vCPU-hour
            'EKS': 0.04048,       # kWh per vCPU-hour
            'SageMaker': {
                'ml.t3.medium': 0.0464,
                'ml.c5.xlarge': 0.432,
                'ml.p3.2xlarge': 3.825
            }
        }

    def calculate_total_footprint(
        self,
        service_type: str,
        resource_id: str,
        region: str,
        usage_data: Dict[str, Any],
        usage_fraction: float = 1.0
    ) -> EnvironmentalMetrics:
        """
        Calculate total environmental footprint for any AWS service.
        
        Args:
            service_type: AWS service (EC2, RDS, Lambda, etc.)
            resource_id: Resource identifier (instance type, function name, etc.)
            region: AWS region code
            usage_data: Service-specific usage metrics
            usage_fraction: Fraction of hardware resources used (0-1)
            
        Returns:
            EnvironmentalMetrics object containing all impact metrics
        """
        try:
            service_type = service_type.lower()
            energy_consumption = 0.0
            
            if 'bedrock' in service_type:
                energy_consumption = self.bedrock_calculator.calculate_energy_consumption(resource_id, usage_data)
            elif 'ec2' in service_type or 'compute' in service_type:
                # EC2 energy calculation based on hours of usage
                # Assuming average power consumption per hour for the instance type
                instance_power = {
                    't3.micro': 15,  # 15W average
                    't3.small': 30,  # 30W average
                    't3.medium': 60, # 60W average
                    'm5.large': 75,  # Added estimate
                    'c5.xlarge': 95 # Added estimate
                }
                power_watts = instance_power.get(resource_id, 50)  # Keep default for others
                hours = usage_data.get('hours', 0)
                energy_consumption = (power_watts * hours) / 1000.0  # Convert to kWh
                
            elif 'lambda' in service_type:
                # Lambda energy calculation based on memory and duration
                memory_gb = usage_data.get('memory_gb', 0)
                duration_seconds = usage_data.get('duration_seconds', 0)
                invocations = usage_data.get('invocations', 1)
                # Assuming 1GB memory = 10W power consumption
                power_watts = memory_gb * 10
                energy_consumption = (power_watts * duration_seconds * invocations) / (3600 * 1000)  # Convert to kWh
                
            elif 'dynamodb' in service_type:
                # DynamoDB energy calculation based on requests
                read_requests = usage_data.get('read_requests', 0)
                write_requests = usage_data.get('write_requests', 0)
                # Assuming energy per request: 0.0000001 kWh for read, 0.0000002 kWh for write
                energy_consumption = (read_requests * 0.0000001) + (write_requests * 0.0000002)
            
            elif any(x in service_type for x in ['ecs', 'eks', 'container']):
                # Container services energy calculation based on vCPU hours
                vcpu_hours = usage_data.get('vcpu_hours', 0)
                # Assuming 8W per vCPU hour
                energy_consumption = (vcpu_hours * 8) / 1000.0
                
            elif 'storage' in service_type or 's3' in service_type:
                # Storage services energy calculation based on GB stored
                storage_gb = usage_data.get('storage_gb', 0)
                # Assuming 0.001 kWh per GB per month for storage
                energy_consumption = storage_gb * 0.001
                
            elif 'database' in service_type or 'rds' in service_type:
                # Database services energy calculation
                hours = usage_data.get('hours', 0)
                # Default to medium instance if not specified
                instance_type = usage_data.get('db_instance_type', 'medium')
                # Assuming average power in watts based on instance size
                power_map = {
                    'small': 30,
                    'medium': 60,
                    'large': 120
                }
                power_watts = 60  # Default medium power
                for size, watts in power_map.items():
                    if size in instance_type.lower():
                        power_watts = watts
                        break
                energy_consumption = (power_watts * hours) / 1000.0
            
            # All other services: use a default calculation based on hours if available
            else:
                hours = usage_data.get('hours', 0)
                # Assume a default power consumption of 20W
                energy_consumption = (20 * hours) / 1000.0
            
            # Calculate carbon emissions using PUE and carbon intensity
            pue = self.bedrock_calculator.get_pue(region)
            carbon_intensity = self.bedrock_calculator.get_carbon_intensity(region)
            total_energy = energy_consumption * pue
            carbon_emissions = total_energy * carbon_intensity / 1000  # Convert to kg CO2e
            
            # Calculate water usage
            water_usage_per_kwh = self.bedrock_calculator.get_water_usage(region)
            water_usage = total_energy * water_usage_per_kwh
            
            # Calculate embodied emissions based on service type
            embodied_emissions = self._calculate_service_embodied_emissions(
                service_type, resource_id, usage_fraction
            )
            
            # Calculate water stress
            water_stress = self.bedrock_calculator.get_water_stress(region)
            
            # Calculate total impact score
            total_impact = self._calculate_impact_score(
                carbon_emissions=carbon_emissions,
                embodied_emissions=embodied_emissions,
                water_usage=water_usage,
                water_stress=water_stress
            )
            
            # Calculate environmental equivalents
            total_emissions = carbon_emissions + embodied_emissions
            equivalents = self._calculate_environmental_equivalents(
                total_emissions, water_usage
            )
            
            return EnvironmentalMetrics(
                carbon_footprint=carbon_emissions,
                embodied_emissions=embodied_emissions,
                water_usage=water_usage,
                water_stress_level=water_stress,
                total_impact_score=total_impact,
                environmental_equivalents=equivalents,
                energy_kwh=energy_consumption
            )
            
        except Exception as e:
            print(f"Error calculating environmental metrics: {str(e)}")
            return EnvironmentalMetrics(
                carbon_footprint=0.0,
                embodied_emissions=0.0,
                water_usage=0.0,
                water_stress_level='Medium',
                total_impact_score=0.0,
                environmental_equivalents={},
                energy_kwh=0.0
            )

    def _calculate_service_embodied_emissions(
        self,
        service_type: str,
        resource_id: str,
        usage_fraction: float
    ) -> float:
        """Calculate embodied emissions for a specific service"""
        try:
            if service_type == 'bedrock':
                # For Bedrock models, use a simplified estimate based on GPU infrastructure
                # Assuming each model runs on high-performance GPU servers
                gpu_server_profile = {
                    'carbon': 2500,  # kgCO2e for a high-end GPU server
                    'lifespan_years': 3
                }
                
                # Calculate hourly embodied emissions
                lifespan_hours = gpu_server_profile['lifespan_years'] * 365 * 24
                hourly_emissions = (gpu_server_profile['carbon'] / lifespan_hours) * usage_fraction
                
                # Convert to gCO2e
                return hourly_emissions * 1000
                
            elif service_type in ['EC2', 'RDS', 'SageMaker']:
                # Use hardware profiles based on instance type
                result = self.embodied_calculator._calculate_hardware_embodied_carbon(
                    resource_id, usage_fraction=usage_fraction
                )
                if result is None or 'hourly_embodied_kgco2e' not in result:
                    return 0.0
                return result['hourly_embodied_kgco2e'] * 1000  # Convert to gCO2e
                
            elif service_type in ['Lambda', 'DynamoDB', 'ECS', 'EKS']:
                # Use simplified embodied emissions for serverless/managed services
                base_emissions = {
                    'Lambda': 50.0,      # gCO2e per GB of memory
                    'DynamoDB': 100.0,   # gCO2e per GB of storage
                    'ECS': 200.0,        # gCO2e per vCPU
                    'EKS': 200.0         # gCO2e per vCPU
                }
                return base_emissions.get(service_type, 0.0) * usage_fraction
                
        except Exception as e:
            print(f"Warning: Error calculating embodied emissions for {service_type}: {e}")
            return 0.0
            
        return 0.0

    def compare_models(
        self,
        model_ids: List[str],
        region: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, EnvironmentalMetrics]:
        """
        Compare environmental impact of multiple models.
        
        Args:
            model_ids: List of model identifiers to compare
            region: AWS region code
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary mapping model IDs to their environmental metrics
        """
        results = {}
        for model_id in model_ids:
            results[model_id] = self.calculate_total_footprint(
                model_id, region, input_tokens, output_tokens
            )
        return results

    def find_lowest_impact_region(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        metric: str = "combined"
    ) -> Tuple[str, EnvironmentalMetrics]:
        """
        Find the region with lowest environmental impact for a given model.
        
        Args:
            model_id: AWS Bedrock model identifier
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            metric: Impact metric to optimize for ('carbon', 'water', or 'combined')
            
        Returns:
            Tuple of (region_code, EnvironmentalMetrics)
        """
        regions = self.bedrock_calculator.get_supported_regions()
        best_region = None
        best_metrics = None
        best_score = float('inf')
        
        for region in regions:
            metrics = self.calculate_total_footprint(
                model_id, region, input_tokens, output_tokens
            )
            
            if metric == "carbon":
                score = metrics.carbon_footprint + metrics.embodied_emissions
            elif metric == "water":
                score = metrics.water_usage
            else:  # combined
                score = metrics.total_impact_score
                
            if score < best_score:
                best_score = score
                best_region = region
                best_metrics = metrics
                
        return best_region, best_metrics

    def _calculate_impact_score(
        self,
        carbon_emissions: float,
        embodied_emissions: float,
        water_usage: float,
        water_stress: str
    ) -> float:
        """
        Calculate a combined environmental impact score.
        
        Args:
            carbon_emissions: Operational carbon emissions in kg CO2e
            embodied_emissions: Embodied emissions in kg CO2e
            water_usage: Water usage in liters
            water_stress: Water stress level (Low, Medium, High, Very High)
        
        Returns:
            Float representing combined environmental impact score
        """
        # Normalize all metrics to a 0-100 scale
        
        # Carbon emissions normalization (assuming 1000 kg CO2e is max score of 100)
        carbon_score = min(100, (carbon_emissions / 10) * 100)
        
        # Embodied emissions normalization
        embodied_score = min(100, (embodied_emissions / 10) * 100)
        
        # Water usage score with stress multiplier
        water_stress_multiplier = {
            "Low": 1.0,
            "Medium": 1.5,
            "High": 2.0,
            "Very High": 3.0
        }.get(water_stress, 1.0)
        
        water_score = min(100, (water_usage * water_stress_multiplier / 1000) * 100)
        
        # Combined score with different weights
        weights = {
            'carbon': 0.5,
            'embodied': 0.3,
            'water': 0.2
        }
        
        impact_score = (
            carbon_score * weights['carbon'] +
            embodied_score * weights['embodied'] +
            water_score * weights['water']
        )
        
        return impact_score

    def _calculate_environmental_equivalents(
        self,
        emissions_kg: float,
        water_usage: float
    ) -> Dict[str, float]:
        """
        Calculate environmental equivalents for emissions and water usage.
        
        Args:
            emissions_kg: Total emissions in kg CO2e
            water_usage: Water usage in liters
            
        Returns:
            Dictionary with environmental equivalents
        """
        # Environmental equivalents for emissions
        trees_needed = emissions_kg * 0.039  # Trees needed to offset emissions annually
        car_miles = emissions_kg * 2.481     # Equivalent car miles driven
        laptop_hours = emissions_kg * 33.33  # Equivalent laptop usage hours
        
        # Environmental equivalents for water
        shower_minutes = water_usage / 9.5   # Average shower uses 9.5 liters per minute
        
        return {
            "trees_needed": round(trees_needed, 2),
            "car_miles": round(car_miles, 2),
            "laptop_hours": round(laptop_hours, 2),
            "shower_minutes": round(shower_minutes, 2)
        }

    def get_regions_with_water_usage(self) -> Dict[str, float]:
        """Get a dictionary of AWS regions with their water usage effectiveness."""
        return self.water_calculator.get_regions_with_wue()

if __name__ == "__main__":
    # Example usage
    calculator = AWSEnvironmentalCalculator()
    
    # Calculate total footprint for a model
    metrics = calculator.calculate_total_footprint(
        service_type="EC2",
        resource_id="t2.micro",
        region="us-east-1",
        usage_data={"hours": 24},
        usage_fraction=1.0
    )
    
    print(f"Carbon Footprint: {metrics.carbon_footprint:.2f} gCO2e")
    print(f"Embodied Emissions: {metrics.embodied_emissions:.2f} gCO2e")
    print(f"Water Usage: {metrics.water_usage:.2f} liters")
    print(f"Water Stress Level: {metrics.water_stress_level}")
    print(f"Total Impact Score: {metrics.total_impact_score:.2f}")
    print("\nEnvironmental Equivalents:")
    for key, value in metrics.environmental_equivalents.items():
        print(f"- {key}: {value:.2f}") 
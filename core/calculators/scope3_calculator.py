import os
import pandas as pd
from typing import Dict, Any, Optional, Union

from ..base.calculator_base import BaseCalculator
from ..data_providers.data_loader import DataLoader
from ..models.metrics import EnvironmentalMetrics

class Scope3Calculator(BaseCalculator):
    """
    Calculate environmental impact of AWS services using Scope 3 methodology.
    Focuses on carbon emissions, energy consumption, and water usage.
    """
    
    def __init__(self, data_dir: str = "data", mock_mode: bool = False):
        super().__init__(data_dir)
        self.mock_mode = mock_mode
        self.data_loader = DataLoader(data_dir=self.data_dir, mock_mode=self.mock_mode)
        
        # Load all needed data
        self._load_data()
        
    def _load_data(self):
        """Load all necessary data files"""
        self.carbon_intensity = self.data_loader.load_region_data("carbon_intensity")
        self.pue = self.data_loader.load_region_data("pue")
        self.water_usage = self.data_loader.load_region_data("water_usage")
        self.water_stress = self.data_loader.load_region_data("water_stress")
        self.model_energy = self.data_loader.load_model_data("energy_consumption")
        self.model_training = self.data_loader.load_model_data("training_footprint")
        
        # Default values for missing data
        self.default_carbon_intensity = 500.0  # gCO2e/kWh
        self.default_pue = 1.5
        self.default_water_usage = 1.8  # liters/kWh
        self.default_water_stress = "Medium"
    
    def get_carbon_intensity(self, region: str) -> float:
        """Get carbon intensity for a region (gCO2e/kWh)"""
        return self.carbon_intensity.get(region, self.default_carbon_intensity)
    
    def get_pue(self, region: str) -> float:
        """Get PUE (Power Usage Effectiveness) for a region"""
        return self.pue.get(region, self.default_pue)
    
    def get_water_usage(self, region: str) -> float:
        """Get water usage for a region (liters/kWh)"""
        return self.water_usage.get(region, self.default_water_usage)
    
    def get_water_stress(self, region: str) -> str:
        """Get water stress level for a region"""
        return self.water_stress.get(region, self.default_water_stress)
    
    def calculate(self, service_type: str, resource_id: str, 
                 region: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate environmental impact metrics for a resource
        
        Args:
            service_type: Type of AWS service (EC2, Lambda, Bedrock, etc.)
            resource_id: Resource identifier (instance type, model ID, etc.)
            region: AWS region
            usage_data: Usage metrics for the resource
            
        Returns:
            Dictionary with environmental impact metrics
        """
        service_type = service_type.lower()
        
        # Calculate energy consumption based on service type
        energy_kwh = self._calculate_energy_consumption(
            service_type, resource_id, usage_data
        )
        
        # Get region-specific factors
        carbon_intensity = self.get_carbon_intensity(region)
        pue = self.get_pue(region)
        water_usage_factor = self.get_water_usage(region)
        water_stress_level = self.get_water_stress(region)
        
        # Apply PUE to energy consumption
        total_energy = energy_kwh * pue
        
        # Calculate carbon emissions (convert to grams CO2e)
        carbon_emissions = total_energy * carbon_intensity
        
        # Calculate water usage (liters)
        water_usage = total_energy * water_usage_factor
        
        # Calculate embodied emissions if applicable
        embodied_emissions = self._calculate_embodied_emissions(
            service_type, resource_id, usage_data
        )
        
        # Create environmental metrics
        metrics = EnvironmentalMetrics(
            carbon_footprint_grams=carbon_emissions,
            energy_kwh=energy_kwh,
            water_usage_liters=water_usage,
            water_stress_level=water_stress_level,
            embodied_emissions_grams=embodied_emissions
        )
        
        # Calculate environmental equivalents
        equivalents = self._calculate_environmental_equivalents(
            carbon_emissions + (embodied_emissions or 0),
            water_usage
        )
        
        return {
            "environmental_metrics": metrics,
            "equivalents": equivalents
        }
    
    def _calculate_energy_consumption(
        self, service_type: str, resource_id: str, usage_data: Dict[str, Any]
    ) -> float:
        """Calculate energy consumption in kWh"""
        if 'bedrock' in service_type or 'ai' in service_type:
            return self._calculate_ai_energy_consumption(resource_id, usage_data)
        elif 'ec2' in service_type or 'compute' in service_type:
            return self._calculate_compute_energy_consumption(resource_id, usage_data)
        elif 'lambda' in service_type:
            return self._calculate_lambda_energy_consumption(usage_data)
        # Add more service types as needed
        else:
            # Default calculation
            return 0.05 * usage_data.get('hours', 1)
    
    def _calculate_ai_energy_consumption(
        self, model_id: str, usage_data: Dict[str, Any]
    ) -> float:
        """Calculate energy consumption for AI/ML models"""
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        
        # Get energy consumption data for this model
        model_data = self.model_energy.get(model_id, {})
        
        # Get energy consumption per million tokens
        input_kwh_per_million = model_data.get('input_kwh_per_million_tokens', 0.05)
        output_kwh_per_million = model_data.get('output_kwh_per_million_tokens', 0.15)
        
        # Calculate energy consumption
        input_energy = (input_tokens / 1000000) * input_kwh_per_million
        output_energy = (output_tokens / 1000000) * output_kwh_per_million
        
        return input_energy + output_energy
    
    def _calculate_compute_energy_consumption(
        self, instance_type: str, usage_data: Dict[str, Any]
    ) -> float:
        """Calculate energy consumption for compute resources"""
        hours = usage_data.get('hours', 1)
        
        # Power consumption estimates for EC2 instances (in watts)
        power_consumption = {
            't3.micro': 20,
            't3.small': 40,
            't3.medium': 80,
            'm5.large': 120,
            'c5.large': 135,
            'r5.large': 145,
            'p3.2xlarge': 650,
            'default': 100
        }
        
        # Get power consumption for this instance type (in watts)
        watts = power_consumption.get(instance_type, power_consumption['default'])
        
        # Convert watts to kWh
        kwh = (watts / 1000) * hours
        
        return kwh
    
    def _calculate_lambda_energy_consumption(
        self, usage_data: Dict[str, Any]
    ) -> float:
        """Calculate energy consumption for Lambda functions"""
        gb_seconds = usage_data.get('gb_seconds', 1)
        requests = usage_data.get('requests', 1)
        
        # Estimate energy consumption based on GB-seconds
        # Assumption: 1 GB-second consumes approximately 0.0000035 kWh
        energy_per_gb_second = 0.0000035
        
        return gb_seconds * energy_per_gb_second
    
    def _calculate_embodied_emissions(
        self, service_type: str, resource_id: str, usage_data: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate embodied emissions for hardware resources"""
        # Only apply embodied emissions to EC2 instances
        if 'ec2' in service_type or 'compute' in service_type:
            hours = usage_data.get('hours', 1)
            
            # Get instance family
            instance_family = resource_id.split('.')[0] if '.' in resource_id else 'default'
            
            # Embodied emissions estimates (gCO2e per hour)
            embodied_emissions = {
                't3': 10,  # Low for shared instances
                'm5': 25,  # Medium for general purpose
                'c5': 30,  # Higher for compute optimized
                'r5': 35,  # Higher for memory optimized
                'p3': 100, # Much higher for GPU instances
                'default': 20
            }
            
            # Get embodied emissions for this instance family
            hourly_emissions = embodied_emissions.get(instance_family, embodied_emissions['default'])
            
            return hourly_emissions * hours
        
        # For AI/ML models, use training footprint
        elif 'bedrock' in service_type or 'ai' in service_type:
            model_id = resource_id
            
            # Get training footprint data for this model
            model_data = self.model_training.get(model_id, {})
            
            # Get total emissions and expected inferences
            total_emissions = model_data.get('total_emissions_gco2e', 0)
            expected_inferences = model_data.get('expected_inferences', 1000000000)
            
            # Calculate amortized emissions per inference
            input_tokens = usage_data.get('input_tokens', 0)
            output_tokens = usage_data.get('output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            # Emission per token
            emission_per_token = total_emissions / (expected_inferences * 100)  # Assuming 100 tokens per inference
            
            return emission_per_token * total_tokens
        
        return None
    
    def _calculate_environmental_equivalents(
        self, total_emissions_g: float, water_usage_liters: float
    ) -> Dict[str, float]:
        """Calculate environmental equivalents for context"""
        # Convert emissions to kg
        emissions_kg = total_emissions_g / 1000
        
        # Environmental equivalents
        equivalents = {
            # Carbon equivalents
            "miles_driven": emissions_kg * 2.5,  # 1 kg CO2 = ~2.5 miles driven
            "smartphone_charges": emissions_kg * 63,  # 1 kg CO2 = ~63 smartphone charges
            "tree_days": emissions_kg * 4.3,  # Days of carbon sequestered by 1 tree
            
            # Water equivalents
            "water_bottles": water_usage_liters / 0.5,  # Number of 500ml water bottles
            "shower_minutes": water_usage_liters / 10,  # Minutes of shower time (10L/minute)
        }
        
        return equivalents 
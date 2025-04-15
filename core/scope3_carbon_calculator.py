"""
Scope3 Carbon Calculator for AWS Services.

This module implements the Scope3 methodology for assessing the environmental impact of AWS services,
with a particular focus on generative AI models. The implementation follows a lifecycle assessment 
approach that aligns with established standards such as GHG Protocol and ISO 14067.

The calculator categorizes impacts into scopes (1, 2, 3):
- Scope 1: Direct emissions from owned or controlled sources
- Scope 2: Indirect emissions from electricity consumption
- Scope 3: All other indirect emissions in the value chain

For AWS services, this calculator measures:
- Operational CO2e emissions (Scope 2)
- Embodied CO2e emissions (Scope 3)
- Water consumption and impact

References:
- https://github.com/scope3/methodology
- https://github.com/scope3/methodology/blob/main/methodology-genai-overview.md
- https://github.com/scope3/methodology/blob/main/methodology-genai-training.md
- https://github.com/scope3/methodology/blob/main/methodology-genai-inference.md
"""

import os
import csv
import logging
import pandas as pd
from typing import Dict, Tuple, Any, Optional, List, Union
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Scope3Calculator:
    """
    Calculator for AWS service environmental impact using the Scope3 methodology.
    
    This calculator provides methods to assess the carbon footprint and water usage
    of AWS services, particularly focusing on generative AI models.
    """
    
    # Default values when data is missing
    default_carbon_intensity = 300.0  # gCO2e/kWh (global average)
    default_pue = 1.2  # Power Usage Effectiveness
    default_wue = 1.8  # Water Usage Effectiveness (L/kWh)
    default_water_stress = 3.0  # Normalized water stress index (1-5)
    
    # Estimated power consumption for EC2 instances in watts
    # These are approximate values based on AWS documentation and third-party sources
    ec2_power_consumption = {
        # General Purpose
        "t2.micro": 5, "t2.small": 10, "t2.medium": 20, "t2.large": 40,
        "t3.micro": 5, "t3.small": 10, "t3.medium": 20, "t3.large": 35,
        "m5.large": 100, "m5.xlarge": 200, "m5.2xlarge": 400, "m5.4xlarge": 750,
        "m6i.large": 80, "m6i.xlarge": 160, "m6i.2xlarge": 320, "m6i.4xlarge": 640,
        # Compute Optimized
        "c5.large": 85, "c5.xlarge": 170, "c5.2xlarge": 340, "c5.4xlarge": 680,
        "c6i.large": 80, "c6i.xlarge": 155, "c6i.2xlarge": 310, "c6i.4xlarge": 620,
        # Memory Optimized
        "r5.large": 120, "r5.xlarge": 230, "r5.2xlarge": 450, "r5.4xlarge": 870,
        "r6i.large": 110, "r6i.xlarge": 210, "r6i.2xlarge": 420, "r6i.4xlarge": 840,
        # Storage Optimized
        "i3.large": 150, "i3.xlarge": 300, "i3.2xlarge": 600, "i3.4xlarge": 1200,
        # GPU Instances
        "p3.2xlarge": 650, "p3.8xlarge": 2500, "p3.16xlarge": 5000,
        "g4dn.xlarge": 300, "g4dn.2xlarge": 450, "g4dn.4xlarge": 750,
        # Default for unknown instances (per vCPU)
        "default_per_vcpu": 25
    }
    
    # Embodied emissions factor (manufacturing, transport, etc.) as ratio of operational emissions
    embodied_emissions_factor = 0.15  # 15% of operational emissions
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the calculator with regional and model-specific data.
        
        Args:
            data_dir: Directory containing the necessary data files
        """
        self.data_dir = data_dir
        
        # Load all required datasets
        self.carbon_intensity_df = self._load_carbon_intensity()
        self.pue_df = self._load_pue()
        self.wue_df = self._load_water_usage()
        self.water_stress_df = self._load_water_stress()
        self.model_energy_df = self._load_model_energy_consumption()
        self.model_training_df = self._load_model_training_footprint()
        
        # Log the number of regions and models loaded
        logger.info(f"Loaded carbon intensity data for {len(self.carbon_intensity_df)} regions")
        logger.info(f"Loaded PUE data for {len(self.pue_df)} regions")
        logger.info(f"Loaded water usage data for {len(self.wue_df)} regions")
        logger.info(f"Loaded water stress data for {len(self.water_stress_df)} regions")
        logger.info(f"Loaded energy consumption data for {len(self.model_energy_df)} models")
        logger.info(f"Loaded training footprint data for {len(self.model_training_df)} models")
    
    def _load_carbon_intensity(self) -> pd.DataFrame:
        """
        Load the carbon intensity data for each AWS region.
        
        Returns:
            DataFrame with region and carbon intensity (gCO2e/kWh)
        """
        try:
            file_path = os.path.join(self.data_dir, "region_carbon_intensity.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded carbon intensity data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load carbon intensity data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=["region", "carbon_intensity_gco2e_per_kwh"])
    
    def _load_pue(self) -> pd.DataFrame:
        """
        Load the Power Usage Effectiveness (PUE) data for each AWS region.
        
        Returns:
            DataFrame with region and PUE values
        """
        try:
            file_path = os.path.join(self.data_dir, "region_pue.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded PUE data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load PUE data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=["region", "pue"])
    
    def _load_water_usage(self) -> pd.DataFrame:
        """
        Load the Water Usage Effectiveness (WUE) data for each AWS region.
        
        Returns:
            DataFrame with region and WUE values (L/kWh)
        """
        try:
            file_path = os.path.join(self.data_dir, "region_water_usage.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded water usage data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load water usage data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=["region", "wue"])
    
    def _load_water_stress(self) -> pd.DataFrame:
        """
        Load the water stress data for each AWS region.
        
        Returns:
            DataFrame with region and water stress values (1-5 scale)
        """
        try:
            file_path = os.path.join(self.data_dir, "region_water_stress.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded water stress data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load water stress data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=["region", "water_stress"])
    
    def _load_model_energy_consumption(self) -> pd.DataFrame:
        """
        Load the energy consumption data for AI models.
        
        Returns:
            DataFrame with model_id and energy consumption values (Wh/1k tokens)
        """
        try:
            file_path = os.path.join(self.data_dir, "model_energy_consumption.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded model energy consumption data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load model energy consumption data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=[
                "model_id", "input_wh_per_1k_tokens", "output_wh_per_1k_tokens"
            ])
    
    def _load_model_training_footprint(self) -> pd.DataFrame:
        """
        Load the training footprint data for AI models.
        
        Returns:
            DataFrame with model_id, emissions, and expected inferences
        """
        try:
            file_path = os.path.join(self.data_dir, "model_training_footprint.csv")
            df = pd.read_csv(file_path)
            logger.info(f"Successfully loaded model training footprint data from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load model training footprint data: {str(e)}")
            # Return an empty DataFrame with the expected columns
            return pd.DataFrame(columns=[
                "model_id", "total_emissions_gco2e", "expected_inferences"
            ])
    
    def get_carbon_intensity(self, region: str) -> float:
        """
        Get the carbon intensity for a given AWS region.
        
        Args:
            region: AWS region code (e.g., 'us-east-1')
            
        Returns:
            Carbon intensity in gCO2e/kWh
        """
        if not self.carbon_intensity_df.empty:
            region_data = self.carbon_intensity_df[
                self.carbon_intensity_df["region"] == region
            ]
            
            if not region_data.empty:
                return region_data["carbon_intensity_gco2e_per_kwh"].iloc[0]
        
        logger.warning(
            f"Carbon intensity data not found for region {region}. "
            f"Using default value: {self.default_carbon_intensity} gCO2e/kWh"
        )
        return self.default_carbon_intensity
    
    def get_pue(self, region: str) -> float:
        """
        Get the Power Usage Effectiveness (PUE) for a given AWS region.
        
        Args:
            region: AWS region code (e.g., 'us-east-1')
            
        Returns:
            PUE value (dimensionless)
        """
        if not self.pue_df.empty:
            region_data = self.pue_df[self.pue_df["region"] == region]
            
            if not region_data.empty:
                return region_data["pue"].iloc[0]
        
        logger.warning(
            f"PUE data not found for region {region}. "
            f"Using default value: {self.default_pue}"
        )
        return self.default_pue
    
    def get_wue(self, region: str) -> float:
        """
        Get the Water Usage Effectiveness (WUE) for a given AWS region.
        
        Args:
            region: AWS region code (e.g., 'us-east-1')
            
        Returns:
            WUE value in L/kWh
        """
        if not self.wue_df.empty:
            region_data = self.wue_df[self.wue_df["region"] == region]
            
            if not region_data.empty:
                return region_data["wue"].iloc[0]
        
        logger.warning(
            f"Water usage data not found for region {region}. "
            f"Using default value: {self.default_wue} L/kWh"
        )
        return self.default_wue
    
    def get_water_stress(self, region: str) -> float:
        """
        Get the water stress index for a given AWS region.
        
        Args:
            region: AWS region code (e.g., 'us-east-1')
            
        Returns:
            Water stress index (1-5 scale)
        """
        if not self.water_stress_df.empty:
            region_data = self.water_stress_df[
                self.water_stress_df["region"] == region
            ]
            
            if not region_data.empty:
                return region_data["water_stress"].iloc[0]
        
        logger.warning(
            f"Water stress data not found for region {region}. "
            f"Using default value: {self.default_water_stress}"
        )
        return self.default_water_stress
    
    def get_model_energy_consumption(self, model_id: str) -> Tuple[float, float]:
        """
        Get the energy consumption data for a given AI model.
        
        Args:
            model_id: Identifier for the AI model
            
        Returns:
            Tuple of (input_wh_per_1k_tokens, output_wh_per_1k_tokens)
        """
        if not self.model_energy_df.empty:
            model_data = self.model_energy_df[
                self.model_energy_df["model_id"] == model_id
            ]
            
            if not model_data.empty:
                return (
                    model_data["input_wh_per_1k_tokens"].iloc[0],
                    model_data["output_wh_per_1k_tokens"].iloc[0]
                )
        
        # If model not found, use average values from the dataset
        if not self.model_energy_df.empty:
            avg_input = self.model_energy_df["input_wh_per_1k_tokens"].mean()
            avg_output = self.model_energy_df["output_wh_per_1k_tokens"].mean()
            
            logger.warning(
                f"Energy consumption data not found for model {model_id}. "
                f"Using average values: {avg_input:.5f} Wh/1k input tokens, "
                f"{avg_output:.5f} Wh/1k output tokens"
            )
            
            return avg_input, avg_output
        
        # If no data available at all
        logger.warning(
            f"No energy consumption data available. "
            f"Using default values: 0.1 Wh/1k input tokens, 0.3 Wh/1k output tokens"
        )
        return 0.1, 0.3
    
    def get_model_training_footprint(self, model_id: str) -> Tuple[float, float]:
        """
        Get the training footprint data for a given AI model.
        
        Args:
            model_id: Identifier for the AI model
            
        Returns:
            Tuple of (total_emissions_gco2e, expected_inferences)
        """
        if not self.model_training_df.empty:
            model_data = self.model_training_df[
                self.model_training_df["model_id"] == model_id
            ]
            
            if not model_data.empty:
                return (
                    model_data["total_emissions_gco2e"].iloc[0],
                    model_data["expected_inferences"].iloc[0]
                )
        
        logger.warning(
            f"Training footprint data not found for model {model_id}. "
            f"Using default values: 0 gCO2e total emissions, 1 expected inference"
        )
        return 0.0, 1.0
    
    def calculate_inference_carbon_footprint(
        self,
        model_id: str,
        region: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Calculate the carbon footprint for a specific AI model inference.
        
        Args:
            model_id: Identifier for the AI model
            region: AWS region code (e.g., 'us-east-1')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary with emissions data, energy usage, and water impact
        """
        # Get region-specific data
        carbon_intensity = self.get_carbon_intensity(region)
        pue = self.get_pue(region)
        wue = self.get_wue(region)
        water_stress = self.get_water_stress(region)
        
        # Get model-specific energy consumption
        input_energy_per_1k, output_energy_per_1k = self.get_model_energy_consumption(model_id)
        
        # Calculate energy consumption in kWh
        input_energy_wh = (input_tokens / 1000) * input_energy_per_1k
        output_energy_wh = (output_tokens / 1000) * output_energy_per_1k
        total_energy_wh = input_energy_wh + output_energy_wh
        
        # Apply PUE to get total energy including data center overhead
        total_energy_with_pue_wh = total_energy_wh * pue
        total_energy_kwh = total_energy_with_pue_wh / 1000
        
        # Calculate Scope 2 emissions (from electricity)
        scope2_emissions = total_energy_kwh * carbon_intensity
        
        # Get training footprint data for Scope 3 emissions
        training_emissions, expected_inferences = self.get_model_training_footprint(model_id)
        scope3_emissions = training_emissions / expected_inferences
        
        # Calculate total emissions
        total_emissions = scope2_emissions + scope3_emissions
        
        # Calculate water usage
        water_usage = total_energy_kwh * wue
        
        # Calculate water impact (water usage weighted by water stress)
        water_impact = water_usage * (water_stress / self.default_water_stress)
        
        return {
            "scope1_emissions_gco2e": 0.0,  # No direct emissions for cloud services
            "scope2_emissions_gco2e": scope2_emissions,
            "scope3_emissions_gco2e": scope3_emissions,
            "total_emissions_gco2e": total_emissions,
            "energy_kwh": total_energy_kwh,
            "water_usage_liters": water_usage,
            "water_impact_score": water_impact
        }
    
    def calculate_ec2_carbon_footprint(
        self,
        instance_type: str,
        region: str,
        hours: float,
        count: int = 1
    ) -> Dict[str, float]:
        """
        Calculate the carbon footprint for EC2 instance usage.
        
        Args:
            instance_type: EC2 instance type (e.g., 'm5.xlarge')
            region: AWS region code (e.g., 'us-east-1')
            hours: Usage hours
            count: Number of instances
            
        Returns:
            Dictionary with emissions data, energy usage, and water impact
        """
        # Get region-specific data
        carbon_intensity = self.get_carbon_intensity(region)
        pue = self.get_pue(region)
        wue = self.get_wue(region)
        water_stress = self.get_water_stress(region)
        
        # Get power consumption for the instance type in watts
        if instance_type in self.ec2_power_consumption:
            power_watts = self.ec2_power_consumption[instance_type]
        else:
            # Estimate based on instance size if not in our database
            if "." in instance_type:
                instance_family = instance_type.split(".")[0]
                instance_size = instance_type.split(".")[1]
                
                # Estimate vCPUs based on instance size
                vcpus = 1
                if "micro" in instance_size:
                    vcpus = 1
                elif "small" in instance_size:
                    vcpus = 1
                elif "medium" in instance_size:
                    vcpus = 2
                elif "large" in instance_size:
                    vcpus = 2
                elif "xlarge" in instance_size:
                    vcpus = 4
                elif "2xlarge" in instance_size:
                    vcpus = 8
                elif "4xlarge" in instance_size:
                    vcpus = 16
                elif "8xlarge" in instance_size:
                    vcpus = 32
                elif "16xlarge" in instance_size:
                    vcpus = 64
                
                # Estimate power based on vCPUs
                power_watts = vcpus * self.ec2_power_consumption["default_per_vcpu"]
            else:
                # Default power consumption if we can't determine instance type
                power_watts = 100
                
            logger.warning(
                f"Power consumption data not found for instance type {instance_type}. "
                f"Estimated value: {power_watts} watts"
            )
        
        # Calculate energy consumption in kWh
        # Energy (kWh) = Power (W) * Time (h) * Count / 1000
        energy_kwh = (power_watts * hours * count) / 1000
        
        # Apply PUE to get total energy including data center overhead
        total_energy_kwh = energy_kwh * pue
        
        # Calculate Scope 2 emissions (from electricity)
        scope2_emissions = total_energy_kwh * carbon_intensity
        
        # Calculate Scope 3 emissions (embodied emissions)
        scope3_emissions = scope2_emissions * self.embodied_emissions_factor
        
        # Calculate total emissions
        total_emissions = scope2_emissions + scope3_emissions
        
        # Calculate water usage
        water_usage = total_energy_kwh * wue
        
        # Calculate water impact (water usage weighted by water stress)
        water_impact = water_usage * (water_stress / self.default_water_stress)
        
        return {
            "scope1_emissions_gco2e": 0.0,  # No direct emissions for cloud services
            "scope2_emissions_gco2e": scope2_emissions,
            "scope3_emissions_gco2e": scope3_emissions,
            "total_emissions_gco2e": total_emissions,
            "energy_kwh": total_energy_kwh,
            "water_usage_liters": water_usage,
            "water_impact_score": water_impact
        }
    
    def calculate_total_environmental_impact(
        self,
        service_type: str,
        resource_id: str,
        region: str,
        usage_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate the total environmental impact for any AWS service.
        
        Args:
            service_type: Type of AWS service (e.g., 'ec2', 'bedrock')
            resource_id: Identifier for the resource (instance type, model ID)
            region: AWS region code (e.g., 'us-east-1')
            usage_data: Dictionary with usage data specific to the service type
            
        Returns:
            Dictionary with emissions data, energy usage, and water impact
        """
        if service_type.lower() == "ec2":
            return self.calculate_ec2_carbon_footprint(
                instance_type=resource_id,
                region=region,
                hours=usage_data.get("hours", 0),
                count=usage_data.get("count", 1)
            )
        elif service_type.lower() in ["bedrock", "sagemaker"]:
            return self.calculate_inference_carbon_footprint(
                model_id=resource_id,
                region=region,
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0)
            )
        else:
            # For other services, use a generic approach based on estimated kWh
            # Get region-specific data
            carbon_intensity = self.get_carbon_intensity(region)
            pue = self.get_pue(region)
            wue = self.get_wue(region)
            water_stress = self.get_water_stress(region)
            
            # Use provided energy estimate or a default value
            estimated_kwh = usage_data.get("estimated_kwh", 0)
            
            # Apply PUE to get total energy including data center overhead
            total_energy_kwh = estimated_kwh * pue
            
            # Calculate Scope 2 emissions (from electricity)
            scope2_emissions = total_energy_kwh * carbon_intensity
            
            # Calculate Scope 3 emissions (embodied emissions)
            scope3_emissions = scope2_emissions * self.embodied_emissions_factor
            
            # Calculate total emissions
            total_emissions = scope2_emissions + scope3_emissions
            
            # Calculate water usage
            water_usage = total_energy_kwh * wue
            
            # Calculate water impact (water usage weighted by water stress)
            water_impact = water_usage * (water_stress / self.default_water_stress)
            
            return {
                "scope1_emissions_gco2e": 0.0,
                "scope2_emissions_gco2e": scope2_emissions,
                "scope3_emissions_gco2e": scope3_emissions,
                "total_emissions_gco2e": total_emissions,
                "energy_kwh": total_energy_kwh,
                "water_usage_liters": water_usage,
                "water_impact_score": water_impact
            } 
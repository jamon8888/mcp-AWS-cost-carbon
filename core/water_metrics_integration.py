#!/usr/bin/env python3
"""
Water Metrics Integration
------------------------
Integration with water usage and stress metrics for AWS services.
"""

import os
from typing import Dict, Any, Optional

from .data_providers.data_loader import DataLoader

class BedrockWaterCalculator:
    """Calculator for water usage and stress metrics for AWS services."""
    
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
        
        # Load data using DataLoader
        self.region_water_usage = self.data_loader.load_region_data("water_usage")
        self.region_water_stress = self.data_loader.load_region_data("water_stress")
        
        # Default values
        self.default_water_usage = 1.8  # liters/kWh
        self.default_water_stress = "Medium"
    
    def get_water_usage(self, region: str) -> float:
        """Get water usage for a region (liters/kWh)."""
        return self.region_water_usage.get(region, self.default_water_usage)
    
    def get_water_stress(self, region: str) -> str:
        """Get water stress level for a region."""
        return self.region_water_stress.get(region, self.default_water_stress)
    
    def calculate_water_metrics(self, region: str, energy_kwh: float) -> Dict[str, Any]:
        """
        Calculate water metrics for a region and energy consumption.
        
        Args:
            region: AWS region
            energy_kwh: Energy consumption in kWh
            
        Returns:
            Dictionary with water metrics
        """
        water_usage = self.get_water_usage(region) * energy_kwh
        water_stress = self.get_water_stress(region)
        
        return {
            "water_usage_liters": water_usage,
            "water_stress_level": water_stress
        } 
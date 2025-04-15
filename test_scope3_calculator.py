"""
Unit tests for the Scope3Calculator class.

This module contains tests for the Scope3Calculator class, which is used
to calculate the environmental impact of AWS services using the Scope3 methodology.
"""

import unittest
import os
import pandas as pd
import tempfile
import shutil
from core.scope3_carbon_calculator import Scope3Calculator

class TestScope3Calculator(unittest.TestCase):
    """Test cases for the Scope3Calculator class."""
    
    def setUp(self):
        """Set up test environment with sample data files."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample carbon intensity data
        carbon_intensity_data = pd.DataFrame({
            "region": ["us-east-1", "us-west-2", "eu-west-1"],
            "carbon_intensity_gco2e_per_kwh": [385.0, 136.3, 267.5]
        })
        carbon_intensity_data.to_csv(
            os.path.join(self.temp_dir, "region_carbon_intensity.csv"),
            index=False
        )
        
        # Create sample PUE data
        pue_data = pd.DataFrame({
            "region": ["us-east-1", "us-west-2", "eu-west-1"],
            "pue": [1.2, 1.15, 1.18]
        })
        pue_data.to_csv(
            os.path.join(self.temp_dir, "region_pue.csv"),
            index=False
        )
        
        # Create sample water usage data
        wue_data = pd.DataFrame({
            "region": ["us-east-1", "us-west-2", "eu-west-1"],
            "wue": [1.8, 1.5, 1.6]
        })
        wue_data.to_csv(
            os.path.join(self.temp_dir, "region_water_usage.csv"),
            index=False
        )
        
        # Create sample water stress data
        water_stress_data = pd.DataFrame({
            "region": ["us-east-1", "us-west-2", "eu-west-1"],
            "water_stress": [3.2, 4.1, 2.5]
        })
        water_stress_data.to_csv(
            os.path.join(self.temp_dir, "region_water_stress.csv"),
            index=False
        )
        
        # Create sample model energy consumption data
        model_energy_data = pd.DataFrame({
            "model_id": ["anthropic.claude-v2", "anthropic.claude-instant-v1", "amazon.titan-text-express-v1"],
            "input_wh_per_1k_tokens": [0.01, 0.005, 0.008],
            "output_wh_per_1k_tokens": [0.03, 0.015, 0.02]
        })
        model_energy_data.to_csv(
            os.path.join(self.temp_dir, "model_energy_consumption.csv"),
            index=False
        )
        
        # Create sample model training footprint data
        model_training_data = pd.DataFrame({
            "model_id": ["anthropic.claude-v2", "anthropic.claude-instant-v1", "amazon.titan-text-express-v1"],
            "total_emissions_gco2e": [250000, 120000, 180000],
            "expected_inferences": [1000000000, 800000000, 900000000]
        })
        model_training_data.to_csv(
            os.path.join(self.temp_dir, "model_training_footprint.csv"),
            index=False
        )
        
        # Initialize the calculator with the temp directory
        self.calculator = Scope3Calculator(data_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.temp_dir)
    
    def test_data_loading(self):
        """Test that data frames are loaded correctly."""
        # Check that all data frames have been loaded
        self.assertFalse(self.calculator.carbon_intensity_df.empty)
        self.assertFalse(self.calculator.pue_df.empty)
        self.assertFalse(self.calculator.wue_df.empty)
        self.assertFalse(self.calculator.water_stress_df.empty)
        self.assertFalse(self.calculator.model_energy_df.empty)
        self.assertFalse(self.calculator.model_training_df.empty)
        
        # Check the number of regions loaded
        self.assertEqual(len(self.calculator.carbon_intensity_df), 3)
    
    def test_get_carbon_intensity(self):
        """Test getting carbon intensity for a region."""
        # Test known region
        self.assertEqual(self.calculator.get_carbon_intensity("us-east-1"), 385.0)
        
        # Test unknown region (should return default)
        self.assertEqual(
            self.calculator.get_carbon_intensity("non-existent-region"),
            self.calculator.default_carbon_intensity
        )
    
    def test_get_pue(self):
        """Test getting PUE for a region."""
        # Test known region
        self.assertEqual(self.calculator.get_pue("us-west-2"), 1.15)
        
        # Test unknown region (should return default)
        self.assertEqual(
            self.calculator.get_pue("non-existent-region"),
            self.calculator.default_pue
        )
    
    def test_get_wue(self):
        """Test getting WUE for a region."""
        # Test known region
        self.assertEqual(self.calculator.get_wue("eu-west-1"), 1.6)
        
        # Test unknown region (should return default)
        self.assertEqual(
            self.calculator.get_wue("non-existent-region"),
            self.calculator.default_wue
        )
    
    def test_get_water_stress(self):
        """Test getting water stress for a region."""
        # Test known region
        self.assertEqual(self.calculator.get_water_stress("us-west-2"), 4.1)
        
        # Test unknown region (should return default)
        self.assertEqual(
            self.calculator.get_water_stress("non-existent-region"),
            self.calculator.default_water_stress
        )
    
    def test_get_model_energy_consumption(self):
        """Test getting energy consumption for a model."""
        # Test known model
        input_energy, output_energy = self.calculator.get_model_energy_consumption("anthropic.claude-v2")
        self.assertEqual(input_energy, 0.01)
        self.assertEqual(output_energy, 0.03)
        
        # Test unknown model (should return average values)
        input_energy, output_energy = self.calculator.get_model_energy_consumption("non-existent-model")
        self.assertIsInstance(input_energy, float)
        self.assertIsInstance(output_energy, float)
    
    def test_get_model_training_footprint(self):
        """Test getting training footprint for a model."""
        # Test known model
        emissions, inferences = self.calculator.get_model_training_footprint("anthropic.claude-instant-v1")
        self.assertEqual(emissions, 120000)
        self.assertEqual(inferences, 800000000)
        
        # Test unknown model (should return defaults)
        emissions, inferences = self.calculator.get_model_training_footprint("non-existent-model")
        self.assertEqual(emissions, 0.0)
        self.assertEqual(inferences, 1.0)
    
    def test_calculate_inference_carbon_footprint(self):
        """Test calculating carbon footprint for model inference."""
        result = self.calculator.calculate_inference_carbon_footprint(
            model_id="anthropic.claude-v2",
            region="us-east-1",
            input_tokens=10000,
            output_tokens=5000
        )
        
        # Check that all expected keys are present
        expected_keys = [
            "scope1_emissions_gco2e",
            "scope2_emissions_gco2e", 
            "scope3_emissions_gco2e",
            "total_emissions_gco2e",
            "energy_kwh",
            "water_usage_liters",
            "water_impact_score"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify correct calculations for a few key values
        self.assertEqual(result["scope1_emissions_gco2e"], 0.0)
        
        # Check that values are in a reasonable range
        self.assertGreater(result["scope2_emissions_gco2e"], 0)
        self.assertGreater(result["total_emissions_gco2e"], 0)
        self.assertGreater(result["energy_kwh"], 0)
        self.assertGreater(result["water_usage_liters"], 0)
        
        # Calculate expected values manually to verify
        # Energy: (10000 / 1000 * 0.01 + 5000 / 1000 * 0.03) * 1.2 / 1000 = 0.00027 kWh
        # Scope2: 0.00027 * 385 = 0.10395 gCO2e
        # Scope3: 250000 / 1000000000 = 0.00025 gCO2e
        # Total: 0.10395 + 0.00025 = 0.1042 gCO2e
        # Water: 0.00027 * 1.8 = 0.000486 L
        
        # Allow for small floating point differences
        self.assertAlmostEqual(result["energy_kwh"], 0.00027, places=5)
        self.assertAlmostEqual(result["scope2_emissions_gco2e"], 0.10395, places=5)
        self.assertAlmostEqual(result["scope3_emissions_gco2e"], 0.00025, places=5)
        self.assertAlmostEqual(result["total_emissions_gco2e"], 0.1042, places=4)
        self.assertAlmostEqual(result["water_usage_liters"], 0.000486, places=6)
    
    def test_calculate_ec2_carbon_footprint(self):
        """Test calculating carbon footprint for EC2 instance."""
        result = self.calculator.calculate_ec2_carbon_footprint(
            instance_type="m5.xlarge",
            region="us-west-2",
            hours=24,
            count=2
        )
        
        # Check that all expected keys are present
        expected_keys = [
            "scope1_emissions_gco2e",
            "scope2_emissions_gco2e", 
            "scope3_emissions_gco2e",
            "total_emissions_gco2e",
            "energy_kwh",
            "water_usage_liters",
            "water_impact_score"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify correct calculations for a few key values
        self.assertEqual(result["scope1_emissions_gco2e"], 0.0)
        
        # Check that values are in a reasonable range
        self.assertGreater(result["scope2_emissions_gco2e"], 0)
        self.assertGreater(result["total_emissions_gco2e"], 0)
        self.assertGreater(result["energy_kwh"], 0)
        self.assertGreater(result["water_usage_liters"], 0)
        
        # Calculate expected values manually to verify
        # Energy: 200W * 24h * 2 * 1.15 / 1000 = 11.04 kWh
        # Scope2: 11.04 * 136.3 = 1504.752 gCO2e
        # Scope3: 1504.752 * 0.15 = 225.7128 gCO2e
        # Total: 1504.752 + 225.7128 = 1730.4648 gCO2e
        # Water: 11.04 * 1.5 = 16.56 L
        
        # Allow for small floating point differences
        self.assertAlmostEqual(result["energy_kwh"], 11.04, places=2)
        self.assertAlmostEqual(result["scope2_emissions_gco2e"], 1504.752, places=2)
        self.assertAlmostEqual(result["scope3_emissions_gco2e"], 225.7128, places=2)
        self.assertAlmostEqual(result["total_emissions_gco2e"], 1730.4648, places=2)
        self.assertAlmostEqual(result["water_usage_liters"], 16.56, places=2)
    
    def test_calculate_ec2_carbon_footprint_unknown_instance(self):
        """Test calculating carbon footprint for unknown EC2 instance type."""
        result = self.calculator.calculate_ec2_carbon_footprint(
            instance_type="custom.4xlarge",
            region="eu-west-1",
            hours=10,
            count=1
        )
        
        # Check that calculation succeeds even with unknown instance type
        self.assertGreater(result["energy_kwh"], 0)
        self.assertGreater(result["total_emissions_gco2e"], 0)
    
    def test_calculate_total_environmental_impact(self):
        """Test calculating total environmental impact for different service types."""
        # Test for EC2
        ec2_result = self.calculator.calculate_total_environmental_impact(
            service_type="ec2",
            resource_id="m5.large",
            region="us-east-1",
            usage_data={"hours": 12, "count": 3}
        )
        
        # Test for Bedrock
        bedrock_result = self.calculator.calculate_total_environmental_impact(
            service_type="bedrock",
            resource_id="anthropic.claude-instant-v1",
            region="us-west-2",
            usage_data={"input_tokens": 20000, "output_tokens": 10000}
        )
        
        # Test for generic service
        generic_result = self.calculator.calculate_total_environmental_impact(
            service_type="s3",
            resource_id="storage",
            region="eu-west-1",
            usage_data={"estimated_kwh": 0.5}
        )
        
        # Check that all results have the same structure
        for result in [ec2_result, bedrock_result, generic_result]:
            self.assertIn("total_emissions_gco2e", result)
            self.assertIn("water_usage_liters", result)
            self.assertGreater(result["total_emissions_gco2e"], 0)
            
        # Results should be different for different service types
        self.assertNotEqual(ec2_result["total_emissions_gco2e"], bedrock_result["total_emissions_gco2e"])
        self.assertNotEqual(bedrock_result["total_emissions_gco2e"], generic_result["total_emissions_gco2e"])

if __name__ == "__main__":
    unittest.main() 
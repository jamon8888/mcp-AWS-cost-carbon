"""
Tests for the Scope3 Calculator implementation.
"""

import os
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add the parent directory to the path to import the calculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scope3_carbon_calculator import Scope3Calculator

class TestScope3Calculator(unittest.TestCase):
    """Test cases for the Scope3Calculator class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary directory for test data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name
        
        # Create sample test data
        self._create_test_data()
        
        # Initialize the calculator with the test data directory
        self.calculator = Scope3Calculator(data_dir=self.data_dir)
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def _create_test_data(self):
        """Create sample data files for testing."""
        # Sample carbon intensity data
        carbon_df = pd.DataFrame({
            'region': ['us-east-1', 'eu-west-1', 'ap-southeast-2'],
            'carbon_intensity_gco2e_per_kwh': [360.0, 240.0, 790.0]
        })
        carbon_df.to_csv(os.path.join(self.data_dir, 'region_carbon_intensity.csv'), index=False)
        
        # Sample PUE data
        pue_df = pd.DataFrame({
            'region': ['us-east-1', 'eu-west-1', 'ap-southeast-2'],
            'pue': [1.2, 1.15, 1.25]
        })
        pue_df.to_csv(os.path.join(self.data_dir, 'region_pue.csv'), index=False)
        
        # Sample water usage data
        wue_df = pd.DataFrame({
            'region': ['us-east-1', 'eu-west-1', 'ap-southeast-2'],
            'wue': [1.8, 1.6, 2.0]
        })
        wue_df.to_csv(os.path.join(self.data_dir, 'region_water_usage.csv'), index=False)
        
        # Sample water stress data
        stress_df = pd.DataFrame({
            'region': ['us-east-1', 'eu-west-1', 'ap-southeast-2'],
            'water_stress': [3.5, 2.0, 4.0]
        })
        stress_df.to_csv(os.path.join(self.data_dir, 'region_water_stress.csv'), index=False)
        
        # Sample model energy data
        model_energy_df = pd.DataFrame({
            'model_id': ['anthropic.claude-v2', 'amazon.titan-text-express-v1', 'ai21.j2-mid-v1'],
            'input_wh_per_1k_tokens': [0.1, 0.05, 0.08],
            'output_wh_per_1k_tokens': [0.3, 0.15, 0.25]
        })
        model_energy_df.to_csv(os.path.join(self.data_dir, 'model_energy_consumption.csv'), index=False)
        
        # Sample model training data
        model_training_df = pd.DataFrame({
            'model_id': ['anthropic.claude-v2', 'amazon.titan-text-express-v1', 'ai21.j2-mid-v1'],
            'total_emissions_gco2e': [1000000.0, 500000.0, 800000.0],
            'expected_inferences': [10000000, 8000000, 9000000]
        })
        model_training_df.to_csv(os.path.join(self.data_dir, 'model_training_footprint.csv'), index=False)
    
    def test_data_loading(self):
        """Test that data is loaded correctly."""
        # Check that data frames were loaded
        self.assertEqual(len(self.calculator.carbon_intensity_df), 3)
        self.assertEqual(len(self.calculator.pue_df), 3)
        self.assertEqual(len(self.calculator.wue_df), 3)
        self.assertEqual(len(self.calculator.water_stress_df), 3)
        self.assertEqual(len(self.calculator.model_energy_df), 3)
        self.assertEqual(len(self.calculator.model_training_df), 3)
    
    def test_get_carbon_intensity(self):
        """Test the get_carbon_intensity method."""
        # Test with existing region
        self.assertEqual(self.calculator.get_carbon_intensity('us-east-1'), 360.0)
        self.assertEqual(self.calculator.get_carbon_intensity('eu-west-1'), 240.0)
        
        # Test with non-existent region (should return default)
        self.assertEqual(self.calculator.get_carbon_intensity('non-existent-region'), 
                         self.calculator.default_carbon_intensity)
    
    def test_get_pue(self):
        """Test the get_pue method."""
        # Test with existing region
        self.assertEqual(self.calculator.get_pue('us-east-1'), 1.2)
        self.assertEqual(self.calculator.get_pue('eu-west-1'), 1.15)
        
        # Test with non-existent region (should return default)
        self.assertEqual(self.calculator.get_pue('non-existent-region'), 
                         self.calculator.default_pue)
    
    def test_get_wue(self):
        """Test the get_wue method."""
        # Test with existing region
        self.assertEqual(self.calculator.get_wue('us-east-1'), 1.8)
        self.assertEqual(self.calculator.get_wue('eu-west-1'), 1.6)
        
        # Test with non-existent region (should return default)
        self.assertEqual(self.calculator.get_wue('non-existent-region'), 
                         self.calculator.default_wue)
    
    def test_get_water_stress(self):
        """Test the get_water_stress method."""
        # Test with existing region
        self.assertEqual(self.calculator.get_water_stress('us-east-1'), 3.5)
        self.assertEqual(self.calculator.get_water_stress('eu-west-1'), 2.0)
        
        # Test with non-existent region (should return default)
        self.assertEqual(self.calculator.get_water_stress('non-existent-region'), 
                         self.calculator.default_water_stress)
    
    def test_get_model_energy_consumption(self):
        """Test the get_model_energy_consumption method."""
        # Test with existing model
        input_energy, output_energy = self.calculator.get_model_energy_consumption('anthropic.claude-v2')
        self.assertEqual(input_energy, 0.1)
        self.assertEqual(output_energy, 0.3)
        
        # Test with non-existent model (should return average values)
        with patch('logging.Logger.warning') as mock_warning:
            input_energy, output_energy = self.calculator.get_model_energy_consumption('non-existent-model')
            mock_warning.assert_called_once()
            self.assertAlmostEqual(input_energy, 0.07666, places=4)  # average of input values
            self.assertAlmostEqual(output_energy, 0.23333, places=4)  # average of output values
    
    def test_get_model_training_footprint(self):
        """Test the get_model_training_footprint method."""
        # Test with existing model
        emissions, inferences = self.calculator.get_model_training_footprint('anthropic.claude-v2')
        self.assertEqual(emissions, 1000000.0)
        self.assertEqual(inferences, 10000000)
        
        # Test with non-existent model (should return default values)
        with patch('logging.Logger.warning') as mock_warning:
            emissions, inferences = self.calculator.get_model_training_footprint('non-existent-model')
            mock_warning.assert_called_once()
            self.assertEqual(emissions, 0.0)
            self.assertEqual(inferences, 1.0)
    
    def test_calculate_inference_carbon_footprint(self):
        """Test the calculate_inference_carbon_footprint method."""
        # Calculate footprint for a specific model and region
        result = self.calculator.calculate_inference_carbon_footprint(
            model_id='anthropic.claude-v2',
            region='us-east-1',
            input_tokens=1000,
            output_tokens=500
        )
        
        # Check that all expected keys are present
        expected_keys = [
            "scope1_emissions_gco2e", "scope2_emissions_gco2e", "scope3_emissions_gco2e",
            "total_emissions_gco2e", "energy_kwh", "water_usage_liters", "water_impact_score"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify the calculations
        # Input: 1000 tokens = 1 * 0.1Wh = 0.1Wh
        # Output: 500 tokens = 0.5 * 0.3Wh = 0.15Wh
        # Total: 0.25Wh = 0.00025kWh
        # With PUE (1.2): 0.0003kWh
        # Scope2 emissions: 0.0003kWh * 360gCO2e/kWh = 0.108gCO2e
        # Scope3 emissions: 1000000gCO2e / 10000000 = 0.1gCO2e
        # Total emissions: 0.108 + 0.1 = 0.208gCO2e
        
        self.assertAlmostEqual(result["energy_kwh"], 0.0003, places=5)
        self.assertAlmostEqual(result["scope2_emissions_gco2e"], 0.108, places=3)
        self.assertAlmostEqual(result["scope3_emissions_gco2e"], 0.1, places=3)
        self.assertAlmostEqual(result["total_emissions_gco2e"], 0.208, places=3)
        
        # Water usage: 0.0003kWh * 1.8L/kWh = 0.00054L
        # Water impact: 0.00054L * (3.5/3.0) = 0.00063L
        self.assertAlmostEqual(result["water_usage_liters"], 0.00054, places=5)
        self.assertAlmostEqual(result["water_impact_score"], 0.00063, places=5)
    
    def test_calculate_ec2_carbon_footprint(self):
        """Test the calculate_ec2_carbon_footprint method."""
        # Calculate footprint for a specific instance and region
        result = self.calculator.calculate_ec2_carbon_footprint(
            instance_type='m5.xlarge',
            region='eu-west-1',
            hours=10,
            count=2
        )
        
        # Check that all expected keys are present
        expected_keys = [
            "scope1_emissions_gco2e", "scope2_emissions_gco2e", "scope3_emissions_gco2e",
            "total_emissions_gco2e", "energy_kwh", "water_usage_liters", "water_impact_score"
        ]
        for key in expected_keys:
            self.assertIn(key, result)
        
        # Verify the calculations
        # Power: 200W for m5.xlarge
        # Energy: 200W * 10h * 2 instances = 4000Wh = 4kWh
        # With PUE (1.15): 4.6kWh
        # Scope2 emissions: 4.6kWh * 240gCO2e/kWh = 1104gCO2e
        # Scope3 emissions: 1104gCO2e * 0.15 = 165.6gCO2e
        # Total emissions: 1104 + 165.6 = 1269.6gCO2e
        
        self.assertAlmostEqual(result["energy_kwh"], 4.6, places=1)
        self.assertAlmostEqual(result["scope2_emissions_gco2e"], 1104, places=1)
        self.assertAlmostEqual(result["scope3_emissions_gco2e"], 165.6, places=1)
        self.assertAlmostEqual(result["total_emissions_gco2e"], 1269.6, places=1)
        
        # Water usage: 4.6kWh * 1.6L/kWh = 7.36L
        # Water impact: 7.36L * (2.0/3.0) = 4.90667L
        self.assertAlmostEqual(result["water_usage_liters"], 7.36, places=2)
        self.assertAlmostEqual(result["water_impact_score"], 4.91, places=2)
    
    def test_calculate_total_environmental_impact(self):
        """Test the calculate_total_environmental_impact method."""
        # Test EC2 calculation
        ec2_result = self.calculator.calculate_total_environmental_impact(
            service_type='ec2',
            resource_id='c5.xlarge',
            region='us-east-1',
            usage_data={'hours': 5, 'count': 1}
        )
        self.assertIn("total_emissions_gco2e", ec2_result)
        
        # Test Bedrock calculation
        bedrock_result = self.calculator.calculate_total_environmental_impact(
            service_type='bedrock',
            resource_id='anthropic.claude-v2',
            region='us-east-1',
            usage_data={'input_tokens': 2000, 'output_tokens': 1000}
        )
        self.assertIn("total_emissions_gco2e", bedrock_result)
        
        # Test generic calculation
        generic_result = self.calculator.calculate_total_environmental_impact(
            service_type='s3',
            resource_id='my-bucket',
            region='us-east-1',
            usage_data={'estimated_kwh': 1.5}
        )
        self.assertIn("total_emissions_gco2e", generic_result)
        self.assertAlmostEqual(generic_result["energy_kwh"], 1.5 * 1.2, places=2)

if __name__ == '__main__':
    unittest.main() 
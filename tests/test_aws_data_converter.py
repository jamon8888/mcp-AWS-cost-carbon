#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for the AWS Cost Explorer data converter.
"""

import os
import unittest
import tempfile
import pandas as pd
import json
import sys
import datetime
from unittest.mock import patch, MagicMock

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.tools.convert_aws_data import (
    load_aws_cost_data,
    convert_to_mcp_format,
    save_mcp_data,
    add_environmental_metrics,
    process_aws_cost_data
)


class TestAWSDataConverter(unittest.TestCase):
    """Tests for AWS data converter functions."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-02'],
            'service': ['EC2', 'S3', 'EC2', 'Lambda'],
            'region': ['us-east-1', 'us-east-1', 'eu-west-1', 'us-east-1'],
            'cost': [10.5, 5.25, 8.75, 2.0],
            'usage_type': ['BoxUsage', 'StorageUsage', 'BoxUsage', 'LambdaUsage'],
            'usage_amount': [24.0, 100.0, 20.0, 1000.0]
        })
        
        # Sample CSV file path
        self.sample_csv_path = os.path.join(self.test_dir, 'sample_cost_data.csv')
        self.sample_data.to_csv(self.sample_csv_path, index=False)
        
        # Sample JSON output path
        self.output_path = os.path.join(self.test_dir, 'mcp_output.json')
        
        # Sample environmental metrics
        self.env_metrics = {
            "services": {
                "EC2": {
                    "carbon_emissions": 5.2,
                    "energy_consumption": 10.5,
                    "water_usage": 20.1
                },
                "S3": {
                    "carbon_emissions": 0.5,
                    "energy_consumption": 1.2,
                    "water_usage": 2.3
                }
            },
            "regions": {
                "us-east-1": {
                    "carbon_intensity": 0.32,
                    "pue": 1.2,
                    "water_usage": 0.8
                },
                "eu-west-1": {
                    "carbon_intensity": 0.15,
                    "pue": 1.1,
                    "water_usage": 0.5
                }
            }
        }
        
        # Sample environmental metrics file path
        self.env_metrics_path = os.path.join(self.test_dir, 'env_metrics.json')
        with open(self.env_metrics_path, 'w') as f:
            json.dump(self.env_metrics, f)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory and its contents
        for file_name in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, file_name)
            os.remove(file_path)
        os.rmdir(self.test_dir)

    def test_load_aws_cost_data(self):
        """Test loading AWS cost data from CSV."""
        df = load_aws_cost_data(self.sample_csv_path)
        
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 4)
        self.assertListEqual(list(df.columns), ['date', 'service', 'region', 'cost', 'usage_type', 'usage_amount'])

    def test_convert_to_mcp_format(self):
        """Test conversion of AWS cost data to MCP format."""
        mcp_data = convert_to_mcp_format(self.sample_data)
        
        # Check metadata and summary
        self.assertIn('metadata', mcp_data)
        self.assertIn('version', mcp_data['metadata'])
        self.assertIn('summary', mcp_data)
        self.assertEqual(mcp_data['summary']['total_cost'], 26.5)
        self.assertEqual(mcp_data['summary']['service_count'], 3)
        self.assertEqual(mcp_data['summary']['region_count'], 2)
        
        # Check services
        self.assertIn('services', mcp_data)
        self.assertEqual(len(mcp_data['services']), 3)
        self.assertIn('EC2', mcp_data['services'])
        self.assertEqual(mcp_data['services']['EC2']['total_cost'], 19.25)
        
        # Check regions
        self.assertIn('regions', mcp_data)
        self.assertEqual(len(mcp_data['regions']), 2)
        self.assertIn('us-east-1', mcp_data['regions'])
        self.assertEqual(mcp_data['regions']['us-east-1']['total_cost'], 17.75)
        
        # Check daily costs
        self.assertIn('daily_costs', mcp_data)
        self.assertEqual(len(mcp_data['daily_costs']), 2)
        self.assertEqual(mcp_data['daily_costs'][0]['date'], '2023-01-01')
        self.assertEqual(mcp_data['daily_costs'][0]['total_cost'], 15.75)
        self.assertEqual(mcp_data['daily_costs'][1]['date'], '2023-01-02')
        self.assertEqual(mcp_data['daily_costs'][1]['total_cost'], 10.75)

    def test_save_mcp_data(self):
        """Test saving MCP data to a JSON file."""
        mcp_data = {
            "metadata": {"version": "1.0"},
            "summary": {"total_cost": 100.0}
        }
        
        output_file = save_mcp_data(mcp_data, self.output_path)
        
        self.assertTrue(os.path.exists(output_file))
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
            self.assertEqual(loaded_data['metadata']['version'], "1.0")
            self.assertEqual(loaded_data['summary']['total_cost'], 100.0)

    def test_add_environmental_metrics(self):
        """Test adding environmental metrics to MCP data."""
        mcp_data = {
            "metadata": {"version": "1.0"},
            "summary": {"total_cost": 100.0},
            "services": {
                "EC2": {"total_cost": 70.0},
                "S3": {"total_cost": 30.0},
                "Lambda": {"total_cost": 10.0}
            },
            "regions": {
                "us-east-1": {"total_cost": 80.0},
                "eu-west-1": {"total_cost": 20.0}
            }
        }
        
        updated_data = add_environmental_metrics(mcp_data, self.env_metrics)
        
        # Check environmental metrics in metadata
        self.assertTrue(updated_data['metadata']['includes_environmental_metrics'])
        
        # Check environmental summary
        self.assertIn('environmental_summary', updated_data)
        self.assertEqual(updated_data['environmental_summary']['total_carbon_emissions'], 5.7)
        
        # Check service metrics
        self.assertIn('environmental_metrics', updated_data['services']['EC2'])
        self.assertEqual(updated_data['services']['EC2']['environmental_metrics']['carbon_emissions'], 5.2)
        
        # Check region metrics
        self.assertIn('environmental_metrics', updated_data['regions']['us-east-1'])
        self.assertEqual(updated_data['regions']['us-east-1']['environmental_metrics']['carbon_intensity'], 0.32)

    @patch('core.tools.convert_aws_data.load_aws_cost_data')
    @patch('core.tools.convert_aws_data.convert_to_mcp_format')
    @patch('core.tools.convert_aws_data.add_environmental_metrics')
    @patch('core.tools.convert_aws_data.save_mcp_data')
    def test_process_aws_cost_data(self, mock_save, mock_add_env, mock_convert, mock_load):
        """Test the full process of AWS cost data conversion."""
        # Set up mocks
        mock_load.return_value = self.sample_data
        mock_convert.return_value = {"metadata": {}, "services": {}}
        mock_add_env.return_value = {"metadata": {}, "services": {}, "environmental_summary": {}}
        mock_save.return_value = self.output_path
        
        # Call the function
        result = process_aws_cost_data(self.sample_csv_path, self.output_path, self.env_metrics_path)
        
        # Verify the function calls
        mock_load.assert_called_once_with(self.sample_csv_path)
        mock_convert.assert_called_once()
        mock_add_env.assert_called_once()
        mock_save.assert_called_once()
        
        # Check the result
        self.assertEqual(result, self.output_path)

    def test_process_aws_cost_data_integration(self):
        """Integration test for AWS cost data processing."""
        result = process_aws_cost_data(self.sample_csv_path, self.output_path, self.env_metrics_path)
        
        self.assertTrue(os.path.exists(result))
        with open(result, 'r') as f:
            mcp_data = json.load(f)
            
            # Check that the output contains the expected data
            self.assertIn('metadata', mcp_data)
            self.assertIn('includes_environmental_metrics', mcp_data['metadata'])
            self.assertIn('environmental_summary', mcp_data)
            self.assertIn('services', mcp_data)
            self.assertIn('regions', mcp_data)
            self.assertIn('daily_costs', mcp_data)


if __name__ == '__main__':
    unittest.main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Add the project root to Python path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

print("Python path:", flush=True)
for path in sys.path:
    print(f"  {path}", flush=True)

print("\nTrying to import BedrockCarbonCalculator...", flush=True)
try:
    from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator
    print("Successfully imported BedrockCarbonCalculator", flush=True)
    
    # Create calculator instance
    calculator = BedrockCarbonCalculator(data_dir="tests/data")
    print("Successfully created calculator instance", flush=True)
    
    # Test a simple calculation
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    region = "us-west-2"
    result = calculator.calculate_carbon_footprint(
        model_id=model_id,
        region=region,
        input_tokens=1000000,
        output_tokens=200000
    )
    print(f"\nTest calculation result:", flush=True)
    print(f"Model: {model_id}", flush=True)
    print(f"Region: {region}", flush=True)
    print(f"Energy consumption:", flush=True)
    print(f"  Input: {result['energy_consumption']['input_energy_wh']:.2f} Wh", flush=True)
    print(f"  Output: {result['energy_consumption']['output_energy_wh']:.2f} Wh", flush=True)
    print(f"  Total: {result['energy_consumption']['total_energy_kwh']:.4f} kWh", flush=True)
    print(f"Carbon footprint: {result['emissions']['operational_emissions_gco2e']:.2f} gCO2e", flush=True)
    print(f"Carbon intensity: {result['carbon_intensity_gco2e_kwh']:.2f} gCO2e/kWh", flush=True)
    
except Exception as e:
    print(f"Error: {str(e)}", flush=True)
    print(f"Error type: {type(e)}", flush=True)
    import traceback
    traceback.print_exc() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Model Inference Environmental Impact Analysis

This script analyzes and visualizes the environmental impact of AI model inferences
across different models and regions, helping users make more sustainable choices.
"""

import os
import sys
import json
import argparse
import logging
import matplotlib.pyplot as plt
from datetime import datetime

# Add the parent directory to the path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use BedrockCarbonCalculator instead of the non-existent analyzer
from core.aws_bedrock_carbon_calculator import BedrockCarbonCalculator

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze environmental impact of AI model inferences')
    
    parser.add_argument('--output-dir', '-o', type=str, default='model_impact_results',
                        help='Directory to save analysis results and visualizations (default: model_impact_results)')
    parser.add_argument('--model-id', '-m', type=str, default='Claude-3-Sonnet',
                        help='Model ID to analyze (default: Claude-3-Sonnet)')
    parser.add_argument('--regions', '-r', type=str, nargs='+',
                        default=['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-2'],
                        help='AWS regions to compare (default: us-east-1 us-west-2 eu-west-1 eu-central-1 ap-southeast-2)')
    parser.add_argument('--input-tokens', '-i', type=int, default=1000000,
                        help='Number of input tokens to analyze (default: 1000000)')
    parser.add_argument('--output-tokens', '-ot', type=int, default=500000,
                        help='Number of output tokens to analyze (default: 500000)')
    parser.add_argument('--data-dir', '-d', type=str, default='data',
                        help='Directory containing environmental data files (default: data)')
    parser.add_argument('--compare-models', '-c', action='store_true',
                        help='Compare different models instead of regions')
    parser.add_argument('--models', type=str, nargs='+',
                        default=['Claude-3-Sonnet', 'Claude-3-Haiku', 'Claude-3-Opus', 'Llama-2-70b'],
                        help='Models to compare when using --compare-models (default: Claude-3-Sonnet Claude-3-Haiku Claude-3-Opus Llama-2-70b)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose output')
    
    return parser.parse_args()

def setup_logging(verbose=False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def ensure_output_directory(output_dir):
    """Ensure the output directory exists."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logging.info(f"Created output directory: {output_dir}")

def analyze_region_impact(calculator, model_id, regions, input_tokens, output_tokens, output_dir):
    """Analyze the environmental impact of a model across different regions."""
    logging.info(f"Analyzing impact of {model_id} across {len(regions)} regions")
    
    # Calculate impact across regions
    impact_results = {}
    for region in regions:
        try:
            result = calculator.calculate_carbon_footprint(
                model_id=model_id,
                region=region,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            # Structure the result similarly to the expected format (may need water data)
            impact_results[region] = {
                'carbon_footprint': result['emissions']['operational_emissions_gco2e'] / 1000, # Convert to kg
                'energy_kwh': result['energy_consumption']['total_energy_kwh'],
                # Placeholder for water usage - calculator needs water methods
                'water_usage': 0 # calculator.calculate_water_metrics(region, result['energy_consumption']['total_energy_kwh'])['water_usage_liters'] 
            }
        except ValueError as e:
            logging.warning(f"Could not calculate impact for {region}: {e}")
            impact_results[region] = {'error': str(e)}

    valid_results = {k: v for k, v in impact_results.items() if 'error' not in v}
    if not valid_results:
        logging.error("No valid impact results could be calculated.")
        return None

    # Find lowest carbon regions
    lowest_carbon_regions = sorted(valid_results.items(), key=lambda item: item[1]['carbon_footprint'])[:len(regions)]
    lowest_carbon_regions_dict = {region: impact for region, impact in lowest_carbon_regions}

    # Find lowest water regions (placeholder)
    # Need to integrate water calculation properly
    lowest_water_regions_dict = {region: {'water_usage': 0} for region in regions} # Placeholder
    
    # Generate visualization
    fig, axs = plt.subplots(2, 1, figsize=(12, 10))

    regions_plot = list(valid_results.keys())
    carbon_footprints = [valid_results[r]['carbon_footprint'] for r in regions_plot]
    water_usages = [valid_results[r].get('water_usage', 0) for r in regions_plot] # Use 0 if water usage not calculated

    axs[0].bar(regions_plot, carbon_footprints, color='skyblue')
    axs[0].set_title(f"Carbon Footprint (kg CO2e) of {model_id} Across AWS Regions")
    axs[0].set_ylabel("kg CO2e")
    axs[0].tick_params(axis='x', rotation=45)

    axs[1].bar(regions_plot, water_usages, color='lightcoral')
    axs[1].set_title(f"Water Usage (Liters) of {model_id} Across AWS Regions (Placeholder)")
    axs[1].set_ylabel("Liters")
    axs[1].tick_params(axis='x', rotation=45)
    
    # Save the figure
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"{model_id}_region_comparison.png")
    fig.savefig(plot_path)
    plt.close(fig)
    logging.info(f"Saved region comparison plot to {plot_path}")
    
    # Create summary dictionary
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "model_id": model_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "regions_analyzed": regions,
        "impact_results": impact_results,
        "lowest_carbon_regions": lowest_carbon_regions_dict,
        "lowest_water_regions": lowest_water_regions_dict # Placeholder
    }
    
    # Save summary to file
    summary_path = os.path.join(output_dir, f"{model_id}_region_analysis.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logging.info(f"Saved region analysis summary to {summary_path}")

    # Print key findings
    print("\n==== REGION IMPACT ANALYSIS SUMMARY ====")
    print(f"Model: {model_id}")
    print(f"Input tokens: {input_tokens:,}")
    print(f"Output tokens: {output_tokens:,}")
    
    print("\nLowest Carbon Footprint Regions:")
    for i, (region, impact) in enumerate(lowest_carbon_regions, 1):
        print(f"  {i}. {region}: {impact['carbon_footprint']:.3f} kg CO2e")
    
    # Placeholder for water usage
    # print("\nLowest Water Usage Regions:")
    # for i, (region, impact) in enumerate(lowest_water_regions_dict.items(), 1):
    #     print(f"  {i}. {region}: {impact['water_usage']:.3f} liters")
    
    # Calculate potential savings
    if len(lowest_carbon_regions) > 1:
        best_carbon_region = lowest_carbon_regions[0][0]
        worst_carbon_region = lowest_carbon_regions[-1][0]
        
        carbon_savings = valid_results[worst_carbon_region]['carbon_footprint'] - valid_results[best_carbon_region]['carbon_footprint']
        if valid_results[worst_carbon_region]['carbon_footprint'] > 0:
             carbon_savings_percentage = (carbon_savings / valid_results[worst_carbon_region]['carbon_footprint']) * 100
        else:
             carbon_savings_percentage = 0

        print(f"\nPotential carbon savings by switching from {worst_carbon_region} to {best_carbon_region}:")
        print(f"  {carbon_savings:.3f} kg CO2e ({carbon_savings_percentage:.1f}%)")
    
    return summary

def compare_models_impact(calculator, models, region, input_tokens, output_tokens, output_dir):
    """Compare the environmental impact across different models in a specific region."""
    logging.info(f"Comparing impact of {len(models)} models in {region}")
    
    # Compare models using the calculator's compare_models method
    comparison_results = calculator.compare_models(
        model_ids=models,
        region=region,
        input_tokens=input_tokens,
        output_tokens=output_tokens
    )

    # Extract valid results for plotting
    valid_plot_results = []
    for res in comparison_results.get('results', []):
        if 'error' not in res:
            valid_plot_results.append({
                'model_id': res['model_id'],
                'carbon_footprint': res['emissions']['operational_emissions_gco2e'] / 1000, # kg CO2e
                # Placeholder for water usage
                'water_usage': 0 # Need water calculation
            })
        else:
            logging.warning(f"Skipping model {res['model_id']} due to error: {res['error']}")

    if not valid_plot_results:
        logging.error("No valid model comparison results to plot.")
        return None

    # Generate visualization
    fig, axs = plt.subplots(2, 1, figsize=(12, 10))

    model_ids_plot = [r['model_id'] for r in valid_plot_results]
    carbon_footprints = [r['carbon_footprint'] for r in valid_plot_results]
    water_usages = [r.get('water_usage', 0) for r in valid_plot_results] # Use 0 if water usage not calculated

    axs[0].bar(model_ids_plot, carbon_footprints, color='skyblue')
    axs[0].set_title(f"Carbon Footprint (kg CO2e) Comparison of Models in {region}")
    axs[0].set_ylabel("kg CO2e")
    axs[0].tick_params(axis='x', rotation=45)

    axs[1].bar(model_ids_plot, water_usages, color='lightcoral')
    axs[1].set_title(f"Water Usage (Liters) Comparison of Models in {region} (Placeholder)")
    axs[1].set_ylabel("Liters")
    axs[1].tick_params(axis='x', rotation=45)
    
    # Save the figure
    plt.tight_layout()
    plot_path = os.path.join(output_dir, f"model_comparison_{region}.png")
    fig.savefig(plot_path)
    plt.close(fig)
    logging.info(f"Saved model comparison plot to {plot_path}")

    # Create summary dictionary
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "models": models,
        "region": region,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "comparison_results": comparison_results # Store the raw comparison results
    }
    
    # Save summary to file
    summary_path = os.path.join(output_dir, f"model_comparison_{region}_analysis.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    logging.info(f"Saved model comparison summary to {summary_path}")

    # Print key findings
    print("\n==== MODEL COMPARISON SUMMARY ====")
    print(f"Region: {region}")
    print(f"Input tokens: {input_tokens:,}")
    print(f"Output tokens: {output_tokens:,}")

    valid_results_print = sorted([r for r in comparison_results.get('results', []) if 'error' not in r], key=lambda x: x['emissions']['operational_emissions_gco2e'])

    print("\nModel Carbon Footprints (Lowest First):")
    for i, result in enumerate(valid_results_print, 1):
        print(f"  {i}. {result['model_id']}: {result['emissions']['operational_emissions_gco2e'] / 1000:.3f} kg CO2e")

    # Placeholder for water usage
    # print("\nModel Water Usage (Lowest First):")
    # ... similar logic for water ...

    if len(valid_results_print) > 1:
        lowest_model = valid_results_print[0]['model_id']
        highest_model = valid_results_print[-1]['model_id']
        savings = (valid_results_print[-1]['emissions']['operational_emissions_gco2e'] - valid_results_print[0]['emissions']['operational_emissions_gco2e']) / 1000
        if valid_results_print[-1]['emissions']['operational_emissions_gco2e'] > 0:
             savings_percentage = (savings * 1000 / valid_results_print[-1]['emissions']['operational_emissions_gco2e']) * 100
        else:
             savings_percentage = 0

        print(f"\nPotential carbon savings by choosing {lowest_model} over {highest_model}:")
        print(f"  {savings:.3f} kg CO2e ({savings_percentage:.1f}%)")

    return summary

def main():
    args = parse_arguments()
    setup_logging(args.verbose)
    ensure_output_directory(args.output_dir)
    
    # Initialize the Bedrock Carbon Calculator
    try:
        calculator = BedrockCarbonCalculator(data_dir=args.data_dir)
    except Exception as e:
        logging.error(f"Failed to initialize calculator: {e}")
        sys.exit(1)
    
    if args.compare_models:
        # Adjust model names if needed to match BedrockCalculator's expected format
        # Example: 'Claude-3-Sonnet' -> 'anthropic.claude-3-sonnet-...' 
        # This adjustment is crucial and depends on the actual keys in BedrockCalculator
        # For now, we assume the args.models are directly usable or need mapping
        compare_models_impact(
            calculator=calculator,
            models=args.models, 
            region=args.regions[0], # Use the first region for comparison
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            output_dir=args.output_dir
        )
    else:
        # Adjust model name if needed
        analyze_region_impact(
            calculator=calculator,
            model_id=args.model_id, # Needs adjustment if not matching BedrockCalculator format
            regions=args.regions,
            input_tokens=args.input_tokens,
            output_tokens=args.output_tokens,
            output_dir=args.output_dir
        )

if __name__ == "__main__":
    main() 
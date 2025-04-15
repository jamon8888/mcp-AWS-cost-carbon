#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
EC2 Environmental Impact Analyzer

This script analyzes and visualizes the environmental impact of EC2 instances
across different instance types and regions, helping users make more sustainable choices.
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

from core.ec2_impact_analyzer import EC2ImpactAnalyzer
from core.scope3_carbon_calculator import Scope3Calculator
from core.aws_environmental_calculator import AWSEnvironmentalCalculator

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Analyze environmental impact of EC2 instances')
    
    parser.add_argument('--output-dir', '-o', type=str, default='ec2_impact_results',
                        help='Directory to save analysis results and visualizations (default: ec2_impact_results)')
    parser.add_argument('--instance-types', '-i', type=str, nargs='+',
                        default=['t3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge', 't3.2xlarge'],
                        help='EC2 instance types to analyze (default: t3.micro t3.small t3.medium t3.large t3.xlarge t3.2xlarge)')
    parser.add_argument('--regions', '-r', type=str, nargs='+',
                        default=['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-2'],
                        help='AWS regions to compare (default: us-east-1 us-west-2 eu-west-1 eu-central-1 ap-southeast-2)')
    parser.add_argument('--hours', type=int, default=730,
                        help='Number of hours to run per month (default: 730, approx. 1 month)')
    parser.add_argument('--data-dir', '-d', type=str, default='data',
                        help='Directory containing environmental data files (default: data)')
    parser.add_argument('--compare-regions', action='store_true',
                        help='Compare instance in different regions instead of comparing instance types')
    parser.add_argument('--instance-type', type=str, default='t3.xlarge',
                        help='Instance type to use when comparing regions (only used with --compare-regions)')
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

def initialize_environmental_calculator(data_dir):
    """Initialize the AWS environmental calculator."""
    try:
        calculator = AWSEnvironmentalCalculator(data_dir=data_dir)
        return calculator
    except Exception as e:
        logging.error(f"Failed to initialize environmental calculator: {e}")
        sys.exit(1)

def analyze_instance_types(calculator, instance_types, region, hours, output_dir):
    """Analyze environmental impact across different EC2 instance types in a specific region."""
    logging.info(f"Analyzing {len(instance_types)} instance types in {region}")
    
    results = {}
    for instance_type in instance_types:
        try:
            # Calculate environmental impact
            impact = calculator.calculate_total_footprint(
                service_type='ec2',
                resource_id=instance_type,
                region=region,
                usage_data={'hours': hours}
            )
            
            results[instance_type] = impact
            logging.info(f"Calculated impact for {instance_type} in {region}")
            
        except Exception as e:
            logging.warning(f"Failed to calculate impact for {instance_type}: {e}")
    
    # Sort results by carbon footprint
    sorted_results = sorted(
        [(instance, data) for instance, data in results.items()],
        key=lambda x: x[1]['carbon_footprint']
    )
    
    # Create visualizations
    plt.figure(figsize=(12, 8))
    
    instances = [i[0] for i in sorted_results]
    carbon_values = [i[1]['carbon_footprint'] for i in sorted_results]
    
    bars = plt.bar(instances, carbon_values, color='green')
    
    # Add value labels on top of bars
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{carbon_values[i]:.2f}',
                ha='center', fontsize=9)
    
    plt.title(f'Carbon Footprint by Instance Type in {region}')
    plt.xlabel('Instance Type')
    plt.ylabel('Carbon Footprint (kg CO₂e)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    carbon_plot_path = os.path.join(output_dir, f'carbon_by_instance_type_{region}.png')
    plt.savefig(carbon_plot_path)
    plt.close()
    
    # Create water usage visualization
    plt.figure(figsize=(12, 8))
    
    water_values = [i[1]['water_usage'] for i in sorted_results]
    
    bars = plt.bar(instances, water_values, color='blue')
    
    # Add value labels on top of bars
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{water_values[i]:.2f}',
                ha='center', fontsize=9)
    
    plt.title(f'Water Usage by Instance Type in {region}')
    plt.xlabel('Instance Type')
    plt.ylabel('Water Usage (Liters)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    water_plot_path = os.path.join(output_dir, f'water_by_instance_type_{region}.png')
    plt.savefig(water_plot_path)
    plt.close()
    
    # Prepare summary
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "region": region,
        "instance_types": instance_types,
        "hours": hours,
        "results": results,
        "sorted_results": [(i[0], i[1]) for i in sorted_results],
        "most_efficient_instance": sorted_results[0][0],
        "least_efficient_instance": sorted_results[-1][0]
    }
    
    # Calculate efficiency ratios
    best_carbon = sorted_results[0][1]['carbon_footprint']
    worst_carbon = sorted_results[-1][1]['carbon_footprint']
    
    summary["efficiency_improvement"] = (worst_carbon - best_carbon) / worst_carbon * 100
    
    # Save results to file
    result_path = os.path.join(output_dir, f'instance_type_comparison_{region}.json')
    with open(result_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Results saved to {result_path}")
    
    return summary, carbon_plot_path, water_plot_path

def analyze_regions(calculator, instance_type, regions, hours, output_dir):
    """Analyze environmental impact of a specific EC2 instance type across different regions."""
    logging.info(f"Analyzing {instance_type} across {len(regions)} regions")
    
    results = {}
    for region in regions:
        try:
            # Calculate environmental impact
            impact = calculator.calculate_total_footprint(
                service_type='ec2',
                resource_id=instance_type,
                region=region,
                usage_data={'hours': hours}
            )
            
            results[region] = impact
            logging.info(f"Calculated impact for {instance_type} in {region}")
            
        except Exception as e:
            logging.warning(f"Failed to calculate impact for region {region}: {e}")
    
    # Sort results by carbon footprint
    sorted_results = sorted(
        [(region, data) for region, data in results.items()],
        key=lambda x: x[1]['carbon_footprint']
    )
    
    # Create carbon footprint visualization
    plt.figure(figsize=(12, 8))
    
    regions_sorted = [r[0] for r in sorted_results]
    carbon_values = [r[1]['carbon_footprint'] for r in sorted_results]
    
    bars = plt.bar(regions_sorted, carbon_values, color='green')
    
    # Add value labels on top of bars
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{carbon_values[i]:.2f}',
                ha='center', fontsize=9)
    
    plt.title(f'Carbon Footprint of {instance_type} Across AWS Regions')
    plt.xlabel('AWS Region')
    plt.ylabel('Carbon Footprint (kg CO₂e)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    carbon_plot_path = os.path.join(output_dir, f'carbon_by_region_{instance_type}.png')
    plt.savefig(carbon_plot_path)
    plt.close()
    
    # Create water usage visualization
    plt.figure(figsize=(12, 8))
    
    water_values = [r[1]['water_usage'] for r in sorted_results]
    
    bars = plt.bar(regions_sorted, water_values, color='blue')
    
    # Add value labels on top of bars
    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                f'{water_values[i]:.2f}',
                ha='center', fontsize=9)
    
    plt.title(f'Water Usage of {instance_type} Across AWS Regions')
    plt.xlabel('AWS Region')
    plt.ylabel('Water Usage (Liters)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    water_plot_path = os.path.join(output_dir, f'water_by_region_{instance_type}.png')
    plt.savefig(water_plot_path)
    plt.close()
    
    # Prepare summary
    summary = {
        "analysis_date": datetime.now().isoformat(),
        "instance_type": instance_type,
        "regions": regions,
        "hours": hours,
        "results": results,
        "sorted_results": [(r[0], r[1]) for r in sorted_results],
        "best_region": sorted_results[0][0],
        "worst_region": sorted_results[-1][0]
    }
    
    # Calculate potential savings
    best_carbon = sorted_results[0][1]['carbon_footprint']
    worst_carbon = sorted_results[-1][1]['carbon_footprint']
    
    summary["carbon_savings"] = {
        "absolute": worst_carbon - best_carbon,
        "percentage": (worst_carbon - best_carbon) / worst_carbon * 100
    }
    
    # Save results to file
    result_path = os.path.join(output_dir, f'region_comparison_{instance_type}.json')
    with open(result_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Results saved to {result_path}")
    
    return summary, carbon_plot_path, water_plot_path

def generate_html_report(summary, carbon_plot, water_plot, output_dir, compare_regions=False):
    """Generate an HTML report with analysis results and visualizations."""
    if compare_regions:
        report_filename = f"region_comparison_{summary['instance_type']}.html"
        title = f"Region Comparison for {summary['instance_type']}"
    else:
        report_filename = f"instance_type_comparison_{summary['region']}.html"
        title = f"Instance Type Comparison in {summary['region']}"
    
    report_path = os.path.join(output_dir, report_filename)
    
    with open(report_path, 'w') as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333; }}
        h1, h2, h3 {{ color: #0d6efd; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .visualization {{ margin: 20px 0; text-align: center; }}
        .visualization img {{ max-width: 100%; height: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .highlight {{ background-color: #e6ffe6; }}
        .footer {{ margin-top: 30px; text-align: center; font-size: 0.8em; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <p>Analysis date: {summary['analysis_date']}</p>
""")

        if compare_regions:
            # Region comparison specific content
            f.write(f"""
        <h2>Analysis Parameters</h2>
        <ul>
            <li><strong>Instance Type:</strong> {summary['instance_type']}</li>
            <li><strong>Regions Analyzed:</strong> {', '.join(summary['regions'])}</li>
            <li><strong>Hours:</strong> {summary['hours']}</li>
        </ul>
        
        <h2>Carbon Footprint Results</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Region</th>
                <th>Carbon Footprint (kg CO₂e)</th>
                <th>Water Usage (Liters)</th>
            </tr>
""")
            
            # Add rows for each region
            for i, (region, data) in enumerate(summary['sorted_results']):
                highlight = ' class="highlight"' if i == 0 else ''
                f.write(f"""
            <tr{highlight}>
                <td>{i+1}</td>
                <td>{region}</td>
                <td>{data['carbon_footprint']:.2f}</td>
                <td>{data['water_usage']:.2f}</td>
            </tr>""")
            
            f.write(f"""
        </table>
        
        <h2>Potential Carbon Savings</h2>
        <p>By choosing the most efficient region ({summary['best_region']}) instead of the least efficient ({summary['worst_region']}), you could save:</p>
        <ul>
            <li><strong>Monthly Carbon Savings:</strong> {summary['carbon_savings']['absolute']:.2f} kg CO₂e ({summary['carbon_savings']['percentage']:.1f}%)</li>
            <li><strong>Annual Carbon Savings:</strong> {summary['carbon_savings']['absolute'] * 12:.2f} kg CO₂e</li>
        </ul>
""")
            
        else:
            # Instance type comparison specific content
            f.write(f"""
        <h2>Analysis Parameters</h2>
        <ul>
            <li><strong>Region:</strong> {summary['region']}</li>
            <li><strong>Instance Types Analyzed:</strong> {', '.join(summary['instance_types'])}</li>
            <li><strong>Hours:</strong> {summary['hours']}</li>
        </ul>
        
        <h2>Carbon Footprint Results</h2>
        <table>
            <tr>
                <th>Rank</th>
                <th>Instance Type</th>
                <th>Carbon Footprint (kg CO₂e)</th>
                <th>Water Usage (Liters)</th>
            </tr>
""")
            
            # Add rows for each instance type
            for i, (instance, data) in enumerate(summary['sorted_results']):
                highlight = ' class="highlight"' if i == 0 else ''
                f.write(f"""
            <tr{highlight}>
                <td>{i+1}</td>
                <td>{instance}</td>
                <td>{data['carbon_footprint']:.2f}</td>
                <td>{data['water_usage']:.2f}</td>
            </tr>""")
            
            f.write(f"""
        </table>
        
        <h2>Efficiency Analysis</h2>
        <p>The most efficient instance type is <strong>{summary['most_efficient_instance']}</strong>, while the least efficient is <strong>{summary['least_efficient_instance']}</strong>.</p>
        <p>Choosing the most efficient instance type results in a <strong>{summary['efficiency_improvement']:.1f}%</strong> reduction in carbon footprint.</p>
""")
        
        # Common visualization section
        carbon_plot_filename = os.path.basename(carbon_plot)
        water_plot_filename = os.path.basename(water_plot)
        
        f.write(f"""
        <h2>Visualizations</h2>
        <div class="visualization">
            <h3>Carbon Footprint Comparison</h3>
            <img src="{carbon_plot_filename}" alt="Carbon Footprint Comparison">
        </div>
        
        <div class="visualization">
            <h3>Water Usage Comparison</h3>
            <img src="{water_plot_filename}" alt="Water Usage Comparison">
        </div>
        
        <div class="footer">
            <p>Generated by AWS Cost Explorer MCP Server - EC2 Environmental Impact Analysis Tool</p>
        </div>
    </div>
</body>
</html>""")

    logging.info(f"HTML report generated at: {report_path}")
    return report_path

def main():
    """Main function to run the analyzer."""
    args = parse_arguments()
    
    # Set logging level based on verbosity
    setup_logging(args.verbose)
    
    # Ensure output directory exists
    ensure_output_directory(args.output_dir)
    
    # Initialize calculator
    calculator = initialize_environmental_calculator(args.data_dir)
    
    try:
        if args.compare_regions:
            # Analyze regions
            summary, carbon_plot, water_plot = analyze_regions(
                calculator=calculator,
                instance_type=args.instance_type,
                regions=args.regions,
                hours=args.hours,
                output_dir=args.output_dir
            )
            
            # Generate HTML report
            report_path = generate_html_report(
                summary=summary,
                carbon_plot=carbon_plot,
                water_plot=water_plot,
                output_dir=args.output_dir,
                compare_regions=True
            )
            
            # Print summary
            print("\n===== Region Comparison Summary =====")
            print(f"Instance type: {args.instance_type}")
            print(f"Best region: {summary['best_region']} ({summary['sorted_results'][0][1]['carbon_footprint']:.2f} kg CO₂e)")
            print(f"Worst region: {summary['worst_region']} ({summary['sorted_results'][-1][1]['carbon_footprint']:.2f} kg CO₂e)")
            print(f"Potential monthly carbon savings: {summary['carbon_savings']['absolute']:.2f} kg CO₂e ({summary['carbon_savings']['percentage']:.1f}%)")
            print(f"\nDetailed report: {report_path}")
            
        else:
            # Analyze instance types
            summary, carbon_plot, water_plot = analyze_instance_types(
                calculator=calculator,
                instance_types=args.instance_types,
                region=args.regions[0],  # Use the first region
                hours=args.hours,
                output_dir=args.output_dir
            )
            
            # Generate HTML report
            report_path = generate_html_report(
                summary=summary,
                carbon_plot=carbon_plot,
                water_plot=water_plot,
                output_dir=args.output_dir,
                compare_regions=False
            )
            
            # Print summary
            print("\n===== Instance Type Comparison Summary =====")
            print(f"Region: {summary['region']}")
            print(f"Most efficient instance: {summary['most_efficient_instance']} ({summary['sorted_results'][0][1]['carbon_footprint']:.2f} kg CO₂e)")
            print(f"Least efficient instance: {summary['least_efficient_instance']} ({summary['sorted_results'][-1][1]['carbon_footprint']:.2f} kg CO₂e)")
            print(f"Efficiency improvement: {summary['efficiency_improvement']:.1f}%")
            print(f"\nDetailed report: {report_path}")
        
    except Exception as e:
        logging.error(f"Error during analysis: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    
    logging.info("Analysis completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
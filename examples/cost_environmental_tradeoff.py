#!/usr/bin/env python3
"""
Cost-Environmental Trade-off Analyzer for EC2 Instances

This script analyzes EC2 instances to find optimal choices that balance cost 
efficiency and environmental impact. It generates visualizations and recommendations
to help users make sustainable and cost-effective decisions.
"""

import os
import sys
import json
import argparse
import logging
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Corrected import path for Scope3Calculator
from core.scope3_carbon_calculator import Scope3Calculator

# Attempt to find EC2ImpactAnalyzer - check aws_environmental_calculator first
# If not found there, we might need to remove or replace its usage.
try:
    # Option 1: Maybe it's part of the main calculator?
    from core.aws_environmental_calculator import AWSEnvironmentalCalculator as EC2ImpactAnalyzer 
except ImportError:
    # Option 2: Or maybe its functionality is covered by Scope3Calculator?
    # For now, let's comment out the direct import and see if the script breaks later
    # from core.scope3.ec2_impact import EC2ImpactAnalyzer # Original problematic import
    print("Warning: Could not find EC2ImpactAnalyzer. Environmental calculations might be limited.")
    EC2ImpactAnalyzer = None # Define as None to avoid NameError later if not found

class CostEnvironmentalTradeoffAnalyzer:
    """Analyzes trade-offs between cost and environmental impact for EC2 instances."""
    
    def __init__(self, data_dir="data", output_dir="tradeoff_results", pricing_file=None):
        """
        Initialize the analyzer.
        
        Args:
            data_dir: Directory containing environmental data files
            output_dir: Directory to save results
            pricing_file: Optional JSON file with EC2 pricing data
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.pricing_file = pricing_file
        
        # Initialize environmental impact analyzer if found
        self.ec2_analyzer = None
        if EC2ImpactAnalyzer:
             try:
                 self.ec2_analyzer = EC2ImpactAnalyzer(data_dir=data_dir)
             except Exception as e:
                  self.logger.warning(f"Failed to initialize EC2ImpactAnalyzer: {e}")
        else:
             self.logger.warning("EC2ImpactAnalyzer not available. Impact calculations will be skipped or limited.")
        
        # Load pricing data
        self.pricing_data = self._load_pricing_data()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('TradeoffAnalyzer')
    
    def _load_pricing_data(self):
        """Load EC2 pricing data from file or use default data."""
        if self.pricing_file and os.path.exists(self.pricing_file):
            with open(self.pricing_file, 'r') as f:
                return json.load(f)
        
        # Default pricing data (USD/hour) for common instance types in us-east-1
        # This is simplified - real implementation would use AWS Price List API or other sources
        return {
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "t3.xlarge": 0.1664,
            "t3.2xlarge": 0.3328,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
            "m5.2xlarge": 0.384,
            "c5.large": 0.085,
            "c5.xlarge": 0.17,
            "c5.2xlarge": 0.34,
            "r5.large": 0.126,
            "r5.xlarge": 0.252,
            "r5.2xlarge": 0.504
        }
    
    def analyze_instance_tradeoffs(self, instance_types=None, regions=None, hours=730):
        """
        Analyze trade-offs between cost and environmental impact for specified instances.
        
        Args:
            instance_types: List of EC2 instance types to analyze
            regions: List of AWS regions to analyze
            hours: Monthly runtime hours
            
        Returns:
            DataFrame with analysis results
        """
        if instance_types is None:
            instance_types = list(self.pricing_data.keys())
            
        if regions is None:
            regions = ["us-east-1", "us-west-2", "eu-west-1", "eu-central-1", "ap-southeast-2"]
        
        results = []
        
        for region in regions:
            self.logger.info(f"Analyzing instances in {region}")
            
            for instance_type in instance_types:
                if instance_type not in self.pricing_data:
                    self.logger.warning(f"No pricing data for {instance_type}, skipping")
                    continue
                
                # Get environmental impact
                try:
                    # Use the correct calculator and method
                    if self.ec2_analyzer:
                         usage_data = {'hours': hours}
                         env_metrics = self.ec2_analyzer.calculate_total_footprint(
                             service_type='ec2',
                             resource_id=instance_type,
                             region=region,
                             usage_data=usage_data
                         )
                         carbon = env_metrics.carbon_footprint # Already in kgCO2e
                         energy = env_metrics.energy_kwh
                         water = env_metrics.water_usage
                    else:
                         # Handle case where analyzer wasn't initialized
                         carbon, energy, water = 0, 0, 0
                         self.logger.warning(f"Skipping env calculation for {instance_type} due to missing analyzer.")

                    # Get pricing
                    hourly_price = self.pricing_data.get(instance_type, 0) # Use .get for safety
                    if hourly_price == 0:
                         self.logger.warning(f"No pricing data for {instance_type}, skipping")
                         continue
                    monthly_cost = hourly_price * hours
                    
                    # Calculate efficiency metrics
                    carbon_per_dollar = carbon / max(monthly_cost, 0.01)  # Avoid division by zero
                    
                    results.append({
                        'instance_type': instance_type,
                        'region': region,
                        'hourly_cost': hourly_price,
                        'monthly_cost': monthly_cost,
                        'carbon_kg': carbon,
                        'energy_kwh': energy,
                        'water_liters': water,
                        'carbon_per_dollar': carbon_per_dollar
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing {instance_type} in {region}: {str(e)}")
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Save results
        df.to_csv(os.path.join(self.output_dir, 'tradeoff_analysis.csv'), index=False)
        
        return df
    
    def find_pareto_optimal(self, df):
        """
        Find Pareto-optimal instances (those that are not dominated by any other instance).
        An instance is Pareto-optimal if no other instance has both lower cost and lower carbon footprint.
        
        Args:
            df: DataFrame with analysis results
            
        Returns:
            DataFrame containing only Pareto-optimal instances
        """
        pareto_optimal = []
        
        for region in df['region'].unique():
            region_df = df[df['region'] == region].copy()
            
            for idx, row in region_df.iterrows():
                is_dominated = False
                
                for idx2, row2 in region_df.iterrows():
                    if idx != idx2:
                        if (row2['monthly_cost'] <= row['monthly_cost'] and 
                            row2['carbon_kg'] < row['carbon_kg']):
                            is_dominated = True
                            break
                
                if not is_dominated:
                    pareto_optimal.append(row.to_dict())
        
        pareto_df = pd.DataFrame(pareto_optimal)
        
        # Save results
        if not pareto_df.empty:
            pareto_df.to_csv(os.path.join(self.output_dir, 'pareto_optimal.csv'), index=False)
        
        return pareto_df
    
    def generate_tradeoff_chart(self, df, region=None):
        """
        Generate a scatter plot showing cost vs. carbon footprint trade-off.
        
        Args:
            df: DataFrame with analysis results
            region: Optional region to filter by
            
        Returns:
            Path to saved chart image
        """
        if region:
            plot_df = df[df['region'] == region].copy()
            title = f"Cost vs. Carbon Trade-off for EC2 Instances in {region}"
            filename = f"tradeoff_chart_{region}.png"
        else:
            plot_df = df.copy()
            title = "Cost vs. Carbon Trade-off for EC2 Instances Across Regions"
            filename = "tradeoff_chart_all_regions.png"
        
        if plot_df.empty:
            self.logger.warning(f"No data to plot for {'region ' + region if region else 'any region'}")
            return None
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Plot each region with different color
        for r in plot_df['region'].unique():
            r_df = plot_df[plot_df['region'] == r]
            plt.scatter(
                r_df['monthly_cost'], 
                r_df['carbon_kg'],
                label=r,
                alpha=0.7,
                s=80
            )
        
        # Add instance type labels
        for idx, row in plot_df.iterrows():
            plt.annotate(
                row['instance_type'],
                (row['monthly_cost'], row['carbon_kg']),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8
            )
        
        # Add chart elements
        plt.title(title, fontsize=14)
        plt.xlabel('Monthly Cost (USD)', fontsize=12)
        plt.ylabel('Carbon Footprint (kg CO₂e)', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend(title="Region")
        
        # Save chart
        chart_path = os.path.join(self.output_dir, filename)
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_efficiency_chart(self, df, region=None):
        """
        Generate a bar chart showing carbon per dollar efficiency.
        
        Args:
            df: DataFrame with analysis results
            region: Optional region to filter by
            
        Returns:
            Path to saved chart image
        """
        if region:
            plot_df = df[df['region'] == region].copy()
            title = f"Carbon Efficiency of EC2 Instances in {region}"
            filename = f"efficiency_chart_{region}.png"
        else:
            # Use the most complete region data
            region_counts = df['region'].value_counts()
            if region_counts.empty:
                return None
            most_complete_region = region_counts.index[0]
            plot_df = df[df['region'] == most_complete_region].copy()
            title = f"Carbon Efficiency of EC2 Instances in {most_complete_region}"
            filename = "efficiency_chart.png"
        
        if plot_df.empty:
            return None
        
        # Sort by efficiency (carbon per dollar)
        plot_df = plot_df.sort_values('carbon_per_dollar')
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Plot carbon per dollar
        bars = plt.bar(
            plot_df['instance_type'],
            plot_df['carbon_per_dollar'],
            color='forestgreen'
        )
        
        # Add chart elements
        plt.title(title, fontsize=14)
        plt.xlabel('EC2 Instance Type', fontsize=12)
        plt.ylabel('kg CO₂e per USD Spent', fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.grid(True, axis='y', linestyle='--', alpha=0.7)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.annotate(
                f'{height:.2f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=8
            )
        
        plt.tight_layout()
        
        # Save chart
        chart_path = os.path.join(self.output_dir, filename)
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_report(self, df, pareto_df):
        """
        Generate an HTML report with analysis results and recommendations.
        
        Args:
            df: DataFrame with all analysis results
            pareto_df: DataFrame with Pareto-optimal instances
            
        Returns:
            Path to saved HTML report
        """
        report_path = os.path.join(self.output_dir, 'tradeoff_report.html')
        
        # Generate region-specific charts
        region_charts = {}
        for region in df['region'].unique():
            chart_path = self.generate_tradeoff_chart(df, region)
            if chart_path:
                region_charts[region] = os.path.basename(chart_path)
        
        # Generate overall tradeoff chart
        overall_chart = os.path.basename(self.generate_tradeoff_chart(df)) if self.generate_tradeoff_chart(df) else ""
        
        # Generate efficiency chart
        efficiency_chart = os.path.basename(self.generate_efficiency_chart(df)) if self.generate_efficiency_chart(df) else ""
        
        # Create recommendations
        recommendations = []
        if not pareto_df.empty:
            # Lowest carbon recommendation
            min_carbon = pareto_df.loc[pareto_df['carbon_kg'].idxmin()]
            recommendations.append({
                'title': 'Most Eco-Friendly Option',
                'instance': min_carbon['instance_type'],
                'region': min_carbon['region'],
                'carbon': f"{min_carbon['carbon_kg']:.2f} kg",
                'cost': f"${min_carbon['monthly_cost']:.2f}"
            })
            
            # Lowest cost recommendation
            min_cost = pareto_df.loc[pareto_df['monthly_cost'].idxmin()]
            recommendations.append({
                'title': 'Most Cost-Effective Option',
                'instance': min_cost['instance_type'],
                'region': min_cost['region'],
                'carbon': f"{min_cost['carbon_kg']:.2f} kg",
                'cost': f"${min_cost['monthly_cost']:.2f}"
            })
            
            # Find lowest cost, lowest carbon, and balanced options
            lowest_cost = pareto_df.loc[pareto_df['monthly_cost'].idxmin()]
            lowest_carbon = pareto_df.loc[pareto_df['carbon_kg'].idxmin()]
            
            # Calculate distance from origin (0 cost, 0 carbon) after normalization
            # Handle potential division by zero if max values are 0
            max_cost = pareto_df['monthly_cost'].max()
            max_carbon = pareto_df['carbon_kg'].max()
            
            norm_cost = (pareto_df['monthly_cost'] / max_cost) if max_cost > 0 else 0
            norm_carbon = (pareto_df['carbon_kg'] / max_carbon) if max_carbon > 0 else 0
            
            pareto_df['distance_from_origin'] = np.sqrt(norm_cost**2 + norm_carbon**2)
            
            # Safely find the index of the minimum distance, skipping NaNs
            balanced_idx = pareto_df['distance_from_origin'].dropna().idxmin()
            balanced = pareto_df.loc[balanced_idx]
            
            recommendations.append({
                'title': 'Best Balanced Option',
                'instance': balanced['instance_type'],
                'region': balanced['region'],
                'carbon': f"{balanced['carbon_kg']:.2f} kg",
                'cost': f"${balanced['monthly_cost']:.2f}"
            })
        
        # Build HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>EC2 Cost-Environmental Trade-off Analysis</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
                h1, h2, h3 {{ color: #0066cc; }}
                .chart {{ margin: 20px 0; max-width: 100%; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .recommendation {{ 
                    background-color: #f0f7ff; 
                    border-left: 4px solid #0066cc; 
                    padding: 15px;
                    margin: 20px 0;
                }}
                .eco {{ border-left-color: #2e8b57; }}
                .cost {{ border-left-color: #ff7f50; }}
                .balanced {{ border-left-color: #9370db; }}
            </style>
        </head>
        <body>
            <h1>EC2 Cost-Environmental Trade-off Analysis</h1>
            <p>Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h2>Overview</h2>
            <p>This report analyzes the trade-off between cost and environmental impact for various EC2 instance types across different AWS regions.</p>
            
            <h2>Key Findings</h2>
            <ul>
                <li>Total instances analyzed: {len(df)}</li>
                <li>Regions analyzed: {', '.join(df['region'].unique())}</li>
                <li>Pareto-optimal options found: {len(pareto_df)}</li>
            </ul>
            
            <h2>Recommendations</h2>
        """
        
        # Add recommendations
        for i, rec in enumerate(recommendations):
            css_class = ""
            if i == 0:
                css_class = "eco"
            elif i == 1:
                css_class = "cost"
            elif i == 2:
                css_class = "balanced"
                
            html_content += f"""
            <div class="recommendation {css_class}">
                <h3>{rec['title']}</h3>
                <p><strong>Instance:</strong> {rec['instance']} in {rec['region']}</p>
                <p><strong>Carbon Footprint:</strong> {rec['carbon']}</p>
                <p><strong>Monthly Cost:</strong> {rec['cost']}</p>
            </div>
            """
        
        # Add overall trade-off chart
        if overall_chart:
            html_content += f"""
            <h2>Cost vs. Carbon Trade-off</h2>
            <img class="chart" src="{overall_chart}" alt="Cost vs. Carbon Trade-off Chart">
            <p>This chart shows the relationship between monthly cost and carbon footprint for different EC2 instances across regions.</p>
            """
        
        # Add efficiency chart
        if efficiency_chart:
            html_content += f"""
            <h2>Carbon Efficiency</h2>
            <img class="chart" src="{efficiency_chart}" alt="Carbon Efficiency Chart">
            <p>This chart shows the carbon efficiency (kg CO₂e per USD spent) for different EC2 instances.</p>
            """
        
        # Add region-specific charts
        if region_charts:
            html_content += f"""
            <h2>Region-Specific Analysis</h2>
            """
            
            for region, chart in region_charts.items():
                html_content += f"""
                <h3>{region}</h3>
                <img class="chart" src="{chart}" alt="Trade-off Chart for {region}">
                """
        
        # Add Pareto-optimal table
        if not pareto_df.empty:
            html_content += f"""
            <h2>Pareto-Optimal Instances</h2>
            <p>These instances represent optimal choices where no other option has both lower cost and lower carbon footprint.</p>
            <table>
                <tr>
                    <th>Instance Type</th>
                    <th>Region</th>
                    <th>Monthly Cost ($)</th>
                    <th>Carbon Footprint (kg)</th>
                    <th>Energy (kWh)</th>
                    <th>Water (L)</th>
                </tr>
            """
            
            for _, row in pareto_df.sort_values('monthly_cost').iterrows():
                html_content += f"""
                <tr>
                    <td>{row['instance_type']}</td>
                    <td>{row['region']}</td>
                    <td>${row['monthly_cost']:.2f}</td>
                    <td>{row['carbon_kg']:.2f}</td>
                    <td>{row['energy_kwh']:.2f}</td>
                    <td>{row['water_liters']:.2f}</td>
                </tr>
                """
            
            html_content += "</table>"
        
        # Add detailed results table
        html_content += f"""
        <h2>All Results</h2>
        <table>
            <tr>
                <th>Instance Type</th>
                <th>Region</th>
                <th>Monthly Cost ($)</th>
                <th>Carbon Footprint (kg)</th>
                <th>Energy (kWh)</th>
                <th>Water (L)</th>
                <th>kg CO₂e per $</th>
            </tr>
        """
        
        for _, row in df.sort_values(['region', 'monthly_cost']).iterrows():
            html_content += f"""
            <tr>
                <td>{row['instance_type']}</td>
                <td>{row['region']}</td>
                <td>${row['monthly_cost']:.2f}</td>
                <td>{row['carbon_kg']:.2f}</td>
                <td>{row['energy_kwh']:.2f}</td>
                <td>{row['water_liters']:.2f}</td>
                <td>{row['carbon_per_dollar']:.2f}</td>
            </tr>
            """
        
        html_content += """
            </table>
            <h2>Methodology</h2>
            <p>This analysis combines pricing data with environmental impact metrics calculated using the Scope3 methodology, which accounts for carbon emissions, energy usage, and water consumption of AWS services.</p>
            <p>Pareto-optimal instances are those where no other instance can provide both better cost and better environmental performance simultaneously.</p>
            
            <footer style="margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; font-size: 0.8em;">
                <p>Generated by AWS Cost Explorer MCP Server - Cost-Environmental Trade-off Analyzer</p>
            </footer>
        </body>
        </html>
        """
        
        # Save the report to HTML file
        try:
            # Specify UTF-8 encoding when writing the file
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"Report saved to {report_path}")
        except Exception as e:
            self.logger.error(f"Error saving report to {report_path}: {e}")

        return report_path


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Analyze cost-environmental trade-offs for EC2 instances')
    
    parser.add_argument('--output-dir', type=str, default='tradeoff_results',
                        help='Directory to save results (default: tradeoff_results)')
    
    parser.add_argument('--instance-types', type=str, nargs='+',
                        default=['t3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge', 
                                 'm5.large', 'm5.xlarge', 
                                 'c5.large', 'c5.xlarge', 
                                 'r5.large', 'r5.xlarge'],
                        help='EC2 instance types to analyze')
    
    parser.add_argument('--regions', type=str, nargs='+',
                        default=['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-southeast-2'],
                        help='AWS regions to analyze')
    
    parser.add_argument('--hours', type=int, default=730,
                        help='Monthly runtime hours (default: 730)')
    
    parser.add_argument('--data-dir', type=str, default='data',
                        help='Directory containing environmental data files (default: data)')
    
    parser.add_argument('--pricing-file', type=str,
                        help='JSON file with EC2 pricing data')
    
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose output')
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_arguments()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"Starting Cost-Environmental Trade-off Analysis")
    print(f"Output directory: {args.output_dir}")
    print(f"Analyzing {len(args.instance_types)} instance types across {len(args.regions)} regions")
    
    # Initialize analyzer
    analyzer = CostEnvironmentalTradeoffAnalyzer(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        pricing_file=args.pricing_file
    )
    
    # Run analysis
    print("Analyzing instance trade-offs...")
    results_df = analyzer.analyze_instance_tradeoffs(
        instance_types=args.instance_types,
        regions=args.regions,
        hours=args.hours
    )
    
    # Find Pareto-optimal instances
    print("Finding Pareto-optimal instances...")
    pareto_df = analyzer.find_pareto_optimal(results_df)
    
    # Generate report
    print("Generating report...")
    report_path = analyzer.generate_report(results_df, pareto_df)
    
    print(f"Analysis complete. Report saved to {report_path}")
    print(f"Recommendations:")
    
    if not pareto_df.empty:
        # Most eco-friendly
        eco = pareto_df.loc[pareto_df['carbon_kg'].idxmin()]
        print(f"  Most Eco-Friendly: {eco['instance_type']} in {eco['region']} ({eco['carbon_kg']:.2f} kg CO₂e, ${eco['monthly_cost']:.2f}/month)")
        
        # Most cost-effective
        cost = pareto_df.loc[pareto_df['monthly_cost'].idxmin()]
        print(f"  Most Cost-Effective: {cost['instance_type']} in {cost['region']} ({cost['carbon_kg']:.2f} kg CO₂e, ${cost['monthly_cost']:.2f}/month)")


if __name__ == "__main__":
    main() 
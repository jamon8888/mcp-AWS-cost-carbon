#!/usr/bin/env python3
"""
S3 Environmental Impact Analyzer

This script analyzes the environmental impact of AWS S3 storage across
different regions and storage classes. It helps users make more sustainable
choices by providing insights into carbon emissions, energy consumption,
and water usage associated with their S3 storage.

Features:
- Calculates carbon footprint of S3 storage in different regions
- Compares environmental impact of different storage classes
- Analyzes water usage and stress levels across regions
- Generates visualizations for comparison
- Provides recommendations for more sustainable storage options

Usage:
    python s3_environmental_impact.py [options]

Author: AWS Cost Explorer MCP Server Team
"""

import os
import sys
import json
import argparse
import logging
import datetime
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Tuple
import pandas as pd

# Add the parent directory to sys.path to import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.aws_environmental_calculator import AWSEnvironmentalCalculator
from core.calculators.scope3_calculator import Scope3Calculator
from utils.visualization import create_bar_chart, create_line_chart

# Configure logging
logger = logging.getLogger("s3_environmental_impact")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze environmental impact of S3 storage")
    
    parser.add_argument("--output-dir", type=str, default="s3_impact_results",
                        help="Directory to save results (default: s3_impact_results)")
    
    parser.add_argument("--storage-sizes", type=str, default="100,500,1000,5000,10000",
                        help="Comma-separated list of storage sizes in GB to analyze (default: 100,500,1000,5000,10000)")
    
    parser.add_argument("--regions", type=str, 
                        default="us-east-1,us-west-2,eu-west-1,eu-central-1,ap-southeast-2",
                        help="Comma-separated list of AWS regions to compare")
    
    parser.add_argument("--storage-classes", type=str,
                        default="Standard,Standard-IA,Glacier,Glacier-Deep-Archive",
                        help="Comma-separated list of S3 storage classes to compare")
    
    parser.add_argument("--timespan", type=int, default=12,
                        help="Timespan in months for analysis (default: 12)")
    
    parser.add_argument("--data-dir", type=str, default="data",
                        help="Directory containing environmental data files (default: data)")
    
    parser.add_argument("--compare-regions", action="store_true",
                        help="Compare storage impact across different regions")
    
    parser.add_argument("--compare-classes", action="store_true",
                        help="Compare storage impact across different storage classes")
    
    parser.add_argument("--access-pattern", type=str, default="light",
                        choices=["light", "medium", "heavy"],
                        help="Access pattern for S3 storage (affects GET/PUT operations)")
    
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose output")
    
    return parser.parse_args()

def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def ensure_output_dir(output_dir: str) -> str:
    """Ensure output directory exists."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = os.path.join(output_dir, f"s3_impact_{timestamp}")
    os.makedirs(result_dir, exist_ok=True)
    return result_dir

def get_access_pattern_metrics(access_pattern: str, storage_gb: int) -> Dict[str, int]:
    """Define access pattern metrics based on storage size and pattern type."""
    # Define access metrics based on pattern
    if access_pattern == "light":
        get_requests_per_gb = 10
        put_requests_per_gb = 1
    elif access_pattern == "medium":
        get_requests_per_gb = 50
        put_requests_per_gb = 5
    else:  # heavy
        get_requests_per_gb = 100
        put_requests_per_gb = 10
    
    # Calculate total requests based on storage size
    get_requests = int(storage_gb * get_requests_per_gb)
    put_requests = int(storage_gb * put_requests_per_gb)
    
    return {
        "storage_gb": storage_gb,
        "get_requests": get_requests,
        "put_requests": put_requests
    }

def analyze_storage_sizes(calculator: AWSEnvironmentalCalculator, 
                         region: str,
                         storage_sizes: List[int],
                         storage_class: str,
                         access_pattern: str,
                         output_dir: str) -> Dict[str, Any]:
    """
    Analyze environmental impact for different storage sizes in a specific region.
    
    Args:
        calculator: The AWSEnvironmentalCalculator instance
        region: AWS region
        storage_sizes: List of storage sizes to analyze (in GB)
        storage_class: S3 storage class
        access_pattern: Access pattern (light, medium, heavy)
        output_dir: Directory to save results
        
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing impact of different storage sizes in {region}...")
    
    results = []
    
    for size in storage_sizes:
        usage_data = get_access_pattern_metrics(access_pattern, size)
        
        # Add storage class to the service type
        service_type = f"s3:{storage_class}"
        
        # Calculate environmental impact
        impact = calculator.calculate_total_footprint(
            service_type=service_type,
            resource_id=storage_class,
            region=region,
            usage_data=usage_data
        )
        
        # Extract metrics
        results.append({
            "storage_gb": size,
            "region": region,
            "storage_class": storage_class,
            "carbon_footprint_grams": impact.carbon_footprint,
            "energy_kwh": impact.energy_kwh,
            "water_usage_liters": impact.water_usage,
            "water_stress_level": impact.water_stress_level
        })
    
    # Save results to JSON
    file_path = os.path.join(output_dir, f"storage_size_impact_{region}_{storage_class}.json")
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate visualization for carbon footprint
    sizes = [r["storage_gb"] for r in results]
    carbon = [r["carbon_footprint_grams"] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(sizes)), carbon, color="green")
    plt.xlabel("Storage Size (GB)")
    plt.ylabel("Carbon Footprint (grams CO2e)")
    plt.title(f"Carbon Footprint by Storage Size - {region} - {storage_class}")
    plt.xticks(range(len(sizes)), [str(s) for s in sizes])
    plt.savefig(os.path.join(output_dir, f"carbon_by_size_{region}_{storage_class}.png"))
    
    # Generate visualization for water usage
    water = [r["water_usage_liters"] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(sizes)), water, color="blue")
    plt.xlabel("Storage Size (GB)")
    plt.ylabel("Water Usage (liters)")
    plt.title(f"Water Usage by Storage Size - {region} - {storage_class}")
    plt.xticks(range(len(sizes)), [str(s) for s in sizes])
    plt.savefig(os.path.join(output_dir, f"water_by_size_{region}_{storage_class}.png"))
    
    return {"results": results}

def analyze_regions(calculator: AWSEnvironmentalCalculator,
                  regions: List[str],
                  storage_size: int,
                  storage_class: str,
                  access_pattern: str,
                  output_dir: str) -> Dict[str, Any]:
    """
    Analyze environmental impact across different regions for the same storage size.
    
    Args:
        calculator: The AWSEnvironmentalCalculator instance
        regions: List of AWS regions to analyze
        storage_size: Storage size in GB
        storage_class: S3 storage class
        access_pattern: Access pattern (light, medium, heavy)
        output_dir: Directory to save results
        
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing impact of {storage_size}GB storage across regions...")
    
    results = []
    
    for region in regions:
        usage_data = get_access_pattern_metrics(access_pattern, storage_size)
        
        # Add storage class to the service type
        service_type = f"s3:{storage_class}"
        
        # Calculate environmental impact
        impact = calculator.calculate_total_footprint(
            service_type=service_type,
            resource_id=storage_class,
            region=region,
            usage_data=usage_data
        )
        
        # Extract metrics
        results.append({
            "storage_gb": storage_size,
            "region": region,
            "storage_class": storage_class,
            "carbon_footprint_grams": impact.carbon_footprint,
            "energy_kwh": impact.energy_kwh,
            "water_usage_liters": impact.water_usage,
            "water_stress_level": impact.water_stress_level
        })
    
    # Save results to JSON
    file_path = os.path.join(output_dir, f"regional_impact_{storage_size}GB_{storage_class}.json")
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate visualization for carbon footprint by region
    region_names = [r["region"] for r in results]
    carbon = [r["carbon_footprint_grams"] for r in results]
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(region_names)), carbon, color="green")
    plt.xlabel("AWS Region")
    plt.ylabel("Carbon Footprint (grams CO2e)")
    plt.title(f"Carbon Footprint by Region - {storage_size}GB - {storage_class}")
    plt.xticks(range(len(region_names)), region_names, rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"carbon_by_region_{storage_size}GB_{storage_class}.png"))
    
    # Generate visualization for water stress by region
    water_stress = [r["water_stress_level"] for r in results]
    
    plt.figure(figsize=(12, 6))
    plt.bar(range(len(region_names)), water_stress, color="orange")
    plt.xlabel("AWS Region")
    plt.ylabel("Water Stress Level")
    plt.title(f"Water Stress Level by Region - {storage_size}GB - {storage_class}")
    plt.xticks(range(len(region_names)), region_names, rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"water_stress_by_region_{storage_size}GB_{storage_class}.png"))
    
    # Find the region with the lowest carbon footprint
    min_carbon_region = min(results, key=lambda x: x["carbon_footprint_grams"])
    
    # Find the region with the lowest water stress
    min_water_stress_region = min(results, key=lambda x: x["water_stress_level"])
    
    return {
        "results": results,
        "best_carbon_region": min_carbon_region["region"],
        "best_water_region": min_water_stress_region["region"]
    }

def analyze_storage_classes(calculator: AWSEnvironmentalCalculator,
                          region: str,
                          storage_size: int,
                          storage_classes: List[str],
                          access_pattern: str,
                          output_dir: str) -> Dict[str, Any]:
    """
    Analyze environmental impact across different storage classes in a region.
    
    Args:
        calculator: The AWSEnvironmentalCalculator instance
        region: AWS region
        storage_size: Storage size in GB
        storage_classes: List of S3 storage classes to analyze
        access_pattern: Access pattern (light, medium, heavy)
        output_dir: Directory to save results
        
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing impact of different storage classes in {region}...")
    
    results = []
    
    for storage_class in storage_classes:
        usage_data = get_access_pattern_metrics(access_pattern, storage_size)
        
        # Add storage class to the service type
        service_type = f"s3:{storage_class}"
        
        # Calculate environmental impact
        impact = calculator.calculate_total_footprint(
            service_type=service_type,
            resource_id=storage_class,
            region=region,
            usage_data=usage_data
        )
        
        # Different storage classes have different energy consumption factors
        # This simplified model assumes:
        # - Standard: 1.0x energy factor
        # - Standard-IA: 0.8x energy factor (less frequent access = less energy)
        # - Glacier: 0.6x energy factor (minimal access)
        # - Glacier-Deep-Archive: 0.4x energy factor (rarely accessed)
        
        energy_factor = 1.0
        if "IA" in storage_class:
            energy_factor = 0.8
        elif "Glacier-Deep" in storage_class:
            energy_factor = 0.4
        elif "Glacier" in storage_class:
            energy_factor = 0.6
        
        # Apply the energy factor
        adjusted_energy = impact.energy_kwh * energy_factor
        adjusted_carbon = impact.carbon_footprint * energy_factor
        adjusted_water = impact.water_usage * energy_factor
        
        results.append({
            "storage_gb": storage_size,
            "region": region,
            "storage_class": storage_class,
            "carbon_footprint_grams": adjusted_carbon,
            "energy_kwh": adjusted_energy,
            "water_usage_liters": adjusted_water,
            "water_stress_level": impact.water_stress_level
        })
    
    # Save results to JSON
    file_path = os.path.join(output_dir, f"storage_class_impact_{region}_{storage_size}GB.json")
    with open(file_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Generate visualization for carbon footprint by storage class
    class_names = [r["storage_class"] for r in results]
    carbon = [r["carbon_footprint_grams"] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(class_names)), carbon, color="green")
    plt.xlabel("Storage Class")
    plt.ylabel("Carbon Footprint (grams CO2e)")
    plt.title(f"Carbon Footprint by Storage Class - {region} - {storage_size}GB")
    plt.xticks(range(len(class_names)), class_names)
    plt.savefig(os.path.join(output_dir, f"carbon_by_class_{region}_{storage_size}GB.png"))
    
    # Generate visualization for energy consumption by storage class
    energy = [r["energy_kwh"] for r in results]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(class_names)), energy, color="purple")
    plt.xlabel("Storage Class")
    plt.ylabel("Energy Consumption (kWh)")
    plt.title(f"Energy Consumption by Storage Class - {region} - {storage_size}GB")
    plt.xticks(range(len(class_names)), class_names)
    plt.savefig(os.path.join(output_dir, f"energy_by_class_{region}_{storage_size}GB.png"))
    
    # Find the storage class with the lowest carbon footprint
    min_carbon_class = min(results, key=lambda x: x["carbon_footprint_grams"])
    
    return {
        "results": results,
        "best_carbon_class": min_carbon_class["storage_class"]
    }

def generate_html_report(results: Dict[str, Any], output_dir: str):
    """Generate an HTML report summarizing the analysis results."""
    logger.info("Generating HTML report...")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>S3 Storage Environmental Impact Analysis</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                line-height: 1.6;
            }
            h1, h2, h3 {
                color: #0066cc;
            }
            .section {
                margin-bottom: 30px;
            }
            .image-container {
                display: flex;
                flex-wrap: wrap;
                gap: 20px;
                margin-top: 20px;
            }
            .image-card {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                max-width: 500px;
            }
            .image-card img {
                max-width: 100%;
                height: auto;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .recommendation {
                background-color: #e6f7ff;
                border-left: 5px solid #0066cc;
                padding: 10px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <h1>S3 Storage Environmental Impact Analysis</h1>
        
        <div class="section">
            <h2>Overview</h2>
            <p>
                This report analyzes the environmental impact of AWS S3 storage across
                different regions, storage sizes, and storage classes. It provides insights
                into carbon emissions, energy consumption, and water usage to help
                make more sustainable storage choices.
            </p>
        </div>
    """
    
    # Add image sections
    image_files = [f for f in os.listdir(output_dir) if f.endswith(".png")]
    
    # Group images by type
    region_images = [f for f in image_files if "by_region" in f]
    size_images = [f for f in image_files if "by_size" in f]
    class_images = [f for f in image_files if "by_class" in f]
    
    # Add regions section if applicable
    if region_images:
        html_content += """
        <div class="section">
            <h2>Regional Impact Analysis</h2>
            <p>
                This section compares the environmental impact of S3 storage across different AWS regions.
                The carbon footprint and water stress levels can vary significantly by region due to
                differences in energy sources and water availability.
            </p>
            
            <div class="recommendation">
                <h3>Recommendation</h3>
        """
        
        if "best_carbon_region" in results:
            html_content += f"""
                <p>
                    <strong>Best Region for Carbon Footprint:</strong> {results["best_carbon_region"]}
                </p>
            """
        
        if "best_water_region" in results:
            html_content += f"""
                <p>
                    <strong>Best Region for Water Sustainability:</strong> {results["best_water_region"]}
                </p>
            """
        
        html_content += """
            </div>
            
            <div class="image-container">
        """
        
        for image in region_images:
            html_content += f"""
                <div class="image-card">
                    <img src="{image}" alt="{image}">
                    <p>{image.replace("_", " ").replace(".png", "")}</p>
                </div>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    # Add storage class section if applicable
    if class_images:
        html_content += """
        <div class="section">
            <h2>Storage Class Analysis</h2>
            <p>
                This section compares the environmental impact of different S3 storage classes.
                Storage classes with less frequent access patterns typically have lower
                energy requirements and therefore lower carbon footprints.
            </p>
            
            <div class="recommendation">
                <h3>Recommendation</h3>
        """
        
        if "best_carbon_class" in results:
            html_content += f"""
                <p>
                    <strong>Most Eco-friendly Storage Class:</strong> {results["best_carbon_class"]}
                </p>
            """
        
        html_content += """
            </div>
            
            <div class="image-container">
        """
        
        for image in class_images:
            html_content += f"""
                <div class="image-card">
                    <img src="{image}" alt="{image}">
                    <p>{image.replace("_", " ").replace(".png", "")}</p>
                </div>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    # Add storage size section if applicable
    if size_images:
        html_content += """
        <div class="section">
            <h2>Storage Size Impact</h2>
            <p>
                This section shows how environmental impact scales with storage size.
                The relationship between storage size and environmental impact is typically linear,
                but regions and storage classes can affect the exact scaling factor.
            </p>
            
            <div class="image-container">
        """
        
        for image in size_images:
            html_content += f"""
                <div class="image-card">
                    <img src="{image}" alt="{image}">
                    <p>{image.replace("_", " ").replace(".png", "")}</p>
                </div>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    # Add summary and recommendations
    html_content += """
        <div class="section">
            <h2>Summary and Recommendations</h2>
            
            <div class="recommendation">
                <h3>Key Findings</h3>
                <ul>
                    <li>Storage class selection can significantly impact the environmental footprint of your data.</li>
                    <li>Region selection is one of the most powerful levers for reducing carbon emissions.</li>
                    <li>Consider lifecycle policies to automatically move infrequently accessed data to more eco-friendly storage classes.</li>
                    <li>Water stressed regions may have lower carbon footprints but higher water impact - consider both factors.</li>
                </ul>
            </div>
        </div>
        
        <div class="section">
            <h2>Methodology</h2>
            <p>
                This analysis calculates the environmental impact of S3 storage based on:
            </p>
            <ul>
                <li>Storage size in GB</li>
                <li>Access patterns (GET/PUT operations)</li>
                <li>Region-specific factors (carbon intensity, PUE, water stress)</li>
                <li>Storage class energy efficiency assumptions</li>
            </ul>
            <p>
                The calculation uses the AWS Environmental Calculator and Scope3Calculator 
                from the AWS Cost Explorer MCP Server framework.
            </p>
        </div>
        
        <footer>
            <p>Generated on: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>AWS Cost Explorer MCP Server - S3 Environmental Impact Analyzer</p>
        </footer>
    </body>
    </html>
    """
    
    # Write HTML to file
    html_path = os.path.join(output_dir, "s3_impact_report.html")
    with open(html_path, "w") as f:
        f.write(html_content)
    
    logger.info(f"HTML report generated at: {html_path}")
    return html_path

def main():
    """Main function to run the analysis."""
    args = parse_arguments()
    setup_logging(args.verbose)
    
    # Ensure output directory exists
    output_dir = ensure_output_dir(args.output_dir)
    logger.info(f"Results will be saved to: {output_dir}")
    
    # Parse storage sizes
    storage_sizes = [int(size) for size in args.storage_sizes.split(",")]
    logger.info(f"Analyzing storage sizes: {storage_sizes} GB")
    
    # Parse regions
    regions = args.regions.split(",")
    logger.info(f"Analyzing regions: {regions}")
    
    # Parse storage classes
    storage_classes = args.storage_classes.split(",")
    logger.info(f"Analyzing storage classes: {storage_classes}")
    
    # Initialize environmental calculator
    calculator = AWSEnvironmentalCalculator(data_dir=args.data_dir)
    
    # Results dictionary
    results = {}
    
    # Analyze storage sizes if comparing regions
    if args.compare_regions:
        # Use the first storage size for regional comparison
        region_results = analyze_regions(
            calculator=calculator,
            regions=regions,
            storage_size=storage_sizes[0],
            storage_class=storage_classes[0],
            access_pattern=args.access_pattern,
            output_dir=output_dir
        )
        results.update(region_results)
    
    # Analyze storage classes if comparing classes
    if args.compare_classes:
        # Use the first region for storage class comparison
        class_results = analyze_storage_classes(
            calculator=calculator,
            region=regions[0],
            storage_size=storage_sizes[0],
            storage_classes=storage_classes,
            access_pattern=args.access_pattern,
            output_dir=output_dir
        )
        results.update(class_results)
    
    # Analyze storage sizes for the default region and storage class
    size_results = analyze_storage_sizes(
        calculator=calculator,
        region=regions[0],
        storage_sizes=storage_sizes,
        storage_class=storage_classes[0],
        access_pattern=args.access_pattern,
        output_dir=output_dir
    )
    results.update(size_results)
    
    # Generate HTML report
    html_report = generate_html_report(results, output_dir)
    
    logger.info(f"Analysis complete. Results saved to: {output_dir}")
    logger.info(f"HTML report available at: {html_report}")

if __name__ == "__main__":
    main() 
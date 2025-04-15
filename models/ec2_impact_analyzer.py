"""
EC2 Impact Analyzer Module

This module provides tools for analyzing the environmental impact of EC2 instances
using the Scope3 methodology. It builds on the core Scope3Calculator to provide
specialized analyses and visualizations for EC2 usage.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Any, Optional, Union
import sys

# Add parent directory to path to import core module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.scope3_carbon_calculator import Scope3Calculator

class EC2ImpactAnalyzer:
    """
    Analyzer for environmental impact of EC2 instances.
    
    This class builds on the Scope3Calculator to provide specialized
    analyses and visualizations for understanding the environmental
    impact of EC2 instances.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the EC2ImpactAnalyzer.
        
        Args:
            data_dir: Directory containing the required data files
        """
        self.calculator = Scope3Calculator(data_dir=data_dir)
        self.ec2_types = list(self.calculator.EC2_POWER_CONSUMPTION.keys())
    
    def get_available_instance_types(self) -> List[str]:
        """
        Get a list of EC2 instance types that can be analyzed.
        
        Returns:
            List of EC2 instance types
        """
        return self.ec2_types
    
    def get_available_regions(self) -> List[str]:
        """
        Get a list of AWS regions available for analysis.
        
        Returns:
            List of AWS region codes
        """
        if self.calculator.carbon_intensity_df.empty:
            return []
        
        return self.calculator.carbon_intensity_df["region"].tolist()
    
    def calculate_batch_ec2_impact(
        self,
        instance_type: str,
        regions: List[str],
        hours: int,
        count: int = 1
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate the environmental impact of EC2 instances across multiple regions.
        
        Args:
            instance_type: EC2 instance type (e.g., m5.xlarge)
            regions: List of AWS region codes
            hours: Number of hours the instances run
            count: Number of instances
            
        Returns:
            Dictionary mapping regions to impact metrics
        """
        results = {}
        
        for region in regions:
            impact = self.calculator.calculate_ec2_carbon_footprint(
                instance_type=instance_type,
                region=region,
                hours=hours,
                count=count
            )
            
            results[region] = impact
        
        return results
    
    def find_lowest_carbon_regions(
        self,
        instance_type: str,
        hours: int,
        count: int = 1,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find regions with the lowest carbon footprint for a given EC2 instance.
        
        Args:
            instance_type: EC2 instance type (e.g., m5.xlarge)
            hours: Number of hours the instances run
            count: Number of instances
            top_n: Number of top regions to return
            
        Returns:
            List of dictionaries with region and impact details
        """
        regions = self.get_available_regions()
        if not regions:
            return []
        
        all_impacts = self.calculate_batch_ec2_impact(
            instance_type=instance_type,
            regions=regions,
            hours=hours,
            count=count
        )
        
        # Sort regions by total emissions
        sorted_regions = sorted(
            [
                {
                    "region": region,
                    "total_emissions_gco2e": impact["total_emissions_gco2e"],
                    "energy_kwh": impact["energy_kwh"],
                    "water_usage_liters": impact["water_usage_liters"]
                }
                for region, impact in all_impacts.items()
            ],
            key=lambda x: x["total_emissions_gco2e"]
        )
        
        return sorted_regions[:top_n]
    
    def find_lowest_water_regions(
        self,
        instance_type: str,
        hours: int,
        count: int = 1,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find regions with the lowest water impact for a given EC2 instance.
        
        Args:
            instance_type: EC2 instance type (e.g., m5.xlarge)
            hours: Number of hours the instances run
            count: Number of instances
            top_n: Number of top regions to return
            
        Returns:
            List of dictionaries with region and impact details
        """
        regions = self.get_available_regions()
        if not regions:
            return []
        
        all_impacts = self.calculate_batch_ec2_impact(
            instance_type=instance_type,
            regions=regions,
            hours=hours,
            count=count
        )
        
        # Sort regions by water impact score
        sorted_regions = sorted(
            [
                {
                    "region": region,
                    "water_impact_score": impact["water_impact_score"],
                    "water_usage_liters": impact["water_usage_liters"],
                    "total_emissions_gco2e": impact["total_emissions_gco2e"]
                }
                for region, impact in all_impacts.items()
            ],
            key=lambda x: x["water_impact_score"]
        )
        
        return sorted_regions[:top_n]
    
    def compare_instance_types(
        self,
        instance_types: List[str],
        region: str,
        hours: int,
        count: int = 1
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare the environmental impact of different EC2 instance types.
        
        Args:
            instance_types: List of EC2 instance types to compare
            region: AWS region code
            hours: Number of hours the instances run
            count: Number of instances
            
        Returns:
            Dictionary mapping instance types to impact metrics
        """
        results = {}
        
        for instance_type in instance_types:
            impact = self.calculator.calculate_ec2_carbon_footprint(
                instance_type=instance_type,
                region=region,
                hours=hours,
                count=count
            )
            
            results[instance_type] = impact
        
        return results
    
    def plot_region_comparison(
        self,
        instance_type: str,
        regions: List[str],
        hours: int,
        count: int = 1,
        output_file: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a comparison of environmental impact across regions.
        
        Args:
            instance_type: EC2 instance type (e.g., m5.xlarge)
            regions: List of AWS region codes to compare
            hours: Number of hours the instances run
            count: Number of instances
            output_file: Path to save the plot (optional)
            
        Returns:
            Matplotlib figure object
        """
        impacts = self.calculate_batch_ec2_impact(
            instance_type=instance_type,
            regions=regions,
            hours=hours,
            count=count
        )
        
        # Extract data for plotting
        carbon_emissions = [impacts[region]["total_emissions_gco2e"] for region in regions]
        water_usage = [impacts[region]["water_usage_liters"] for region in regions]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot carbon emissions
        ax1.bar(regions, carbon_emissions, color="green")
        ax1.set_title(f"Carbon Emissions by Region: {instance_type} × {count} for {hours} hours")
        ax1.set_xlabel("AWS Region")
        ax1.set_ylabel("Carbon Emissions (gCO2e)")
        ax1.tick_params(axis="x", rotation=90)
        
        # Plot water usage
        ax2.bar(regions, water_usage, color="blue")
        ax2.set_title(f"Water Usage by Region: {instance_type} × {count} for {hours} hours")
        ax2.set_xlabel("AWS Region")
        ax2.set_ylabel("Water Usage (Liters)")
        ax2.tick_params(axis="x", rotation=90)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        return fig
    
    def plot_instance_comparison(
        self,
        instance_types: List[str],
        region: str,
        hours: int,
        count: int = 1,
        output_file: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot a comparison of environmental impact across different instance types.
        
        Args:
            instance_types: List of EC2 instance types to compare
            region: AWS region code
            hours: Number of hours the instances run
            count: Number of instances
            output_file: Path to save the plot (optional)
            
        Returns:
            Matplotlib figure object
        """
        impacts = self.compare_instance_types(
            instance_types=instance_types,
            region=region,
            hours=hours,
            count=count
        )
        
        # Extract data for plotting
        carbon_emissions = [impacts[instance]["total_emissions_gco2e"] for instance in instance_types]
        water_usage = [impacts[instance]["water_usage_liters"] for instance in instance_types]
        energy_usage = [impacts[instance]["energy_kwh"] for instance in instance_types]
        
        # Create figure with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
        
        # Plot carbon emissions
        ax1.bar(instance_types, carbon_emissions, color="green")
        ax1.set_title(f"Carbon Emissions by Instance Type in {region}")
        ax1.set_xlabel("Instance Type")
        ax1.set_ylabel("Carbon Emissions (gCO2e)")
        ax1.tick_params(axis="x", rotation=90)
        
        # Plot water usage
        ax2.bar(instance_types, water_usage, color="blue")
        ax2.set_title(f"Water Usage by Instance Type in {region}")
        ax2.set_xlabel("Instance Type")
        ax2.set_ylabel("Water Usage (Liters)")
        ax2.tick_params(axis="x", rotation=90)
        
        # Plot energy usage
        ax3.bar(instance_types, energy_usage, color="orange")
        ax3.set_title(f"Energy Usage by Instance Type in {region}")
        ax3.set_xlabel("Instance Type")
        ax3.set_ylabel("Energy Usage (kWh)")
        ax3.tick_params(axis="x", rotation=90)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
        
        return fig
    
    def generate_impact_report(
        self,
        instance_type: str,
        region: str,
        hours: int,
        count: int = 1,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive report detailing the environmental impact
        of EC2 instance usage.
        
        Args:
            instance_type: EC2 instance type (e.g., m5.xlarge)
            region: AWS region code
            hours: Number of hours the instances run
            count: Number of instances
            output_file: Path to save the report (optional)
            
        Returns:
            Dictionary with the full report data
        """
        # Calculate impact for the specified instance and region
        impact = self.calculator.calculate_ec2_carbon_footprint(
            instance_type=instance_type,
            region=region,
            hours=hours,
            count=count
        )
        
        # Find lowest carbon regions
        lowest_carbon_regions = self.find_lowest_carbon_regions(
            instance_type=instance_type,
            hours=hours,
            count=count,
            top_n=3
        )
        
        # Find lowest water regions
        lowest_water_regions = self.find_lowest_water_regions(
            instance_type=instance_type,
            hours=hours,
            count=count,
            top_n=3
        )
        
        # Calculate potential savings
        carbon_savings = None
        water_savings = None
        
        if lowest_carbon_regions and lowest_carbon_regions[0]["region"] != region:
            carbon_savings = {
                "current_region": region,
                "best_region": lowest_carbon_regions[0]["region"],
                "current_emissions": impact["total_emissions_gco2e"],
                "best_emissions": lowest_carbon_regions[0]["total_emissions_gco2e"],
                "savings_gco2e": impact["total_emissions_gco2e"] - lowest_carbon_regions[0]["total_emissions_gco2e"],
                "savings_percentage": (
                    (impact["total_emissions_gco2e"] - lowest_carbon_regions[0]["total_emissions_gco2e"]) /
                    impact["total_emissions_gco2e"] * 100
                    if impact["total_emissions_gco2e"] > 0 else 0
                )
            }
        
        if lowest_water_regions and lowest_water_regions[0]["region"] != region:
            water_savings = {
                "current_region": region,
                "best_region": lowest_water_regions[0]["region"],
                "current_water_usage": impact["water_usage_liters"],
                "best_water_usage": lowest_water_regions[0]["water_usage_liters"],
                "savings_liters": impact["water_usage_liters"] - lowest_water_regions[0]["water_usage_liters"],
                "savings_percentage": (
                    (impact["water_usage_liters"] - lowest_water_regions[0]["water_usage_liters"]) /
                    impact["water_usage_liters"] * 100
                    if impact["water_usage_liters"] > 0 else 0
                )
            }
        
        # Get similar instance types for comparison
        instance_family = instance_type.split('.')[0]
        similar_instances = [i for i in self.ec2_types if i.startswith(instance_family) and i != instance_type][:5]
        instance_comparison = None
        
        if similar_instances:
            comparison_data = self.compare_instance_types(
                instance_types=[instance_type] + similar_instances,
                region=region,
                hours=hours,
                count=count
            )
            
            sorted_instances = sorted(
                [
                    {
                        "instance_type": inst,
                        "total_emissions_gco2e": data["total_emissions_gco2e"],
                        "energy_kwh": data["energy_kwh"],
                        "water_usage_liters": data["water_usage_liters"]
                    }
                    for inst, data in comparison_data.items()
                ],
                key=lambda x: x["total_emissions_gco2e"]
            )
            
            # If there's a better instance in the same family
            if sorted_instances[0]["instance_type"] != instance_type:
                best_instance = sorted_instances[0]
                current_instance_data = next(
                    item for item in sorted_instances 
                    if item["instance_type"] == instance_type
                )
                
                instance_comparison = {
                    "current_instance": instance_type,
                    "best_instance": best_instance["instance_type"],
                    "current_emissions": current_instance_data["total_emissions_gco2e"],
                    "best_emissions": best_instance["total_emissions_gco2e"],
                    "savings_gco2e": current_instance_data["total_emissions_gco2e"] - best_instance["total_emissions_gco2e"],
                    "savings_percentage": (
                        (current_instance_data["total_emissions_gco2e"] - best_instance["total_emissions_gco2e"]) /
                        current_instance_data["total_emissions_gco2e"] * 100
                        if current_instance_data["total_emissions_gco2e"] > 0 else 0
                    )
                }
        
        # Build the report
        report = {
            "instance_type": instance_type,
            "region": region,
            "hours": hours,
            "count": count,
            "impact_data": impact,
            "carbon_intensity_gco2e_per_kwh": self.calculator.get_carbon_intensity(region),
            "pue": self.calculator.get_pue(region),
            "wue": self.calculator.get_wue(region),
            "water_stress": self.calculator.get_water_stress(region),
            "power_consumption_watts": self.calculator.EC2_POWER_CONSUMPTION.get(instance_type, 0),
            "lowest_carbon_regions": lowest_carbon_regions,
            "lowest_water_regions": lowest_water_regions,
            "potential_carbon_savings": carbon_savings,
            "potential_water_savings": water_savings,
            "instance_family_comparison": instance_comparison,
            "recommendations": []
        }
        
        # Add recommendations
        if carbon_savings and carbon_savings["savings_percentage"] > 10:
            report["recommendations"].append(
                f"Consider moving workloads to {carbon_savings['best_region']} to reduce carbon emissions by {carbon_savings['savings_percentage']:.1f}%"
            )
        
        if water_savings and water_savings["savings_percentage"] > 10:
            report["recommendations"].append(
                f"Consider moving workloads to {water_savings['best_region']} to reduce water usage by {water_savings['savings_percentage']:.1f}%"
            )
        
        if instance_comparison and instance_comparison["savings_percentage"] > 10:
            report["recommendations"].append(
                f"Consider using {instance_comparison['best_instance']} instead of {instance_type} to reduce carbon emissions by {instance_comparison['savings_percentage']:.1f}%"
            )
        
        # Add per-hour metrics
        if hours > 0:
            report["per_hour_metrics"] = {
                "carbon_per_hour_gco2e": impact["total_emissions_gco2e"] / hours,
                "energy_per_hour_kwh": impact["energy_kwh"] / hours,
                "water_per_hour_liters": impact["water_usage_liters"] / hours
            }
        
        # Save report to file if specified
        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2)
        
        return report

    def analyze_fleet_impact(
        self,
        fleet_config: Dict[str, Dict[str, int]],
        region: str,
        hours: int = 24,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze the environmental impact of a fleet of EC2 instances.
        
        Args:
            fleet_config: Dictionary mapping instance types to count
                e.g., {"m5.xlarge": {"count": 2}, "t2.micro": {"count": 10}}
            region: AWS region code
            hours: Number of hours the instances run
            output_file: Path to save the report (optional)
            
        Returns:
            Dictionary with the fleet impact report
        """
        instances_impacts = {}
        total_emissions = 0
        total_energy = 0
        total_water = 0
        
        # Calculate impact for each instance type
        for instance_type, config in fleet_config.items():
            count = config.get("count", 1)
            impact = self.calculator.calculate_ec2_carbon_footprint(
                instance_type=instance_type,
                region=region,
                hours=hours,
                count=count
            )
            
            instances_impacts[instance_type] = {
                "count": count,
                "impact": impact
            }
            
            total_emissions += impact["total_emissions_gco2e"]
            total_energy += impact["energy_kwh"]
            total_water += impact["water_usage_liters"]
        
        # Build the fleet report
        fleet_report = {
            "region": region,
            "hours": hours,
            "instance_count": sum(config.get("count", 1) for config in fleet_config.values()),
            "instance_types": list(fleet_config.keys()),
            "total_emissions_gco2e": total_emissions,
            "total_energy_kwh": total_energy,
            "total_water_usage_liters": total_water,
            "instances_breakdown": instances_impacts,
        }
        
        # Find best alternative region
        all_regions = self.get_available_regions()
        region_impacts = {}
        
        for alt_region in all_regions:
            region_total_emissions = 0
            region_total_water = 0
            
            for instance_type, config in fleet_config.items():
                count = config.get("count", 1)
                impact = self.calculator.calculate_ec2_carbon_footprint(
                    instance_type=instance_type,
                    region=alt_region,
                    hours=hours,
                    count=count
                )
                
                region_total_emissions += impact["total_emissions_gco2e"]
                region_total_water += impact["water_usage_liters"]
            
            region_impacts[alt_region] = {
                "total_emissions_gco2e": region_total_emissions,
                "total_water_usage_liters": region_total_water
            }
        
        # Sort regions by emissions
        sorted_regions = sorted(
            [
                {
                    "region": r,
                    "total_emissions_gco2e": impact["total_emissions_gco2e"],
                    "total_water_usage_liters": impact["total_water_usage_liters"]
                }
                for r, impact in region_impacts.items()
            ],
            key=lambda x: x["total_emissions_gco2e"]
        )
        
        fleet_report["best_regions"] = sorted_regions[:3]
        
        # Calculate potential savings
        if sorted_regions[0]["region"] != region:
            best_region = sorted_regions[0]["region"]
            best_emissions = sorted_regions[0]["total_emissions_gco2e"]
            
            fleet_report["potential_savings"] = {
                "best_region": best_region,
                "current_emissions_gco2e": total_emissions,
                "best_emissions_gco2e": best_emissions,
                "savings_gco2e": total_emissions - best_emissions,
                "savings_percentage": (
                    (total_emissions - best_emissions) / total_emissions * 100
                    if total_emissions > 0 else 0
                )
            }
            
            if fleet_report["potential_savings"]["savings_percentage"] > 10:
                fleet_report["recommendations"] = [
                    f"Consider moving your fleet to {best_region} to reduce carbon emissions by {fleet_report['potential_savings']['savings_percentage']:.1f}%"
                ]
        
        # Save report to file if specified
        if output_file:
            with open(output_file, "w") as f:
                json.dump(fleet_report, f, indent=2)
        
        return fleet_report


# Example usage when run directly
if __name__ == "__main__":
    analyzer = EC2ImpactAnalyzer()
    
    # Generate an impact report for a single instance
    report = analyzer.generate_impact_report(
        instance_type="m5.xlarge",
        region="us-east-1",
        hours=24,
        count=1,
        output_file="m5_xlarge_impact_report.json"
    )
    
    print(f"Generated impact report for {report['instance_type']} in {report['region']}")
    print(f"Total carbon footprint: {report['impact_data']['total_emissions_gco2e']:.2f} gCO2e")
    print(f"Total water usage: {report['impact_data']['water_usage_liters']:.2f} liters")
    
    if report.get('potential_carbon_savings'):
        print(f"Potential carbon savings by moving to {report['potential_carbon_savings']['best_region']}: "
              f"{report['potential_carbon_savings']['savings_percentage']:.1f}%")
    
    if report.get('instance_family_comparison'):
        print(f"Potential carbon savings by switching to {report['instance_family_comparison']['best_instance']}: "
              f"{report['instance_family_comparison']['savings_percentage']:.1f}%")
    
    # Analyze a fleet of instances
    fleet_report = analyzer.analyze_fleet_impact(
        fleet_config={
            "m5.xlarge": {"count": 2},
            "t2.micro": {"count": 10},
            "r5.2xlarge": {"count": 1}
        },
        region="us-east-1",
        hours=24,
        output_file="fleet_impact_report.json"
    )
    
    print(f"\nFleet analysis completed for {len(fleet_report['instance_types'])} instance types in {fleet_report['region']}")
    print(f"Total carbon footprint: {fleet_report['total_emissions_gco2e']:.2f} gCO2e")
    print(f"Total water usage: {fleet_report['total_water_usage_liters']:.2f} liters")
    
    if 'potential_savings' in fleet_report:
        print(f"Potential carbon savings by moving fleet to {fleet_report['potential_savings']['best_region']}: "
              f"{fleet_report['potential_savings']['savings_percentage']:.1f}%") 
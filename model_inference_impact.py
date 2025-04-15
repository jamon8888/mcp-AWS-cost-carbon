"""
Model Inference Environmental Impact Analysis Module

This module provides specialized functionality for analyzing the environmental impact
of AI model inferences using the Scope3 methodology. It builds on the core 
Scope3Calculator to provide more specific analysis and visualization capabilities
for generative AI workloads.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.scope3_carbon_calculator import Scope3Calculator
from typing import Dict, List, Tuple, Any, Optional

class ModelInferenceImpactAnalyzer:
    """
    Specialized analyzer for AI model inference environmental impacts.
    
    This class extends the functionality of the Scope3Calculator with specific
    methods for analyzing and visualizing the environmental impact of AI model
    inferences across different models, regions, and usage patterns.
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the ModelInferenceImpactAnalyzer.
        
        Args:
            data_dir: Directory containing the required data files
        """
        self.calculator = Scope3Calculator(data_dir)
        self.data_dir = data_dir
        
    def get_supported_models(self) -> List[str]:
        """
        Get a list of all supported models for impact analysis.
        
        Returns:
            List of model IDs that can be analyzed
        """
        if not self.calculator.model_energy_df.empty:
            return self.calculator.model_energy_df["model_id"].tolist()
        return []
    
    def get_available_regions(self) -> List[str]:
        """
        Get a list of all available AWS regions for impact analysis.
        
        Returns:
            List of region IDs that can be analyzed
        """
        if not self.calculator.carbon_intensity_df.empty:
            return self.calculator.carbon_intensity_df["region"].tolist()
        return []
    
    def calculate_batch_inference_impact(
        self, 
        model_id: str,
        regions: List[str],
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate the environmental impact of model inference across multiple regions.
        
        Args:
            model_id: ID of the model to analyze
            regions: List of regions to analyze
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Dictionary with region as key and impact metrics as values
        """
        results = {}
        
        for region in regions:
            impact = self.calculator.calculate_inference_carbon_footprint(
                model_id=model_id,
                region=region,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            results[region] = impact
            
        return results
    
    def find_lowest_carbon_regions(
        self, 
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the regions with the lowest carbon footprint for model inference.
        
        Args:
            model_id: ID of the model to analyze
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            top_n: Number of top regions to return
            
        Returns:
            List of dictionaries with region and impact information
        """
        regions = self.get_available_regions()
        results = self.calculate_batch_inference_impact(
            model_id=model_id,
            regions=regions,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Sort regions by total emissions
        sorted_regions = sorted(
            results.items(), 
            key=lambda x: x[1]["total_emissions_gco2e"]
        )
        
        # Format the results
        formatted_results = []
        for i, (region, impact) in enumerate(sorted_regions[:top_n]):
            formatted_results.append({
                "rank": i + 1,
                "region": region,
                "emissions_gco2e": impact["total_emissions_gco2e"],
                "energy_kwh": impact["energy_kwh"],
                "water_usage_liters": impact["water_usage_liters"],
                "carbon_intensity": self.calculator.get_carbon_intensity(region),
                "pue": self.calculator.get_pue(region),
                "wue": self.calculator.get_wue(region),
                "water_stress": self.calculator.get_water_stress(region)
            })
            
        return formatted_results
    
    def find_lowest_water_regions(
        self, 
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find the regions with the lowest water impact for model inference.
        
        Args:
            model_id: ID of the model to analyze
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            top_n: Number of top regions to return
            
        Returns:
            List of dictionaries with region and impact information
        """
        regions = self.get_available_regions()
        results = self.calculate_batch_inference_impact(
            model_id=model_id,
            regions=regions,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Calculate water impact score (water usage * stress)
        for region, impact in results.items():
            impact["water_impact_score"] = (
                impact["water_usage_liters"] * 
                self.calculator.get_water_stress(region)
            )
            
        # Sort regions by water impact score
        sorted_regions = sorted(
            results.items(), 
            key=lambda x: x[1]["water_impact_score"]
        )
        
        # Format the results
        formatted_results = []
        for i, (region, impact) in enumerate(sorted_regions[:top_n]):
            formatted_results.append({
                "rank": i + 1,
                "region": region,
                "water_usage_liters": impact["water_usage_liters"],
                "water_stress": self.calculator.get_water_stress(region),
                "water_impact_score": impact["water_impact_score"],
                "emissions_gco2e": impact["total_emissions_gco2e"],
                "energy_kwh": impact["energy_kwh"]
            })
            
        return formatted_results
    
    def compare_models(
        self,
        model_ids: List[str],
        region: str,
        input_tokens: int,
        output_tokens: int
    ) -> List[Dict[str, Any]]:
        """
        Compare the environmental impact of different models for the same workload.
        
        Args:
            model_ids: List of model IDs to compare
            region: AWS region for the comparison
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            List of dictionaries with model and impact information
        """
        results = []
        
        for model_id in model_ids:
            impact = self.calculator.calculate_inference_carbon_footprint(
                model_id=model_id,
                region=region,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Add model information to the results
            results.append({
                "model_id": model_id,
                "total_emissions_gco2e": impact["total_emissions_gco2e"],
                "scope1_emissions_gco2e": impact["scope1_emissions_gco2e"],
                "scope2_emissions_gco2e": impact["scope2_emissions_gco2e"],
                "scope3_emissions_gco2e": impact["scope3_emissions_gco2e"],
                "energy_kwh": impact["energy_kwh"],
                "water_usage_liters": impact["water_usage_liters"],
                "water_impact_score": impact["water_impact_score"]
            })
            
        # Sort by total emissions
        results.sort(key=lambda x: x["total_emissions_gco2e"])
        
        return results
    
    def plot_region_comparison(
        self,
        model_id: str,
        regions: List[str],
        input_tokens: int,
        output_tokens: int,
        metric: str = "total_emissions_gco2e",
        output_file: Optional[str] = None
    ) -> None:
        """
        Plot a comparison of environmental impact across regions.
        
        Args:
            model_id: ID of the model to analyze
            regions: List of regions to compare
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            metric: Metric to compare ("total_emissions_gco2e", "energy_kwh", "water_usage_liters")
            output_file: Path to save the plot (if None, the plot is displayed but not saved)
        """
        # Calculate impact for each region
        results = self.calculate_batch_inference_impact(
            model_id=model_id,
            regions=regions,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Extract the specified metric for each region
        metric_labels = {
            "total_emissions_gco2e": "Carbon Emissions (gCO2e)",
            "energy_kwh": "Energy Consumption (kWh)",
            "water_usage_liters": "Water Usage (liters)",
            "water_impact_score": "Water Impact Score"
        }
        
        if metric not in metric_labels:
            raise ValueError(f"Invalid metric: {metric}")
            
        values = [results[region][metric] for region in regions]
        
        # Create the plot
        plt.figure(figsize=(12, 8))
        bars = plt.bar(regions, values)
        
        # Add value labels on top of each bar
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{height:.4f}',
                ha='center', 
                va='bottom',
                rotation=45
            )
            
        plt.xlabel('AWS Region')
        plt.ylabel(metric_labels[metric])
        plt.title(f'{metric_labels[metric]} for {model_id} Across AWS Regions')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def plot_model_comparison(
        self,
        model_ids: List[str],
        region: str,
        input_tokens: int,
        output_tokens: int,
        output_file: Optional[str] = None
    ) -> None:
        """
        Plot a comparison of environmental impact across different models.
        
        Args:
            model_ids: List of model IDs to compare
            region: AWS region for the comparison
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            output_file: Path to save the plot (if None, the plot is displayed but not saved)
        """
        # Get model comparison data
        results = self.compare_models(
            model_ids=model_ids,
            region=region,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Extract data for plotting
        models = [result["model_id"] for result in results]
        emissions = [result["total_emissions_gco2e"] for result in results]
        
        # Create a stacked bar chart for scope 1, 2, and 3 emissions
        scope1 = [result["scope1_emissions_gco2e"] for result in results]
        scope2 = [result["scope2_emissions_gco2e"] for result in results]
        scope3 = [result["scope3_emissions_gco2e"] for result in results]
        
        plt.figure(figsize=(12, 8))
        
        # Create the stacked bars
        p1 = plt.bar(models, scope1, label='Scope 1 (Direct)')
        p2 = plt.bar(models, scope2, bottom=scope1, label='Scope 2 (Electricity)')
        p3 = plt.bar(models, scope3, bottom=[s1+s2 for s1, s2 in zip(scope1, scope2)], label='Scope 3 (Supply Chain)')
        
        # Add value labels on top of each bar
        for i, model in enumerate(models):
            total = emissions[i]
            plt.text(
                i,
                total,
                f'{total:.4f}',
                ha='center', 
                va='bottom'
            )
            
        plt.xlabel('AI Model')
        plt.ylabel('Carbon Emissions (gCO2e)')
        plt.title(f'Carbon Emissions by Model in {region} for {input_tokens/1000}k Input + {output_tokens/1000}k Output Tokens')
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
    
    def generate_impact_report(
        self,
        model_id: str,
        region: str,
        input_tokens: int,
        output_tokens: int,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive impact report for a model inference.
        
        Args:
            model_id: ID of the model to analyze
            region: AWS region for the analysis
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            output_file: Path to save the report as JSON (if None, the report is only returned)
            
        Returns:
            Dictionary with the comprehensive impact report
        """
        # Calculate the basic impact
        impact = self.calculator.calculate_inference_carbon_footprint(
            model_id=model_id,
            region=region,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Find best alternative regions
        lowest_carbon_regions = self.find_lowest_carbon_regions(
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            top_n=3
        )
        
        lowest_water_regions = self.find_lowest_water_regions(
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            top_n=3
        )
        
        # Get model energy data
        input_energy, output_energy = self.calculator.get_model_energy_consumption(model_id)
        
        # Create the report
        report = {
            "model_id": model_id,
            "region": region,
            "workload": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens
            },
            "model_data": {
                "input_energy_wh_per_1k_tokens": input_energy,
                "output_energy_wh_per_1k_tokens": output_energy
            },
            "region_data": {
                "carbon_intensity_gco2e_per_kwh": self.calculator.get_carbon_intensity(region),
                "pue": self.calculator.get_pue(region),
                "wue": self.calculator.get_wue(region),
                "water_stress": self.calculator.get_water_stress(region)
            },
            "impact": impact,
            "comparisons": {
                "lowest_carbon_regions": lowest_carbon_regions,
                "lowest_water_regions": lowest_water_regions
            },
            "potential_savings": {}
        }
        
        # Calculate potential savings with best region
        if lowest_carbon_regions and lowest_carbon_regions[0]["region"] != region:
            best_carbon_region = lowest_carbon_regions[0]["region"]
            current_emissions = impact["total_emissions_gco2e"]
            best_emissions = lowest_carbon_regions[0]["emissions_gco2e"]
            
            report["potential_savings"]["carbon"] = {
                "best_region": best_carbon_region,
                "current_emissions_gco2e": current_emissions,
                "best_emissions_gco2e": best_emissions,
                "savings_gco2e": current_emissions - best_emissions,
                "savings_percentage": (current_emissions - best_emissions) / current_emissions * 100
            }
        
        # Calculate potential savings for water
        if lowest_water_regions and lowest_water_regions[0]["region"] != region:
            best_water_region = lowest_water_regions[0]["region"]
            current_water = impact["water_usage_liters"]
            best_water = lowest_water_regions[0]["water_usage_liters"]
            
            report["potential_savings"]["water"] = {
                "best_region": best_water_region,
                "current_usage_liters": current_water,
                "best_usage_liters": best_water,
                "savings_liters": current_water - best_water,
                "savings_percentage": (current_water - best_water) / current_water * 100
            }
        
        # Save the report to a file if requested
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        return report

if __name__ == "__main__":
    # Example usage
    analyzer = ModelInferenceImpactAnalyzer()
    
    # Get list of supported models
    models = analyzer.get_supported_models()
    print(f"Supported models: {models}")
    
    # Example impact report
    report = analyzer.generate_impact_report(
        model_id="anthropic.claude-v2",
        region="us-east-1",
        input_tokens=10000,
        output_tokens=5000,
        output_file="claude_v2_impact_report.json"
    )
    
    print(f"Total carbon footprint: {report['impact']['total_emissions_gco2e']:.4f} gCO2e")
    print(f"Total water usage: {report['impact']['water_usage_liters']:.4f} liters")
    
    if "carbon" in report["potential_savings"]:
        savings = report["potential_savings"]["carbon"]
        print(f"Potential carbon savings by switching to {savings['best_region']}: "
              f"{savings['savings_percentage']:.2f}% ({savings['savings_gco2e']:.4f} gCO2e)")
    
    # Compare multiple models
    analyzer.plot_model_comparison(
        model_ids=["anthropic.claude-v2", "anthropic.claude-instant-v1", "amazon.titan-text-express-v1"],
        region="us-west-2",
        input_tokens=10000,
        output_tokens=5000,
        output_file="model_comparison.png"
    )
    
    # Compare regions
    analyzer.plot_region_comparison(
        model_id="anthropic.claude-v2",
        regions=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-2"],
        input_tokens=10000,
        output_tokens=5000,
        metric="total_emissions_gco2e",
        output_file="region_comparison.png"
    ) 
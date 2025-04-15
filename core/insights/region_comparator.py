from typing import Dict, Any, List, Optional, Tuple
from ..calculators.unified_calculator import UnifiedCalculator

class RegionComparator:
    """
    Compare metrics across different AWS regions to identify
    cost savings and environmental impact reduction opportunities.
    """
    
    def __init__(self, calculator: Optional[UnifiedCalculator] = None, data_dir: str = "data"):
        self.calculator = calculator or UnifiedCalculator(data_dir)
    
    def compare_regions(
        self, 
        service_type: str,
        resource_id: str,
        regions: List[str],
        usage_data: Dict[str, Any],
        metrics: List[str] = ["cost", "carbon", "water", "combined"]
    ) -> Dict[str, Any]:
        """
        Compare metrics across different AWS regions
        
        Args:
            service_type: Type of AWS service
            resource_id: Resource identifier
            regions: List of regions to compare
            usage_data: Usage metrics for the resource
            metrics: List of metrics to compare
            
        Returns:
            Dictionary with comparison results
        """
        results = {}
        region_results = {}
        
        # Calculate metrics for each region
        for region in regions:
            metrics_result = self.calculator.calculate_metrics(
                service_type, resource_id, region, usage_data
            )
            region_results[region] = metrics_result.get("unified_metrics")
        
        # Find best region for each metric
        metric_rankings = {}
        for metric in metrics:
            if metric == "cost":
                sorted_regions = sorted(
                    region_results.items(),
                    key=lambda x: x[1].cost.monthly_cost
                )
                metric_rankings[metric] = [{
                    "region": region,
                    "value": data.cost.monthly_cost,
                    "unit": "USD"
                } for region, data in sorted_regions]
                
            elif metric == "carbon":
                sorted_regions = sorted(
                    region_results.items(),
                    key=lambda x: x[1].environment.carbon_footprint_grams
                )
                metric_rankings[metric] = [{
                    "region": region,
                    "value": data.environment.carbon_footprint_grams,
                    "unit": "gCO2e"
                } for region, data in sorted_regions]
                
            elif metric == "water":
                sorted_regions = sorted(
                    region_results.items(),
                    key=lambda x: x[1].environment.water_usage_liters
                )
                metric_rankings[metric] = [{
                    "region": region,
                    "value": data.environment.water_usage_liters,
                    "unit": "liters"
                } for region, data in sorted_regions]
                
            elif metric == "combined":
                # Create a combined score (normalized and weighted)
                combined_scores = []
                for region, data in region_results.items():
                    # Normalize each metric to a 0-100 scale and apply weights
                    cost_normalized = min(100, data.cost.monthly_cost / 100 * 100)
                    carbon_normalized = min(100, data.environment.carbon_footprint_grams / 1000 * 100)
                    water_normalized = min(100, data.environment.water_usage_liters / 100 * 100)
                    
                    # Weights: cost 50%, carbon 30%, water 20%
                    combined_score = (
                        cost_normalized * 0.5 +
                        carbon_normalized * 0.3 +
                        water_normalized * 0.2
                    )
                    
                    combined_scores.append((region, combined_score))
                
                sorted_combined = sorted(combined_scores, key=lambda x: x[1])
                metric_rankings[metric] = [{
                    "region": region,
                    "value": score,
                    "unit": "score"
                } for region, score in sorted_combined]
        
        # Find potential savings
        best_cost_region = metric_rankings["cost"][0]["region"]
        best_carbon_region = metric_rankings["carbon"][0]["region"]
        best_water_region = metric_rankings["water"][0]["region"]
        best_combined_region = metric_rankings["combined"][0]["region"]
        
        # Calculate savings for each metric
        savings = {
            "cost": {
                "best_region": best_cost_region,
                "savings_percentage": self._calculate_savings_percentage(
                    region_results, "cost", best_cost_region
                )
            },
            "carbon": {
                "best_region": best_carbon_region,
                "savings_percentage": self._calculate_savings_percentage(
                    region_results, "carbon", best_carbon_region
                )
            },
            "water": {
                "best_region": best_water_region,
                "savings_percentage": self._calculate_savings_percentage(
                    region_results, "water", best_water_region
                )
            },
            "combined": {
                "best_region": best_combined_region,
                "savings_percentage": {}
            }
        }
        
        return {
            "rankings": metric_rankings,
            "savings": savings,
            "region_data": region_results
        }
    
    def _calculate_savings_percentage(
        self, region_results: Dict[str, Any], metric: str, best_region: str
    ) -> Dict[str, float]:
        """Calculate savings percentage compared to each region"""
        savings = {}
        best_value = None
        
        if metric == "cost":
            best_value = region_results[best_region].cost.monthly_cost
            for region, data in region_results.items():
                if region != best_region:
                    current_value = data.cost.monthly_cost
                    savings[region] = ((current_value - best_value) / current_value) * 100
        
        elif metric == "carbon":
            best_value = region_results[best_region].environment.carbon_footprint_grams
            for region, data in region_results.items():
                if region != best_region:
                    current_value = data.environment.carbon_footprint_grams
                    savings[region] = ((current_value - best_value) / current_value) * 100
        
        elif metric == "water":
            best_value = region_results[best_region].environment.water_usage_liters
            for region, data in region_results.items():
                if region != best_region:
                    current_value = data.environment.water_usage_liters
                    savings[region] = ((current_value - best_value) / current_value) * 100
        
        return savings
    
    def find_optimal_region(
        self,
        service_type: str,
        resource_id: str,
        usage_data: Dict[str, Any],
        priority: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Find the optimal region based on different priorities
        
        Args:
            service_type: Type of AWS service
            resource_id: Resource identifier
            usage_data: Usage metrics for the resource
            priority: Priority for optimization (cost, carbon, water, balanced)
            
        Returns:
            Dictionary with optimal region information
        """
        from ..config import AWS_REGIONS
        
        # Use subset of regions for better performance
        regions_to_check = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1", "eu-north-1",
            "ap-northeast-1", "ap-southeast-1", "ap-southeast-2",
            "ca-central-1"
        ]
        
        # Compare regions
        comparison = self.compare_regions(
            service_type, resource_id, regions_to_check, usage_data
        )
        
        # Select optimal region based on priority
        if priority == "cost":
            optimal_region = comparison["rankings"]["cost"][0]["region"]
            metric_value = comparison["rankings"]["cost"][0]["value"]
            unit = comparison["rankings"]["cost"][0]["unit"]
            metric_name = "Monthly Cost"
        elif priority == "carbon":
            optimal_region = comparison["rankings"]["carbon"][0]["region"]
            metric_value = comparison["rankings"]["carbon"][0]["value"]
            unit = comparison["rankings"]["carbon"][0]["unit"]
            metric_name = "Carbon Footprint"
        elif priority == "water":
            optimal_region = comparison["rankings"]["water"][0]["region"]
            metric_value = comparison["rankings"]["water"][0]["value"]
            unit = comparison["rankings"]["water"][0]["unit"]
            metric_name = "Water Usage"
        else:  # balanced
            optimal_region = comparison["rankings"]["combined"][0]["region"]
            metric_value = comparison["rankings"]["combined"][0]["value"]
            unit = comparison["rankings"]["combined"][0]["unit"]
            metric_name = "Combined Score"
        
        return {
            "optimal_region": optimal_region,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "unit": unit,
            "comparison": comparison
        } 
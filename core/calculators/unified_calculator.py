from typing import Dict, Any, List, Optional

from ..base.calculator_base import BaseCalculator
from ..models.metrics import UnifiedMetrics, CostMetrics, EnvironmentalMetrics
from .scope3_calculator import Scope3Calculator
from .cloud_calculator import CloudCostCalculator

class UnifiedCalculator:
    """
    Unified calculator that combines cost and environmental impact metrics
    for both cloud and AI services.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize with all component calculators"""
        self.data_dir = data_dir
        self.environmental_calculator = Scope3Calculator(data_dir)
        self.cost_calculator = CloudCostCalculator(data_dir)
        
    def calculate_metrics(
        self, service_type: str, resource_id: str, region: str, 
        usage_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate all metrics (cost and environmental impact) for a resource.
        
        Args:
            service_type: Type of AWS service
            resource_id: Resource identifier
            region: AWS region
            usage_data: Usage metrics for the resource
            
        Returns:
            Dictionary with combined metrics
        """
        service_type_lower = service_type.lower()
        
        # Calculate cost metrics
        cost_results = self.cost_calculator.calculate(
            service_type, resource_id, region, usage_data
        )
        
        # Calculate environmental metrics
        env_results = self.environmental_calculator.calculate(
            service_type, resource_id, region, usage_data
        )
        
        cost_metrics = cost_results.get("cost_metrics")
        env_metrics = env_results.get("environmental_metrics")
        equivalents = env_results.get("equivalents", {})
        
        # Calculate optimization options
        optimization_options = self._calculate_optimization_options(
            service_type, resource_id, region, usage_data,
            cost_metrics, env_metrics
        )
        
        # Create unified metrics object
        usage_period_days = usage_data.get('days', 30)
        unified_metrics = UnifiedMetrics(
            service_type=service_type,
            resource_id=resource_id,
            region=region,
            usage_period_days=usage_period_days,
            cost=cost_metrics,
            environment=env_metrics,
            equivalents=equivalents,
            optimization_options=optimization_options
        )
        
        return {
            "unified_metrics": unified_metrics,
            "additional_metrics": {}
        }
    
    def _calculate_optimization_options(
        self, service_type: str, resource_id: str, region: str,
        usage_data: Dict[str, Any], cost_metrics: CostMetrics,
        env_metrics: EnvironmentalMetrics
    ) -> Dict[str, Any]:
        """Calculate potential optimization options"""
        options = {}
        
        # Check for lower-cost regions
        options["lower_cost_regions"] = self._find_lower_cost_regions(
            service_type, resource_id, region, usage_data
        )
        
        # Check for lower-carbon regions
        options["lower_carbon_regions"] = self._find_lower_carbon_regions(
            service_type, resource_id, region, usage_data
        )
        
        # Check for right-sizing opportunities (EC2)
        if 'ec2' in service_type.lower():
            options["rightsizing_options"] = self._find_rightsizing_options(
                resource_id, usage_data
            )
        
        # Check for reserved instance or savings plan opportunities
        if hasattr(cost_metrics, "on_demand_cost") and hasattr(cost_metrics, "reserved_cost") and cost_metrics.reserved_cost:
            potential_savings = cost_metrics.on_demand_cost - cost_metrics.reserved_cost
            if potential_savings > 0:
                options["commitment_discounts"] = {
                    "potential_savings": potential_savings,
                    "percentage": (potential_savings / cost_metrics.on_demand_cost) * 100,
                    "recommendations": ["Reserved Instances", "Savings Plans"]
                }
        
        return options
    
    def _find_lower_cost_regions(
        self, service_type: str, resource_id: str, current_region: str,
        usage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find regions with lower costs for the same workload"""
        from ..config import AWS_REGIONS
        
        # Sample list of regions to check (limited for performance)
        regions_to_check = [
            "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ca-central-1"
        ]
        
        # Filter out current region
        regions_to_check = [r for r in regions_to_check if r != current_region]
        
        results = []
        current_cost = self.cost_calculator.calculate(
            service_type, resource_id, current_region, usage_data
        ).get("cost_metrics").monthly_cost
        
        for region in regions_to_check:
            # Calculate cost in this region
            cost_results = self.cost_calculator.calculate(
                service_type, resource_id, region, usage_data
            )
            region_cost = cost_results.get("cost_metrics").monthly_cost
            
            # If cost is lower, add to results
            if region_cost < current_cost:
                savings = current_cost - region_cost
                savings_percent = (savings / current_cost) * 100
                
                results.append({
                    "region": region,
                    "cost": region_cost,
                    "savings": savings,
                    "savings_percent": savings_percent
                })
        
        # Sort by savings (highest first)
        results.sort(key=lambda x: x["savings"], reverse=True)
        
        return results
    
    def _find_lower_carbon_regions(
        self, service_type: str, resource_id: str, current_region: str,
        usage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find regions with lower carbon emissions for the same workload"""
        from ..config import AWS_REGIONS
        
        # Sample list of regions to check (limited for performance)
        regions_to_check = [
            "us-west-2", "us-east-2", "eu-west-1", "eu-north-1", "ca-central-1"
        ]
        
        # Filter out current region
        regions_to_check = [r for r in regions_to_check if r != current_region]
        
        results = []
        current_emissions = self.environmental_calculator.calculate(
            service_type, resource_id, current_region, usage_data
        ).get("environmental_metrics").carbon_footprint_grams
        
        for region in regions_to_check:
            # Calculate emissions in this region
            env_results = self.environmental_calculator.calculate(
                service_type, resource_id, region, usage_data
            )
            region_emissions = env_results.get("environmental_metrics").carbon_footprint_grams
            
            # If emissions are lower, add to results
            if region_emissions < current_emissions:
                savings = current_emissions - region_emissions
                savings_percent = (savings / current_emissions) * 100
                
                results.append({
                    "region": region,
                    "emissions": region_emissions,
                    "savings": savings,
                    "savings_percent": savings_percent
                })
        
        # Sort by savings (highest first)
        results.sort(key=lambda x: x["savings"], reverse=True)
        
        return results
    
    def _find_rightsizing_options(
        self, instance_type: str, usage_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find rightsizing options for EC2 instances"""
        # Define instance families and their sizing options
        instance_families = {
            't3': ['t3.nano', 't3.micro', 't3.small', 't3.medium', 't3.large', 't3.xlarge'],
            'm5': ['m5.large', 'm5.xlarge', 'm5.2xlarge', 'm5.4xlarge'],
            'c5': ['c5.large', 'c5.xlarge', 'c5.2xlarge', 'c5.4xlarge'],
            'r5': ['r5.large', 'r5.xlarge', 'r5.2xlarge', 'r5.4xlarge']
        }
        
        # Get instance family
        family = None
        for f in instance_families:
            if instance_type.startswith(f):
                family = f
                break
        
        if not family:
            return []
        
        # Get current size index
        current_size_index = -1
        for i, size in enumerate(instance_families[family]):
            if size == instance_type:
                current_size_index = i
                break
        
        if current_size_index == -1:
            return []
        
        # For simplicity, suggest one size down if available
        options = []
        if current_size_index > 0:
            smaller_instance = instance_families[family][current_size_index - 1]
            
            # Calculate savings
            hours = usage_data.get('hours', 720)
            current_cost = self.cost_calculator.calculate(
                'EC2', instance_type, 'us-east-1', usage_data
            ).get("cost_metrics").monthly_cost
            
            smaller_usage_data = usage_data.copy()
            smaller_cost = self.cost_calculator.calculate(
                'EC2', smaller_instance, 'us-east-1', smaller_usage_data
            ).get("cost_metrics").monthly_cost
            
            savings = current_cost - smaller_cost
            savings_percent = (savings / current_cost) * 100
            
            options.append({
                "instance_type": smaller_instance,
                "savings": savings,
                "savings_percent": savings_percent,
                "recommendation": f"Consider downsizing from {instance_type} to {smaller_instance} for potential savings of ${savings:.2f} per month."
            })
        
        return options 
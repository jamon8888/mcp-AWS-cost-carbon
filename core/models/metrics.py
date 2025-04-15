from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class CostMetrics:
    """Cost metrics for AWS resources"""
    hourly_cost: float
    monthly_cost: float
    on_demand_cost: float
    reserved_cost: Optional[float] = None
    savings_plan_cost: Optional[float] = None
    
@dataclass
class EnvironmentalMetrics:
    """Environmental impact metrics"""
    carbon_footprint_grams: float  # gCO2e
    energy_kwh: float              # kilowatt-hours
    water_usage_liters: float      # liters
    water_stress_level: str        # Low, Medium, High, Very High
    embodied_emissions_grams: Optional[float] = None  # gCO2e
    
@dataclass
class UnifiedMetrics:
    """Combined metrics for comprehensive resource analysis"""
    service_type: str
    resource_id: str
    region: str
    usage_period_days: int
    cost: CostMetrics
    environment: EnvironmentalMetrics
    equivalents: Dict[str, float]  # Environmental equivalents
    optimization_options: Dict[str, Any]  # Potential optimizations 
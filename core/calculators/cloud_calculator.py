from typing import Dict, Any, Optional

from ..base.calculator_base import BaseCalculator
from ..models.metrics import CostMetrics

class CloudCostCalculator(BaseCalculator):
    """Calculate cost metrics for AWS cloud services"""
    
    def __init__(self, data_dir: str = "data"):
        super().__init__(data_dir)
        # Initialize pricing data
        self._load_pricing_data()
    
    def _load_pricing_data(self):
        """Load AWS pricing data"""
        # Simplified pricing data - would typically come from AWS Price List API
        self.ec2_pricing = {
            't3.micro': 0.0104,  # per hour
            't3.small': 0.0208,  # per hour
            't3.medium': 0.0416,  # per hour
            'm5.large': 0.096,   # per hour
            'c5.large': 0.085,   # per hour
            'r5.large': 0.126,   # per hour
            'p3.2xlarge': 3.06,  # per hour
            'default': 0.05      # default price
        }
        
        self.lambda_pricing = {
            'request_cost': 0.20,  # per million requests
            'compute_cost': 0.0000166667  # per GB-second
        }
        
        self.s3_pricing = {
            'storage': 0.023,  # per GB per month
            'get_request': 0.0004,  # per 1000 requests
            'put_request': 0.005   # per 1000 requests
        }
        
        self.bedrock_pricing = {
            'anthropic.claude-3-opus-20240229-v1:0': {
                'input': 0.00150, 'output': 0.00750
            },
            'anthropic.claude-3-sonnet-20240229-v1:0': {
                'input': 0.00080, 'output': 0.00240
            },
            'anthropic.claude-3-haiku-20240307-v1:0': {
                'input': 0.00025, 'output': 0.00125
            },
            'default': {
                'input': 0.0005, 'output': 0.0015
            }
        }
        
        # Add more pricing data as needed
    
    def calculate(self, service_type: str, resource_id: str, 
                 region: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate cost metrics for a resource
        
        Args:
            service_type: Type of AWS service (EC2, Lambda, S3, etc.)
            resource_id: Resource identifier (instance type, function name, etc.)
            region: AWS region
            usage_data: Usage metrics for the resource
            
        Returns:
            Dictionary with cost metrics
        """
        service_type = service_type.lower()
        
        if 'ec2' in service_type or 'compute' in service_type:
            cost = self._calculate_ec2_cost(resource_id, usage_data)
        elif 'lambda' in service_type:
            cost = self._calculate_lambda_cost(usage_data)
        elif 's3' in service_type or 'storage' in service_type:
            cost = self._calculate_s3_cost(usage_data)
        elif 'bedrock' in service_type or 'ai' in service_type:
            cost = self._calculate_bedrock_cost(resource_id, usage_data)
        # Add more service types as needed
        else:
            # Default calculation
            cost = self._calculate_default_cost(usage_data)
        
        return {"cost_metrics": cost}
    
    def _calculate_ec2_cost(self, instance_type: str, usage_data: Dict[str, Any]) -> CostMetrics:
        """Calculate EC2 instance cost"""
        hours = usage_data.get('hours', 720)  # Default to monthly hours
        hourly_rate = self.ec2_pricing.get(instance_type, self.ec2_pricing['default'])
        
        hourly_cost = hourly_rate
        monthly_cost = hourly_rate * hours
        
        # Calculate reserved instance cost (simplified)
        reserved_cost = monthly_cost * 0.6  # Assume 40% savings
        savings_plan_cost = monthly_cost * 0.7  # Assume 30% savings
        
        return CostMetrics(
            hourly_cost=hourly_cost,
            monthly_cost=monthly_cost,
            on_demand_cost=monthly_cost,
            reserved_cost=reserved_cost,
            savings_plan_cost=savings_plan_cost
        )
    
    def _calculate_lambda_cost(self, usage_data: Dict[str, Any]) -> CostMetrics:
        """Calculate Lambda function cost"""
        gb_seconds = usage_data.get('gb_seconds', 100000)
        requests = usage_data.get('requests', 1000000)
        
        # Calculate request cost and compute cost
        request_cost = (requests / 1000000) * self.lambda_pricing['request_cost']
        compute_cost = gb_seconds * self.lambda_pricing['compute_cost']
        
        # Total cost
        total_cost = request_cost + compute_cost
        
        return CostMetrics(
            hourly_cost=total_cost / 720,  # Approximate hourly cost
            monthly_cost=total_cost,
            on_demand_cost=total_cost,
            reserved_cost=None,  # No reserved pricing for Lambda
            savings_plan_cost=total_cost * 0.85  # Approximate savings with Compute Savings Plan
        )
    
    def _calculate_s3_cost(self, usage_data: Dict[str, Any]) -> CostMetrics:
        """Calculate S3 storage cost"""
        storage_gb = usage_data.get('storage_gb', 100)
        get_requests = usage_data.get('get_requests', 100000)
        put_requests = usage_data.get('put_requests', 10000)
        
        # Calculate storage cost and request costs
        storage_cost = storage_gb * self.s3_pricing['storage']
        get_cost = (get_requests / 1000) * self.s3_pricing['get_request']
        put_cost = (put_requests / 1000) * self.s3_pricing['put_request']
        
        # Total cost
        total_cost = storage_cost + get_cost + put_cost
        
        return CostMetrics(
            hourly_cost=total_cost / 720,  # Approximate hourly cost
            monthly_cost=total_cost,
            on_demand_cost=total_cost,
            reserved_cost=None,  # No reserved pricing for S3
            savings_plan_cost=None  # No savings plans for S3
        )
    
    def _calculate_bedrock_cost(self, model_id: str, usage_data: Dict[str, Any]) -> CostMetrics:
        """Calculate Bedrock model cost"""
        input_tokens = usage_data.get('input_tokens', 0)
        output_tokens = usage_data.get('output_tokens', 0)
        
        # Get pricing for this model
        model_pricing = self.bedrock_pricing.get(model_id, self.bedrock_pricing['default'])
        
        # Calculate costs
        input_cost = (input_tokens / 1000) * model_pricing['input']
        output_cost = (output_tokens / 1000) * model_pricing['output']
        
        # Total cost
        total_cost = input_cost + output_cost
        
        # Estimate monthly cost (assuming daily usage for 30 days)
        monthly_cost = total_cost * 30
        
        return CostMetrics(
            hourly_cost=total_cost,  # For token-based services, this is per request
            monthly_cost=monthly_cost,
            on_demand_cost=total_cost,
            reserved_cost=None,  # No reserved pricing for Bedrock
            savings_plan_cost=None  # No savings plans for Bedrock
        )
    
    def _calculate_default_cost(self, usage_data: Dict[str, Any]) -> CostMetrics:
        """Calculate default cost for unknown services"""
        # For unknown services, provide a basic estimate
        hours = usage_data.get('hours', 720)  # Default to monthly hours
        hourly_rate = 0.05  # Default hourly rate
        
        monthly_cost = hourly_rate * hours
        
        return CostMetrics(
            hourly_cost=hourly_rate,
            monthly_cost=monthly_cost,
            on_demand_cost=monthly_cost,
            reserved_cost=None,
            savings_plan_cost=None
        ) 
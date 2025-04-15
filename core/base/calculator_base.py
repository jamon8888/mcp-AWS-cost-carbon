from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseCalculator(ABC):
    """Base interface for all metric calculators"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
    
    @abstractmethod
    def calculate(self, service_type: str, resource_id: str, 
                 region: str, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate metrics for a resource
        
        Args:
            service_type: Type of AWS service
            resource_id: Resource identifier 
            region: AWS region
            usage_data: Usage metrics for the resource
            
        Returns:
            Dictionary with calculated metrics
        """
        pass 
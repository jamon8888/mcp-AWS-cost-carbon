"""
AWS Cost Explorer MCP Server - Core Module
------------------------------------------
Core functionality for the AWS Cost Explorer MCP Server including calculators, 
data providers, models, and tools for analyzing AWS cloud costs and environmental impact.
"""

import os
import logging
from .config import LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"]
)

# Import main calculators for easy access
from core.aws_environmental_calculator import AWSEnvironmentalCalculator
from core.calculators.scope3_calculator import Scope3Calculator

# Version information
__version__ = '1.0.0'

# Ensure data directory exists
def ensure_data_dir():
    """Create data directory if it doesn't exist"""
    from .config import DEFAULT_DATA_DIR
    
    if not os.path.exists(DEFAULT_DATA_DIR):
        try:
            os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
            logging.info(f"Created data directory at {DEFAULT_DATA_DIR}")
        except Exception as e:
            logging.error(f"Failed to create data directory: {str(e)}")

# Initialize on import
ensure_data_dir()
